"""
COMPLETE Retail Materials Seed - Tailored for Your Company's DXF Files
Covers D&G GONDOLA and similar project layers
Location: apps/retail_materials/management/commands/seed_company_materials.py

Run: python manage.py seed_company_materials
"""
from django.core.management.base import BaseCommand
from apps.retail_materials.models import MaterialCategory, Material


class Command(BaseCommand):
    help = 'Seed materials for company DXF files (D&G Gondola structure)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🌱 Seeding Company Materials...'))
        self.stdout.write('Based on: D&G GONDOLA.dxf layer structure\n')

        # Don't clear - just add/update
        materials_created = 0
        materials_updated = 0

        # Get or create categories
        sheet_cat, _ = MaterialCategory.objects.get_or_create(
            category_type='SHEET',
            defaults={'name': 'Sheet Materials', 'display_order': 1}
        )
        
        lighting_cat, _ = MaterialCategory.objects.get_or_create(
            category_type='LIGHTING',
            defaults={'name': 'Lighting', 'display_order': 2}
        )
        
        hardware_cat, _ = MaterialCategory.objects.get_or_create(
            category_type='HARDWARE',
            defaults={'name': 'Hardware', 'display_order': 3}
        )

        # =====================================================
        # COMPANY-SPECIFIC MATERIALS
        # Based on actual D&G GONDOLA layers
        # =====================================================

        company_materials = [
            # === ACRYLIC (Layer: "Acrylic - opal") ===
            {
                'category': sheet_cat,
                'name': 'Acrylic',
                'specification': '5mm Opal/White',
                'unit': 'sqft',
                'rate': 280,
                'dxf_layer_names': 'Acrylic - opal,Acrylic-opal,ACRYLIC - OPAL,Acrylic,ACRYLIC,ACR,Opal,OPAL',
            },
            {
                'category': sheet_cat,
                'name': 'Acrylic',
                'specification': '3mm Clear',
                'unit': 'sqft',
                'rate': 200,
                'dxf_layer_names': 'ACRYLIC_3MM,ACR_3MM,Acrylic 3mm,ACR3',
            },
            {
                'category': sheet_cat,
                'name': 'Acrylic',
                'specification': '5mm Clear',
                'unit': 'sqft',
                'rate': 280,
                'dxf_layer_names': 'ACRYLIC_5MM,ACR_5MM,Acrylic 5mm,ACR5,ACRYLIC CLEAR',
            },
            
            # === MDF (Layer: "MDF") ===
            {
                'category': sheet_cat,
                'name': 'MDF',
                'specification': '6mm',
                'unit': 'sqft',
                'rate': 50,
                'dxf_layer_names': 'MDF_6MM,MDF 6mm,MDF6,MDF_6',
            },
            {
                'category': sheet_cat,
                'name': 'MDF',
                'specification': '12mm',
                'unit': 'sqft',
                'rate': 80,
                'dxf_layer_names': 'MDF_12MM,MDF 12mm,MDF12,MDF_12,MDF',
            },
            {
                'category': sheet_cat,
                'name': 'MDF',
                'specification': '18mm',
                'unit': 'sqft',
                'rate': 110,
                'dxf_layer_names': 'MDF_18MM,MDF 18mm,MDF18,MDF_18,PANEL_MDF,MDF PANEL',
            },
            
            # === METAL (Layer: "METAL") ===
            {
                'category': hardware_cat,
                'name': 'Metal Frame',
                'specification': 'MS Square Tube',
                'unit': 'piece',
                'rate': 100,
                'dxf_layer_names': 'METAL,Metal,STEEL,Steel,MS,FRAME,Frame,STRUCTURE',
            },
            {
                'category': hardware_cat,
                'name': 'Metal Sheet',
                'specification': '1mm MS',
                'unit': 'sqft',
                'rate': 150,
                'dxf_layer_names': 'METAL SHEET,Metal Sheet,MS SHEET',
            },
            
            # === HARDWARE (Layer: "Hardware") ===
            {
                'category': hardware_cat,
                'name': 'Hardware',
                'specification': 'General/Misc',
                'unit': 'piece',
                'rate': 20,
                'dxf_layer_names': 'HARDWARE,Hardware,FITTINGS,Fittings,MISC',
            },
            {
                'category': hardware_cat,
                'name': 'Glass Shelf',
                'specification': '6mm Tempered',
                'unit': 'piece',
                'rate': 600,
                'dxf_layer_names': 'GLASS SHELF,Glass Shelf,SHELF GLASS,GLASS,Glass',
            },
            {
                'category': hardware_cat,
                'name': 'Shelf Bracket',
                'specification': 'Standard',
                'unit': 'piece',
                'rate': 60,
                'dxf_layer_names': 'BRACKET,Bracket,SHELF BRACKET,Shelf Bracket',
            },
            
            # === LED LIGHTING (Layers: "LED 4600K", "LED lights") ===
            {
                'category': lighting_cat,
                'name': 'LED Strip',
                'specification': '4600K Warm White',
                'unit': 'meter',
                'rate': 180,
                'dxf_layer_names': 'LED 4600K,LED4600K,LED 4600,LED_4600K',
            },
            {
                'category': lighting_cat,
                'name': 'LED Strip',
                'specification': 'Standard 5050',
                'unit': 'meter',
                'rate': 160,
                'dxf_layer_names': 'LED lights,LED LIGHTS,LED,Lights,LIGHTING,LED STRIP,LED Strip',
            },
            {
                'category': lighting_cat,
                'name': 'LED Driver',
                'specification': '12V 5A',
                'unit': 'piece',
                'rate': 900,
                'dxf_layer_names': 'DRIVER,Driver,TRANSFORMER,Transformer,LED DRIVER',
            },
            
            # === DIM LAYERS (for dimensions - skip in materials) ===
            # These are dimension layers, not materials
            # DIM-2, DIM-10, DIM-15, Dim will be ignored
            
            # === PDF/GEOMETRY LAYERS ===
            {
                'category': sheet_cat,
                'name': 'Panel',
                'specification': 'Generic/PDF',
                'unit': 'sqft',
                'rate': 120,
                'dxf_layer_names': 'PDF3_Geometry,PDF4_Geometry,PDF5_Geometry,PDF Geometry,GEOMETRY',
            },
            {
                'category': sheet_cat,
                'name': 'Background Panel',
                'specification': 'MDF/Laminate',
                'unit': 'sqft',
                'rate': 140,
                'dxf_layer_names': 'BY OTHERS,By Others,OTHERS,BACKGROUND,Background',
            },
            
            # === HATCH (Pattern fill layer) ===
            {
                'category': sheet_cat,
                'name': 'Decorative Panel',
                'specification': 'Textured/Patterned',
                'unit': 'sqft',
                'rate': 180,
                'dxf_layer_names': 'HATCH,Hatch,PATTERN,Pattern,TEXTURE',
            },
            
            # === WALL/BACKWALL ===
            {
                'category': sheet_cat,
                'name': 'Back Wall',
                'specification': 'MDF 18mm + Laminate',
                'unit': 'sqft',
                'rate': 200,
                'dxf_layer_names': 'WALL,Wall,BACKWALL,Back Wall,BACK WALL,Backwall',
            },
        ]

        # Create/Update materials
        for mat_data in company_materials:
            material, created = Material.objects.update_or_create(
                name=mat_data['name'],
                specification=mat_data['specification'],
                defaults={
                    'category': mat_data['category'],
                    'unit': mat_data['unit'],
                    'rate': mat_data['rate'],
                    'dxf_layer_names': mat_data['dxf_layer_names'],
                    'is_active': True,
                }
            )
            
            if created:
                materials_created += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  ✅ Created: {material.name} {material.specification}'
                ))
            else:
                materials_updated += 1
                self.stdout.write(
                    f'  🔄 Updated: {material.name} {material.specification}'
                )

        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS(
            f'✅ DONE! Created: {materials_created}, Updated: {materials_updated}'
        ))
        self.stdout.write('='*80 + '\n')
        
        # Show layer coverage
        self.stdout.write('\n📋 LAYER COVERAGE FOR D&G GONDOLA:')
        self.stdout.write('='*80)
        layers_covered = [
            ('Acrylic - opal', '✅ Acrylic 5mm Opal/White'),
            ('MDF', '✅ MDF 12mm'),
            ('METAL', '✅ Metal Frame'),
            ('Hardware', '✅ Hardware General'),
            ('LED 4600K', '✅ LED Strip 4600K'),
            ('LED lights', '✅ LED Strip Standard'),
            ('PDF3_Geometry', '✅ Panel Generic'),
            ('BY OTHERS', '✅ Background Panel'),
            ('HATCH', '✅ Decorative Panel'),
            ('DIM-2, DIM-10, DIM-15, Dim', '⚠️  Dimension layers (ignored)'),
            ('0', '⚠️  Default layer (ignored)'),
        ]
        
        for layer, status in layers_covered:
            self.stdout.write(f'  {layer:30s} → {status}')
        
        self.stdout.write('='*80)