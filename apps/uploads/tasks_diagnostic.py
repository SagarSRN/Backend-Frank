from .models import PlanUpload
from .dxf_processor import detect_rooms_from_dxf

from apps.rooms.models import Room
from apps.rooms.services import classify_room
from apps.estimates.services_enhanced import generate_detailed_estimate
from apps.estimates.models import EstimateLineItem, RoomEstimate, Estimate


def process_dxf_upload(upload_id):
    """
    Process DXF upload - CORRECTED VERSION
    """
    print("\n" + "="*80)
    print("🚀 DXF TASK STARTED")
    print("="*80)

    upload = PlanUpload.objects.get(id=upload_id)
    project = upload.project

    # Detect rooms from DXF
    rooms_data = detect_rooms_from_dxf(
        upload.file.path,
        scale=upload.scale
    )

    print(f"🏠 Rooms detected: {len(rooms_data)}")

    # Delete old data
    Room.objects.filter(project=project).delete()
    RoomEstimate.objects.filter(project=project).delete()
    EstimateLineItem.objects.filter(estimate__project=project).delete()

    # Save new rooms
    saved = 0
    for r in rooms_data:
        area = float(r["area"])
        center = r["center"]

        if area < 5:  # Skip very small rooms
            continue

        Room.objects.create(
            project=project,
            name=classify_room(r["name"]),  # FIX: Only 1 argument!
            area=area,
            x_center=center.x,
            y_center=center.y,
        )
        saved += 1

    print(f"✅ Rooms saved: {saved}")

    # Generate estimate if rooms were saved
    if saved > 0:
        generate_detailed_estimate(project.id)
        print("💰 Detailed estimate generated")

    upload.processed = True
    upload.save()
    
    print("="*80 + "\n")