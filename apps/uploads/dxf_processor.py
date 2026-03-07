
import ezdxf
from shapely.geometry import Point, Polygon, LineString
from shapely.ops import unary_union, polygonize
from shapely.errors import ShapelyError
import logging
import math
from collections import defaultdict

logger = logging.getLogger(__name__)


def auto_detect_scale(rooms):
    """
    Auto-detect scale based on polygon areas
    Returns: (unit_name, conversion_factor)
    """
    if not rooms:
        return "ft", 0.0929  # Default to square feet
    
    avg_area = sum(r['area_raw'] for r in rooms) / len(rooms)
    max_area = max(r['area_raw'] for r in rooms)
    
    logger.info(f"Average room area (raw): {avg_area:.2f}")
    logger.info(f"Maximum room area (raw): {max_area:.2f}")
    
    # Square millimeters (huge values > 1 million)
    if max_area > 1000000:
        logger.info("Detected: square millimeters (mm²)")
        return "mm", 0.000001
    
    # Square centimeters (100k - 1M)
    elif max_area > 100000:
        logger.info("Detected: square centimeters (cm²)")
        return "cm", 0.0001
    
    # Square inches (10k - 100k)
    elif max_area > 10000:
        logger.info("Detected: square inches (in²)")
        return "inches", 0.00064516
    
    # Square feet (10 - 10000) ← MOST COMMON
    elif max_area > 10:
        logger.info("Detected: square feet (ft²)")
        return "ft", 0.0929
    
    # Square meters (1 - 1000)
    elif max_area >= 1:
        logger.info("Detected: square meters (m²)")
        return "m", 1.0
    
    # Default to square feet
    else:
        logger.info("Defaulting to square feet (ft²)")
        return "ft", 0.0929


def extract_room_labels(doc):
    """Extract text labels from DXF file"""
    msp = doc.modelspace()
    labels = []

    for e in msp:
        try:
            if e.dxftype() in ["TEXT", "MTEXT"]:
                text = e.plain_text().strip().upper()
                if not text or len(text) < 2:
                    continue

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
            continue

    logger.info(f"Found {len(labels)} text labels")
    return labels


def extract_lines_and_polylines(doc):
    """
    Extract ALL lines and polylines from DXF
    """
    msp = doc.modelspace()
    all_lines = []
    closed_polys = []
    
    logger.info("Extracting entities from DXF...")
    
    entity_counts = defaultdict(int)
    
    for e in msp:
        try:
            entity_type = e.dxftype()
            entity_counts[entity_type] += 1
            
            # LWPOLYLINE (closed)
            if entity_type == "LWPOLYLINE":
                if e.closed or e.is_closed:
                    pts = [(p[0], p[1]) for p in e.get_points()]
                    if len(pts) >= 3:
                        try:
                            poly = Polygon(pts)
                            if poly.is_valid and poly.area > 0.1:
                                closed_polys.append(poly)
                                logger.debug(f"Added closed LWPOLYLINE: area={poly.area}")
                        except:
                            pass
                else:
                    pts = list(e.get_points())
                    for i in range(len(pts) - 1):
                        line = LineString([(pts[i][0], pts[i][1]), (pts[i+1][0], pts[i+1][1])])
                        all_lines.append(line)
            
            # POLYLINE (closed)
            elif entity_type == "POLYLINE":
                if e.is_closed:
                    pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
                    if len(pts) >= 3:
                        try:
                            poly = Polygon(pts)
                            if poly.is_valid and poly.area > 0.1:
                                closed_polys.append(poly)
                                logger.debug(f"Added closed POLYLINE: area={poly.area}")
                        except:
                            pass
                else:
                    vertices = list(e.vertices)
                    for i in range(len(vertices) - 1):
                        p1 = vertices[i].dxf.location
                        p2 = vertices[i+1].dxf.location
                        line = LineString([(p1.x, p1.y), (p2.x, p2.y)])
                        all_lines.append(line)
            
            # LINE entities
            elif entity_type == "LINE":
                start = e.dxf.start
                end = e.dxf.end
                line = LineString([(start.x, start.y), (end.x, end.y)])
                all_lines.append(line)
            
            # ARC entities
            elif entity_type == "ARC":
                center = e.dxf.center
                radius = e.dxf.radius
                start_angle = math.radians(e.dxf.start_angle)
                end_angle = math.radians(e.dxf.end_angle)
                
                num_segments = 10
                angle_step = (end_angle - start_angle) / num_segments
                
                for i in range(num_segments):
                    angle1 = start_angle + i * angle_step
                    angle2 = start_angle + (i + 1) * angle_step
                    
                    x1 = center.x + radius * math.cos(angle1)
                    y1 = center.y + radius * math.sin(angle1)
                    x2 = center.x + radius * math.cos(angle2)
                    y2 = center.y + radius * math.sin(angle2)
                    
                    line = LineString([(x1, y1), (x2, y2)])
                    all_lines.append(line)
            
            # CIRCLE
            elif entity_type == "CIRCLE":
                center = e.dxf.center
                radius = e.dxf.radius
                
                pts = []
                for i in range(36):
                    angle = (i / 36.0) * 2 * math.pi
                    x = center.x + radius * math.cos(angle)
                    y = center.y + radius * math.sin(angle)
                    pts.append((x, y))
                
                try:
                    poly = Polygon(pts)
                    if poly.is_valid and poly.area > 0.1:
                        closed_polys.append(poly)
                        logger.debug(f"Added CIRCLE: area={poly.area}")
                except:
                    pass
                    
        except Exception as ex:
            continue
    
    logger.info(f"Entity counts: {dict(entity_counts)}")
    logger.info(f"Found {len(closed_polys)} closed polylines")
    logger.info(f"Found {len(all_lines)} line segments")
    
    return closed_polys, all_lines


def create_polygons_from_lines(lines, tolerance=10):
    """
    Create closed polygons from separate LINE entities
    """
    if not lines:
        return []
    
    logger.info(f"Attempting to create polygons from {len(lines)} lines...")
    
    try:
        merged = unary_union(lines)
        polygons = list(polygonize(merged))
        
        logger.info(f"Created {len(polygons)} polygons from lines")
        
        # Ultra low threshold
        valid_polygons = []
        min_area = 0.1
        
        for i, poly in enumerate(polygons):
            if poly.is_valid and poly.area > min_area:
                valid_polygons.append(poly)
                if i < 10:
                    logger.info(f"✓ Kept polygon {i+1}: area={poly.area:.2f}")
            else:
                if i < 10:
                    logger.debug(f"✗ Rejected polygon {i+1}: area={poly.area:.2f}")
        
        logger.info(f"Kept {len(valid_polygons)} valid polygons (min area: {min_area})")
        
        if len(valid_polygons) == 0 and len(polygons) > 0:
            logger.warning(f"All {len(polygons)} polygons were rejected!")
            areas = sorted([p.area for p in polygons if p.is_valid])
            if areas:
                logger.warning(f"  Smallest: {areas[0]:.2f}")
                logger.warning(f"  Largest: {areas[-1]:.2f}")
                logger.warning(f"  Average: {sum(areas)/len(areas):.2f}")
        
        return valid_polygons
        
    except Exception as e:
        logger.error(f"Error creating polygons from lines: {e}")
        return []


def match_rooms(labels, boundaries):
    """Match room labels to boundaries"""
    if not boundaries:
        logger.warning("No boundaries to match!")
        return []
    
    rooms = []
    used_labels = set()

    logger.info(f"Matching {len(labels)} labels to {len(boundaries)} boundaries...")

    for i, poly in enumerate(boundaries):
        matched = False
        best_match = None
        
        for j, label in enumerate(labels):
            if j in used_labels:
                continue
                
            if poly.contains(label["point"]):
                best_match = label
                used_labels.add(j)
                matched = True
                logger.debug(f"Matched '{label['name']}' to boundary {i}")
                break
        
        room_name = best_match["name"] if best_match else f"ROOM_{i + 1}"
        
        rooms.append({
            "name": room_name,
            "polygon": poly,
            "area_raw": poly.area,
            "center": poly.centroid
        })

    logger.info(f"Matched {len(rooms)} rooms")
    return rooms


def detect_rooms_from_dxf(file_path, scale="mm"):
    """
    Main function to detect rooms from DXF file
    ALWAYS auto-detects scale regardless of input parameter
    """
    try:
        doc = ezdxf.readfile(file_path)
        logger.info(f"✓ Opened DXF file: {file_path}")
        logger.info(f"  DXF Version: {doc.dxfversion}")
        
        labels = extract_room_labels(doc)
        
        if not labels:
            logger.warning("No text labels found in DXF!")
        
        closed_polys, lines = extract_lines_and_polylines(doc)
        
        all_boundaries = list(closed_polys)
        
        if lines:
            logger.info("Attempting to create rooms from LINE entities...")
            line_polygons = create_polygons_from_lines(lines)
            all_boundaries.extend(line_polygons)
        
        logger.info(f"Total boundaries found: {len(all_boundaries)}")
        
        if not all_boundaries:
            logger.error("❌ No room boundaries detected!")
            logger.error("This DXF file may use:")
            logger.error("  - Blocks/References instead of polylines")
            logger.error("  - 3D geometry (only 2D supported)")
            logger.error("  - Non-standard CAD format")
            return []
        
        rooms = match_rooms(labels, all_boundaries)
        
        if not rooms:
            logger.warning("No rooms matched! Using all boundaries...")
            rooms = [
                {
                    "name": f"ROOM_{i+1}",
                    "polygon": poly,
                    "area_raw": poly.area,
                    "center": poly.centroid
                }
                for i, poly in enumerate(all_boundaries)
            ]
        
        # ALWAYS AUTO-DETECT SCALE
        detected_unit, area_scale = auto_detect_scale(rooms)
        logger.info(f"Using area scale: {area_scale}")
        
        # Calculate final areas
        final_rooms = []
        for room in rooms:
            area_sqm = round(room['area_raw'] * area_scale, 2)
            
            # Accept rooms > 0.1 m² (very permissive)
            if area_sqm >= 0.1:
                final_rooms.append({
                    "name": room['name'],
                    "area": area_sqm,
                    "center": room['center']
                })
                logger.info(f"  ✓ Room: {room['name']} = {area_sqm} m²")
            else:
                logger.warning(f"  ✗ FILTERED: {room['name']} = {area_sqm} m² (< 0.1 m²)")
        
        logger.info(f"🎉 Total rooms detected: {len(final_rooms)}")
        return final_rooms
        
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
        
        text_count = entity_counts.get('TEXT', 0) + entity_counts.get('MTEXT', 0)
        polyline_count = entity_counts.get('LWPOLYLINE', 0) + entity_counts.get('POLYLINE', 0)
        line_count = entity_counts.get('LINE', 0)
        
        info = {
            "version": doc.dxfversion,
            "entities": entity_counts,
            "total_entities": len(list(msp)),
            "text_labels": text_count,
            "polylines": polyline_count,
            "lines": line_count,
        }
        
        return info
        
    except Exception as e:
        logger.error(f"Error reading DXF info: {e}")
        return {"error": str(e)}