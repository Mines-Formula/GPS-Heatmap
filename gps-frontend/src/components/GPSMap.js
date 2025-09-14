import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './GPSMap.css';

// Custom component to handle map updates
const MapController = ({ trackData, currentPoint }) => {
  const map = useMap();
  const layerGroupRef = useRef(null);
  const currentMarkerRef = useRef(null);

  useEffect(() => {
    if (!trackData || !trackData.points) return;

    const points = trackData.points;
    if (points.length === 0) return;

    // Initialize layer group if it doesn't exist
    if (!layerGroupRef.current) {
      layerGroupRef.current = L.layerGroup();
      layerGroupRef.current.addTo(map);
    }

    // Clear all existing layers
    layerGroupRef.current.clearLayers();
    if (currentMarkerRef.current) {
      map.removeLayer(currentMarkerRef.current);
    }

    // Create coordinates array
    const coordinates = points.map(point => [point.latitude, point.longitude]);
    
    // Get speed values for color mapping
    const speeds = points.map(point => point.speed || 0);
    const minSpeed = Math.min(...speeds);
    const maxSpeed = Math.max(...speeds);

    // Function to get color based on speed
    const getSpeedColor = (speed) => {
      if (maxSpeed === minSpeed) return '#667eea';
      
      const ratio = (speed - minSpeed) / (maxSpeed - minSpeed);
      const hue = (1 - ratio) * 240; // Blue (240) to Red (0)
      return `hsl(${hue}, 100%, 50%)`;
    };

    // Create line segments with colors (only up to current point)
    for (let i = 0; i < Math.min(currentPoint, coordinates.length - 1); i++) {
      const color = getSpeedColor(speeds[i]);
      const polyline = L.polyline([coordinates[i], coordinates[i + 1]], {
        color: color,
        weight: 6,
        opacity: 0.8
      });
      layerGroupRef.current.addLayer(polyline);
    }

    // Add current position marker
    if (currentPoint < coordinates.length) {
      const currentCoord = coordinates[currentPoint];
      currentMarkerRef.current = L.circleMarker(currentCoord, {
        radius: 8,
        fillColor: 'white',
        color: 'black',
        weight: 2,
        opacity: 1,
        fillOpacity: 1
      }).addTo(map);
    }

    // Fit map to track bounds on first load
    if (currentPoint === 0) {
      const bounds = L.latLngBounds(coordinates);
      map.fitBounds(bounds, { padding: [20, 20] });
    }

  }, [map, trackData, currentPoint]);

  return null;
};

const GPSMap = ({ trackData, currentPoint }) => {
  const [useSatellite, setUseSatellite] = useState(false);

  if (!trackData || !trackData.points || trackData.points.length === 0) {
    return (
      <div className="map-placeholder">
        <h3>GPS Map</h3>
        <p>Upload a CSV file to see your track visualization</p>
      </div>
    );
  }

  // Calculate center point for initial map view
  const centerLat = (trackData.min_latitude + trackData.max_latitude) / 2;
  const centerLon = (trackData.min_longitude + trackData.max_longitude) / 2;

  return (
    <div className="gps-map">
      <MapContainer
        center={[centerLat, centerLon]}
        zoom={15}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
      >
        <TileLayer
          attribution={useSatellite 
            ? '&copy; <a href="https://www.esri.com/">Esri</a> &mdash; Source: Esri, Maxar, Earthstar Geographics'
            : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          }
          url={useSatellite
            ? "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          }
        />
        
        <MapController trackData={trackData} currentPoint={currentPoint} />
      </MapContainer>
      
      {/* Satellite Background Toggle */}
      <div className="map-controls">
        <div className={`satellite-toggle ${useSatellite ? 'active' : ''}`}>
          <span className="toggle-label">Map</span>
          <div className="toggle-slider" onClick={() => setUseSatellite(!useSatellite)}>
            <div className={`slider-thumb ${useSatellite ? 'active' : ''}`}></div>
          </div>
          <span className="toggle-label">Satellite</span>
        </div>
      </div>
      
      <div className="map-legend">
        <div className="legend-item">
          <div className="color-bar">
            <div className="color-gradient"></div>
          </div>
          <div className="legend-labels">
            <span>Slow</span>
            <span>Fast</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GPSMap;