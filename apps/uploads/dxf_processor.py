import ezdxf
from shapely.geometry import Point, Polygon


def extract_room_labels(doc):
    msp = doc.modelspace()
    labels = []

    for e in msp:
        if e.dxftype() in ["TEXT", "MTEXT"]:
            text = e.plain_text().strip().upper()
            if not text:
                continue

            x = e.dxf.insert.x
            y = e.dxf.insert.y

            labels.append({
                "name": text,
                "point": Point(x, y)
            })

    return labels


def extract_room_boundaries(doc):
    msp = doc.modelspace()
    boundaries = []

    for e in msp:
        if e.dxftype() == "LWPOLYLINE" and e.closed:
            pts = [(p[0], p[1]) for p in e.get_points()]
            if len(pts) < 3:
                continue

            poly = Polygon(pts)

            # ⚠️ LOWERED THRESHOLD TEMPORARILY
            if poly.area > 100000:  # mm²
                boundaries.append(poly)

    return boundaries


def match_rooms(doc, area_scale):
    labels = extract_room_labels(doc)
    boundaries = extract_room_boundaries(doc)

    rooms = []

    for poly in boundaries:
        for label in labels:
            if poly.contains(label["point"]):
                rooms.append({
                    "name": label["name"],
                    "area": round(poly.area * area_scale, 2),
                    "center": poly.centroid
                })

    return rooms


def detect_rooms_from_dxf(file_path, scale="mm"):
    doc = ezdxf.readfile(file_path)

    # ✅ CORRECT AREA SCALE
    if scale == "mm":
        area_scale = 0.000001  # mm² → m²
    else:
        area_scale = 1.0

    return match_rooms(doc, area_scale)
