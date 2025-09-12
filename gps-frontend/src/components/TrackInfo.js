import React from 'react';
import './TrackInfo.css';

const TrackInfo = ({ trackData, currentPoint }) => {
  if (!trackData || !trackData.points || trackData.points.length === 0) {
    return (
      <div className="track-info-panel">
        <h3>Track Information</h3>
        <p className="no-data">No track data available</p>
      </div>
    );
  }

  const currentPointData = trackData.points[currentPoint] || trackData.points[0];
  const progress = ((currentPoint + 1) / trackData.points.length) * 100;
  
  // Speed conversions
  const speedMs = currentPointData.speed || 0;
  const speedMph = speedMs * 2.237; // m/s to mph
  const speedKmh = speedMs * 3.6;   // m/s to km/h

  return (
    <div className="track-info-panel">
      <h3>Live Telemetry</h3>
      
      <div className="info-section">
        <h4>Current Position</h4>
        <div className="info-grid">
          <div className="info-item">
            <span className="label">Time:</span>
            <span className="value">{currentPointData.timestamp?.toFixed(1) || '0.0'} s</span>
          </div>
          <div className="info-item">
            <span className="label">Progress:</span>
            <span className="value">{progress.toFixed(1)}%</span>
          </div>
          <div className="info-item">
            <span className="label">Point:</span>
            <span className="value">{currentPoint + 1} / {trackData.points.length}</span>
          </div>
        </div>
      </div>

      <div className="info-section">
        <h4>Speed Data</h4>
        <div className="speed-display">
          <div className="speed-primary">
            <span className="speed-value">{speedMs.toFixed(1)}</span>
            <span className="speed-unit">m/s</span>
          </div>
          <div className="speed-conversions">
            <div className="speed-item">
              <span className="speed-value">{speedMph.toFixed(1)}</span>
              <span className="speed-unit">mph</span>
            </div>
            <div className="speed-item">
              <span className="speed-value">{speedKmh.toFixed(1)}</span>
              <span className="speed-unit">km/h</span>
            </div>
          </div>
        </div>
      </div>

      <div className="info-section">
        <h4>GPS Coordinates</h4>
        <div className="coordinates">
          <div className="coord-item">
            <span className="label">Latitude:</span>
            <span className="value">{currentPointData.latitude?.toFixed(8) || '0.00000000'}°</span>
          </div>
          <div className="coord-item">
            <span className="label">Longitude:</span>
            <span className="value">{currentPointData.longitude?.toFixed(8) || '0.00000000'}°</span>
          </div>
        </div>
      </div>

      <div className="info-section">
        <h4>Track Statistics</h4>
        <div className="info-grid">
          <div className="info-item">
            <span className="label">Duration:</span>
            <span className="value">{trackData.duration?.toFixed(1) || '0.0'} s</span>
          </div>
          <div className="info-item">
            <span className="label">Max Speed:</span>
            <span className="value">{(trackData.max_speed * 2.237)?.toFixed(1) || '0.0'} mph</span>
          </div>
          <div className="info-item">
            <span className="label">Avg Speed:</span>
            <span className="value">{(trackData.avg_speed * 2.237)?.toFixed(1) || '0.0'} mph</span>
          </div>
          <div className="info-item">
            <span className="label">Total Points:</span>
            <span className="value">{trackData.total_points?.toLocaleString() || '0'}</span>
          </div>
        </div>
      </div>

      <div className="info-section">
        <h4>Geographic Bounds</h4>
        <div className="bounds-grid">
          <div className="bounds-item">
            <span className="label">Lat Range:</span>
            <span className="value">
              {trackData.min_latitude?.toFixed(6)}° to {trackData.max_latitude?.toFixed(6)}°
            </span>
          </div>
          <div className="bounds-item">
            <span className="label">Lon Range:</span>
            <span className="value">
              {trackData.min_longitude?.toFixed(6)}° to {trackData.max_longitude?.toFixed(6)}°
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrackInfo;