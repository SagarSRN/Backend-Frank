"""
Serializers for Retail Materials API
"""

from rest_framework import serializers
from .models import MaterialCategory, Material, RetailEstimate, Component


class MaterialCategorySerializer(serializers.ModelSerializer):
    """Serializer for Material Categories"""
    
    class Meta:
        model = MaterialCategory
        fields = ['id', 'name', 'category_type', 'description']


class MaterialSerializer(serializers.ModelSerializer):
    """Serializer for Materials"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Material
        fields = [
            'id',
            'name',
            'category',
            'category_name',
            'specification',
            'unit',
            'rate',
            'dxf_layer_keywords'
        ]


class ComponentSerializer(serializers.ModelSerializer):
    """Serializer for Components"""
    
    material_name = serializers.CharField(source='material.name', read_only=True)
    category_name = serializers.CharField(source='material.category.name', read_only=True)
    rate = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Component
        fields = [
            'id',
            'estimate',
            'material',
            'material_name',
            'category_name',
            'description',
            'quantity',
            'unit',
            'rate',
            'amount',
            'created_at'
        ]


class RetailEstimateSerializer(serializers.ModelSerializer):
    """Serializer for Retail Estimates"""
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    components = ComponentSerializer(many=True, read_only=True)
    
    class Meta:
        model = RetailEstimate
        fields = [
            'id',
            'project',
            'project_name',
            'material_cost',
            'labor_cost',
            'overhead_percentage',
            'overhead_amount',
            'profit_percentage',
            'profit_amount',
            'subtotal',
            'gst_percentage',
            'gst_amount',
            'total',
            'components',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'overhead_amount',
            'profit_amount',
            'subtotal',
            'gst_amount',
            'total',
            'created_at',
            'updated_at'
        ]