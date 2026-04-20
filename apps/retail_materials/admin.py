"""
Django Admin Configuration for Retail Materials
"""

from django.contrib import admin
from django.utils.html import format_html
from decimal import Decimal
from .models import MaterialCategory, Material, RetailEstimate, Component


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type')
    list_filter = ('category_type',)
    search_fields = ('name',)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'rate_display', 'unit')
    list_filter = ('category', 'unit')
    search_fields = ('name', 'specification')
    
    def rate_display(self, obj):
        """Display rate with currency"""
        try:
            rate_value = float(obj.rate) if isinstance(obj.rate, (Decimal, int, float)) else 0
            return format_html('₹{:,.2f}', rate_value)
        except (ValueError, TypeError):
            return '₹0.00'
    rate_display.short_description = 'Rate'


@admin.register(RetailEstimate)
class RetailEstimateAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'material_cost_display', 'labor_cost_display', 'total_display')
    search_fields = ('project__name',)
    
    def material_cost_display(self, obj):
        """Display material cost with currency"""
        try:
            cost_value = float(obj.material_cost) if isinstance(obj.material_cost, (Decimal, int, float)) else 0
            return format_html('₹{:,.2f}', cost_value)
        except (ValueError, TypeError):
            return '₹0.00'
    material_cost_display.short_description = 'Material Cost'
    
    def labor_cost_display(self, obj):
        """Display labor cost with currency"""
        try:
            cost_value = float(obj.labor_cost) if isinstance(obj.labor_cost, (Decimal, int, float)) else 0
            return format_html('₹{:,.2f}', cost_value)
        except (ValueError, TypeError):
            return '₹0.00'
    labor_cost_display.short_description = 'Labor Cost'
    
    def total_display(self, obj):
        """Display total with currency"""
        try:
            total_value = float(obj.total) if isinstance(obj.total, (Decimal, int, float)) else 0
            return format_html('₹{:,.2f}', total_value)
        except (ValueError, TypeError):
            return '₹0.00'
    total_display.short_description = 'Total'


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ('id', 'estimate', 'material', 'description', 'quantity', 'unit', 'rate_display', 'amount_display')
    list_filter = ('unit',)
    search_fields = ('description', 'material__name')
    
    def rate_display(self, obj):
        """Display rate with currency (from material)"""
        try:
            rate_value = obj.rate
            if isinstance(rate_value, (Decimal, int, float)):
                return format_html('₹{:,.2f}', float(rate_value))
            else:
                return rate_value
        except (ValueError, TypeError, AttributeError):
            return '₹0.00'
    rate_display.short_description = 'Rate'
    
    def amount_display(self, obj):
        """Display calculated amount with currency"""
        try:
            amount_value = obj.amount
            if isinstance(amount_value, (Decimal, int, float)):
                return format_html('₹{:,.2f}', float(amount_value))
            else:
                return amount_value
        except (ValueError, TypeError, AttributeError):
            return '₹0.00'
    amount_display.short_description = 'Amount'
    