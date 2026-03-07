from django.db import models


class Project(models.Model):
    """
    Project model supporting multiple project types
    """
    
    PROJECT_TYPES = [
        ('RESIDENTIAL', 'Residential'),
        ('RETAIL', 'Retail Display'),
        ('COMMERCIAL', 'Commercial'),
    ]
    
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    project_type = models.CharField(
        max_length=20,
        choices=PROJECT_TYPES,
        default='RESIDENTIAL',
        help_text="Select project type"
    )
    builtup_area = models.FloatField(
        default=0,
        blank=True,
        help_text="Built-up area in sq ft (for residential)"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Project"
        verbose_name_plural = "Projects"
    
    def __str__(self):
        return f"{self.name} ({self.get_project_type_display()})"
    
    @property
    def is_residential(self):
        return self.project_type == 'RESIDENTIAL'
    
    @property
    def is_retail(self):
        return self.project_type == 'RETAIL'
    
    @property
    def room_count(self):
        """Get room count for residential projects"""
        if self.is_residential:
            return self.rooms.count()
        return 0
    
    @property
    def component_count(self):
        """Get component count for retail projects"""
        if self.is_retail:
            return self.retail_components.count()
        return 0
























