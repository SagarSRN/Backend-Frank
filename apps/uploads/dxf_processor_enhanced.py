"""
ENHANCED DXF Processor with:
- Auto unit detection
- Multiple entity type support
- Better error handling
- Detailed logging
"""
import ezdxf
from shapely.geometry import Point, Polygon
from shapely.errors import ShapelyError
import logging
import math

logger = logging.getLogger(__name__)


def auto_detect_units(boundaries):
    """
    Auto-detect if DXF is in mm, m, or inches based on polygon areas
    """
    if not boundaries:
        return "mm", 0.000001
    
    avg_area = sum(p.area for p in boundaries) / len(boundaries)
    
    logger.info(f"Average polygon area: {avg_area}")
    
    # If average area is huge (>1,000,000), likely in mm²
    if avg_area > 1000000:
        logger.info("Detected units: millimeters (mm)")
        return "mm", 0.000001  # mm² → m²
    # If average area is reasonable (10-10000), likely in m²
    elif avg_area > 10 and avg_area < 100000:
        logger.info("Detected units: meters (m)")
        return "m", 1.0  # Already in m²
    # If tiny (<1), might be in inches or centimeters
    elif avg_area < 10:
        logger.info("Detected units: centimeters or inches")
        return "cm", 0.0001  # cm² → m²
    else:
        logger.warning(f"Unusual area detected: {avg_area}, defaulting to mm")
        return "mm", 0.000001


def extract_room_labels(doc):
    """Extract text labels from DXF file"""
    msp = doc.modelspace()
    labels = []

    for e in msp:
        try:
            if e.dxftype() in ["TEXT", "MTEXT"]:
                text = e.plain_text().strip().upper()
                if not text:
                    continue

                # Get insertion point
                if hasattr(e.dxf, 'insert'):
                    x = e.dxf.insert.x
                    y = e.dxf.insert.y
                else:
                    continue

                labels.append({
                    "name": text,
                    "point": Point(x, y)
                })
                logger.debug(f"Found label: '{text}' at ({x:.2f}, {y:.2f})")
                
        except Exception as e:
            logger.warning(f"Error processing text entity: {e}")
            continue

    logger.info(f"Found {len(labels)} text labels")
    return labels


def extract_room_boundaries(doc, min_area_threshold=1000):
    """
    Extract ALL possible room boundaries from DXF file
    Supports: LWPOLYLINE, POLYLINE, CIRCLE, RECTANGLE
    """
    msp = doc.modelspace()
    boundaries = []

    for e in msp:
        poly = None
        
        try:
            # 1. LWPOLYLINE (most common - AutoCAD rooms)
            if e.dxftype() == "LWPOLYLINE":
                if e.closed or e.is_closed:
                    pts = [(p[0], p[1]) for p in e.get_points()]
                    
                    if len(pts) >= 3:
                        poly = Polygon(pts)
                        logger.debug(f"LWPOLYLINE: {len(pts)} points, area={poly.area if poly else 0}")
            
            # 2. POLYLINE (older format)
            elif e.dxftype() == "POLYLINE":
                if e.is_closed:
                    pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
                    
                    if len(pts) >= 3:
                        poly = Polygon(pts)
                        logger.debug(f"POLYLINE: {len(pts)} points, area={poly.area if poly else 0}")
            
            # 3. CIRCLE (some plans use circles for rooms)
            elif e.dxftype() == "CIRCLE":
                center = e.dxf.center
                radius = e.dxf.radius
                
                # Create polygon approximation of circle
                pts = []
                for i in range(36):  # 36-point circle
                    angle = (i / 36.0) * 2 * math.pi
                    x = center.x + radius * math.cos(angle)
                    y = center.y + radius * math.sin(angle)
                    pts.append((x, y))
                
                poly = Polygon(pts)
                logger.debug(f"CIRCLE: radius={radius}, area={poly.area}")
            
            # 4. SPLINE (curved boundaries - convert to polygon)
            elif e.dxftype() == "SPLINE":
                # Approximate spline with line segments
                if hasattr(e, 'control_points') and len(e.control_points) >= 3:
                    pts = [(p[0], p[1]) for p in e.control_points]
                    poly = Polygon(pts)
                    logger.debug(f"SPLINE: {len(pts)} control points")
            
            # Validate polygon
            if poly:
                if not poly.is_valid:
                    logger.warning(f"Invalid polygon, attempting to fix")
                    poly = poly.buffer(0)  # Fix self-intersecting
                    
                    if not poly.is_valid:
                        continue

                # Check area threshold
                if poly.area > min_area_threshold:
                    boundaries.append(poly)
                    logger.debug(f"✓ Added boundary: area={poly.area:.2f}")
                else:
                    logger.debug(f"✗ Skipped (too small): area={poly.area:.2f}")
                    
        except (ShapelyError, AttributeError) as e:
            logger.warning(f"Error processing {e.dxftype() if hasattr(e, 'dxftype') else 'entity'}: {e}")
            continue

    logger.info(f"Found {len(boundaries)} valid boundaries")
    return boundaries


def match_rooms(doc, area_scale, min_area_threshold=1000):
    """Match room labels to boundaries"""
    labels = extract_room_labels(doc)
    boundaries = extract_room_boundaries(doc, min_area_threshold)

    if not boundaries:
        logger.warning("No boundaries found! This DXF might not have closed polylines.")
        return []

    rooms = []
    used_labels = set()

    # Try to match each boundary with a label
    for i, poly in enumerate(boundaries):
        matched = False
        best_match = None
        
        for j, label in enumerate(labels):
            if j in used_labels:
                continue
                
            # Check if label point is inside this boundary
            if poly.contains(label["point"]):
                best_match = label
                used_labels.add(j)
                matched = True
                break
        
        # Create room entry
        area_sqm = round(poly.area * area_scale, 2)
        
        if area_sqm > 0.5:  # At least 0.5 sqm
            room_name = best_match["name"] if best_match else f"ROOM_{i + 1}"
            
            rooms.append({
                "name": room_name,
                "area": area_sqm,
                "center": poly.centroid
            })
            
            logger.info(f"Room {i+1}: '{room_name}' = {area_sqm} sqm")

    logger.info(f"Matched {len(rooms)} rooms total")
    return rooms


def detect_rooms_from_dxf(file_path, scale="mm"):
    """
    Main function to detect rooms from DXF file
    With auto unit detection if scale is 'auto'
    """
    try:
        # Read DXF file
        doc = ezdxf.readfile(file_path)
        logger.info(f"✓ Opened DXF file: {file_path}")
        logger.info(f"  DXF Version: {doc.dxfversion}")
        
        # Get entity counts
        msp = doc.modelspace()
        entity_types = {}
        for e in msp:
            et = e.dxftype()
            entity_types[et] = entity_types.get(et, 0) + 1
        
        logger.info(f"  Entity counts: {entity_types}")
        
        # First pass: detect boundaries to determine scale
        preliminary_boundaries = extract_room_boundaries(doc, min_area_threshold=0)
        
        if not preliminary_boundaries:
            logger.error("No closed boundaries found in DXF file!")
            return []
        
        # Auto-detect units if scale is 'auto' or determine from given scale
        if scale == "auto" or scale not in ["mm", "m", "cm"]:
            detected_unit, area_scale = auto_detect_units(preliminary_boundaries)
            logger.info(f"Auto-detected scale: {detected_unit}")
        else:
            # Use provided scale
            if scale == "mm":
                area_scale = 0.000001  # mm² → m²
                min_threshold = 1000  # ~0.001 m² minimum
            elif scale == "m":
                area_scale = 1.0  # Already in m²
                min_threshold = 0.01  # 0.01 m² minimum
            elif scale == "cm":
                area_scale = 0.0001  # cm² → m²
                min_threshold = 10  # ~0.001 m² minimum
            else:
                logger.warning(f"Unknown scale '{scale}', defaulting to mm")
                area_scale = 0.000001
                min_threshold = 1000
        
        logger.info(f"Using area scale: {area_scale} (1 unit² = {area_scale} m²)")
        
        # Extract and match rooms with proper scaling
        rooms = match_rooms(doc, area_scale, min_threshold)
        
        if not rooms:
            logger.warning("No rooms detected! Trying with lower threshold...")
            # Try again with very low threshold
            rooms = match_rooms(doc, area_scale, min_threshold / 100)
        
        logger.info(f"🎉 Total rooms detected: {len(rooms)}")
        for room in rooms:
            logger.info(f"   - {room['name']}: {room['area']} sqm")
        
        return rooms
        
    except ezdxf.DXFStructureError as e:
        logger.error(f"DXF structure error: {e}")
        raise Exception(f"Invalid DXF file structure: {e}")
        
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise Exception(f"DXF file not found: {file_path}")
        
    except Exception as e:
        logger.error(f"Unexpected error processing DXF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise Exception(f"Error processing DXF file: {e}")


def get_dxf_info(file_path):
    """Get detailed information about a DXF file"""
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        entity_counts = {}
        for e in msp:
            entity_type = e.dxftype()
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        # Count text labels
        text_count = entity_counts.get('TEXT', 0) + entity_counts.get('MTEXT', 0)
        
        # Count possible boundaries
        boundary_count = (
            entity_counts.get('LWPOLYLINE', 0) + 
            entity_counts.get('POLYLINE', 0) +
            entity_counts.get('CIRCLE', 0)
        )
        
        info = {
            "version": doc.dxfversion,
            "entities": entity_counts,
            "total_entities": len(list(msp)),
            "text_labels": text_count,
            "possible_boundaries": boundary_count,
        }
        
        return info
        
    except Exception as e:
        logger.error(f"Error reading DXF info: {e}")
        return {"error": str(e)}
