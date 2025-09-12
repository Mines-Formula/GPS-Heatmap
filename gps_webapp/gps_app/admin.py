from django.contrib import admin
from .models import GPSTrack, GPSPoint

@admin.register(GPSTrack)
class GPSTrackAdmin(admin.ModelAdmin):
    list_display = ('name', 'uploaded_at', 'processed', 'total_points', 'duration', 'max_speed')
    list_filter = ('processed', 'uploaded_at')
    search_fields = ('name',)
    readonly_fields = ('id', 'uploaded_at', 'processed', 'total_points', 'duration', 
                      'max_speed', 'avg_speed', 'min_latitude', 'max_latitude', 
                      'min_longitude', 'max_longitude')

@admin.register(GPSPoint)
class GPSPointAdmin(admin.ModelAdmin):
    list_display = ('track', 'latitude', 'longitude', 'timestamp', 'speed')
    list_filter = ('track',)
    search_fields = ('track__name',)
    readonly_fields = ('track', 'latitude', 'longitude', 'timestamp', 'speed', 
                      'original_timestamp', 'altitude')
