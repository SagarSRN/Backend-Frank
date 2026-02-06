"""
Enhanced DXF Processor with improved room detection and error handling
"""
import ezdxf
from shapely.geometry import Point, Polygon
from shapely.errors import ShapelyError
import logging

logger = logging.getLogger(__name__)


def extract_room_labels(doc):
    """
    Extract text labels from DXF file
    
    Args:
        doc: ezdxf document object
        
    Returns:
        list: List of dictionaries with 'name' and 'point' keys
    """
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
        except Exception as e:
            logger.warning(f"Error processing text entity: {e}")
            continue

    logger.info(f"Found {len(labels)} text labels")
    return labels


def extract_room_boundaries(doc, min_area_threshold=100000):
    """
    Extract closed polyline boundaries from DXF file
    
    Args:
        doc: ezdxf document object
        min_area_threshold: Minimum area in mm² to consider (default 100000 = ~10 sqm)
        
    Returns:
        list: List of Shapely Polygon objects
    """
    msp = doc.modelspace()
    boundaries = []

    for e in msp:
        try:
            # Check for closed polylines
            if e.dxftype() == "LWPOLYLINE" and e.closed:
                pts = [(p[0], p[1]) for p in e.get_points()]
                
                if len(pts) < 3:
                    continue

                poly = Polygon(pts)
                
                # Validate polygon
                if not poly.is_valid:
                    logger.warning(f"Invalid polygon found, attempting to fix")
                    poly = poly.buffer(0)  # Fix self-intersecting polygons
                    
                    if not poly.is_valid:
                        continue

                # Check area threshold
                if poly.area > min_area_threshold:
                    boundaries.append(poly)
                    
            # Also check for POLYLINE entities
            elif e.dxftype() == "POLYLINE" and e.is_closed:
                pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
                
                if len(pts) < 3:
                    continue
                    
                poly = Polygon(pts)
                
                if not poly.is_valid:
                    poly = poly.buffer(0)
                    if not poly.is_valid:
                        continue
                
                if poly.area > min_area_threshold:
                    boundaries.append(poly)
                    
        except (ShapelyError, AttributeError) as e:
            logger.warning(f"Error processing boundary entity: {e}")
            continue

    logger.info(f"Found {len(boundaries)} valid boundaries")
    return boundaries


def match_rooms(doc, area_scale, min_area_threshold=100000):
    """
    Match room labels to boundaries
    
    Args:
        doc: ezdxf document object
        area_scale: Conversion factor for area (mm² to m²)
        min_area_threshold: Minimum area threshold in mm²
        
    Returns:
        list: List of room dictionaries with name, area, and center
    """
    labels = extract_room_labels(doc)
    boundaries = extract_room_boundaries(doc, min_area_threshold)

    rooms = []
    used_boundaries = set()

    # Try to match each boundary with a label
    for i, poly in enumerate(boundaries):
        matched = False
        
        for label in labels:
            # Check if label point is inside this boundary
            if poly.contains(label["point"]):
                rooms.append({
                    "name": label["name"],
                    "area": round(poly.area * area_scale, 2),
                    "center": poly.centroid
                })
                used_boundaries.add(i)
                matched = True
                break
        
        # If no label found, create unnamed room
        if not matched:
            area_sqm = round(poly.area * area_scale, 2)
            # Only add unnamed rooms if they're significant
            if area_sqm > 5:  # Greater than 5 sqm
                rooms.append({
                    "name": f"ROOM_{len(rooms) + 1}",
                    "area": area_sqm,
                    "center": poly.centroid
                })
                used_boundaries.add(i)

    logger.info(f"Matched {len(rooms)} rooms")
    return rooms


def detect_rooms_from_dxf(file_path, scale="mm"):
    """
    Main function to detect rooms from DXF file
    
    Args:
        file_path: Path to DXF file
        scale: Unit scale - 'mm' or 'm'
        
    Returns:
        list: List of detected rooms
        
    Raises:
        Exception: If file cannot be read or processed
    """
    try:
        # Read DXF file
        doc = ezdxf.readfile(file_path)
        logger.info(f"Successfully opened DXF file: {file_path}")
        
        # Determine area scale factor
        if scale == "mm":
            area_scale = 0.000001  # mm² → m²
            min_threshold = 100000  # ~10 m² in mm²
        else:
            area_scale = 1.0  # Already in m²
            min_threshold = 0.1  # 0.1 m²
        
        # Extract and match rooms
        rooms = match_rooms(doc, area_scale, min_threshold)
        
        if not rooms:
            logger.warning("No rooms detected in DXF file")
            # Try with lower threshold
            logger.info("Attempting detection with lower threshold")
            rooms = match_rooms(doc, area_scale, min_threshold / 10)
        
        logger.info(f"Total rooms detected: {len(rooms)}")
        return rooms
        
    except ezdxf.DXFStructureError as e:
        logger.error(f"DXF structure error: {e}")
        raise Exception(f"Invalid DXF file structure: {e}")
        
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise Exception(f"DXF file not found: {file_path}")
        
    except Exception as e:
        logger.error(f"Unexpected error processing DXF: {e}")
        raise Exception(f"Error processing DXF file: {e}")


def get_dxf_info(file_path):
    """
    Get basic information about a DXF file
    
    Args:
        file_path: Path to DXF file
        
    Returns:
        dict: Information about the DXF file
    """
    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        
        entity_counts = {}
        for e in msp:
            entity_type = e.dxftype()
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        info = {
            "version": doc.dxfversion,
            "entities": entity_counts,
            "total_entities": len(list(msp)),
        }
        
        return info
        
    except Exception as e:
        logger.error(f"Error reading DXF info: {e}")
        return {"error": str(e)}
