import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from geopy.distance import geodesic

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