from rest_framework import serializers
from .models import PlanUpload


class PlanUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanUpload
        fields = "__all__"
