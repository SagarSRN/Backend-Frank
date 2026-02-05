from django.db import models
from apps.projects.models import Project
from apps.rooms.models import Room


class Estimate(models.Model):
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="estimate"
    )

    total_tiles_sqm = models.FloatField(default=0)
    total_paint_sqm = models.FloatField(default=0)
    cement_bags = models.IntegerField(default=0)
    sand_tons = models.FloatField(default=0)

    total_cost = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Estimate - {self.project.name}"


class RoomEstimate(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="room_estimates"
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="estimate"
    )

    tiles_sqm = models.FloatField(default=0)
    paint_sqm = models.FloatField(default=0)
    cement_bags = models.IntegerField(default=0)
    sand_tons = models.FloatField(default=0)

    cost = models.FloatField(default=0)

    def __str__(self):
        return f"{self.room.name} - ₹{self.cost}"
