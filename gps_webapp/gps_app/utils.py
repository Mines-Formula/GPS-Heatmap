import pandas as pd
import numpy as np
from geopy.distance import geodesic
from .models import GPSTrack, GPSPoint
from django.db import transaction
import os

def process_gps_csv(track_instance):
    """
    Process uploaded CSV file using EXACT same logic as generate.py
    Handles CAN bus data format with Timestamp, CANID, Sensor, Value, Unit columns
    """
    try:
        file_path = track_instance.uploaded_file.path
        file_size = os.path.getsize(file_path)
        
        print(f"Processing CSV file: {file_path} ({file_size / (1024*1024):.1f} MB)")
        
        # Read and filter data more efficiently (EXACT same as generate.py)
        df = pd.read_csv(file_path)
        print(f"Total rows in CSV: {len(df)}")
        print(f"CSV columns: {list(df.columns)}")
        
        # Filter for GPS sensors (EXACT same as generate.py)
        filtered_df = df[df['Sensor'].isin(['Longitude', 'Latitude'])]
        print(f"Rows with GPS data: {len(filtered_df)}")
        
        if len(filtered_df) == 0:
            return False, "No GPS data found. CSV must contain rows with Sensor = 'Longitude' and 'Latitude'"
        
        # Pivot the data to have lat/lon in separate columns (EXACT same as generate.py)
        pivot_df = filtered_df.pivot_table(
            index='Timestamp', 
            columns='Sensor', 
            values='Value', 
            aggfunc='first'
        ).reset_index()
        
        print(f"Pivoted data shape: {pivot_df.shape}")
        print(f"Pivot columns: {list(pivot_df.columns)}")
        
        # Drop rows where either lat or lon is missing (EXACT same as generate.py)
        pivot_df = pivot_df.dropna(subset=['Latitude', 'Longitude'])
        print(f"After dropping NaN: {len(pivot_df)} rows")
        
        if len(pivot_df) < 2:
            return False, "Need at least 2 valid GPS coordinate pairs"
        
        # Convert timestamp to seconds (EXACT same as generate.py)
        pivot_df['seconds'] = pivot_df['Timestamp'] / 1000
        
        # Skip first 3 timestamps and remove duplicates by second (EXACT same as generate.py)
        pivot_df = pivot_df.iloc[3:].copy()
        pivot_df['second_int'] = pivot_df['seconds'].astype(int)
        pivot_df = pivot_df.drop_duplicates(subset=['second_int'], keep='first')
        
        # Sort by timestamp to ensure proper order (EXACT same as generate.py)
        pivot_df = pivot_df.sort_values('seconds').reset_index(drop=True)
        
        print(f"Final processed data: {len(pivot_df)} points")
        
        if len(pivot_df) < 2:
            return False, "Not enough GPS points after processing"
        
        # Calculate speeds using EXACT same logic as generate.py
        speeds = calculate_speeds_vectorized(pivot_df)
        pivot_df['speed'] = speeds
        
        # Create GPS points for database
        gps_points = []
        for i, row in pivot_df.iterrows():
            point = GPSPoint(
                track=track_instance,
                latitude=row['Latitude'],
                longitude=row['Longitude'],
                timestamp=row['seconds'],
                speed=row['speed'],
                original_timestamp=str(row['Timestamp'])
            )
            gps_points.append(point)
        
        # Bulk create all points
        GPSPoint.objects.bulk_create(gps_points, batch_size=1000)
        
        # Update track statistics
        lats = pivot_df['Latitude'].values
        lons = pivot_df['Longitude'].values
        
        track_instance.total_points = len(gps_points)
        track_instance.duration = float(pivot_df['seconds'].iloc[-1]) if len(pivot_df) > 0 else 0.0
        track_instance.max_speed = float(speeds.max()) if len(speeds) > 0 else 0.0
        track_instance.avg_speed = float(np.mean(speeds)) if len(speeds) > 0 else 0.0
        track_instance.min_latitude = float(lats.min())
        track_instance.max_latitude = float(lats.max())
        track_instance.min_longitude = float(lons.min())
        track_instance.max_longitude = float(lons.max())
        track_instance.processed = True
        track_instance.save()
        
        return True, f"Successfully processed {len(gps_points)} GPS points from CAN bus data"
        
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"Error processing CSV: {str(e)}"

def calculate_speeds_vectorized(df):
    """
    EXACT same speed calculation logic as generate.py
    """
    if len(df) <= 1:
        return np.array([0])
    
    # Get coordinate arrays
    coords = df[['Latitude', 'Longitude']].values
    times = df['seconds'].values
    
    # Calculate distances vectorized (for small datasets, loop is still needed for geodesic)
    speeds = np.zeros(len(df))
    
    for i in range(1, len(df)):
        distance = geodesic(coords[i-1], coords[i]).meters
        time_diff = times[i] - times[i-1]
        speed = distance / time_diff if time_diff > 0 else 0
        
        # Cap unrealistic speeds (EXACT same as generate.py)
        speeds[i] = 0 if speed > 134 else speed
    
    return speeds

def get_track_bounds(track_id):
    """Get geographic bounds for a track"""
    try:
        track = GPSTrack.objects.get(id=track_id)
        return {
            'min_lat': track.min_latitude,
            'max_lat': track.max_latitude,
            'min_lon': track.min_longitude,
            'max_lon': track.max_longitude,
            'center_lat': (track.min_latitude + track.max_latitude) / 2,
            'center_lon': (track.min_longitude + track.max_longitude) / 2,
        }
    except GPSTrack.DoesNotExist:
        return None