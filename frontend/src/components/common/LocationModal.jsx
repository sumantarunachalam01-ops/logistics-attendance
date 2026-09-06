import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, X, Navigation, ShieldCheck } from 'lucide-react';

export default function LocationModal({ isOpen, onClose, latitude, longitude, accuracy, title = "Attendance Location", time = null }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);

  useEffect(() => {
    if (!isOpen || !mapContainerRef.current) return;

    const lat = parseFloat(latitude);
    const lng = parseFloat(longitude);
    const acc = parseFloat(accuracy) || 20;

    if (isNaN(lat) || isNaN(lng)) return;

    // Destroy existing instance if any
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    // Initialize Leaflet map
    const map = L.map(mapContainerRef.current, {
      center: [lat, lng],
      zoom: 16,
      zoomControl: true,
    });

    // CartoDB Voyager modern clean map tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map);

    // Custom pulse marker
    const customIcon = L.divIcon({
      className: 'custom-attendance-pin',
      html: `
        <div style="
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 38px;
          height: 38px;
        ">
          <div style="
            position: absolute;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: rgba(37, 99, 235, 0.35);
            animation: pulse 2s infinite;
          "></div>
          <div style="
            position: relative;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: #2563eb;
            border: 3px solid #ffffff;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 14px;
          ">
            📍
          </div>
        </div>
      `,
      iconSize: [38, 38],
      iconAnchor: [19, 19],
    });

    const marker = L.marker([lat, lng], { icon: customIcon }).addTo(map);
    marker.bindPopup(`
      <div style="font-family: sans-serif; font-size: 13px; line-height: 1.4;">
        <strong style="color: #0f172a;">${title}</strong><br/>
        ${time ? `<span style="color: #64748b;">Time: ${time}</span><br/>` : ''}
        <span>Lat: ${lat.toFixed(6)}</span><br/>
        <span>Lng: ${lng.toFixed(6)}</span><br/>
        <span style="color: #10b981; font-weight: 600;">Accuracy: ±${acc}m</span>
      </div>
    `).openPopup();

    // Accuracy Circle
    L.circle([lat, lng], {
      radius: acc,
      color: '#3b82f6',
      fillColor: '#3b82f6',
      fillOpacity: 0.15,
      weight: 1.5,
    }).addTo(map);

    mapInstanceRef.current = map;

    // Invalidate size after rendering
    setTimeout(() => {
      map.invalidateSize();
    }, 200);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [isOpen, latitude, longitude, accuracy, title, time]);

  if (!isOpen) return null;

  const latNum = parseFloat(latitude);
  const lngNum = parseFloat(longitude);
  const accNum = parseFloat(accuracy) || 0;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 9999,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(8px)',
      padding: '16px'
    }}>
      <div style={{
        background: '#111827',
        border: '1px solid rgba(255, 255, 255, 0.15)',
        borderRadius: '20px',
        width: '100%',
        maxWidth: '560px',
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
              background: 'rgba(16, 185, 129, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#34d399'
            }}>
              <MapPin size={20} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 600, color: '#f8fafc' }}>{title}</h3>
              {time && <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>Recorded at {time}</p>}
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

        {/* Map View */}
        <div
          ref={mapContainerRef}
          style={{
            width: '100%',
            height: '360px',
            background: '#0f172a'
          }}
        />

        {/* Coords & Accuracy Bar */}
        <div style={{
          padding: '16px 20px',
          background: '#0f172a',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px'
        }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '2px' }}>GPS Coordinates</div>
            <div style={{ fontSize: '0.92rem', fontWeight: 600, color: '#f1f5f9', fontFamily: 'monospace' }}>
              Lat: {isNaN(latNum) ? '—' : latNum.toFixed(6)} | Lng: {isNaN(lngNum) ? '—' : lngNum.toFixed(6)}
            </div>
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid rgba(16, 185, 129, 0.25)',
            color: '#34d399',
            padding: '6px 12px',
            borderRadius: '9999px',
            fontSize: '0.82rem',
            fontWeight: 600
          }}>
            <ShieldCheck size={16} /> Accuracy: ±{accNum.toFixed(0)} meters
          </div>
        </div>
      </div>
    </div>
  );
}
