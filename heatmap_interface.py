import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.widgets import Slider
from matplotlib.collections import LineCollection
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

print("Creating GPS track with MAP background...")

# Create GPS track with actual map background AND interactive matplotlib version
def create_map_and_interactive_track(df):
    # Filter and prepare data
    df_clean = df[df['speed'] > 0.1].copy().reset_index(drop=True)
    
    if len(df_clean) == 0:
        print("No valid GPS data found!")
        return
    
    print(f"Processing {len(df_clean)} GPS points...")
    
    # FIRST: Create the folium map with actual map background
    center_lat = df_clean['Latitude'].mean()
    center_lon = df_clean['Longitude'].mean()
    
    # Create folium map with satellite view
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=16,
        tiles=None  # Start with no base layer
    )
    
    # Add satellite tiles
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Add OpenStreetMap as alternative
    folium.TileLayer('OpenStreetMap').add_to(m)
    
    # Speed normalization for colors
    min_speed = df_clean['speed'].min()
    max_speed = df_clean['speed'].max()
    norm = colors.Normalize(vmin=min_speed, vmax=max_speed)
    colormap = plt.cm.coolwarm
    
    # Add the track line with speed colors
    coords = []
    for i, row in df_clean.iterrows():
        lat, lon, speed = row['Latitude'], row['Longitude'], row['speed']
        coords.append([lat, lon])
        
        # Get color based on speed
        color_val = norm(speed)
        rgb = colormap(color_val)
        hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        
        # Add circle markers for speed visualization
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            popup=f'Speed: {speed:.1f} m/s ({speed*2.237:.1f} mph)<br>Time: {row["seconds"]:.1f}s',
            color=hex_color,
            fill=True,
            fillColor=hex_color,
            fillOpacity=0.8,
            weight=2
        ).add_to(m)
    
    # Add the main track line
    folium.PolyLine(
        coords,
        color='white',
        weight=3,
        opacity=0.9
    ).add_to(m)
    
    # Add START and FINISH markers
    folium.Marker(
        location=[df_clean.iloc[0]['Latitude'], df_clean.iloc[0]['Longitude']],
        popup='START',
        icon=folium.Icon(color='green', icon='play', prefix='fa')
    ).add_to(m)
    
    folium.Marker(
        location=[df_clean.iloc[-1]['Latitude'], df_clean.iloc[-1]['Longitude']],
        popup='FINISH',
        icon=folium.Icon(color='red', icon='stop', prefix='fa')
    ).add_to(m)
    
    # Add speed legend
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; ">
    <p style="margin: 10px;"><b>🏁 Speed Legend</b></p>
    <p style="margin: 10px; color: blue;">🔵 Blue: Slow ({min_speed:.1f} m/s)</p>
    <p style="margin: 10px; color: red;">🔴 Red: Fast ({max_speed:.1f} m/s)</p>
    <p style="margin: 10px;"><b>📍 Track Info</b></p>
    <p style="margin: 10px;">Points: {len(df_clean):,}</p>
    </div>
    '''
    
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save the interactive map
    map_file = './graphs/gps_track_with_map.html'
    m.save(map_file)
    print(f"🗺️  Interactive map with satellite background saved: {map_file}")
    
    # SECOND: Create matplotlib version for analysis
    fig = plt.figure(figsize=(14, 9))
    fig.patch.set_facecolor('white')
    
    # Main map area
    ax = plt.subplot2grid((4, 4), (0, 0), colspan=3, rowspan=3)
    
    # Info panel
    info_ax = plt.subplot2grid((4, 4), (0, 3), rowspan=2)
    info_ax.axis('off')
    
    # Speed vs time plot
    speed_ax = plt.subplot2grid((4, 4), (2, 3), rowspan=1)
    
    # Slider area
    slider_ax = plt.subplot2grid((4, 4), (3, 0), colspan=4)
    
    # Set up main track plot with dark map-like background
    ax.set_facecolor('#2d2d2d')  # Dark background like satellite map
    ax.grid(True, alpha=0.2, color='white', linestyle='-', linewidth=0.5)
    
    # Prepare track data
    lats = df_clean['Latitude'].values
    lons = df_clean['Longitude'].values
    speeds = df_clean['speed'].values
    times = df_clean['seconds'].values
    
    # Create line segments for speed coloring
    points = np.column_stack([lons, lats])
    segments = np.array([points[:-1], points[1:]]).transpose(1, 0, 2)
    
    # Create line collection with thicker lines
    lc = LineCollection(segments, cmap='coolwarm', norm=norm, linewidths=4, alpha=0.9)
    lc.set_array(speeds[:-1])
    line = ax.add_collection(lc)
    
    # Add track points
    scatter = ax.scatter(lons, lats, c=speeds, cmap='coolwarm', norm=norm, 
                        s=20, alpha=0.8, edgecolors='white', linewidth=0.8, zorder=5)
    
    # Mark start and finish clearly
    ax.scatter(lons[0], lats[0], s=300, c='lime', marker='o', 
              edgecolors='black', linewidth=4, label='START', zorder=10)
    ax.scatter(lons[-1], lats[-1], s=300, c='red', marker='s', 
              edgecolors='black', linewidth=4, label='FINISH', zorder=10)
    
    # Current position marker
    current_marker = ax.scatter([], [], s=200, c='yellow', marker='*', 
                               edgecolors='black', linewidth=3, zorder=15)
    
    # Set map limits with padding
    lat_range = lats.max() - lats.min()
    lon_range = lons.max() - lons.min()
    padding = max(lat_range, lon_range) * 0.05
    
    ax.set_xlim(lons.min() - padding, lons.max() + padding)
    ax.set_ylim(lats.min() - padding, lats.max() + padding)
    ax.set_aspect('equal')
    
    # Labels and title with white text for dark background
    ax.set_xlabel('Longitude', color='white', fontsize=12)
    ax.set_ylabel('Latitude', color='white', fontsize=12)
    ax.set_title('🏁 GPS RACE TRACK - Interactive Analysis\n(Blue: Slow → Red: Fast)', 
                fontsize=16, pad=20, color='white', weight='bold')
    ax.tick_params(colors='white')
    
    # Legend with dark theme
    legend = ax.legend(loc='upper left', facecolor='black', edgecolor='white')
    for text in legend.get_texts():
        text.set_color('white')
    
    # Colorbar with dark theme
    cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
    cbar.set_label('Speed (m/s)', fontsize=12, color='white')
    cbar.ax.tick_params(colors='white')
    
    # Info panel setup
    info_text = plt.figtext(0.76, 0.7, '', fontsize=11, 
                           bbox=dict(boxstyle='round', facecolor='black', 
                                   edgecolor='white', alpha=0.9),
                           color='white', family='monospace')
    
    # Speed vs time plot with dark theme
    speed_ax.set_facecolor('#2d2d2d')
    speed_ax.plot(times, speeds, color='cyan', linewidth=2, alpha=0.8)
    speed_ax.set_xlabel('Time (s)', fontsize=10, color='white')
    speed_ax.set_ylabel('Speed (m/s)', fontsize=10, color='white')
    speed_ax.set_title('Speed Profile', fontsize=12, color='white')
    speed_ax.grid(True, alpha=0.3, color='white')
    speed_ax.tick_params(colors='white')
    
    # Current position line on speed plot
    speed_line = speed_ax.axvline(x=0, color='yellow', linewidth=3, alpha=0.8)
    
    # Slider setup with dark theme
    slider_ax.clear()
    slider_ax.set_facecolor('#404040')
    slider = Slider(slider_ax, 'Track Position', 0, len(df_clean)-1, 
                   valinit=len(df_clean)-1, valfmt='%d', valstep=1,
                   color='#ff6b6b', track_color='#808080')
    
    def update_display(val):
        idx = int(slider.val)
        
        if idx == 0:
            # Reset display
            lc.set_segments([])
            scatter.set_offsets(np.empty((0, 2)))
            current_marker.set_offsets(np.empty((0, 2)))
            speed_line.set_xdata([0])
            info_text.set_text("🏁 Ready to start...")
        else:
            # Update track display
            current_segments = segments[:idx]
            lc.set_segments(current_segments)
            lc.set_array(speeds[:idx])
            
            current_points = points[:idx+1]
            scatter.set_offsets(current_points)
            scatter.set_array(speeds[:idx+1])
            
            # Update current position
            current_marker.set_offsets([[lons[idx], lats[idx]]])
            
            # Update speed plot indicator
            speed_line.set_xdata([times[idx]])
            
            # Update info
            current_time = times[idx]
            current_speed = speeds[idx]
            progress = (idx / len(df_clean)) * 100
            
            info_text.set_text(f"""🏁 LIVE TELEMETRY
⏱️  Time: {current_time:.1f} s
🏎️  Speed: {current_speed:.1f} m/s
    {current_speed*2.237:.1f} mph
📊 Progress: {progress:.1f}%
📍 Point: {idx+1}/{len(df_clean)}
🗺️  Lat: {lats[idx]:.6f}°
🗺️  Lon: {lons[idx]:.6f}°""")
        
        fig.canvas.draw()
    
    # Connect slider
    slider.on_changed(update_display)
    
    # Initial display
    update_display(len(df_clean)-1)
    
    # Dark theme for entire figure
    fig.patch.set_facecolor('black')
    
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.3, wspace=0.3)
    
    # Save and show
    plt.savefig('./graphs/interactive_gps_analysis.png', dpi=300, bbox_inches='tight',
               facecolor='black', edgecolor='white')
    plt.show()
    
    print("🎮 Interactive GPS analysis tool created!")
    print("🗺️  Open the HTML file for satellite map view!")
    return map_file

# Create BOTH the map and interactive versions
map_file = create_map_and_interactive_track(pivot_df)

print(f"All visualizations saved to './graphs/' directory")
print(f"Interactive GPS track will open in a new window!")