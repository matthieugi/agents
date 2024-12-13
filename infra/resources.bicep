@description('The location used for all deployed resources')
param location string = resourceGroup().location

@description('Tags that will be applied to all resources')
param tags object = {}


param agentsExists bool
@secure()
param agentsDefinition object

@description('Id of the user or app to assign application roles')
param principalId string

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = uniqueString(subscription().id, resourceGroup().id, location)

// Monitor application with Azure Monitor
module monitoring 'br/public:avm/ptn/azd/monitoring:0.1.0' = {
  name: 'monitoring'
  params: {
    logAnalyticsName: '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
    applicationInsightsName: '${abbrs.insightsComponents}${resourceToken}'
    applicationInsightsDashboardName: '${abbrs.portalDashboards}${resourceToken}'
    location: location
    tags: tags
  }
}

// Container registry
module containerRegistry 'br/public:avm/res/container-registry/registry:0.1.1' = {
  name: 'registry'
  params: {
    name: '${abbrs.containerRegistryRegistries}${resourceToken}'
    location: location
    acrAdminUserEnabled: true
    tags: tags
    publicNetworkAccess: 'Enabled'
    roleAssignments:[
      {
        principalId: agentsIdentity.outputs.principalId
        principalType: 'ServicePrincipal'
        roleDefinitionIdOrName: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
      }
    ]
  }
}

// Container apps environment
module containerAppsEnvironment 'br/public:avm/res/app/managed-environment:0.4.5' = {
  name: 'container-apps-environment'
  params: {
    logAnalyticsWorkspaceResourceId: monitoring.outputs.logAnalyticsWorkspaceResourceId
    name: '${abbrs.appManagedEnvironments}${resourceToken}'
    location: location
    zoneRedundant: false
  }
}

module agentsIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.2.1' = {
  name: 'agentsidentity'
  params: {
    name: '${abbrs.managedIdentityUserAssignedIdentities}agents-${resourceToken}'
    location: location
  }
}

module agentsFetchLatestImage './modules/fetch-container-image.bicep' = {
  name: 'agents-fetch-image'
  params: {
    exists: agentsExists
    name: 'agents'
  }
}

var agentsAppSettingsArray = filter(array(agentsDefinition.settings), i => i.name != '')
var agentsSecrets = map(filter(agentsAppSettingsArray, i => i.?secret != null), i => {
  name: i.name
  value: i.value
  secretRef: i.?secretRef ?? take(replace(replace(toLower(i.name), '_', '-'), '.', '-'), 32)
})
var agentsEnv = map(filter(agentsAppSettingsArray, i => i.?secret == null), i => {
  name: i.name
  value: i.value
})

module agents 'br/public:avm/res/app/container-app:0.8.0' = {
  name: 'agents'
  params: {
    name: 'agents'
    ingressTargetPort: 5000
    scaleMinReplicas: 1
    scaleMaxReplicas: 10
    secrets: {
      secureList:  union([
      ],
      map(agentsSecrets, secret => {
        name: secret.secretRef
        value: secret.value
      }))
    }
    containers: [
      {
        image: agentsFetchLatestImage.outputs.?containers[?0].?image ?? 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
        name: 'main'
        resources: {
          cpu: json('0.5')
          memory: '1.0Gi'
        }
        env: union([
          {
            name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
            value: monitoring.outputs.applicationInsightsConnectionString
          }
          {
            name: 'AZURE_CLIENT_ID'
            value: agentsIdentity.outputs.clientId
          }
          {
            name: 'PORT'
            value: '5000'
          }
          {
            name: 'AZURE_OPENAI_ENDPOINT'
            value: ''
          }
          {
            name: 'AZURE_OPENAI_KEY'
            value: ''
          }
          {
            name: 'AZURE_OPENAI_DEPLOYMENT'
            value: 'gpt-4o'
          }
          {
            name: 'AZURE_OPENAI_API_VERSION'
            value: '2024-08-01-preview'
          }
          {
            name: 'AZURE_SEARCH_ENDPOINT'
            value: 'https://gptkb-3l4bl64pwg4zy.search.windows.net'
          }
          {
            name: 'AZURE_SEARCH_KEY'
            value: ''
          }
          {
            name: 'AZURE_SEARCH_INDEX'
            value: 'voicerag-intvect'
          }
          {
            name: 'AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED'
            value: 'true'
          }
          {
            name: 'AZURE_SDK_TRACING_IMPLEMENTATION'
            value: 'opentelemetry'
          }
          {
            name: 'AZURE_PROJECT_CONNECTION_STRING'
            value: 'swedencentral.api.azureml.ms;ac9decd5-c5b4-40dd-b637-1b0294837f8f;flights;flights'
          }
          {
            name: 'AZURE_SUBSCRIPTION_ID'
            value: 'ac9decd5-c5b4-40dd-b637-1b0294837f8f'
          }
          {
            name: 'AZURE_RESOURCE_GROUP'
            value: 'flights'
          }
          {
            name: 'AZURE_PROJECT_NAME'
            value: 'flights'
          }
        ],
        agentsEnv,
        map(agentsSecrets, secret => {
            name: secret.name
            secretRef: secret.secretRef
        }))
      }
    ]
    managedIdentities:{
      systemAssigned: true
      userAssignedResourceIds: [agentsIdentity.outputs.resourceId]
    }
    registries:[
      {
        server: containerRegistry.outputs.loginServer
        identity: agentsIdentity.outputs.resourceId
      }
    ]
    environmentResourceId: containerAppsEnvironment.outputs.resourceId
    location: location
    tags: union(tags, { 'azd-service-name': 'agents' })
  }
}
// Create a keyvault to store secrets
module keyVault 'br/public:avm/res/key-vault/vault:0.6.1' = {
  name: 'keyvault'
  params: {
    name: '${abbrs.keyVaultVaults}${resourceToken}'
    location: location
    tags: tags
    enableRbacAuthorization: false
    accessPolicies: [
      {
        objectId: principalId
        permissions: {
          secrets: [ 'get', 'list' ]
        }
      }
      {
        objectId: agentsIdentity.outputs.principalId
        permissions: {
          secrets: [ 'get', 'list' ]
        }
      }
    ]
    secrets: [
    ]
  }
}
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.outputs.loginServer
output AZURE_KEY_VAULT_ENDPOINT string = keyVault.outputs.uri
output AZURE_KEY_VAULT_NAME string = keyVault.outputs.name
output AZURE_RESOURCE_AGENTS_ID string = agents.outputs.resourceId
