"""
Upload Models
Handles file uploads and processing status
"""

from django.db import models
from apps.projects.models import Project


class PlanUpload(models.Model):
    """
    File upload tracking for projects
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    FILE_TYPE_CHOICES = [
        ('dxf', 'DXF File'),
        ('dwg', 'DWG File'),
        ('pdf', 'PDF File'),
    ]
    
    SCALE_CHOICES = [
        ('mm', 'Millimeters'),
        ('cm', 'Centimeters'),
        ('m', 'Meters'),
        ('in', 'Inches'),
        ('ft', 'Feet'),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='uploads'
    )
    
    file = models.FileField(
        upload_to='uploads/%Y/%m/%d/',
        help_text='Upload DXF, DWG, or PDF file'
    )
    
    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        default='dxf'
    )
    
    scale = models.CharField(
        max_length=10,
        choices=SCALE_CHOICES,
        default='mm',
        help_text='Scale unit used in the file'
    )
    
    processing_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        help_text='Current processing status'
    )
    
    processing_result = models.JSONField(
        null=True,
        blank=True,
        help_text='Processing results or error details'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Plan Upload'
        verbose_name_plural = 'Plan Uploads'
    
    def __str__(self):
        return f"{self.project.name} - {self.file.name} ({self.processing_status})"
    
    @property
    def filename(self):
        """Get filename without path"""
        import os
        return os.path.basename(self.file.name)
    
    @property
    def file_size(self):
        """Get file size in bytes"""
        try:
            return self.file.size
        except:
            return 0