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

print("Creating interactive GPS track with working controls...")

# Create interactive folium map with working speed colors and slider
def create_interactive_folium_track(df):
    # Filter and prepare data
    df_clean = df[df['speed'] > 0.1].copy().reset_index(drop=True)
    
    if len(df_clean) == 0:
        print("No valid GPS data found!")
        return
    
    print(f"Processing {len(df_clean)} GPS points...")
    
    # Calculate speed statistics
    min_speed = df_clean['speed'].min()
    max_speed = df_clean['speed'].max()
    
    # Create folium map with satellite view
    center_lat = df_clean['Latitude'].mean()
    center_lon = df_clean['Longitude'].mean()
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=16,
        tiles=None
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
    norm = colors.Normalize(vmin=min_speed, vmax=max_speed)
    colormap = plt.cm.coolwarm
    
    # Prepare track data for JavaScript
    track_points = []
    coords = []
    
    for i, row in df_clean.iterrows():
        lat, lon, speed, time = row['Latitude'], row['Longitude'], row['speed'], row['seconds']
        coords.append([lat, lon])
        
        # Get color based on speed
        color_val = norm(speed)
        rgb = colormap(color_val)
        hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        
        track_points.append({
            'lat': lat,
            'lon': lon,
            'speed': speed,
            'time': time,
            'color': hex_color,
            'index': i
        })
    
    # Add the base track line (will be hidden by JavaScript)
    base_track = folium.PolyLine(
        coords,
        color='white',
        weight=4,
        opacity=0.8,
        popup='GPS Track'
    ).add_to(m)
    
    # Add START and FINISH markers (keeping the icons you like)
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
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Create comprehensive interactive HTML with controls
    import json
    
    interactive_html = f'''
    <!-- Compact Speed Chart and Controls -->
    <div id="controlPanel" style="position: fixed; bottom: 15px; left: 15px; right: 15px; height: 180px; background: linear-gradient(135deg, rgba(0,0,0,0.9), rgba(20,20,20,0.9)); border-radius: 12px; z-index: 1000; padding: 15px; box-shadow: 0 6px 24px rgba(0,0,0,0.8); border: 2px solid #333;">
        
        <!-- Compact info panel -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="color: white; font-family: 'Courier New', monospace; font-size: 14px;">
                <div style="color: #00ff88; font-size: 16px; font-weight: bold;">🏁 TELEMETRY</div>
                <div style="margin-top: 4px;">
                    <span style="color: #4a9eff;">⏱️</span> <span id="current-time" style="color: #ffff00; font-weight: bold;">0.0s</span> |
                    <span style="color: #4a9eff;">🏎️</span> <span id="current-speed" style="color: #ffff00; font-weight: bold;">0.0 m/s</span> |
                    <span style="color: #4a9eff;">📍</span> <span id="current-pos" style="color: #ffff00; font-weight: bold;">0/{len(df_clean)}</span>
                </div>
            </div>
            <div style="color: white; text-align: right; font-family: 'Courier New', monospace; font-size: 11px;">
                <div style="color: #ff6b6b; font-size: 13px; font-weight: bold;">📊 STATS</div>
                <div>🔵 Min: {min_speed:.1f} | 🔴 Max: {max_speed:.1f} | 📈 Avg: {df_clean['speed'].mean():.1f}</div>
            </div>
        </div>
        
        <!-- Compact Speed Chart -->
        <div style="height: 80px; background: linear-gradient(135deg, #1a1a1a, #2d2d2d); border-radius: 8px; margin-bottom: 12px; position: relative; overflow: hidden; border: 1px solid #444;">
            <canvas id="speedChart" width="800" height="80" style="width: 100%; height: 100%; display: block;"></canvas>
        </div>
        
        <!-- Controls -->
        <div style="display: flex; align-items: center; gap: 8px;">
            <button onclick="resetToStart()" style="background: linear-gradient(135deg, #4a9eff, #357abd); color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 12px;">⏮️</button>
            <button onclick="togglePlay()" id="playBtn" style="background: linear-gradient(135deg, #ff6b6b, #e55a5a); color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 12px;">▶️</button>
            <button onclick="resetToEnd()" style="background: linear-gradient(135deg, #4a9eff, #357abd); color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 12px;">⏭️</button>
            <div style="flex: 1; margin: 0 10px;">
                <input type="range" id="positionSlider" min="0" max="{len(df_clean)-1}" value="0" 
                       style="width: 100%; height: 10px; background: linear-gradient(to right, #333, #666); border-radius: 5px; outline: none; -webkit-appearance: none;" 
                       oninput="updatePosition(this.value)">
                <style>
                    #positionSlider::-webkit-slider-thumb {{
                        -webkit-appearance: none;
                        appearance: none;
                        width: 20px;
                        height: 20px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #ffff00, #ffa500);
                        cursor: pointer;
                        box-shadow: 0 0 10px rgba(255, 255, 0, 0.8);
                        border: 2px solid #fff;
                    }}
                    #positionSlider::-moz-range-thumb {{
                        width: 20px;
                        height: 20px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, #ffff00, #ffa500);
                        cursor: pointer;
                        border: 2px solid #fff;
                        box-shadow: 0 0 10px rgba(255, 255, 0, 0.8);
                    }}
                </style>
            </div>
            <span style="color: #4a9eff; font-family: 'Courier New', monospace; font-size: 11px; font-weight: bold;">🎮 CONTROL</span>
        </div>
    </div>
    
    <script>
        // Track data
        const trackData = {json.dumps(track_points)};
        let currentIndex = 0;
        let isPlaying = false;
        let playInterval;
        let speedChart;
        let coloredSegments = [];
        let currentMarker = null;
        let baseTrackLine = null;
        
        // Initialize speed chart
        function initSpeedChart() {{
            const canvas = document.getElementById('speedChart');
            if (!canvas) {{
                console.log('Canvas not found!');
                return;
            }}
            
            const ctx = canvas.getContext('2d');
            const container = canvas.parentElement;
            const rect = container.getBoundingClientRect();
            
            // Set canvas size properly
            canvas.width = rect.width;
            canvas.height = rect.height;
            canvas.style.width = rect.width + 'px';
            canvas.style.height = rect.height + 'px';
            
            speedChart = ctx;
            console.log('Speed chart initialized:', canvas.width, 'x', canvas.height);
            drawSpeedChart();
        }}
        
        function drawSpeedChart() {{
            if (!speedChart) return;
            
            const ctx = speedChart;
            const width = ctx.canvas.width;
            const height = ctx.canvas.height;
            
            // Clear canvas with dark background
            ctx.fillStyle = '#1a1a1a';
            ctx.fillRect(0, 0, width, height);
            
            // Draw grid lines
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 1;
            for (let i = 0; i <= 4; i++) {{
                const y = (height / 4) * i;
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
                ctx.stroke();
            }}
            
            // Draw speed line
            if (trackData.length < 2) return;
            
            ctx.strokeStyle = '#4a9eff';
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            const maxTime = Math.max(...trackData.map(p => p.time));
            const maxSpeed = {max_speed};
            
            trackData.forEach((point, i) => {{
                const x = (point.time / maxTime) * width;
                const y = height - (point.speed / maxSpeed) * height;
                
                if (i === 0) {{
                    ctx.moveTo(x, y);
                }} else {{
                    ctx.lineTo(x, y);
                }}
            }});
            ctx.stroke();
            
            // Draw current position indicator
            if (currentIndex >= 0 && currentIndex < trackData.length) {{
                const point = trackData[currentIndex];
                const x = (point.time / maxTime) * width;
                
                // Vertical line
                ctx.strokeStyle = '#ffff00';
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, height);
                ctx.stroke();
                ctx.setLineDash([]);
                
                // Position dot
                ctx.fillStyle = '#ffff00';
                ctx.strokeStyle = '#000';
                ctx.lineWidth = 2;
                ctx.beginPath();
                const y = height - (point.speed / maxSpeed) * height;
                ctx.arc(x, y, 5, 0, 2 * Math.PI);
                ctx.fill();
                ctx.stroke();
            }}
        }}
        
        // Update display based on current index
        function updateDisplay() {{
            if (currentIndex < 0 || currentIndex >= trackData.length) return;
            
            const point = trackData[currentIndex];
            
            // Update telemetry
            document.getElementById('current-time').textContent = point.time.toFixed(1) + 's';
            document.getElementById('current-speed').textContent = point.speed.toFixed(1) + ' m/s';
            document.getElementById('current-pos').textContent = `${{currentIndex + 1}}/{len(df_clean)}`;
            
            // Update slider
            document.getElementById('positionSlider').value = currentIndex;
            
            // Update speed chart
            drawSpeedChart();
            
            // Update track on map with speed colors
            updateTrackDisplay();
        }}
        
        function updateTrackDisplay() {{
            // Remove existing colored segments
            coloredSegments.forEach(segment => {{
                if (map.hasLayer(segment)) {{
                    map.removeLayer(segment);
                }}
            }});
            coloredSegments = [];
            
            // Remove current marker
            if (currentMarker && map.hasLayer(currentMarker)) {{
                map.removeLayer(currentMarker);
            }}
            
            // Create colored track segments up to current position
            if (currentIndex > 0) {{
                for (let i = 0; i < currentIndex && i < trackData.length - 1; i++) {{
                    const p1 = trackData[i];
                    const p2 = trackData[i + 1];
                    
                    const segment = L.polyline([[p1.lat, p1.lon], [p2.lat, p2.lon]], {{
                        color: p2.color,  // Use the color of the destination point
                        weight: 8,
                        opacity: 0.9,
                        lineCap: 'round',
                        lineJoin: 'round'
                    }});
                    segment.addTo(map);
                    coloredSegments.push(segment);
                }}
            }}
            
            // Add current position marker
            if (currentIndex >= 0 && currentIndex < trackData.length) {{
                const point = trackData[currentIndex];
                currentMarker = L.circleMarker([point.lat, point.lon], {{
                    radius: 10,
                    fillColor: '#ffff00',
                    color: '#000',
                    weight: 3,
                    opacity: 1,
                    fillOpacity: 1
                }}).addTo(map);
                
                // Add speed popup to marker
                currentMarker.bindPopup(`Speed: ${{point.speed.toFixed(1)}} m/s<br>Time: ${{point.time.toFixed(1)}}s`);
            }}
        }}
        
        // Control functions
        function updatePosition(value) {{
            currentIndex = parseInt(value);
            updateDisplay();
            if (isPlaying) {{
                togglePlay(); // Stop playing when manually moved
            }}
        }}
        
        function resetToStart() {{
            currentIndex = 0;
            updateDisplay();
            if (isPlaying) togglePlay();
        }}
        
        function resetToEnd() {{
            currentIndex = trackData.length - 1;
            updateDisplay();
            if (isPlaying) togglePlay();
        }}
        
        function togglePlay() {{
            if (isPlaying) {{
                clearInterval(playInterval);
                isPlaying = false;
                document.getElementById('playBtn').innerHTML = '▶️';
                document.getElementById('playBtn').style.background = 'linear-gradient(135deg, #ff6b6b, #e55a5a)';
            }} else {{
                isPlaying = true;
                document.getElementById('playBtn').innerHTML = '⏸️';
                document.getElementById('playBtn').style.background = 'linear-gradient(135deg, #ffa500, #ff8c00)';
                
                playInterval = setInterval(() => {{
                    currentIndex++;
                    if (currentIndex >= trackData.length) {{
                        currentIndex = trackData.length - 1;
                        togglePlay(); // Auto-stop at end
                        return;
                    }}
                    updateDisplay();
                }}, 100); // 100ms between frames
            }}
        }}
        
        // Store reference to base track and hide it
        function hideBaseTrack() {{
            // Find and hide the white base track line
            map.eachLayer(function(layer) {{
                if (layer instanceof L.Polyline && layer.options.color === 'white') {{
                    baseTrackLine = layer;
                    map.removeLayer(layer);
                    console.log('Base track hidden');
                }}
            }});
        }}
        
        // Initialize everything when map is ready
        function initializeApp() {{
            console.log('Initializing GPS track app...');
            hideBaseTrack();
            initSpeedChart();
            resetToStart();
            console.log('App initialized successfully');
        }}
        
        // Wait for map to be fully loaded
        setTimeout(initializeApp, 2000);
        
        // Handle window resize
        window.addEventListener('resize', function() {{
            setTimeout(() => {{
                initSpeedChart();
                drawSpeedChart();
            }}, 300);
        }});
        
        // Add keyboard controls
        document.addEventListener('keydown', function(e) {{
            switch(e.key) {{
                case ' ': // Spacebar to play/pause
                    e.preventDefault();
                    togglePlay();
                    break;
                case 'ArrowLeft': // Left arrow to go back
                    e.preventDefault();
                    if (currentIndex > 0) {{
                        currentIndex--;
                        updateDisplay();
                    }}
                    break;
                case 'ArrowRight': // Right arrow to go forward
                    e.preventDefault();
                    if (currentIndex < trackData.length - 1) {{
                        currentIndex++;
                        updateDisplay();
                    }}
                    break;
                case 'Home': // Home key to start
                    e.preventDefault();
                    resetToStart();
                    break;
                case 'End': // End key to finish
                    e.preventDefault();
                    resetToEnd();
                    break;
            }}
        }});
    </script>
    '''
    
    # Add the interactive HTML to the map
    m.get_root().html.add_child(folium.Element(interactive_html))
    
    # Save the interactive map
    map_file = './graphs/interactive_gps_track.html'
    m.save(map_file)
    print(f"🚀 Interactive GPS track with working controls saved: {map_file}")
    return map_file
    
# Create the interactive folium track
map_file = create_interactive_folium_track(pivot_df)

print(f"🚀 Interactive GPS track created!")
print(f"📂 Open: {map_file}")
print(f"� Features: Working slider, speed colors, live telemetry!")