def detect_intent(text: str) -> str:
    text = text.lower()

    if any(w in text for w in ["ticket", "flight", "travel", "visa"]):
        return "travel"

    if any(w in text for w in ["health", "medicine", "pain"]):
        return "health"

    return "general"


def generate_ai_reply(lead) -> str:
    if lead.intent == "travel":
        if lead.destination is None:
            return "Great! May I know your travel destination?"
        if lead.travel_date is None:
            return "What is your preferred travel date?"
        if lead.passengers is None:
            return "How many passengers will be travelling?"
        return "Thank you. I will prepare the best travel options for you."

    if lead.intent == "health":
        return "Could you please describe your health concern?"

    return "How can I assist you today?"
