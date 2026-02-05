# apps/ai/services.py

def ai_classify_room(raw_name: str, area: float) -> str:
    """
    AI-assisted room classification (rule-based + heuristic).
    This is SAFE and does not require external AI yet.
    """

    if not raw_name:
        return "Other"

    text = raw_name.upper().strip()

    # ---- KEYWORD RULES ----
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

    # ---- AREA-BASED FALLBACK ----
    if area >= 20:
        return "Living Room"

    if area >= 10:
        return "Bedroom"

    if area >= 5:
        return "Kitchen"

    return "Other"
