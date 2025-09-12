import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import os
from geopy.distance import geodesic
import folium

in_minutes = True

# Read and filter data more efficiently
df = pd.read_csv('EnduranceKnownData.csv')
filtered_df = df[df['Sensor'].isin(['Longitude', 'Latitude'])]

# Pivot the data to have lat/lon in separate columns
pivot_df = filtered_df.pivot_table(
    index='Timestamp', 
    columns='Sensor', 
    values='Value', 
    aggfunc='first'
).reset_index()

# Drop rows where either lat or lon is missing
pivot_df = pivot_df.dropna(subset=['Latitude', 'Longitude'])

# Convert timestamp to seconds
pivot_df['seconds'] = pivot_df['Timestamp'] / 1000

# Skip first 3 timestamps and remove duplicates by second
pivot_df = pivot_df.iloc[3:].copy()
pivot_df['second_int'] = pivot_df['seconds'].astype(int)
pivot_df = pivot_df.drop_duplicates(subset=['second_int'], keep='first')

# Sort by timestamp to ensure proper order
pivot_df = pivot_df.sort_values('seconds').reset_index(drop=True)

# Vectorized speed calculation using numpy
def calculate_speeds_vectorized(df):
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
        
        # Cap unrealistic speeds
        speeds[i] = 0 if speed > 134 else speed
    
    return speeds

# Calculate speeds
speeds = calculate_speeds_vectorized(pivot_df)
pivot_df['speed'] = speeds

# Create final dataset
data_points = list(zip(pivot_df['seconds'], pivot_df['Latitude'], pivot_df['Longitude'], pivot_df['speed']))

print(f"Processed {len(data_points)} data points")

# Save speed data
speed_df = pd.DataFrame({
    'time': pivot_df['seconds'],
    'speed': pivot_df['speed']
})
speed_df.to_csv('speed_data.csv', index=False)

# Create graphs directory if it doesn't exist
os.makedirs('./graphs', exist_ok=True)

# Convert time to minutes if needed
time_data = pivot_df['seconds'] / 60 if in_minutes else pivot_df['seconds']
time_label = 'Time (minutes)' if in_minutes else 'Time (seconds)'

# Plot speed vs time
plt.figure(figsize=(12, 6))
plt.plot(time_data, pivot_df['speed'], linewidth=1, alpha=0.8)
plt.xticks(rotation=45, ticks=np.arange(0, time_data.max(), step=(5 if in_minutes else 200)))
plt.xlabel(time_label)
plt.ylabel('Speed (m/s)')
plt.title('Speed vs Time')
plt.grid(True, alpha=0.3)
plt.xlim(time_data.min(), time_data.max())
plt.ylim(0, max(pivot_df['speed'].max() * 1.1, 1))  # Add some margin at the top
plt.tight_layout()
plt.savefig('./graphs/speed_vs_time_line.png', dpi=300, bbox_inches='tight')
plt.close()

# Create speed vs time heatmap
plt.figure(figsize=(14, 8))

# Create time bins (e.g., 10-second intervals converted to minutes if needed)
time_min = time_data.min()
time_max = time_data.max()
bin_interval = (10/60) if in_minutes else 10  # 10 seconds = 1/6 minute
time_bins = np.arange(time_min, time_max + bin_interval, bin_interval)
speed_bins = np.arange(0, pivot_df['speed'].max() + 5, 2)  # 2 m/s intervals

# Create 2D histogram
hist, xedges, yedges = np.histogram2d(time_data, pivot_df['speed'], bins=[time_bins, speed_bins])

# Create heatmap
plt.imshow(hist.T, origin='lower', aspect='auto', cmap='plasma', extent=[time_bins[0], time_bins[-1], speed_bins[0], speed_bins[-1]])
plt.xticks(rotation=45, ticks=np.arange(0, time_data.max(), step=(5 if in_minutes else 200)))
plt.colorbar(label='Frequency')
plt.xlabel(time_label)
plt.ylabel('Speed (m/s)')
plt.title('Speed vs Time Heatmap')
plt.tight_layout()
plt.savefig('./graphs/speed_vs_time_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

# Alternative: Scatter plot with color-coded time progression
plt.figure(figsize=(12, 6))
scatter = plt.scatter(time_data, pivot_df['speed'], c=time_data, cmap='viridis', alpha=0.6, s=10)
plt.xticks(rotation=45, ticks=np.arange(0, time_data.max(), step=(5 if in_minutes else 200)))
plt.colorbar(scatter, label=time_label)
plt.xlabel(time_label)
plt.ylabel('Speed (m/s)')
plt.title('Speed vs Time (Color-coded by Time Progression)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('./graphs/speed_vs_time_scatter.png', dpi=300, bbox_inches='tight')
plt.close()

print("Creating GPS track visualization...")

# Create speed-based color-coded GPS track
def create_speed_colored_track(df):
    # Remove points with zero speed for better visualization
    df_moving = df[df['speed'] > 0.1].copy()
    
    if len(df_moving) == 0:
        print("No moving points found!")
        return
    
    # Normalize speeds for color mapping (0 = blue, 1 = red)
    min_speed = df_moving['speed'].min()
    max_speed = df_moving['speed'].max()
    print(f"Speed range: {min_speed:.2f} - {max_speed:.2f} m/s")
    
    # Create color map from blue (slow) to red (fast)
    norm = colors.Normalize(vmin=min_speed, vmax=max_speed)
    colormap = plt.cm.coolwarm  # Blue to red colormap
    
    # Create folium map centered on the track
    center_lat = df_moving['Latitude'].mean()
    center_lon = df_moving['Longitude'].mean()
    
    # Create the map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=15,
        tiles='OpenStreetMap'
    )
    
    # Add points with speed-based colors
    coords = []
    for i, row in df_moving.iterrows():
        lat, lon, speed = row['Latitude'], row['Longitude'], row['speed']
        coords.append([lat, lon])
        
        # Get color based on speed
        color_val = norm(speed)
        rgb = colormap(color_val)
        hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        
        # Add circle marker for this point
        folium.CircleMarker(
            location=[lat, lon],
            radius=3,
            popup=f'Speed: {speed:.1f} m/s',
            color=hex_color,
            fill=True,
            fillColor=hex_color,
            fillOpacity=0.8
        ).add_to(m)
    
    # Add the track line
    folium.PolyLine(
        coords,
        color='black',
        weight=2,
        opacity=0.8
    ).add_to(m)
    
    # Add a legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 150px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; ">
    <p style="margin: 10px;"><b>Speed Legend</b></p>
    <p style="margin: 10px; color: blue;">Blue: Slow ({:.1f} m/s)</p>
    <p style="margin: 10px; color: red;">Red: Fast ({:.1f} m/s)</p>
    </div>
    '''.format(min_speed, max_speed)
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save the map
    m.save('./graphs/gps_speed_track.html')
    print("GPS track saved as './graphs/gps_speed_track.html'")
    
    # Also create a matplotlib version
    plt.figure(figsize=(12, 10))
    
    # Plot the track with speed colors
    for i in range(len(df_moving) - 1):
        lat1, lon1 = df_moving.iloc[i]['Latitude'], df_moving.iloc[i]['Longitude']
        lat2, lon2 = df_moving.iloc[i+1]['Latitude'], df_moving.iloc[i+1]['Longitude']
        speed = df_moving.iloc[i]['speed']
        
        color_val = norm(speed)
        color = colormap(color_val)
        
        plt.plot([lon1, lon2], [lat1, lat2], color=color, linewidth=2, alpha=0.8)
    
    plt.scatter(df_moving['Longitude'], df_moving['Latitude'], 
               c=df_moving['speed'], cmap='coolwarm', s=10, alpha=0.6)
    
    cbar = plt.colorbar(label='Speed (m/s)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('GPS Track - Speed Visualization\n(Blue: Slow, Red: Fast)')
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig('./graphs/gps_speed_track.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Static GPS track saved as './graphs/gps_speed_track.png'")

# Create the speed-colored track
create_speed_colored_track(pivot_df)

print(f"All visualizations saved to './graphs/' directory")
print(f"Open './graphs/gps_speed_track.html' in a web browser to see the interactive map!")