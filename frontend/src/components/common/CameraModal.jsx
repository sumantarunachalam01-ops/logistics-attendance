import React, { useState, useRef, useEffect } from 'react';
import { Camera, RefreshCw, CheckCircle, X, AlertCircle } from 'lucide-react';

export default function CameraModal({ isOpen, onClose, onCapture, title = "Capture Attendance Selfie" }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const [capturedImage, setCapturedImage] = useState(null);
  const [cameraError, setCameraError] = useState(null);
  const [loadingCamera, setLoadingCamera] = useState(false);

  // Start Camera Stream (Live Camera Only)
  const startCamera = async () => {
    setCameraError(null);
    setLoadingCamera(true);
    setCapturedImage(null);

    // Stop existing stream if running
    stopCamera();

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Live camera is not supported in this browser. Please use a modern browser with webcam/camera support.");
      }

      let stream;
      try {
        // Prefer front selfie camera
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 640 },
            height: { ideal: 480 }
          },
          audio: false
        });
      } catch (frontErr) {
        // Fallback to any active device camera
        console.warn("Front camera constraint unavailable, falling back to default camera:", frontErr);
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false
        });
      }

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
      }
    } catch (err) {
      console.warn("Camera access error:", err);
      let errorMsg = "Could not access device camera. Please allow camera permissions in your browser.";
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        errorMsg = "Camera permission was denied. Please allow camera access in your browser settings to mark attendance.";
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        errorMsg = "No camera was detected on this device. A live camera is strictly required to mark attendance.";
      }
      setCameraError(errorMsg);
    } finally {
      setLoadingCamera(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  useEffect(() => {
    if (isOpen) {
      startCamera();
    } else {
      stopCamera();
      setCapturedImage(null);
      setCameraError(null);
    }

    return () => {
      stopCamera();
    };
  }, [isOpen]);

  // Capture video frame to canvas
  const handleSnap = () => {
    if (!videoRef.current) return;

    try {
      const video = videoRef.current;
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;

      const ctx = canvas.getContext('2d');
      // Mirror horizontally for natural selfie view
      ctx.translate(canvas.width, 0);
      ctx.scale(-1, 1);
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
      setCapturedImage(dataUrl);
      stopCamera();
    } catch (err) {
      console.error("Failed to capture snapshot:", err);
    }
  };

  const handleRetake = () => {
    setCapturedImage(null);
    startCamera();
  };

  const handleConfirm = () => {
    if (capturedImage) {
      onCapture(capturedImage);
      stopCamera();
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 9999,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      backdropFilter: 'blur(8px)',
      padding: '16px'
    }}>
      <div style={{
        background: '#111827',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        borderRadius: '20px',
        width: '100%',
        maxWidth: '460px',
        overflow: 'hidden',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'rgba(37, 99, 235, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#38bdf8'
            }}>
              <Camera size={20} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 600, color: '#f8fafc' }}>{title}</h3>
              <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>Live camera capture only</p>
            </div>
          </div>
          <button
            onClick={() => { stopCamera(); onClose(); }}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '8px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Viewfinder / Capture Box */}
        <div style={{
          position: 'relative',
          width: '100%',
          aspectRatio: '4/3',
          background: '#030712',
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          {capturedImage ? (
            <img
              src={capturedImage}
              alt="Captured Live Selfie"
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              }}
            />
          ) : cameraError ? (
            <div style={{ padding: '28px 24px', textAlign: 'center', color: '#94a3b8', maxWidth: '360px' }}>
              <AlertCircle size={44} style={{ color: '#f87171', marginBottom: '14px' }} />
              <h4 style={{ margin: '0 0 8px 0', color: '#f8fafc', fontSize: '1rem', fontWeight: 600 }}>
                Live Camera Required
              </h4>
              <p style={{ fontSize: '0.85rem', marginBottom: '20px', color: '#cbd5e1', lineHeight: 1.5 }}>
                {cameraError}
              </p>
              <button
                type="button"
                onClick={startCamera}
                disabled={loadingCamera}
                style={{
                  background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '10px',
                  padding: '10px 20px',
                  fontSize: '0.88rem',
                  fontWeight: 600,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  cursor: loadingCamera ? 'not-allowed' : 'pointer',
                  boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)'
                }}
              >
                <RefreshCw size={16} style={{ animation: loadingCamera ? 'spin 1s linear infinite' : 'none' }} />
                <span>{loadingCamera ? 'Connecting...' : 'Retry Camera Access'}</span>
              </button>
            </div>
          ) : (
            <>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  transform: 'scaleX(-1)' // Mirror view for natural selfie
                }}
              />
              {/* Face Guide Oval */}
              <div style={{
                position: 'absolute',
                width: '180px',
                height: '240px',
                border: '2px dashed rgba(56, 189, 248, 0.7)',
                borderRadius: '50%',
                pointerEvents: 'none',
                boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.25)'
              }} />
              <div style={{
                position: 'absolute',
                bottom: '12px',
                background: 'rgba(15, 23, 42, 0.75)',
                color: '#f8fafc',
                fontSize: '0.75rem',
                padding: '4px 12px',
                borderRadius: '9999px',
                backdropFilter: 'blur(4px)'
              }}>
                Align face inside oval & take photo
              </div>
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div style={{
          padding: '18px 20px',
          background: '#0f172a',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px'
        }}>
          {capturedImage ? (
            <>
              <button
                type="button"
                onClick={handleRetake}
                style={{
                  flex: 1,
                  background: 'rgba(255, 255, 255, 0.08)',
                  color: '#e2e8f0',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  borderRadius: '12px',
                  padding: '12px',
                  fontSize: '0.92rem',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  cursor: 'pointer'
                }}
              >
                <RefreshCw size={18} /> Retake
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                style={{
                  flex: 1.5,
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '12px',
                  padding: '12px',
                  fontSize: '0.95rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)'
                }}
              >
                <CheckCircle size={18} /> Confirm Selfie
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={handleSnap}
              disabled={loadingCamera || !!cameraError}
              style={{
                width: '100%',
                background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                color: '#ffffff',
                border: 'none',
                borderRadius: '12px',
                padding: '14px',
                fontSize: '0.98rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                cursor: loadingCamera || cameraError ? 'not-allowed' : 'pointer',
                opacity: loadingCamera || cameraError ? 0.5 : 1,
                boxShadow: '0 4px 14px rgba(37, 99, 235, 0.4)'
              }}
            >
              <Camera size={20} />
              <span>{loadingCamera ? 'Connecting to Camera...' : 'Take Photo from Camera'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
