import React, { useState } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';
import GPSMap from './components/GPSMap';
import TrackControls from './components/TrackControls';
import TrackInfo from './components/TrackInfo';

function App() {
  const [trackData, setTrackData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentPoint, setCurrentPoint] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const handleTrackUpload = (data) => {
    setTrackData(data);
    setCurrentPoint(0);
    setIsPlaying(false);
  };

  const handlePlaybackControl = (point) => {
    setCurrentPoint(point);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>GPS Track Visualizer</h1>
        <p>Interactive GPS track visualization with speed mapping</p>
      </header>

      <main className="App-main">
        <div className="upload-section">
          <FileUpload 
            onTrackUpload={handleTrackUpload} 
            loading={loading} 
            setLoading={setLoading} 
          />
        </div>

        {trackData && (
          <>
            <div className="controls-section">
              <TrackControls
                trackData={trackData}
                currentPoint={currentPoint}
                isPlaying={isPlaying}
                setIsPlaying={setIsPlaying}
                onPointChange={handlePlaybackControl}
              />
            </div>

            <div className="visualization-section">
              <div className="map-container">
                <GPSMap 
                  trackData={trackData} 
                  currentPoint={currentPoint}
                />
              </div>
              
              <div className="info-panel">
                <TrackInfo 
                  trackData={trackData} 
                  currentPoint={currentPoint}
                />
              </div>
            </div>
          </>
        )}

        {!trackData && !loading && (
          <div className="welcome-message">
            <h3>Ready for GPS Data</h3>
            <p>Upload a CSV file to see your interactive GPS track visualization</p>
            <p>Supports the same format as your original matplotlib visualization!</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
