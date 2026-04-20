"""
Retail Materials Models
Handles material categories, materials, retail estimates, and components
"""

from django.db import models
from decimal import Decimal
from apps.projects.models import Project


class MaterialCategory(models.Model):
    """Categories for organizing materials"""
    
    CATEGORY_TYPES = [
        ('SHEET', 'Sheet Materials'),
        ('LIGHTING', 'Lighting'),
        ('HARDWARE', 'Hardware'),
        ('FINISHING', 'Finishing'),
        ('LABOR', 'Labor'),
    ]
    
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Material Categories"
        ordering = ['category_type', 'name']
    
    def __str__(self):
        return self.name


class Material(models.Model):
    """Materials used in retail displays"""
    
    name = models.CharField(max_length=100)
    category = models.ForeignKey(MaterialCategory, on_delete=models.CASCADE, related_name='materials')
    unit = models.CharField(max_length=20, default='sqft')
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    specification = models.TextField(blank=True)
    dxf_layer_keywords = models.TextField(
        blank=True,
        help_text="Comma-separated keywords for DXF layer matching"
    )
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} - ₹{self.rate}/{self.unit}"


class RetailEstimate(models.Model):
    """Retail display estimate for a project"""
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='retail_estimates'
    )
    
    material_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    labor_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    overhead_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00')
    )
    
    profit_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00')
    )
    
    gst_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('18.00')
    )
    
    overhead_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    profit_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    gst_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Estimate for {self.project.name} - ₹{self.total}"
    
    def calculate_totals(self):
        """Calculate all totals and save"""
        
        # Calculate overhead
        base_cost = self.material_cost + self.labor_cost
        self.overhead_amount = base_cost * (self.overhead_percentage / Decimal('100'))
        
        # Calculate subtotal before profit
        subtotal_before_profit = base_cost + self.overhead_amount
        
        # Calculate profit
        self.profit_amount = subtotal_before_profit * (self.profit_percentage / Decimal('100'))
        
        # Calculate subtotal (before GST)
        self.subtotal = subtotal_before_profit + self.profit_amount
        
        # Calculate GST
        self.gst_amount = self.subtotal * (self.gst_percentage / Decimal('100'))
        
        # Calculate total
        self.total = self.subtotal + self.gst_amount
        
        self.save()
    
    def save(self, *args, **kwargs):
        """Override save to auto-calculate totals"""
        
        # Only auto-calculate if not explicitly disabled
        skip_calculation = kwargs.pop('skip_calculation', False)
        
        if not skip_calculation:
            # Calculate overhead
            base_cost = self.material_cost + self.labor_cost
            self.overhead_amount = base_cost * (self.overhead_percentage / Decimal('100'))
            
            # Calculate subtotal before profit
            subtotal_before_profit = base_cost + self.overhead_amount
            
            # Calculate profit
            self.profit_amount = subtotal_before_profit * (self.profit_percentage / Decimal('100'))
            
            # Calculate subtotal (before GST)
            self.subtotal = subtotal_before_profit + self.profit_amount
            
            # Calculate GST
            self.gst_amount = self.subtotal * (self.gst_percentage / Decimal('100'))
            
            # Calculate total
            self.total = self.subtotal + self.gst_amount
        
        super().save(*args, **kwargs)


class Component(models.Model):
    """Individual component in a retail estimate"""
    
    estimate = models.ForeignKey(
        RetailEstimate,
        on_delete=models.CASCADE,
        related_name='components'
    )
    
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name='components'
    )
    
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['material__category', 'description']
    
    def __str__(self):
        return f"{self.description} - {self.quantity} {self.unit}"
    
    @property
    def rate(self):
        """Get rate from material"""
        return self.material.rate
    
    @property
    def amount(self):
        """Calculate amount (quantity × rate)"""
        return self.quantity * self.material.rate
    
    @property
    def material_spec(self):
        """Get material specification"""
        return self.material.specification