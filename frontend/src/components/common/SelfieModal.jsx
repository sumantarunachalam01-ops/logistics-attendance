import React, { useState, useEffect } from 'react';
import { Camera, X, ShieldCheck, Download, AlertTriangle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function SelfieModal({ isOpen, onClose, filename, title = "Attendance Selfie", time = null, employeeName = null }) {
  const { token } = useAuth();
  const [imageSrc, setImageSrc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!isOpen || !filename) {
      setImageSrc(null);
      setError(false);
      return;
    }

    setLoading(true);
    setError(false);

    // If filename is already a data URL (e.g. freshly captured client-side)
    if (filename.startsWith('data:')) {
      setImageSrc(filename);
      setLoading(false);
      return;
    }

    // Load through authenticated endpoint
    const url = `/api/attendance/selfie/${filename}?token=${token || localStorage.getItem('logitrack_token')}`;
    
    // Test image loading
    const img = new Image();
    img.onload = () => {
      setImageSrc(url);
      setLoading(false);
    };
    img.onerror = () => {
      console.warn("Failed to load selfie image from URL:", url);
      setError(true);
      setLoading(false);
    };
    img.src = url;
  }, [isOpen, filename, token]);

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
        maxWidth: '440px',
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
              background: 'rgba(56, 189, 248, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#38bdf8'
            }}>
              <Camera size={20} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 600, color: '#f8fafc' }}>{title}</h3>
              {employeeName && <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>{employeeName}</p>}
            </div>
          </div>
          <button
            onClick={onClose}
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

        {/* Image Preview Box */}
        <div style={{
          position: 'relative',
          width: '100%',
          aspectRatio: '1/1',
          background: '#030712',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden'
        }}>
          {loading ? (
            <div style={{ color: '#94a3b8', fontSize: '0.9rem' }}>Loading secure selfie...</div>
          ) : error ? (
            <div style={{ padding: '24px', textAlign: 'center', color: '#94a3b8' }}>
              <AlertTriangle size={36} style={{ color: '#f59e0b', marginBottom: '8px' }} />
              <p style={{ margin: 0, fontSize: '0.88rem', color: '#e2e8f0' }}>Selfie image not accessible or expired.</p>
            </div>
          ) : imageSrc ? (
            <img
              src={imageSrc}
              alt="Attendance Selfie"
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              }}
            />
          ) : null}

          {/* Verification Badge */}
          <div style={{
            position: 'absolute',
            bottom: '12px',
            right: '12px',
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            color: '#34d399',
            fontSize: '0.75rem',
            fontWeight: 600,
            padding: '4px 10px',
            borderRadius: '9999px',
            backdropFilter: 'blur(6px)',
            display: 'flex',
            alignItems: 'center',
            gap: '5px'
          }}>
            <ShieldCheck size={14} /> Verified Live Capture
          </div>
        </div>

        {/* Footer info */}
        <div style={{
          padding: '14px 20px',
          background: '#0f172a',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
            {time ? `Captured at ${time}` : 'Live device capture'}
          </span>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
            {filename ? filename.split('/').pop() : ''}
          </span>
        </div>
      </div>
    </div>
  );
}
