def classify_room(area):
    if area < 6:
        return "Toilet"
    elif area < 12:
        return "Kitchen"
    elif area < 20:
        return "Bedroom"
    else:
        return "Hall"
