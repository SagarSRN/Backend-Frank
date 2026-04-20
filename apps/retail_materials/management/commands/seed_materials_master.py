"""
Master Material Seeding Command - FINAL VERSION
Creates all retail materials with correct rates and exact layer matching
"""

from django.core.management.base import BaseCommand
from apps.retail_materials.models import MaterialCategory, Material
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed retail materials with exact DXF layer keyword matching'

    def handle(self, *args, **kwargs):
        self.stdout.write('\n' + '='*80)
        self.stdout.write('Creating materials with exact layer matching...')
        self.stdout.write('='*80 + '\n')

        # Clear existing materials
        Material.objects.all().delete()
        MaterialCategory.objects.all().delete()

        # Create categories
        categories = {
            'SHEET': MaterialCategory.objects.create(
                name='Sheet Materials',
                category_type='SHEET',
                description='Acrylic, Glass, MDF, Plywood, etc.'
            ),
            'METAL': MaterialCategory.objects.create(
                name='Metal & Frames',
                category_type='METAL',
                description='Stainless steel, Aluminum frames'
            ),
            'LIGHTING': MaterialCategory.objects.create(
                name='Lighting',
                category_type='LIGHTING',
                description='LED strips, lights, drivers'
            ),
            'HARDWARE': MaterialCategory.objects.create(
                name='Hardware & Fittings',
                category_type='HARDWARE',
                description='Brackets, screws, fittings'
            ),
            'FINISHING': MaterialCategory.objects.create(
                name='Finishing',
                category_type='FINISHING',
                description='Lacquer, paint, lipping'
            ),
            'LABOR': MaterialCategory.objects.create(
                name='Labor',
                category_type='LABOR',
                description='Fabrication and installation labor'
            ),
        }

        # Material definitions with exact layer keywords
        materials_data = [
            # SHEET MATERIALS
            {
                'name': 'Acrylic 5mm Clear',
                'category': categories['SHEET'],
                'unit': 'sqft',
                'rate': Decimal('3800.00'),
                'specification': '5mm clear cast acrylic sheet',
                'keywords': 'Acrylic - clear,Acrylic-clear,ACRYLIC CLEAR,acrylic clear,Acrylic clear'
            },
            {
                'name': 'Acrylic 5mm Opal',
                'category': categories['SHEET'],
                'unit': 'sqft',
                'rate': Decimal('3500.00'),
                'specification': '5mm opal white acrylic sheet',
                'keywords': 'Acrylic - opal,Acrylic-opal,ACRYLIC OPAL,acrylic opal,Acrylic opal'
            },
            {
                'name': 'Acrylic 8mm Clear',
                'category': categories['SHEET'],
                'unit': 'sqft',
                'rate': Decimal('4500.00'),
                'specification': '8mm clear cast acrylic sheet',
                'keywords': 'Acrylic 8mm,ACRYLIC 8MM'
            },
            {
                'name': 'Glass 10mm Tempered',
                'category': categories['SHEET'],
                'unit': 'sqft',
                'rate': Decimal('6500.00'),
                'specification': '10mm tempered safety glass',
                'keywords': 'glass,Glass,GLASS,tempered glass'
            },
            {
                'name': 'Mirror 5mm',
                'category': categories['SHEET'],
                'unit': 'sqft',
                'rate': Decimal('4500.00'),
                'specification': '5mm silver mirror',
                'keywords': 'Mirror,MIRROR,mirror'
            },
            {
                'name': 'MDF 18mm',
                'category': categories['SHEET'],
                'unit': 'sqft',
                'rate': Decimal('800.00'),
                'specification': '18mm medium density fiberboard',
                'keywords': 'MDF,mdf,Mdf'
            },
            {
                'name': 'Plywood 18mm',
                'category': categories['SHEET'],
                'unit': 'sqft',
                'rate': Decimal('1200.00'),
                'specification': '18mm commercial plywood',
                'keywords': 'Plywood,PLYWOOD,plywood'
            },
            {
                'name': 'Bendy Plywood 6mm',
                'category': categories['SHEET'],
                'unit': 'sqft',
                'rate': Decimal('1800.00'),
                'specification': '6mm flexible plywood',
                'keywords': 'Bendy Plywood,BENDY PLYWOOD,bendy plywood'
            },
            {
                'name': 'Corian 12mm',
                'category': categories['SHEET'],
                'unit': 'sqft',
                'rate': Decimal('8000.00'),
                'specification': '12mm solid surface',
                'keywords': 'Corian,CORIAN,corian'
            },
            {
                'name': 'Marble 18mm',
                'category': categories['SHEET'],
                'unit': 'sqft',
                'rate': Decimal('5500.00'),
                'specification': '18mm natural marble',
                'keywords': 'Marble,MARBLE,marble'
            },
            {
                'name': 'Solid Wood',
                'category': categories['SHEET'],
                'unit': 'sqft',
                'rate': Decimal('2500.00'),
                'specification': 'Solid wood boards',
                'keywords': 'Solid wood,SOLID WOOD,solid wood,Timber,TIMBER'
            },

            # METAL & FRAMES
            {
                'name': 'Metal Frame SS304',
                'category': categories['METAL'],
                'unit': 'meter',
                'rate': Decimal('2500.00'),
                'specification': 'Stainless steel 304 frame profile',
                'keywords': 'METAL,Metal,metal,stainless steel,Stainless steel,STAINLESS STEEL,steel,Steel,SS304'
            },
            {
                'name': 'Aluminum Extrusion',
                'category': categories['METAL'],
                'unit': 'meter',
                'rate': Decimal('1800.00'),
                'specification': 'Aluminum frame extrusion',
                'keywords': 'aluminium,Aluminium,ALUMINIUM,aluminum,Aluminum'
            },

            # LIGHTING - CRITICAL: LED as PIECE unit!
            {
                'name': 'LED Strip 4600K',
                'category': categories['LIGHTING'],
                'unit': 'piece',  # CHANGED TO PIECE!
                'rate': Decimal('1200.00'),
                'specification': 'LED strip light 4600K daylight',
                'keywords': 'LED 4600K,led 4600k,LED4600K,EL_LIGHTING'
            },
            {
                'name': 'LED Lights',
                'category': categories['LIGHTING'],
                'unit': 'piece',
                'rate': Decimal('1200.00'),
                'specification': 'LED light fixtures',
                'keywords': 'LED lights,LED Lights,led lights'
            },
            {
                'name': 'LED Lumisheet',
                'category': categories['LIGHTING'],
                'unit': 'sqft',
                'rate': Decimal('2500.00'),
                'specification': 'LED backlit sheet',
                'keywords': 'LED lumisheet,LED Lumisheet,lumisheet'
            },
            {
                'name': 'T5 Lighting',
                'category': categories['LIGHTING'],
                'unit': 'meter',
                'rate': Decimal('600.00'),
                'specification': 'T5 fluorescent tube',
                'keywords': 'T5 lighting,T5 Lighting,T5'
            },

            # HARDWARE & FITTINGS
            {
                'name': 'Hardware General',
                'category': categories['HARDWARE'],
                'unit': 'piece',
                'rate': Decimal('500.00'),
                'specification': 'General hardware and fittings',
                'keywords': 'Hardware,HARDWARE,hardware,Fitting,fittings,Fittings'
            },
            {
                'name': 'Screws & Fasteners',
                'category': categories['HARDWARE'],
                'unit': 'piece',
                'rate': Decimal('50.00'),
                'specification': 'Screws and fasteners',
                'keywords': 'Screw,SCREW,screw,screws'
            },
            {
                'name': 'Drawer Box',
                'category': categories['HARDWARE'],
                'unit': 'piece',
                'rate': Decimal('3500.00'),
                'specification': 'Drawer box assembly',
                'keywords': 'Drawer box,DRAWER BOX,drawer box'
            },
            {
                'name': 'Rails',
                'category': categories['HARDWARE'],
                'unit': 'meter',
                'rate': Decimal('800.00'),
                'specification': 'Drawer/door rails',
                'keywords': 'Rails,RAILS,rails'
            },
            {
                'name': 'Gaskets',
                'category': categories['HARDWARE'],
                'unit': 'meter',
                'rate': Decimal('150.00'),
                'specification': 'Rubber gaskets',
                'keywords': 'Gaskets,GASKETS,gaskets'
            },
            {
                'name': 'Sleeve',
                'category': categories['HARDWARE'],
                'unit': 'piece',
                'rate': Decimal('200.00'),
                'specification': 'Cable/pipe sleeve',
                'keywords': 'Sleeve,SLEEVE,sleeve'
            },
            {
                'name': 'Threshold',
                'category': categories['HARDWARE'],
                'unit': 'meter',
                'rate': Decimal('600.00'),
                'specification': 'Door threshold',
                'keywords': 'Threshold,THRESHOLD,threshold'
            },

            # FINISHING
            {
                'name': 'Lacquered Surface',
                'category': categories['FINISHING'],
                'unit': 'sqft',
                'rate': Decimal('1200.00'),
                'specification': 'Lacquer finish coating',
                'keywords': 'Lacquered surface,LACQUERED SURFACE,lacquered,Lacquered'
            },
            {
                'name': 'Lipping PVC',
                'category': categories['FINISHING'],
                'unit': 'meter',
                'rate': Decimal('150.00'),
                'specification': 'PVC edge lipping',
                'keywords': 'Lipping - PVC,LIPPING PVC,lipping pvc'
            },
            {
                'name': 'Lipping Melamine',
                'category': categories['FINISHING'],
                'unit': 'meter',
                'rate': Decimal('200.00'),
                'specification': 'Melamine edge lipping',
                'keywords': 'Lipping - melamine,LIPPING MELAMINE,lipping melamine'
            },
            {
                'name': 'Lipping General',
                'category': categories['FINISHING'],
                'unit': 'meter',
                'rate': Decimal('180.00'),
                'specification': 'Edge lipping general',
                'keywords': 'Lipping,LIPPING,lipping'
            },

            # LABOR
            {
                'name': 'Fabrication Labor',
                'category': categories['LABOR'],
                'unit': 'hour',
                'rate': Decimal('800.00'),
                'specification': 'Skilled fabrication labor',
                'keywords': 'fabrication,Fabrication,FABRICATION'
            },
            {
                'name': 'Installation Labor',
                'category': categories['LABOR'],
                'unit': 'hour',
                'rate': Decimal('1200.00'),
                'specification': 'On-site installation labor',
                'keywords': 'installation,Installation,INSTALLATION'
            },
        ]

        # Create materials
        created_count = 0
        for mat_data in materials_data:
            material = Material.objects.create(
                name=mat_data['name'],
                category=mat_data['category'],
                unit=mat_data['unit'],
                rate=mat_data['rate'],
                specification=mat_data['specification'],
                dxf_layer_keywords=mat_data['keywords']
            )
            created_count += 1
            self.stdout.write(f'  ✓ Created: {material.name} (₹{material.rate}/{material.unit})')

        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully created {created_count} materials!'))
        self.stdout.write('='*80 + '\n')

        # Summary
        self.stdout.write('\nLayer keywords configured for:')
        self.stdout.write('  - Acrylic (clear, opal)')
        self.stdout.write('  - Glass, Mirror')
        self.stdout.write('  - MDF, Plywood, Bendy Plywood')
        self.stdout.write('  - Metal (SS304, Aluminum)')
        self.stdout.write('  - Corian, Marble, Solid Wood')
        self.stdout.write('  - LED (4600K, lights, lumisheet) ← PIECE UNIT!')
        self.stdout.write('  - Hardware, Fittings, Screws')
        self.stdout.write('  - Lacquered surface, Lipping')
        self.stdout.write('  - Labor (Fabrication, Installation)')
        self.stdout.write('\nNow upload your DXF file!\n')