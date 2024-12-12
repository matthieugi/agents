from autogen import ConversableAgent, UserProxyAgent, GroupChat, GroupChatManager

llm_config = {
        'config_list': [{
            'model': 'gpt-4o',
            'base_url': 'https://ceos-swe.openai.azure.com/',
            'api_type': 'azure',
            'api_key': '10fac90530b3477087d056b017d1c34b',
            'api_version': '2023-12-01-preview'
        }] 
    }

routing_agent = ConversableAgent(
    name='routing_agent',
    llm_config=llm_config,
    system_message='''
        you are a helpful routing agent that classifies request and routes them to the appropriate agent
        if request concerns an attestation, route to attestation_agent
        if request concern a damage declaration, route to damage_agent''',
)

attestation_agent = ConversableAgent(
    name='attestation_agent',
    llm_config=llm_config,
    system_message='''
        you are an attestation agent that can provide attestation to users
        you can ask for the user name and call your tool to generate the attestation'''
)

def generate_attestation(user_name: str) -> str:
    return f'Attestation for {user_name}'

damage_agent = ConversableAgent(
    name='damage_agent',
    llm_config=llm_config,
    system_message='''
        you are a damage agent that can help users declare damage
        you can ask for the user name and type of damage (water, weather, car) call your tool to generate the damage declaration''',
)

def generate_damage_declaration(user_name: str, damage_type: str) -> str:
    return f'Damage declaration for {user_name} with type {damage_type}'
    
attestation_agent.register_for_llm(
    name='generate_attestation',
    description='Generate an attestation for a user'
)(generate_attestation)

damage_agent.register_for_llm(
    name='generate_damage_declaration',
    description='Generate a damage declaration for a user'
)(generate_damage_declaration)

user_proxy_agent = UserProxyAgent(
    name='user_proxy_agent',
    llm_config=llm_config,
)

user_proxy_agent.register_for_execution(name='generate_attestation')(generate_attestation)
user_proxy_agent.register_for_execution(name='generate_damage_declaration')(generate_damage_declaration)



group_chat = GroupChat(
    agents=[routing_agent, attestation_agent, damage_agent, user_proxy_agent],
    max_round=3,
    messages=[]
)

manager = GroupChatManager(group_chat=group_chat, llm_config=llm_config)
user_proxy_agent.initiate_chat(manager, message='I need an attestation')