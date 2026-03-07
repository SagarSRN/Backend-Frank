
from django.db import models
from apps.projects.models import Project


class MaterialCategory(models.Model):
    """
    Material categories for retail displays
    """
    
    CATEGORY_TYPES = [
        ('SHEET', 'Sheet Materials'),
        ('LIGHTING', 'Lighting'),
        ('HARDWARE', 'Hardware'),
        ('LABOR', 'Labor & Fabrication'),
        ('FINISHING', 'Finishing'),
    ]
    
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Material Category"
        verbose_name_plural = "Material Categories"
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class Material(models.Model):
    """
    Individual materials with rates
    """
    
    UNIT_CHOICES = [
        ('sqft', 'Square Feet'),
        ('meter', 'Meter'),
        ('piece', 'Piece'),
        ('unit', 'Unit'),
        ('hour', 'Hour'),
        ('liter', 'Liter'),
        ('kg', 'Kilogram'),
    ]
    
    category = models.ForeignKey(
        MaterialCategory,
        on_delete=models.CASCADE,
        related_name='materials'
    )
    name = models.CharField(max_length=100)
    specification = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Rate in ₹"
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # DXF Layer mapping (for auto-detection)
    dxf_layer_names = models.TextField(
        blank=True,
        help_text="Comma-separated layer names (e.g., MDF_18MM, MDF18, PANEL_MDF)"
    )
    
    class Meta:
        ordering = ['category', 'name', 'specification']
        verbose_name = "Material"
        verbose_name_plural = "Materials"
    
    def __str__(self):
        if self.specification:
            return f"{self.name} {self.specification} - ₹{self.rate}/{self.unit}"
        return f"{self.name} - ₹{self.rate}/{self.unit}"
    
    @property
    def layer_list(self):
        """Get list of layer names"""
        if self.dxf_layer_names:
            return [l.strip() for l in self.dxf_layer_names.split(',')]
        return []


class Component(models.Model):
    """
    Components detected/added to retail display projects
    """
    
    COMPONENT_TYPES = [
        ('PANEL', 'Panel'),
        ('SHELF', 'Shelf'),
        ('LIGHTING', 'Lighting'),
        ('HARDWARE', 'Hardware'),
        ('CUSTOM', 'Custom'),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='retail_components'
    )
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPES)
    material = models.ForeignKey(
        Material,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='components'
    )
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    
    # Optional dimensions (stored as JSON)
    dimensions = models.JSONField(
        blank=True,
        null=True,
        help_text="Store length, width, height if applicable"
    )
    
    # DXF metadata
    layer_name = models.CharField(max_length=100, blank=True)
    auto_detected = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['component_type', 'description']
        verbose_name = "Component"
        verbose_name_plural = "Components"
    
    def __str__(self):
        return f"{self.description} ({self.quantity} {self.unit})"
    
    @property
    def rate(self):
        """Get rate from material"""
        if self.material:
            return self.material.rate
        return 0
    
    @property
    def amount(self):
        """Calculate total amount"""
        return float(self.quantity) * float(self.rate)


class RetailEstimate(models.Model):
    """
    Bill of Quantities for retail display projects
    """
    
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='retail_estimate'
    )
    
    # Cost breakdown
    material_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Tax
    gst_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=18.00,
        help_text="GST percentage"
    )
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Total
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Additional info
    notes = models.TextField(blank=True)
    validity_days = models.IntegerField(default=30, help_text="Quote validity in days")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Retail Estimate"
        verbose_name_plural = "Retail Estimates"
    
    def __str__(self):
        return f"Retail Estimate - {self.project.name} (₹{self.total})"
    
    def calculate_totals(self):
        """
        Calculate all totals from components
        """
        components = self.project.retail_components.all()
        
        # Separate material and labor costs
        material_total = 0
        labor_total = 0
        
        for component in components:
            if component.material:
                if component.material.category.category_type == 'LABOR':
                    labor_total += component.amount
                else:
                    material_total += component.amount
        
        self.material_cost = material_total
        self.labor_cost = labor_total
        self.subtotal = material_total + labor_total
        self.gst_amount = self.subtotal * (self.gst_percentage / 100)
        self.total = self.subtotal + self.gst_amount
        
        self.save()
        return self.total
    
    def get_components_by_category(self):
        """
        Group components by material category
        """
        from collections import defaultdict
        
        grouped = defaultdict(list)
        
        for component in self.project.retail_components.select_related('material__category'):
            if component.material:
                category_name = component.material.category.name
                grouped[category_name].append({
                    'description': component.description,
                    'quantity': component.quantity,
                    'unit': component.unit,
                    'rate': component.rate,
                    'amount': component.amount,
                })
        
        return dict(grouped)