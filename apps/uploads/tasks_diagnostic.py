"""
DIAGNOSTIC VERSION - Enhanced tasks.py with detailed logging
This will show EXACTLY what's happening during DXF processing
"""
from .models import PlanUpload
from .dxf_processor import detect_rooms_from_dxf

from apps.rooms.models import Room
from apps.rooms.services import classify_room
from apps.estimates.services_enhanced import generate_detailed_estimate
from apps.estimates.models import EstimateLineItem, RoomEstimate, Estimate


def process_dxf_upload(upload_id):
    """
    Process DXF upload with detailed logging
    """
    print("\n" + "="*80)
    print("🚀 DXF PROCESSING STARTED")
    print("="*80)
    print(f"📋 Upload ID: {upload_id}")

    upload = PlanUpload.objects.get(id=upload_id)
    project = upload.project
    
    print(f"\n📦 PROJECT INFORMATION:")
    print(f"   Project ID: {project.id}")
    print(f"   Project Name: {project.name}")
    print(f"   Location: {project.location}")
    
    print(f"\n📂 FILE INFORMATION:")
    print(f"   File Path: {upload.file.path}")
    print(f"   File Name: {upload.file.name}")
    print(f"   Scale: {upload.scale}")
    print(f"   Previously Processed: {upload.processed}")

    # STEP 1: Detect rooms from DXF
    print(f"\n🔍 STEP 1: ANALYZING DXF FILE...")
    
    try:
        rooms_data = detect_rooms_from_dxf(
            upload.file.path,
            scale=upload.scale
        )
        print(f"✅ DXF Analysis Complete")
        print(f"   Rooms Detected: {len(rooms_data)}")
        
        if rooms_data:
            print(f"\n📐 DETECTED ROOMS:")
            for i, r in enumerate(rooms_data, 1):
                print(f"   {i}. {r['name']}")
                print(f"      Area: {r['area']} sqm")
                print(f"      Center: ({r['center'].x:.2f}, {r['center'].y:.2f})")
        else:
            print("   ⚠️ WARNING: No rooms detected in DXF file!")
            
    except Exception as e:
        print(f"   ❌ ERROR analyzing DXF: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise

    # STEP 2: Clear old data
    print(f"\n🗑️ STEP 2: CLEARING OLD DATA...")
    
    old_rooms = Room.objects.filter(project=project)
    old_room_count = old_rooms.count()
    
    old_room_estimates = RoomEstimate.objects.filter(project=project)
    old_room_est_count = old_room_estimates.count()
    
    old_line_items = EstimateLineItem.objects.filter(estimate__project=project)
    old_line_item_count = old_line_items.count()
    
    print(f"   Deleting {old_room_count} old rooms")
    print(f"   Deleting {old_room_est_count} old room estimates")
    print(f"   Deleting {old_line_item_count} old line items")
    
    # Delete in correct order to avoid foreign key issues
    old_line_items.delete()
    old_room_estimates.delete()
    old_rooms.delete()
    
    print(f"✅ Old data cleared")

    # STEP 3: Save new rooms
    print(f"\n💾 STEP 3: SAVING NEW ROOMS...")
    
    saved = 0
    skipped = 0

    for r in rooms_data:
        area = float(r["area"])
        center = r["center"]
        
        print(f"\n   Processing: {r['name']}")
        print(f"      Area: {area} sqm")

        if area < 5:
            print(f"      ⏭️ SKIPPED (area < 5 sqm)")
            skipped += 1
            continue

        classified_name = classify_room(r["name"], area)
        
        new_room = Room.objects.create(
            project=project,
            name=classified_name,
            area=area,
            x_center=center.x,
            y_center=center.y,
        )
        
        print(f"      ✅ SAVED as: {classified_name}")
        print(f"      Database ID: {new_room.id}")
        saved += 1

    print(f"\n📊 SAVE SUMMARY:")
    print(f"   Total detected: {len(rooms_data)}")
    print(f"   Saved: {saved}")
    print(f"   Skipped: {skipped}")

    # STEP 4: Generate estimate
    print(f"\n💰 STEP 4: GENERATING ESTIMATE...")
    
    if saved > 0:
        try:
            # Get current rooms to verify
            current_rooms = Room.objects.filter(project=project)
            print(f"   Rooms in database: {current_rooms.count()}")
            
            for room in current_rooms:
                print(f"      - {room.name}: {room.area} sqm")
            
            # Generate estimate
            estimate = generate_detailed_estimate(project.id)
            
            if estimate:
                print(f"✅ Estimate generated successfully")
                print(f"   Total Cost: ₹{estimate.total_cost:,.2f}")
                print(f"   Tiles: {estimate.total_tiles_sqm} sqm")
                print(f"   Paint: {estimate.total_paint_sqm} sqm")
                
                # Count line items
                line_items = EstimateLineItem.objects.filter(estimate=estimate)
                print(f"   Line Items: {line_items.count()}")
                
                # Show category breakdown
                categories = {}
                for item in line_items:
                    categories[item.category] = categories.get(item.category, 0) + item.amount
                
                print(f"\n   💵 COST BY CATEGORY:")
                for cat, cost in categories.items():
                    print(f"      {cat}: ₹{cost:,.2f}")
            else:
                print(f"   ⚠️ Estimate generation returned None")
                
        except Exception as e:
            print(f"   ❌ ERROR generating estimate: {str(e)}")
            import traceback
            print(traceback.format_exc())
    else:
        print(f"   ⏭️ No estimate generated (no rooms saved)")

    # STEP 5: Mark as processed
    print(f"\n✅ STEP 5: FINALIZING...")
    upload.processed = True
    upload.save()
    print(f"   Upload marked as processed")

    print(f"\n" + "="*80)
    print("🏁 DXF PROCESSING COMPLETED")
    print("="*80 + "\n")
