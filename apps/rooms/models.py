from django.db import models
from apps.projects.models import Project

class Room(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="rooms"
    )

    name = models.CharField(max_length=100)
    area = models.FloatField()   # sqm
    x_center = models.FloatField()
    y_center = models.FloatField()

    def __str__(self):
        return f"{self.name} ({self.area:.2f} sqm)"
