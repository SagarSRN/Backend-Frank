"""
Enhanced Estimation Models with detailed line items
Add this to apps/estimates/models.py
"""

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
    updated_at = models.DateTimeField(auto_now=True)

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


# ========== NEW MODELS FOR DETAILED ESTIMATION ==========

class EstimateLineItem(models.Model):
    """
    Detailed line items for estimate (like Brickwork, Plastering, etc.)
    """
    CATEGORY_CHOICES = [
        ('Civil', 'Civil Work'),
        ('Interior', 'Interior Work'),
        ('Electrical', 'Electrical Work'),
        ('Plumbing', 'Plumbing Work'),
        ('Painting', 'Painting Work'),
        ('Flooring', 'Flooring Work'),
    ]

    estimate = models.ForeignKey(
        Estimate,
        on_delete=models.CASCADE,
        related_name='line_items'
    )
    
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Room this item belongs to (if applicable)"
    )

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    item_name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    
    quantity = models.FloatField(help_text="Quantity of work")
    unit = models.CharField(max_length=20, help_text="sqm, sqft, nos, etc.")
    rate = models.FloatField(help_text="Rate per unit in ₹")
    amount = models.FloatField(help_text="Total amount (quantity × rate)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'item_name']

    def save(self, *args, **kwargs):
        # Auto-calculate amount
        self.amount = self.quantity * self.rate
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category} - {self.item_name}"


class RateCard(models.Model):
    """
    Rate card for different work items
    Allows admin to configure and update rates
    """
    CATEGORY_CHOICES = EstimateLineItem.CATEGORY_CHOICES

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    item_name = models.CharField(max_length=150)
    unit = models.CharField(max_length=20)
    rate = models.FloatField(help_text="Rate per unit in ₹")
    
    location = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Specific location for this rate (optional)"
    )
    
    effective_from = models.DateField()
    is_active = models.BooleanField(default=True)
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'item_name']
        unique_together = ['category', 'item_name', 'location', 'effective_from']

    def __str__(self):
        return f"{self.category} - {self.item_name} @ ₹{self.rate}/{self.unit}"


class WorkProgress(models.Model):
    """
    Track progress of work items
    """
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='work_progress')
    line_item = models.OneToOneField(
        EstimateLineItem,
        on_delete=models.CASCADE,
        related_name='progress'
    )
    
    planned_quantity = models.FloatField()
    completed_quantity = models.FloatField(default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    
    start_date = models.DateField(null=True, blank=True)
    target_completion_date = models.DateField(null=True, blank=True)
    actual_completion_date = models.DateField(null=True, blank=True)
    
    remarks = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def completion_percentage(self):
        """Calculate completion percentage"""
        if self.planned_quantity == 0:
            return 0
        return round((self.completed_quantity / self.planned_quantity) * 100, 2)

    @property
    def is_delayed(self):
        """Check if work is delayed"""
        if self.target_completion_date and self.status != 'completed':
            from datetime import date
            return date.today() > self.target_completion_date
        return False

    def __str__(self):
        return f"{self.line_item.item_name} - {self.completion_percentage}%"
