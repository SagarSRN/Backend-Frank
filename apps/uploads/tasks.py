"""
FINAL FIXED Tasks.py - Component model has rate and amount as @property
Location: apps/uploads/tasks.py

BOTH rate and amount are calculated properties - can't be set!
"""
from decimal import Decimal

from .models import PlanUpload
from apps.projects.models import Project
from apps.rooms.models import Room
from apps.rooms.services import classify_room
from apps.estimates.services_enhanced import generate_detailed_estimate

from apps.retail_materials.models import Material, Component, RetailEstimate
from apps.retail_materials.dxf_processor import analyze_retail_display_dxf


def process_dxf_upload(upload_id):
    """
    Process DXF upload - handles BOTH residential and retail projects
    """
    print("\n" + "=" * 80)
    print("🚀 DXF TASK STARTED")
    print("=" * 80)

    upload = PlanUpload.objects.get(id=upload_id)
    project = upload.project

    print(f"📦 Project: {project.name}")
    print(f"🏷️  Type: {project.get_project_type_display()}")

    # Route to appropriate processor based on project type
    if project.is_residential:
        process_residential_dxf(upload)
    elif project.is_retail:
        process_retail_dxf(upload)
    else:
        print(f"⚠️ Unknown project type: {project.project_type}")

    upload.processed = True
    upload.save()

    print("✅ Processing complete!")
    print("=" * 80 + "\n")


# ============================================================================
# RESIDENTIAL PROCESSOR
# ============================================================================

def process_residential_dxf(upload):
    """
    Process residential floor plan DXF
    """
    from .dxf_processor import detect_rooms_from_dxf

    project = upload.project

    print("🏠 Processing RESIDENTIAL project...")

    # Detect rooms from DXF
    rooms_data = detect_rooms_from_dxf(
        upload.file.path,
        scale=upload.scale
    )

    print(f"🏠 Rooms detected: {len(rooms_data)}")

    # Delete old rooms
    Room.objects.filter(project=project).delete()

    # Save new rooms
    saved = 0
    for r in rooms_data:
        area = float(r["area"])
        center = r["center"]

        if area < 5:  # Skip very small rooms
            continue

        Room.objects.create(
            project=project,
            name=classify_room(r["name"]),
            area=area,
            x_center=center.x,
            y_center=center.y,
        )
        saved += 1

    print(f"✅ Rooms saved: {saved}")

    # Generate estimate if rooms were saved
    if saved > 0:
        generate_detailed_estimate(project.id)
        print("💰 Residential estimate generated")


# ============================================================================
# RETAIL PROCESSOR
# ============================================================================

def process_retail_dxf(upload):
    """
    Process retail display DXF file
    
    IMPORTANT: Component model has 'rate' and 'amount' as @property
    They are calculated automatically - DON'T set them!
    """
    project = upload.project

    print("🛍️  Processing RETAIL project...")

    # Build material mapping from layer names
    materials = Material.objects.filter(is_active=True).select_related("category")
    material_mapping = {}

    for material in materials:
        if material.dxf_layer_names:
            layer_list = [
                name.strip().upper()
                for name in material.dxf_layer_names.split(",")
            ]
            for layer_name in layer_list:
                material_mapping[layer_name] = material

    print(f"📋 Material mapping: {len(material_mapping)} layers mapped")

    try:
        # Analyze DXF file
        components_data = analyze_retail_display_dxf(
            upload.file.path,
            material_mapping=material_mapping
        )

        print(f"🔧 Components detected: {len(components_data)}")

        # Delete old components for this project
        Component.objects.filter(project=project).delete()

        # Save components to database
        saved_count = 0

        for comp in components_data:
            # Get material object
            material_obj = comp.get("material")

            # Skip if no material found
            if material_obj is None:
                print(
                    f"  ⚠️  Skipping '{comp['description']}' - no material"
                )
                continue

            # Skip fallback materials (dictionaries, not database objects)
            if isinstance(material_obj, dict):
                print(
                    f"  ⚠️  Skipping '{comp['description']}' - fallback material"
                )
                continue

            # Convert quantity to Decimal
            quantity_decimal = Decimal(str(comp["quantity"]))

            # Create component
            # CRITICAL: DON'T set 'rate' or 'amount' - they are @property!
            # They calculate automatically from material.rate and quantity
            Component.objects.create(
                project=project,
                material=material_obj,
                component_type=comp.get("type", "CUSTOM"),
                description=comp["description"],
                quantity=quantity_decimal,
                unit=comp["unit"],
                dimensions=comp.get("dimensions", {}),
                auto_detected=comp.get("auto_detected", True)
            )

            saved_count += 1

        print(f"✅ Components saved: {saved_count}")

        # Create or update retail estimate
        estimate, created = RetailEstimate.objects.get_or_create(
            project=project
        )

        # Calculate totals (this will sum up all component amounts)
        total = estimate.calculate_totals()

        print(f"💰 Retail estimate generated: ₹{total:,.2f}")

    except Exception as e:
        print(f"❌ Error processing retail DXF: {e}")
        import traceback
        print(traceback.format_exc())