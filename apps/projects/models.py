from django.db import models


class Project(models.Model):
    PROJECT_TYPE_CHOICES = [
        ("Residential", "Residential"),
        ("Commercial", "Commercial"),
    ]

    SCOPE_CHOICES = [
        ("Civil + Interior", "Civil + Interior"),
        ("Civil Only", "Civil Only"),
        ("Interior Only", "Interior Only"),
    ]

    name = models.CharField(max_length=255)
    project_type = models.CharField(
        max_length=20, choices=PROJECT_TYPE_CHOICES
    )
    scope = models.CharField(
        max_length=30, choices=SCOPE_CHOICES
    )
    location = models.CharField(max_length=100)
    builtup_area = models.FloatField(help_text="Area in sqft")

    status = models.CharField(
        max_length=50, default="Planning"
    )
    total_cost = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
