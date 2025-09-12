import React, { useEffect, useRef } from 'react';
import './TrackControls.css';

const TrackControls = ({ 
  trackData, 
  currentPoint, 
  isPlaying, 
  setIsPlaying, 
  onPointChange 
}) => {
  const intervalRef = useRef(null);

  useEffect(() => {
    if (isPlaying && trackData) {
      intervalRef.current = setInterval(() => {
        onPointChange(prev => {
          if (prev >= trackData.points.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 100); // Update every 100ms for smooth animation
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, trackData, onPointChange, setIsPlaying]);

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleSliderChange = (event) => {
    const newPoint = parseInt(event.target.value);
    onPointChange(newPoint);
  };

  const handleRestart = () => {
    setIsPlaying(false);
    onPointChange(0);
  };

  if (!trackData || !trackData.points) {
    return null;
  }

  const progress = (currentPoint / (trackData.points.length - 1)) * 100;
  const currentTime = trackData.points[currentPoint]?.timestamp || 0;

  return (
    <div className="track-controls">
      <div className="controls-header">
        <h3>Track Playback</h3>
        <div className="track-info">
          <span>Point {currentPoint + 1} of {trackData.points.length}</span>
          <span>Time: {currentTime.toFixed(1)}s</span>
        </div>
      </div>

      <div className="progress-section">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        
        <input
          type="range"
          min="0"
          max={trackData.points.length - 1}
          value={currentPoint}
          onChange={handleSliderChange}
          className="progress-slider"
        />
      </div>

      <div className="control-buttons">
        <button 
          className="control-btn restart-btn"
          onClick={handleRestart}
          title="Restart"
        >
          ⏮
        </button>
        
        <button 
          className="control-btn play-pause-btn"
          onClick={handlePlayPause}
          title={isPlaying ? "Pause" : "Play"}
        >
          {isPlaying ? '⏸' : '▶'}
        </button>
        
        <button 
          className="control-btn step-btn"
          onClick={() => onPointChange(Math.min(currentPoint + 10, trackData.points.length - 1))}
          title="Skip Forward"
        >
          ⏭
        </button>
      </div>
    </div>
  );
};

export default TrackControls;