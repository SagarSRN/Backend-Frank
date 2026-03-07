"""
Room classification service - CORRECTED
"""

def classify_room(room_name):
    """
    Classify room based on name only
    Returns a cleaned/standardized room name
    """
    name = room_name.upper().strip()
    
    # Map common variations to standard names
    if 'LIVING' in name or 'LOUNGE' in name or 'HALL' in name:
        return 'Living Room'
    elif 'BEDROOM' in name or 'BED ROOM' in name or 'BED' in name:
        return 'Bedroom'
    elif 'KITCHEN' in name:
        return 'Kitchen'
    elif 'BATH' in name or 'TOILET' in name or 'WC' in name:
        return 'Bathroom'
    elif 'DINING' in name or 'DINNING' in name:
        return 'Dining Room'
    elif 'STORAGE' in name or 'STORE' in name:
        return 'Storage'
    elif 'BALCONY' in name:
        return 'Balcony'
    elif 'TERRACE' in name:
        return 'Terrace'
    elif 'GARAGE' in name:
        return 'Garage'
    elif 'OFFICE' in name or 'STUDY' in name:
        return 'Office'
    elif 'UTILITY' in name or 'LAUNDRY' in name:
        return 'Utility Room'
    else:
        # Return original name if no match
        return room_name.title()