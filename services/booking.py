from opentelemetry.trace import get_tracer

tracer = get_tracer(__name__)

@tracer.start_as_current_span(name="book_flight")
def book_flight(destination, date):
    """
    Books a flight to the specified destination on the given date.

    Args:
        destination (str): The destination where the flight is headed.
        date (str): The date of the flight in YYYY-MM-DD format.

    Returns:
        dict: A dictionary containing the status of the booking, the destination, and the date.
    """

    return {"status": "Flight booked", "destination": destination, "date": date}

book_flight_tool = {
    "type": "function",
    "function": {
        "name": "book_flight",
        "description": "Book a flight to a specified destination on a specified date.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {"type": "string"},
                "date": {"type": "string"}
            },
            "required": ["destination", "date"]
        }
    }
}