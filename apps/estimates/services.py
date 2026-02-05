from apps.rooms.models import Room
from .models import Estimate, RoomEstimate


def generate_estimate(project_id):
    rooms = Room.objects.filter(project_id=project_id)

    if not rooms.exists():
        print("⚠️ No rooms found, skipping estimate")
        return None

    # 🔥 Clean old estimates (safe re-generate)
    RoomEstimate.objects.filter(project_id=project_id).delete()

    total_tiles = 0
    total_paint = 0
    total_cement = 0
    total_sand = 0
    total_cost = 0

    for room in rooms:
        floor_area = room.area
        wall_area = floor_area * 3  # approx rule

        tiles_sqm = floor_area
        paint_sqm = wall_area
        cement_bags = int(wall_area * 0.2)
        sand_tons = round(cement_bags * 0.035, 2)

        cost = (
            tiles_sqm * 1200 +
            paint_sqm * 15 +
            cement_bags * 420 +
            sand_tons * 1400
        )

        RoomEstimate.objects.create(
            project_id=project_id,
            room=room,
            tiles_sqm=round(tiles_sqm, 2),
            paint_sqm=round(paint_sqm, 2),
            cement_bags=cement_bags,
            sand_tons=sand_tons,
            cost=round(cost, 2)
        )

        total_tiles += tiles_sqm
        total_paint += paint_sqm
        total_cement += cement_bags
        total_sand += sand_tons
        total_cost += cost

    # 🔁 Update / Create project-level estimate
    estimate, _ = Estimate.objects.update_or_create(
        project_id=project_id,
        defaults={
            "total_tiles_sqm": round(total_tiles, 2),
            "total_paint_sqm": round(total_paint, 2),
            "cement_bags": total_cement,
            "sand_tons": round(total_sand, 2),
            "total_cost": round(total_cost, 2),
        }
    )

    return estimate
