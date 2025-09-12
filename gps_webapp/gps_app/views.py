from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import JsonResponse
from .models import GPSTrack, GPSPoint
from .serializers import GPSTrackSerializer, GPSTrackListSerializer, FileUploadSerializer, GPSPointSerializer
from .utils import process_gps_csv, get_track_bounds

class GPSTrackViewSet(viewsets.ModelViewSet):
    queryset = GPSTrack.objects.all()
    parser_classes = (MultiPartParser, FormParser)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return GPSTrackListSerializer
        elif self.action == 'upload':
            return FileUploadSerializer
        return GPSTrackSerializer
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload and process a GPS CSV file"""
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            track = serializer.save()
            
            # Process the CSV file
            success, message = process_gps_csv(track)
            
            if success:
                # Return the processed track data
                track_serializer = GPSTrackSerializer(track)
                return Response({
                    'track': track_serializer.data,
                    'message': message
                }, status=status.HTTP_201_CREATED)
            else:
                # Delete the track if processing failed
                track.delete()
                return Response({
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def points(self, request, pk=None):
        """Get GPS points for a specific track with pagination"""
        track = self.get_object()
        points = track.points.all()
        
        # Optional filtering by time range
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        
        if start_time:
            points = points.filter(timestamp__gte=float(start_time))
        if end_time:
            points = points.filter(timestamp__lte=float(end_time))
        
        # Pagination
        page = self.paginate_queryset(points)
        if page is not None:
            serializer = GPSPointSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = GPSPointSerializer(points, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def bounds(self, request, pk=None):
        """Get geographic bounds for a track"""
        bounds = get_track_bounds(pk)
        if bounds:
            return Response(bounds)
        return Response({'error': 'Track not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get track statistics"""
        track = self.get_object()
        return Response({
            'total_points': track.total_points,
            'duration': track.duration,
            'max_speed': track.max_speed,
            'avg_speed': track.avg_speed,
            'max_speed_mph': track.max_speed * 2.237 if track.max_speed else 0,
            'avg_speed_mph': track.avg_speed * 2.237 if track.avg_speed else 0,
            'bounds': {
                'min_lat': track.min_latitude,
                'max_lat': track.max_latitude,
                'min_lon': track.min_longitude,
                'max_lon': track.max_longitude,
            }
        })

def index(request):
    """Serve the React frontend"""
    return render(request, 'gps_app/index.html')
