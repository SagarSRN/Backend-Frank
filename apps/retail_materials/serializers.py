
from rest_framework import serializers
from .models import MaterialCategory, Material, Component, RetailEstimate


class MaterialCategorySerializer(serializers.ModelSerializer):
    material_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MaterialCategory
        fields = ['id', 'name', 'category_type', 'description', 
                  'display_order', 'is_active', 'material_count']
    
    def get_material_count(self, obj):
        return obj.materials.filter(is_active=True).count()


class MaterialSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_type = serializers.CharField(source='category.category_type', read_only=True)
    
    class Meta:
        model = Material
        fields = ['id', 'category', 'category_name', 'category_type',
                  'name', 'specification', 'unit', 'rate', 'notes',
                  'dxf_layer_names', 'is_active']


class ComponentSerializer(serializers.ModelSerializer):
    material_details = MaterialSerializer(source='material', read_only=True)
    rate = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Component
        fields = ['id', 'project', 'component_type', 'description',
                  'quantity', 'unit', 'material', 'material_details',
                  'rate', 'amount', 'dimensions', 'layer_name',
                  'auto_detected', 'created_at']
        read_only_fields = ['auto_detected', 'created_at']


class RetailEstimateSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    components_by_category = serializers.SerializerMethodField()
    
    class Meta:
        model = RetailEstimate
        fields = ['id', 'project', 'project_name', 'material_cost',
                  'labor_cost', 'subtotal', 'gst_percentage', 'gst_amount',
                  'total', 'notes', 'validity_days', 'components_by_category',
                  'created_at', 'updated_at']
        read_only_fields = ['material_cost', 'labor_cost', 'subtotal',
                           'gst_amount', 'total', 'created_at', 'updated_at']
    
    def get_components_by_category(self, obj):
        return obj.get_components_by_category()


class RetailEstimateDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with all components"""
    project_name = serializers.CharField(source='project.name', read_only=True)
    components = ComponentSerializer(source='project.retail_components', many=True, read_only=True)
    components_by_category = serializers.SerializerMethodField()
    
    class Meta:
        model = RetailEstimate
        fields = ['id', 'project', 'project_name', 'material_cost',
                  'labor_cost', 'subtotal', 'gst_percentage', 'gst_amount',
                  'total', 'notes', 'validity_days', 'components',
                  'components_by_category', 'created_at', 'updated_at']
    
    def get_components_by_category(self, obj):
        return obj.get_components_by_category()