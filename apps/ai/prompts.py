import re

# OPTIONAL: later replace with OpenAI / local LLM
def ai_classify_room(raw_name: str, area: float) -> str:
    """
    AI-assisted room classification (safe fallback version)
    """

    text = raw_name.upper().strip()

    # HARD RULES (FAST & FREE)
    if "BED" in text:
        return "Bedroom"

    if "TOILET" in text or "BATH" in text or "WC" in text:
        return "Bathroom"

    if "KITCHEN" in text:
        return "Kitchen"

    if "LIVING" in text or "LOUNGE" in text:
        return "Living Room"

    if "DINING" in text:
        return "Dining Room"

    if "SERVANT" in text:
        return "Servant Room"

    if "STORE" in text:
        return "Store Room"

    if "BALCONY" in text:
        return "Balcony"

    # AREA-BASED AI HEURISTIC
    if area > 12:
        return "Living Room"

    if area > 9:
        return "Bedroom"

    if area > 4:
        return "Kitchen"

    return "Other"
