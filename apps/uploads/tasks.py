from .models import PlanUpload
from .dxf_processor import detect_rooms_from_dxf

from apps.rooms.models import Room
from apps.rooms.services import classify_room
from apps.estimates.services import generate_estimate


def process_dxf_upload(upload_id):
    print("🚀 DXF TASK STARTED")

    upload = PlanUpload.objects.get(id=upload_id)
    project = upload.project

    rooms_data = detect_rooms_from_dxf(
        upload.file.path,
        scale=upload.scale
    )

    print("🏠 Rooms detected:", len(rooms_data))

    # Remove old rooms
    Room.objects.filter(project=project).delete()

    saved = 0

    for r in rooms_data:
        area = float(r["area"])
        center = r["center"]

        if area < 5:
            continue

        Room.objects.create(
            project=project,
            name=classify_room(r["name"], area),
            area=area,
            x_center=center.x,
            y_center=center.y,
        )
        saved += 1

    print(f"✅ Rooms saved: {saved}")

    if saved > 0:
        generate_estimate(project.id)
        print("💰 Estimate generated")

    upload.processed = True
    upload.save()
