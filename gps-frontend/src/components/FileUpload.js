import React, { useRef, useState } from 'react';
import axios from 'axios';
import './FileUpload.css';

const FileUpload = ({ onTrackUpload, loading, setLoading }) => {
  const fileInputRef = useRef(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [timeResolution, setTimeResolution] = useState(2);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.csv')) {
      alert('Please select a CSV file');
      return;
    }

    // Check file size (500MB limit)
    const maxSize = 500 * 1024 * 1024; // 500MB
    if (file.size > maxSize) {
      alert('File is too large. Maximum size is 300MB.');
      return;
    }

    setLoading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('uploaded_file', file);
      formData.append('name', file.name.replace('.csv', ''));
      formData.append('time_resolution', timeResolution);

      const response = await axios.post(
        'http://localhost:8000/api/tracks/upload/',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 300000, // 5 minute timeout for large files
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(percentCompleted);
          },
        }
      );

      onTrackUpload(response.data.track);
      setUploadProgress(100);
      
    } catch (error) {
      console.error('Upload error:', error);
      if (error.code === 'ECONNABORTED') {
        alert('Upload timeout. Please try with a smaller file or check your connection.');
      } else {
        alert(error.response?.data?.error || 'Failed to upload file');
      }
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="file-upload">
      <div className="upload-area">
        <div className="upload-content">
          <h3>Upload GPS Data</h3>
          <p>Select a CSV file</p>
          
          {/* Time Resolution Setting */}
          <div className="time-resolution-setting">
            <label htmlFor="timeResolution" className="resolution-label">
              Time Resolution (points per second):
            </label>
            <div className="resolution-input-group">
              <input
                id="timeResolution"
                type="number"
                min="1"
                max="100"
                value={timeResolution}
                onChange={(e) => setTimeResolution(parseInt(e.target.value) || 1)}
                className="resolution-input"
                disabled={loading}
              />
              <span className="resolution-unit">pts/sec</span>
            </div>
            <small className="resolution-help">
              Higher values = more detailed tracks (2-4 recommended)
            </small>
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          
          <button
            className="upload-button"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="loading-spinner"></span>
                {uploadProgress > 0 && uploadProgress < 100 ? 
                  `Uploading... ${uploadProgress}%` : 
                  'Processing...'
                }
              </>
            ) : (
              'Choose CSV File'
            )}
          </button>
          
          {loading && uploadProgress > 0 && uploadProgress < 100 && (
            <div className="upload-progress-bar">
              <div 
                className="upload-progress-fill" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          )}
          
          <div className="upload-info">
            <small>
              Supported columns: Timestamp, CANID, Sensor, Value, Unit
              <br />
              Maximum file size: 500MB
            </small>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;