from rest_framework import serializers
from .models import GPSTrack, GPSPoint

class GPSPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPSPoint
        fields = ['latitude', 'longitude', 'timestamp', 'speed', 'altitude']

class GPSTrackSerializer(serializers.ModelSerializer):
    points = GPSPointSerializer(many=True, read_only=True)
    points_count = serializers.IntegerField(source='points.count', read_only=True)
    
    class Meta:
        model = GPSTrack
        fields = [
            'id', 'name', 'uploaded_at', 'processed', 'total_points', 
            'duration', 'max_speed', 'avg_speed', 'min_latitude', 
            'max_latitude', 'min_longitude', 'max_longitude', 
            'points', 'points_count'
        ]

class GPSTrackListSerializer(serializers.ModelSerializer):
    """Lighter serializer for listing tracks without points"""
    points_count = serializers.IntegerField(source='points.count', read_only=True)
    
    class Meta:
        model = GPSTrack
        fields = [
            'id', 'name', 'uploaded_at', 'processed', 'total_points', 
            'duration', 'max_speed', 'avg_speed', 'min_latitude', 
            'max_latitude', 'min_longitude', 'max_longitude', 'points_count'
        ]

class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPSTrack
        fields = ['name', 'uploaded_file']