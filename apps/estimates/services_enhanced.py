"""
Enhanced Estimation Service - Generates detailed line items
"""

from apps.rooms.models import Room
from apps.estimates.models import Estimate, RoomEstimate, EstimateLineItem, RateCard
from datetime import date


# Default rate card if no custom rates exist
DEFAULT_RATES = {
    'Civil': {
        'Brickwork': {'rate': 550, 'unit': 'sqm'},
        'Plastering': {'rate': 180, 'unit': 'sqm'},
        'Concrete Work': {'rate': 8500, 'unit': 'cum'},
    },
    'Interior': {
        'Floor Tiling': {'rate': 1200, 'unit': 'sqm'},
        'Wall Tiling': {'rate': 900, 'unit': 'sqm'},
        'False Ceiling': {'rate': 250, 'unit': 'sqft'},
        'Woodwork': {'rate': 1500, 'unit': 'sqft'},
    },
    'Painting': {
        'Wall Painting': {'rate': 150, 'unit': 'sqm'},
        'Ceiling Painting': {'rate': 120, 'unit': 'sqm'},
    },
    'Electrical': {
        'Wiring': {'rate': 450, 'unit': 'point'},
        'Light Points': {'rate': 350, 'unit': 'nos'},
        'Switch Board': {'rate': 800, 'unit': 'nos'},
    },
    'Plumbing': {
        'Water Supply': {'rate': 350, 'unit': 'point'},
        'Drainage': {'rate': 400, 'unit': 'point'},
    },
}


def get_rate_for_item(category, item_name, location=None):
    """
    Get rate from RateCard or default rates
    """
    try:
        rate_card = RateCard.objects.filter(
            category=category,
            item_name=item_name,
            is_active=True,
            effective_from__lte=date.today()
        ).order_by('-effective_from').first()
        
        if rate_card:
            return {'rate': rate_card.rate, 'unit': rate_card.unit}
    except:
        pass
    
    # Fallback to default rates
    return DEFAULT_RATES.get(category, {}).get(item_name, {'rate': 0, 'unit': 'sqm'})


def calculate_wall_area(floor_area, room_name=''):
    """
    Estimate wall area from floor area
    """
    import math
    
    # Simplified calculation based on room type
    if 'TOILET' in room_name.upper() or 'BATHROOM' in room_name.upper():
        return floor_area * 2.5
    elif 'BEDROOM' in room_name.upper():
        return floor_area * 3.0
    elif 'LIVING' in room_name.upper() or 'HALL' in room_name.upper():
        return floor_area * 3.5
    else:
        return floor_area * 3.0


def generate_detailed_estimate(project_id):
    """
    Generate detailed estimate with line items for each work type
    """
    rooms = Room.objects.filter(project_id=project_id)

    if not rooms.exists():
        print("⚠️ No rooms found, skipping estimate")
        return None

    # Clean old estimates
    EstimateLineItem.objects.filter(estimate__project_id=project_id).delete()
    RoomEstimate.objects.filter(project_id=project_id).delete()

    # Create or get estimate
    estimate, _ = Estimate.objects.get_or_create(project_id=project_id)
    
    total_cost = 0
    line_items_data = []

    for room in rooms:
        floor_area = room.area
        wall_area = calculate_wall_area(floor_area, room.name)
        room_cost = 0

        # ============ CIVIL WORKS ============
        
        # Brickwork
        brickwork_rate = get_rate_for_item('Civil', 'Brickwork')
        brickwork_item = EstimateLineItem.objects.create(
            estimate=estimate,
            room=room,
            category='Civil',
            item_name=f'{room.name} - Brickwork',
            quantity=round(wall_area, 2),
            unit=brickwork_rate['unit'],
            rate=brickwork_rate['rate'],
        )
        room_cost += brickwork_item.amount
        line_items_data.append(brickwork_item)

        # Plastering
        plastering_rate = get_rate_for_item('Civil', 'Plastering')
        plastering_item = EstimateLineItem.objects.create(
            estimate=estimate,
            room=room,
            category='Civil',
            item_name=f'{room.name} - Wall Plastering',
            quantity=round(wall_area, 2),
            unit=plastering_rate['unit'],
            rate=plastering_rate['rate'],
        )
        room_cost += plastering_item.amount
        line_items_data.append(plastering_item)

        # ============ FLOORING ============
        
        # Floor Tiling
        tiling_rate = get_rate_for_item('Interior', 'Floor Tiling')
        tiling_item = EstimateLineItem.objects.create(
            estimate=estimate,
            room=room,
            category='Interior',
            item_name=f'{room.name} - Floor Tiling',
            quantity=round(floor_area, 2),
            unit=tiling_rate['unit'],
            rate=tiling_rate['rate'],
        )
        room_cost += tiling_item.amount
        line_items_data.append(tiling_item)

        # ============ PAINTING ============
        
        # Wall Painting
        painting_rate = get_rate_for_item('Painting', 'Wall Painting')
        painting_item = EstimateLineItem.objects.create(
            estimate=estimate,
            room=room,
            category='Painting',
            item_name=f'{room.name} - Wall Painting',
            quantity=round(wall_area, 2),
            unit=painting_rate['unit'],
            rate=painting_rate['rate'],
        )
        room_cost += painting_item.amount
        line_items_data.append(painting_item)

        # ============ ELECTRICAL ============
        
        # Light points
        light_points = max(1, int(floor_area / 10))
        light_rate = get_rate_for_item('Electrical', 'Light Points')
        light_item = EstimateLineItem.objects.create(
            estimate=estimate,
            room=room,
            category='Electrical',
            item_name=f'{room.name} - Light Points',
            quantity=light_points,
            unit=light_rate['unit'],
            rate=light_rate['rate'],
        )
        room_cost += light_item.amount
        line_items_data.append(light_item)

        # Switch boards
        switch_rate = get_rate_for_item('Electrical', 'Switch Board')
        switch_item = EstimateLineItem.objects.create(
            estimate=estimate,
            room=room,
            category='Electrical',
            item_name=f'{room.name} - Switch Boards',
            quantity=1,
            unit=switch_rate['unit'],
            rate=switch_rate['rate'],
        )
        room_cost += switch_item.amount
        line_items_data.append(switch_item)

        # ============ ROOM SUMMARY ============
        
        RoomEstimate.objects.create(
            project_id=project_id,
            room=room,
            tiles_sqm=floor_area,
            paint_sqm=wall_area,
            cement_bags=int(wall_area * 0.2),
            sand_tons=round(wall_area * 0.007, 2),
            cost=round(room_cost, 2)
        )
        
        total_cost += room_cost

    # ============ UPDATE MAIN ESTIMATE ============
    
    total_tiles = sum(item.quantity for item in line_items_data if 'Tiling' in item.item_name)
    total_paint = sum(item.quantity for item in line_items_data if 'Painting' in item.item_name)
    
    estimate.total_tiles_sqm = round(total_tiles, 2)
    estimate.total_paint_sqm = round(total_paint, 2)
    estimate.cement_bags = int(total_paint * 0.2)
    estimate.sand_tons = round(total_paint * 0.007, 2)
    estimate.total_cost = round(total_cost, 2)
    estimate.save()

    print(f"✅ Generated {len(line_items_data)} line items")
    print(f"💰 Total cost: ₹{total_cost:,.2f}")

    return estimate


def get_estimate_summary_by_category(project_id):
    """
    Get cost breakdown by category
    """
    estimate = Estimate.objects.filter(project_id=project_id).first()
    
    if not estimate:
        return {}
    
    line_items = EstimateLineItem.objects.filter(estimate=estimate)
    
    summary = {}
    for item in line_items:
        if item.category not in summary:
            summary[item.category] = 0
        summary[item.category] += item.amount
    
    return summary


def get_detailed_estimate_for_api(project_id):
    """
    Get complete estimate data for API response
    """
    from apps.projects.models import Project
    
    project = Project.objects.get(id=project_id)
    estimate = Estimate.objects.filter(project=project).first()
    
    if not estimate:
        return None
    
    line_items = EstimateLineItem.objects.filter(estimate=estimate).select_related('room')
    category_summary = get_estimate_summary_by_category(project_id)
    
    return {
        'project': {
            'id': project.id,
            'name': project.name,
            'builtup_area': project.builtup_area,
            'location': project.location,
        },
        'summary': {
            'total_cost': estimate.total_cost,
            'category_wise': category_summary,
            'gst': round(estimate.total_cost * 0.18, 2),
            'grand_total': round(estimate.total_cost * 1.18, 2),
        },
        'line_items': [
            {
                'id': item.id,
                'category': item.category,
                'item_name': item.item_name,
                'room': item.room.name if item.room else None,
                'quantity': item.quantity,
                'unit': item.unit,
                'rate': item.rate,
                'amount': item.amount,
            }
            for item in line_items
        ],
        'materials': {
            'tiles_sqm': estimate.total_tiles_sqm,
            'paint_sqm': estimate.total_paint_sqm,
            'cement_bags': estimate.cement_bags,
            'sand_tons': estimate.sand_tons,
        }
    }
