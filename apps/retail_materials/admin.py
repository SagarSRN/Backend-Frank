
from django.contrib import admin
from django.utils.html import format_html
from .models import MaterialCategory, Material, Component, RetailEstimate


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'material_count', 'display_order', 'is_active']
    list_filter = ['category_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['display_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category_type', 'description')
        }),
        ('Settings', {
            'fields': ('display_order', 'is_active')
        }),
    )
    
    def material_count(self, obj):
        count = obj.materials.filter(is_active=True).count()
        return format_html(
            '<span style="color: #4472C4; font-weight: bold;">{} materials</span>',
            count
        )
    material_count.short_description = 'Active Materials'


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'specification', 'category', 'rate_display', 'unit', 'is_active']
    list_filter = ['category__category_type', 'category', 'unit', 'is_active']
    search_fields = ['name', 'specification', 'dxf_layer_names', 'notes']
    ordering = ['category', 'name', 'specification']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'specification')
        }),
        ('Pricing', {
            'fields': ('rate', 'unit'),
            'description': 'Enter rate in ₹ (Rupees)'
        }),
        ('DXF Layer Mapping', {
            'fields': ('dxf_layer_names',),
            'description': 'Comma-separated layer names that map to this material (e.g., MDF_18MM, MDF18, PANEL_MDF)'
        }),
        ('Additional Info', {
            'fields': ('notes', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def rate_display(self, obj):
        return format_html(
            '<span style="color: #2E7D32; font-weight: bold;">₹{}</span>',
            obj.rate
        )
    rate_display.short_description = 'Rate'
    
    actions = ['activate_materials', 'deactivate_materials', 'export_to_excel']
    
    def activate_materials(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} materials activated.')
    activate_materials.short_description = 'Activate selected materials'
    
    def deactivate_materials(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} materials deactivated.')
    deactivate_materials.short_description = 'Deactivate selected materials'


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ['description', 'project', 'component_type', 'quantity', 'unit', 
                    'material_name', 'rate_display', 'amount_display', 'auto_detected']
    list_filter = ['component_type', 'auto_detected', 'project__project_type']
    search_fields = ['description', 'project__name', 'material__name', 'layer_name']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Project Info', {
            'fields': ('project', 'component_type')
        }),
        ('Component Details', {
            'fields': ('description', 'quantity', 'unit')
        }),
        ('Material', {
            'fields': ('material',)
        }),
        ('DXF Data', {
            'fields': ('layer_name', 'dimensions', 'auto_detected'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['auto_detected', 'created_at']
    
    def material_name(self, obj):
        if obj.material:
            return obj.material.name
        return '-'
    material_name.short_description = 'Material'
    
    def rate_display(self, obj):
        if obj.material:
            return format_html('₹{}', obj.rate)
        return '-'
    rate_display.short_description = 'Rate'
    
    def amount_display(self, obj):
        return format_html(
            '<span style="color: #2E7D32; font-weight: bold;">₹{:,.2f}</span>',
            obj.amount
        )
    amount_display.short_description = 'Amount'


@admin.register(RetailEstimate)
class RetailEstimateAdmin(admin.ModelAdmin):
    list_display = ['project', 'component_count', 'material_cost_display', 
                    'labor_cost_display', 'total_display', 'created_at']
    list_filter = ['created_at']
    search_fields = ['project__name', 'notes']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Project', {
            'fields': ('project',)
        }),
        ('Cost Breakdown', {
            'fields': ('material_cost', 'labor_cost', 'subtotal')
        }),
        ('Tax', {
            'fields': ('gst_percentage', 'gst_amount')
        }),
        ('Total', {
            'fields': ('total',)
        }),
        ('Additional Info', {
            'fields': ('notes', 'validity_days'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['material_cost', 'labor_cost', 'subtotal', 'gst_amount', 'total']
    
    def component_count(self, obj):
        count = obj.project.retail_components.count()
        return format_html(
            '<span style="color: #1976D2;">{} components</span>',
            count
        )
    component_count.short_description = 'Components'
    
    def material_cost_display(self, obj):
        return format_html('₹{:,.2f}', obj.material_cost)
    material_cost_display.short_description = 'Material Cost'
    
    def labor_cost_display(self, obj):
        return format_html('₹{:,.2f}', obj.labor_cost)
    labor_cost_display.short_description = 'Labor Cost'
    
    def total_display(self, obj):
        return format_html(
            '<span style="color: #2E7D32; font-weight: bold; font-size: 14px;">₹{:,.2f}</span>',
            obj.total
        )
    total_display.short_description = 'Total'
    
    actions = ['recalculate_estimates']
    
    def recalculate_estimates(self, request, queryset):
        for estimate in queryset:
            estimate.calculate_totals()
        self.message_user(request, f'{queryset.count()} estimates recalculated.')
    recalculate_estimates.short_description = 'Recalculate selected estimates'