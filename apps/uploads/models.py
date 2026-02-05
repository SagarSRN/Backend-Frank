from django.db import models
from apps.projects.models import Project


class PlanUpload(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="uploads"
    )

    file = models.FileField(upload_to="plans/")

    # ✅ FIX: default added (prevents migration crash)
    file_type = models.CharField(
        max_length=20,
        default="unknown"
    )

    scale = models.CharField(
        max_length=10,
        default="mm",
        choices=[
            ("mm", "Millimeter"),
            ("m", "Meter"),
        ]
    )

    # ✅ THIS IS THE KEY FIELD FOR STEP 1
    processed = models.BooleanField(default=False)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name} - Plan ({self.file_type})"
