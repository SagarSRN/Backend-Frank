"""
DXF File Processor for Retail Display Estimation
SMART VERSION: Separates LED INSERT blocks from METAL layer
"""

import ezdxf
import logging
from decimal import Decimal
from django.db import transaction
from .models import RetailEstimate, Component, Material, MaterialCategory

logger = logging.getLogger(__name__)


class DXFProcessor:
    """Process DXF files and generate retail estimates"""

    def __init__(self, dxf_path, project):
        self.dxf_path = dxf_path
        self.project = project
        self.doc = None
        self.components = []

    def process(self):
        """Main processing method"""
        try:
            # Load DXF file
            self.doc = ezdxf.readfile(self.dxf_path)
            self.msp = self.doc.modelspace()

            # Extract components from layers
            self._extract_components()

            # Create estimate
            estimate = self._create_estimate()

            return estimate

        except Exception as e:
            raise Exception(f"DXF Processing Error: {str(e)}")

    def _extract_components(self):
        """Extract components from DXF layers"""

        # Get all layers in the DXF
        layers = {}
        
        # SPECIAL: Track INSERT blocks separately
        metal_inserts = []

        for entity in self.msp:
            layer_name = entity.dxf.layer
            
            # Skip dimension and utility layers
            if any(skip in layer_name.upper() for skip in ['DIM', 'DIMENSION', 'HATCH', 'PDF', 'LEADER', '0', 'DEFPOINTS', 'BY OTHERS']):
                continue
            
            logger.info(f"🔍 Processing layer: '{layer_name}' (type: {entity.dxftype()})")

            if layer_name not in layers:
                layers[layer_name] = {
                    'entities': [],
                    'total_length': 0,
                    'total_area': 0,
                    'count': 0,
                    'polylines': [],
                    'inserts': []
                }

            layers[layer_name]['entities'].append(entity)
            layers[layer_name]['count'] += 1

            # SMART DETECTION: Separate INSERT blocks on METAL layer
            if entity.dxftype() == 'INSERT' and layer_name.upper() == 'METAL':
                metal_inserts.append(entity)
                logger.info(f"  📌 LED INSERT detected on METAL layer (will be treated as LED)")
                continue  # Don't count INSERT in METAL layer calculations

            # Calculate dimensions based on entity type
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                length = ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
                layers[layer_name]['total_length'] += length

            elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                layers[layer_name]['polylines'].append(entity)
                
                # Calculate polyline length AND area
                points = list(entity.get_points()) if hasattr(entity, 'get_points') else []
                
                if len(points) >= 2:
                    # Calculate perimeter
                    total_length = 0
                    for i in range(len(points) - 1):
                        p1, p2 = points[i], points[i+1]
                        length = ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)**0.5
                        total_length += 1
                    
                    layers[layer_name]['total_length'] += total_length
                    
                    # Calculate area if closed polyline (shoelace formula)
                    if entity.is_closed or (len(points) >= 3 and points[0] == points[-1]):
                        area = self._calculate_polygon_area(points)
                        layers[layer_name]['total_area'] += abs(area)

            elif entity.dxftype() == 'INSERT':
                # Block references (LED lights, hardware, etc.) - NOT on METAL layer
                layers[layer_name]['inserts'].append(entity)
                logger.info(f"  📌 INSERT entity found on '{layer_name}' layer")

            elif entity.dxftype() in ['CIRCLE', 'ARC']:
                radius = entity.dxf.radius
                if entity.dxftype() == 'CIRCLE':
                    area = 3.14159 * radius * radius
                    circumference = 2 * 3.14159 * radius
                    layers[layer_name]['total_area'] += area
                    layers[layer_name]['total_length'] += circumference
                else:
                    # Arc
                    start_angle = entity.dxf.start_angle
                    end_angle = entity.dxf.end_angle
                    angle_range = abs(end_angle - start_angle)
                    arc_length = (angle_range / 360) * 2 * 3.14159 * radius
                    layers[layer_name]['total_length'] += arc_length

        # SMART: Create a virtual LED layer for INSERT blocks found on METAL
        if metal_inserts:
            logger.info(f"\n💡 SMART DETECTION: Found {len(metal_inserts)} LED INSERT blocks on METAL layer")
            logger.info(f"   Creating virtual 'LED 4600K' layer for these blocks")
            
            layers['LED 4600K'] = {
                'entities': metal_inserts,
                'total_length': 0,
                'total_area': 0,
                'count': len(metal_inserts),
                'polylines': [],
                'inserts': metal_inserts
            }

        # Log summary
        logger.info(f"\n📊 LAYER SUMMARY:")
        for layer_name, layer_data in layers.items():
            logger.info(f"  Layer '{layer_name}':")
            logger.info(f"    Entities: {layer_data['count']}")
            logger.info(f"    INSERTs: {len(layer_data['inserts'])}")
            logger.info(f"    Length: {layer_data['total_length']:.2f}mm")
            logger.info(f"    Area: {layer_data['total_area']:.2f}mm²")

        # Convert layers to components
        for layer_name, layer_data in layers.items():
            self._create_component_from_layer(layer_name, layer_data)

    def _calculate_polygon_area(self, points):
        """Calculate area of polygon using shoelace formula"""
        if len(points) < 3:
            return 0
        
        area = 0
        for i in range(len(points) - 1):
            x1, y1 = points[i][0], points[i][1]
            x2, y2 = points[i+1][0], points[i+1][1]
            area += (x1 * y2) - (x2 * y1)
        
        # Close the polygon if not already closed
        if points[0] != points[-1]:
            x1, y1 = points[-1][0], points[-1][1]
            x2, y2 = points[0][0], points[0][1]
            area += (x1 * y2) - (x2 * y1)
        
        return abs(area) / 2

    def _create_component_from_layer(self, layer_name, layer_data):
        """Create component from layer data"""

        logger.info(f"\n🔧 Creating component for layer: '{layer_name}'")

        # Find matching material
        material = self._find_material_for_layer(layer_name)

        if not material:
            # Create generic material if no match
            logger.warning(f"  ⚠️ No material matched for '{layer_name}', creating generic")
            material = self._create_generic_material(layer_name)

        # Calculate quantity based on material unit
        quantity = self._calculate_quantity(material, layer_data)

        logger.info(f"  ✅ Material: {material.name} ({material.unit})")
        logger.info(f"  ✅ Quantity: {quantity} {material.unit}")
        logger.info(f"  ✅ Rate: ₹{material.rate}/{material.unit}")

        if quantity > 0:
            component_data = {
                'layer_name': layer_name,
                'material': material,
                'quantity': quantity,
                'entity_count': layer_data['count'],
                'total_length': layer_data['total_length'],
                'total_area': layer_data['total_area']
            }
            self.components.append(component_data)
        else:
            logger.warning(f"  ⚠️ Quantity is 0, component NOT created!")

    def _find_material_for_layer(self, layer_name):
        """Find best matching material for a layer"""
        
        logger.info(f"  🔍 Looking for material match for '{layer_name}'")

        layer_lower = layer_name.lower().strip()
        layer_upper = layer_name.upper().strip()

        # Try exact match first (case-insensitive)
        materials = Material.objects.all()
        
        for material in materials:
            if not material.dxf_layer_keywords:
                continue
            
            keywords = [k.strip() for k in material.dxf_layer_keywords.split(',')]
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                
                # Exact match
                if keyword_lower == layer_lower:
                    logger.info(f"  ✅ EXACT MATCH! '{layer_name}' → {material.name}")
                    return material
                
                # Contains match
                if keyword_lower in layer_lower or layer_lower in keyword_lower:
                    logger.info(f"  ✅ CONTAINS MATCH! '{layer_name}' → {material.name}")
                    return material

        logger.warning(f"  ❌ NO MATCH found for '{layer_name}'")
        return None

    def _create_generic_material(self, layer_name):
        """Create a generic material for unmatched layers"""

        # Get or create "Other Materials" category
        category, _ = MaterialCategory.objects.get_or_create(
            name='Other Materials',
            defaults={
                'category_type': 'SHEET',
                'description': 'Unmatched materials from DXF'
            }
        )

        # Create generic material
        material, created = Material.objects.get_or_create(
            name=f'Generic - {layer_name}',
            category=category,
            defaults={
                'unit': 'sqft',
                'rate': Decimal('1.00'),  # ₹1 to identify unmatched
                'specification': f'Generic material for layer: {layer_name}',
                'dxf_layer_keywords': layer_name
            }
        )

        return material

    def _calculate_quantity(self, material, layer_data):
        """Calculate quantity based on material unit type"""

        unit = material.unit.lower()

        logger.info(f"    Calculating quantity for unit: {unit}")
        logger.info(f"    Layer data: length={layer_data['total_length']:.2f}mm, area={layer_data['total_area']:.2f}mm², inserts={len(layer_data['inserts'])}, count={layer_data['count']}")

        if unit in ['meter', 'm', 'linear']:
            # Convert mm to meters (DXF is usually in mm)
            quantity = round(layer_data['total_length'] / 1000, 2)
            logger.info(f"    → {layer_data['total_length']:.2f}mm / 1000 = {quantity} meters")
            return quantity

        elif unit in ['sqft', 'sq ft', 'square feet']:
            # Convert mm² to sqft (1 sqft = 92903 mm²)
            area_sqft = layer_data['total_area'] / 92903.04
            quantity = round(area_sqft, 2)
            logger.info(f"    → {layer_data['total_area']:.2f}mm² / 92903.04 = {quantity} sqft")
            return quantity

        elif unit in ['piece', 'pcs', 'unit']:
            # Count INSERT entities (blocks) or total entities
            insert_count = len(layer_data.get('inserts', []))
            if insert_count > 0:
                logger.info(f"    → {insert_count} INSERT entities = {insert_count} pieces")
                return insert_count
            else:
                logger.info(f"    → {layer_data['count']} total entities = {layer_data['count']} pieces")
                return layer_data['count']

        else:
            # Default to area calculation
            area_sqft = layer_data['total_area'] / 92903.04
            if area_sqft > 0:
                quantity = round(area_sqft, 2)
                logger.info(f"    → Default area: {quantity} sqft")
                return quantity
            else:
                # Fallback to count for piece-based materials
                logger.info(f"    → Fallback count: {layer_data['count']} pieces")
                return layer_data['count']

    @transaction.atomic
    def _create_estimate(self):
        """Create RetailEstimate and Components in database"""

        # Create estimate
        estimate = RetailEstimate.objects.create(
            project=self.project,
            material_cost=Decimal('0.00'),
            labor_cost=Decimal('0.00'),
            overhead_percentage=Decimal('15.00'),
            profit_percentage=Decimal('10.00'),
            gst_percentage=Decimal('18.00')
        )

        # Create components
        total_material_cost = Decimal('0.00')

        logger.info(f"\n💾 Creating {len(self.components)} components in database:")

        for comp_data in self.components:
            component = Component.objects.create(
                estimate=estimate,
                material=comp_data['material'],
                description=f"{comp_data['material'].name} - {comp_data['layer_name']}",
                quantity=Decimal(str(comp_data['quantity'])),
                unit=comp_data['material'].unit
            )

            # Component.rate and Component.amount are @property
            # They auto-calculate from material.rate * quantity
            total_material_cost += component.amount
            
            logger.info(f"  ✓ {comp_data['material'].name}: {comp_data['quantity']} {comp_data['material'].unit} × ₹{comp_data['material'].rate} = ₹{component.amount}")

        # Update estimate costs
        estimate.material_cost = total_material_cost
        estimate.labor_cost = total_material_cost * Decimal('0.30')  # 30% of material
        estimate.save()

        # This triggers the estimate's save() method which calculates totals
        estimate.calculate_totals()

        logger.info(f"\n📊 ESTIMATE SUMMARY:")
        logger.info(f"  Material Cost: ₹{estimate.material_cost:,.2f}")
        logger.info(f"  Labor Cost: ₹{estimate.labor_cost:,.2f}")
        logger.info(f"  Total: ₹{estimate.total:,.2f}")

        return estimate


def process_dxf_file(dxf_path, project):
    """
    Main function to process DXF file and create estimate

    Args:
        dxf_path: Path to DXF file
        project: Project instance

    Returns:
        RetailEstimate instance
    """
    processor = DXFProcessor(dxf_path, project)
    return processor.process()