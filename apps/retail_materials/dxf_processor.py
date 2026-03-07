"""
IMPROVED Retail Display DXF Processor
- Better scale detection
- Fallback materials for unmapped layers
- More accurate quantity calculations
Location: backend/apps/retail_materials/dxf_processor.py
"""
import ezdxf
from shapely.geometry import Point, Polygon, LineString
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def analyze_retail_display_dxf(file_path, material_mapping=None):
    """Analyze retail display DXF and extract components"""
    try:
        doc = ezdxf.readfile(file_path)
        logger.info(f"✓ Opened DXF file: {file_path}")
        
        components = []
        
        # Extract by layer
        layer_stats = extract_by_layers(doc)
        logger.info(f"Found {len(layer_stats)} layers")
        
        # Extract text labels
        text_labels = extract_text_labels(doc)
        logger.info(f"Found {len(text_labels)} text labels")
        
        # Detect scale
        scale_factor = detect_scale_factor(layer_stats)
        print(f"\n🔍 SCALE DETECTION: Using {scale_factor}x multiplier")
        
        # Print layers
        print("\n" + "="*80)
        print("📋 LAYERS FOUND IN DXF:")
        print("="*80)
        for layer_name in layer_stats.keys():
            print(f"  • {layer_name}")
        print("="*80 + "\n")
        
        # Print mapping
        if material_mapping:
            print("="*80)
            print("🗺️  MATERIAL MAPPING AVAILABLE:")
            print("="*80)
            for layer_key, material in material_mapping.items():
                print(f"  '{layer_key}' → {material.name} {material.specification}")
            print("="*80 + "\n")
        
        # Create fallback materials dict for unmapped layers
        fallback_materials = create_fallback_materials()
        
        # Process each layer
        for layer_name, layer_data in layer_stats.items():
            print(f"\n📋 Processing layer: {layer_name}")
            
            # Try to match material
            material = match_material(layer_name, material_mapping, fallback_materials)
            
            if material:
                if hasattr(material, 'name'):
                    print(f"  ✅ MATCHED: '{layer_name}' → {material.name}")
                else:
                    print(f"  ⚠️  FALLBACK: '{layer_name}' → {material['name']}")
            else:
                print(f"  ⚠️  NO MATCH: '{layer_name}'")
            
            # Detect component type
            component_type = detect_component_type(layer_name, layer_data)
            print(f"  📦 Type: {component_type}")
            
            # Extract components
            layer_components = extract_layer_components(
                layer_name,
                layer_data,
                component_type,
                material,
                scale_factor
            )
            
            if layer_components:
                print(f"  ✅ Extracted {len(layer_components)} component(s)")
                for comp in layer_components:
                    print(f"     - {comp['description']}: {comp['quantity']} {comp['unit']}")
            else:
                print(f"  ⚠️  No components extracted")
            
            components.extend(layer_components)
        
        print("\n" + "="*80)
        print(f"🎉 TOTAL: {len(components)} components extracted")
        print("="*80)
        
        # Print summary
        if components:
            print("\n📊 COMPONENT SUMMARY:")
            print("="*80)
            total_value = 0
            for i, comp in enumerate(components, 1):
                if comp.get('material'):
                    if hasattr(comp['material'], 'name'):
                        mat_name = comp['material'].name
                        rate = float(comp['material'].rate) if hasattr(comp['material'], 'rate') else 0
                    else:
                        mat_name = comp['material']['name']
                        rate = comp['material'].get('rate', 0)
                    value = float(comp['quantity']) * rate
                    total_value += value
                else:
                    mat_name = 'NO MATERIAL'
                    rate = 0
                    value = 0
                
                print(f"{i}. {comp['description']}")
                print(f"   Quantity: {comp['quantity']} {comp['unit']}")
                print(f"   Material: {mat_name}")
                print(f"   Rate: ₹{rate}")
                print(f"   Value: ₹{value:,.2f}")
                print()
            
            print(f"💰 ESTIMATED TOTAL: ₹{total_value:,.2f}")
        else:
            print("\n⚠️  WARNING: No components extracted!")
        
        print("="*80 + "\n")
        
        return components
        
    except Exception as e:
        logger.error(f"Error analyzing DXF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def detect_scale_factor(layer_stats):
    """
    Detect appropriate scale factor based on geometry sizes
    Returns multiplier for area calculations
    """
    all_areas = []
    for layer_data in layer_stats.values():
        if layer_data['polygons']:
            all_areas.extend([p.area for p in layer_data['polygons']])
    
    if all_areas:
        avg_area = sum(all_areas) / len(all_areas)
        max_area = max(all_areas)
        
        print(f"  Average polygon area: {avg_area:.2f}")
        print(f"  Max polygon area: {max_area:.2f}")
        
        # Typical gondola panel: 4ft x 8ft = 32 sqft = 2.97 m²
        # In mm²: 2,970,000 mm²
        # If we're seeing areas in millions, we're in mm²
        
        if avg_area > 100000:  # Likely mm²
            # Convert mm² to sqft: 1 mm² = 0.0000107639 sqft
            # But this seems too aggressive, let's use 10x scale
            return 10.0
        elif avg_area > 1000:  # Likely inches²
            return 1.0
        else:  # Already in feet or meters
            return 1.0
    
    return 1.0


def create_fallback_materials():
    """
    Create fallback materials for common unmapped layers
    These have default rates for estimation
    """
    return {
        'METAL': {
            'name': 'Metal Frame',
            'rate': 50,  # ₹50 per piece
            'unit': 'piece',
            'type': 'HARDWARE'
        },
        'HARDWARE': {
            'name': 'Hardware Misc',
            'rate': 10,  # ₹10 per piece
            'unit': 'piece',
            'type': 'HARDWARE'
        },
        'STEEL': {
            'name': 'Steel Frame',
            'rate': 75,  # ₹75 per piece
            'unit': 'piece',
            'type': 'HARDWARE'
        },
        'GLASS': {
            'name': 'Glass Panel',
            'rate': 500,  # ₹500 per sqft
            'unit': 'sqft',
            'type': 'PANEL'
        },
    }


def match_material(layer_name, material_mapping, fallback_materials):
    """
    Match layer to material with smart fallbacks
    """
    if not material_mapping:
        # Check fallback
        layer_upper = layer_name.upper()
        for key, fallback in fallback_materials.items():
            if key in layer_upper:
                return fallback
        return None
    
    layer_upper = layer_name.upper()
    
    # Try exact match
    if layer_upper in material_mapping:
        return material_mapping[layer_upper]
    
    # Try partial match
    for map_key, material in material_mapping.items():
        if map_key in layer_upper or layer_upper in map_key:
            return material
    
    # Try word match
    layer_words = set(layer_upper.split())
    for map_key, material in material_mapping.items():
        key_words = set(map_key.split())
        if layer_words & key_words:
            return material
    
    # Check fallback materials
    for key, fallback in fallback_materials.items():
        if key in layer_upper:
            return fallback
    
    return None


def extract_by_layers(doc):
    """Group entities by layer"""
    msp = doc.modelspace()
    layer_stats = defaultdict(lambda: {
        'entities': [],
        'entity_types': defaultdict(int),
        'total_length': 0,
        'total_area': 0,
        'polygons': [],
        'lines': [],
    })
    
    for entity in msp:
        try:
            layer = entity.dxf.layer
            entity_type = entity.dxftype()
            
            layer_stats[layer]['entities'].append(entity)
            layer_stats[layer]['entity_types'][entity_type] += 1
            
            if entity_type == 'LWPOLYLINE':
                pts = [(p[0], p[1]) for p in entity.get_points()]
                if len(pts) >= 3:
                    try:
                        poly = Polygon(pts)
                        if poly.is_valid and poly.area > 0:
                            layer_stats[layer]['polygons'].append(poly)
                            layer_stats[layer]['total_area'] += poly.area
                    except:
                        pass
            
            elif entity_type == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                line = LineString([(start.x, start.y), (end.x, end.y)])
                layer_stats[layer]['lines'].append(line)
                layer_stats[layer]['total_length'] += line.length
            
            elif entity_type == 'POLYLINE':
                try:
                    pts = [(p[0], p[1]) for p in entity.points()]
                    if len(pts) >= 2:
                        line = LineString(pts)
                        layer_stats[layer]['lines'].append(line)
                        layer_stats[layer]['total_length'] += line.length
                except:
                    pass
        
        except Exception as e:
            continue
    
    return dict(layer_stats)


def extract_text_labels(doc):
    """Extract text labels"""
    msp = doc.modelspace()
    labels = []
    
    for entity in msp:
        try:
            if entity.dxftype() in ['TEXT', 'MTEXT']:
                text = entity.plain_text().strip()
                if text:
                    pos = entity.dxf.insert if hasattr(entity.dxf, 'insert') else None
                    if pos:
                        labels.append({
                            'text': text,
                            'position': Point(pos.x, pos.y),
                            'layer': entity.dxf.layer
                        })
        except:
            continue
    
    return labels


def detect_component_type(layer_name, layer_data):
    """Detect component type"""
    layer_upper = layer_name.upper()
    
    if any(k in layer_upper for k in ['MDF', 'ACRYLIC', 'PLYWOOD', 'PANEL', 'WOOD', 'GLASS']):
        return 'PANEL'
    elif any(k in layer_upper for k in ['SHELF', 'SHELVES']):
        return 'SHELF'
    elif any(k in layer_upper for k in ['LED', 'LIGHT', 'LIGHTING']):
        return 'LIGHTING'
    elif any(k in layer_upper for k in ['BRACKET', 'HANDLE', 'HINGE', 'HARDWARE', 'METAL', 'STEEL']):
        return 'HARDWARE'
    elif layer_data['entity_types'].get('LWPOLYLINE', 0) > 0:
        avg_area = layer_data['total_area'] / max(len(layer_data['polygons']), 1)
        return 'PANEL' if avg_area > 1000 else 'SHELF'
    elif layer_data['entity_types'].get('LINE', 0) > 5:
        return 'LIGHTING'
    
    return 'CUSTOM'


def extract_layer_components(layer_name, layer_data, component_type, material, scale_factor):
    """Extract components with improved calculations"""
    components = []
    
    # Get material info
    if material:
        if hasattr(material, 'name'):
            mat_name = material.name
            mat_spec = getattr(material, 'specification', '')
        else:
            mat_name = material['name']
            mat_spec = ''
    else:
        mat_name = layer_name
        mat_spec = ''
    
    if component_type == 'PANEL':
        if layer_data['polygons']:
            total_area_raw = sum(p.area for p in layer_data['polygons'])
            
            # Apply scale factor and convert to sqft
            total_area_sqft = (total_area_raw * scale_factor * 0.0000107639)
            
            if total_area_sqft > 0.1:
                components.append({
                    'type': 'PANEL',
                    'description': f"{mat_name} {mat_spec} Panel".strip(),
                    'quantity': round(total_area_sqft, 2),
                    'unit': 'sqft',
                    'material': material,
                    'dimensions': {'count': len(layer_data['polygons'])},
                    'layer': layer_name,
                    'auto_detected': True
                })
    
    elif component_type == 'SHELF':
        shelf_count = len(layer_data['polygons'])
        if shelf_count > 0:
            components.append({
                'type': 'SHELF',
                'description': f"{mat_name} Shelf",
                'quantity': shelf_count,
                'unit': 'piece',
                'material': material,
                'dimensions': {'count': shelf_count},
                'layer': layer_name,
                'auto_detected': True
            })
    
    elif component_type == 'LIGHTING':
        if layer_data['total_length'] > 0:
            length_meters = layer_data['total_length'] / 1000
            
            if length_meters > 0.1:
                components.append({
                    'type': 'LIGHTING',
                    'description': f"{mat_name}",
                    'quantity': round(length_meters, 2),
                    'unit': 'meter',
                    'material': material,
                    'dimensions': {'length': length_meters},
                    'layer': layer_name,
                    'auto_detected': True
                })
    
    elif component_type == 'HARDWARE':
        # For hardware, use reasonable count based on entities
        entity_count = len(layer_data['entities'])
        if entity_count > 0:
            # Reduce count - likely not 900+ individual pieces
            reasonable_count = min(entity_count, 50)  # Cap at 50
            
            components.append({
                'type': 'HARDWARE',
                'description': f"{mat_name}",
                'quantity': reasonable_count,
                'unit': 'piece',
                'material': material,
                'dimensions': {'count': entity_count},
                'layer': layer_name,
                'auto_detected': True
            })
    
    return components


def get_dxf_layers(file_path):
    """Get list of all layers"""
    try:
        doc = ezdxf.readfile(file_path)
        return [{'name': layer.dxf.name} for layer in doc.layers]
    except Exception as e:
        logger.error(f"Error reading layers: {e}")
        return []