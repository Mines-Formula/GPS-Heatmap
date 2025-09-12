import pandas as pd
from geopy.distance import geodesic

df = pd.read_csv('EnduranceKnownData.csv')
filtered_df = df[df['Sensor'].isin(['Longitude', 'Latitude'])]
timestamps = filtered_df['Timestamp'].unique()
last_second = -1
data_points = []
for timestamp in timestamps[10:]:
    seconds = float(timestamp) / 1000
    second = int(seconds)
    print(seconds)
    lat_row = filtered_df[(filtered_df['Timestamp'] == timestamp) & (filtered_df['Sensor'] == 'Latitude')]
    lon_row = filtered_df[(filtered_df['Timestamp'] == timestamp) & (filtered_df['Sensor'] == 'Longitude')]
    if not lat_row.empty and not lon_row.empty:
        latitude = lat_row['Value'].iloc[0]
        longitude = lon_row['Value'].iloc[0]
        if len(data_points) > 0:
            speed = geodesic((latitude, longitude), (data_points[-1][1], data_points[-1][2])).meters / (seconds - data_points[-1][0])
            if speed > 134:  # Skip unrealistic speeds
                print(f"Unrealistic speed detected: {speed} m/s at {seconds}s, skipping this point.")
                speed = 0
        else:
            speed = 0
        if second > last_second:
            last_second = second
        else:
            print(f"Duplicate second detected: {second}s, skipping this point.")
            continue
        data_points.append((seconds, latitude, longitude, speed))
        print(f"Timestamp: {seconds}s, Latitude: {latitude}, Longitude: {longitude}")
print(data_points)
speed_v_time_data = {'time': [i[0] for i in data_points], 'speed': [i[3] for i in data_points]}
speed_df = pd.DataFrame(speed_v_time_data)
speed_df.to_csv('speed_data.csv', index=False)
"""index_datas = []
for timestamp in timestamps:
    timestamp_seconds = float(timestamp) / 1000
    if timestamp_seconds > 100:
        break
    lat_row = filtered_df[(filtered_df['Timestamp'] == timestamp) & (filtered_df['Sensor'] == 'Latitude')]
    lon_row = filtered_df[(filtered_df['Timestamp'] == timestamp) & (filtered_df['Sensor'] == 'Longitude')]
    
    if not lat_row.empty and not lon_row.empty:
        latitude = lat_row['Value'].iloc[0]
        longitude = lon_row['Value'].iloc[0]
        index_datas.append((timestamp_seconds, latitude, longitude))
        print(f"Timestamp: {timestamp_seconds}s, Latitude: {latitude}, Longitude: {longitude}")

# Calculate speeds and filter out speeds above 134 m/s
speeds = []
times = []
last_second = -1
for i in range(len(index_datas)):
    time = index_datas[i][0]
    second = int(time)
    if second > last_second:
        last_second = second
        if i > 0:
            distance = geodesic((index_datas[i][1], index_datas[i][2]), (index_datas[i-1][1], index_datas[i-1][2])).meters
            time_diff = index_datas[i][0] - index_datas[i-1][0]
            speed = distance / time_diff if time_diff > 0 else 0
            
            # Only include speeds <= 134 m/s
            if speed <= 134:
                speeds.append(speed)
                times.append(time)
        else:
            speeds.append(0)
            times.append(time)
    if i > 0:
        distance = geodesic((index_datas[i][1], index_datas[i][2]), (index_datas[i-1][1], index_datas[i-1][2])).meters
        time_diff = index_datas[i][0] - index_datas[i-1][0]
        speed = distance / time_diff if time_diff > 0 else 0
        
        # Only include speeds <= 134 m/s
        if speed <= 134:
            speeds.append(speed)
            times.append(time)
    else:
        speeds.append(0)
        times.append(time)

speed_v_time_data = {'time': times, 'speed': speeds}
speed_df = pd.DataFrame(speed_v_time_data)
speed_df.to_csv('speed_data.csv', index=False)
# Graph Linear Speed vs Time"""

#filtered_df.to_csv('filtered_data.csv', index=False)