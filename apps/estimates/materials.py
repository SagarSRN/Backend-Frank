# apps/estimates/materials.py

MATERIAL_RULES = {
    "Bedroom": {
        "cement_bags_per_sqm": 0.4,
        "sand_tons_per_sqm": 0.05,
        "paint_sqm_ratio": 3.5,
        "tiles_ratio": 1.0,
    },
    "Kitchen": {
        "cement_bags_per_sqm": 0.5,
        "sand_tons_per_sqm": 0.06,
        "paint_sqm_ratio": 3.0,
        "tiles_ratio": 1.2,
    },
    "Toilet": {
        "cement_bags_per_sqm": 0.6,
        "sand_tons_per_sqm": 0.07,
        "paint_sqm_ratio": 2.8,
        "tiles_ratio": 1.5,
    },
    "Living Room": {
        "cement_bags_per_sqm": 0.35,
        "sand_tons_per_sqm": 0.04,
        "paint_sqm_ratio": 4.0,
        "tiles_ratio": 1.0,
    },
    "Other": {
        "cement_bags_per_sqm": 0.3,
        "sand_tons_per_sqm": 0.04,
        "paint_sqm_ratio": 3.0,
        "tiles_ratio": 1.0,
    }
}


def calculate_materials(rooms):
    data = {
        "cement_bags": 0,
        "sand_tons": 0,
        "total_paint_sqm": 0,
        "total_tiles_sqm": 0,
    }

    for room in rooms:
        rule = MATERIAL_RULES.get(room.room_type, MATERIAL_RULES["Other"])
        area = room.area

        data["cement_bags"] += area * rule["cement_bags_per_sqm"]
        data["sand_tons"] += area * rule["sand_tons_per_sqm"]
        data["total_paint_sqm"] += area * rule["paint_sqm_ratio"]
        data["total_tiles_sqm"] += area * rule["tiles_ratio"]

    # rounding
    data["cement_bags"] = round(data["cement_bags"])
    data["sand_tons"] = round(data["sand_tons"], 2)
    data["total_paint_sqm"] = round(data["total_paint_sqm"], 2)
    data["total_tiles_sqm"] = round(data["total_tiles_sqm"], 2)

    return data
