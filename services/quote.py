from opentelemetry.trace import get_tracer
from datetime import datetime

tracer = get_tracer(__name__)

quote_agent = {
    "type": "function",
    "function": {
        "name": "quote",
        "description": "Devis pour un plan d'assurance habitation ou voiture",
    }
}

@tracer.start_as_current_span(name="devis")
def quote(user_id, messages):
    f"""
    Devis pour un plan d'assurance habitation ou voiture

    Args:
        userId (str): L'identifiant de l'utilisateur
        type (str): Le type d'assurance, les valeurs peuvent être "voiture" ou "habitation"
        date_debut (str): La date de début de l'assurance au format JJ-MM-AAAA. Spécifiez la date du jour ${ datetime.now().strftime("%d-%m-%Y") } pour un début immédiat.

    Returns:
        dict: 
    """

    return "This will be 100€"
