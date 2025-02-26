from opentelemetry.trace import get_tracer
from datetime import datetime

tracer = get_tracer(__name__)

attestation_agent = {
    "type": "function",
    "function": {
        "name": "attestation",
        "description": "Génère une attestation d'assurance pour un client existant. Les attestations peutent être pour une assurance habitation, automobile ou responsabilité civile.",
    }
}



@tracer.start_as_current_span(name="attestation")
def attestation(user_id, messages):
    f"""
    Génère une attestation d'assurance pour un client existant. Les attestations peutent être pour une assurance habitation, automobile ou responsabilité civile.
    Args:
        messages (list): La liste des messages de la conversation
    Returns:
        message (str): Le message de l'assistant


    1. Vérifier si l'utilisateur est authentifié
    2. Vérifier si l'utilisateur a une assurance valide
    3. Générer l'attestation
    """

    return {"attestation_link":"https://www.google.com"}