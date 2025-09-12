from django.db import models
from django.core.validators import FileExtensionValidator
import uuid

class GPSTrack(models.Model):
    """Model to store GPS track information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    uploaded_file = models.FileField(
        upload_to='gps_uploads/',
        validators=[FileExtensionValidator(allowed_extensions=['csv'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    # Track statistics
    total_points = models.IntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True, help_text="Duration in seconds")
    max_speed = models.FloatField(null=True, blank=True, help_text="Max speed in m/s")
    avg_speed = models.FloatField(null=True, blank=True, help_text="Average speed in m/s")
    
    # Geographic bounds
    min_latitude = models.FloatField(null=True, blank=True)
    max_latitude = models.FloatField(null=True, blank=True)
    min_longitude = models.FloatField(null=True, blank=True)
    max_longitude = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.name} ({self.uploaded_at.strftime('%Y-%m-%d %H:%M')})"

class GPSPoint(models.Model):
    """Model to store individual GPS points"""
    track = models.ForeignKey(GPSTrack, on_delete=models.CASCADE, related_name='points')
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.FloatField(help_text="Time in seconds from start")
    speed = models.FloatField(null=True, blank=True, help_text="Speed in m/s")
    
    # Additional data from CSV if available
    original_timestamp = models.CharField(max_length=255, null=True, blank=True)
    altitude = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['track', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Point {self.latitude:.6f}, {self.longitude:.6f} at {self.timestamp:.1f}s"
