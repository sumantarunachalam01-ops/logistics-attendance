import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { LogOut, User, Clock, Shield } from 'lucide-react';

export default function Navbar() {
  const { user, logout } = useAuth();
  const [currentTime, setCurrentTime] = useState('');

  // Live IST Clock
  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      });
      setCurrentTime(timeStr);
    };

    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header style={{
      height: '64px',
      background: '#111827',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px',
      position: 'sticky',
      top: 0,
      zIndex: 40
    }}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(37, 99, 235, 0.35)',
          color: '#ffffff',
          fontWeight: 800,
          fontSize: '18px'
        }}>
          📍
        </div>
        <div>
          <span style={{ fontSize: '1.08rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.01em' }}>
            Staff Attendance Portal
          </span>
          <span style={{
            display: 'block',
            fontSize: '0.72rem',
            color: '#38bdf8',
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            GPS Location & Selfie Verification
          </span>
        </div>
      </div>

      {/* Center/Right Items */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '18px' }}>
        {/* Live IST Clock */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '9999px',
          padding: '6px 14px',
          fontSize: '0.85rem',
          color: '#94a3b8'
        }}>
          <Clock size={15} style={{ color: '#38bdf8' }} />
          <span style={{ fontWeight: 600, color: '#f1f5f9' }}>{currentTime || 'Loading...'}</span>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>IST</span>
        </div>

        {/* User Badge */}
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '34px',
              height: '34px',
              borderRadius: '50%',
              background: user.role === 'ADMIN' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(16, 185, 129, 0.2)',
              border: `1px solid ${user.role === 'ADMIN' ? 'rgba(99, 102, 241, 0.4)' : 'rgba(16, 185, 129, 0.4)'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: user.role === 'ADMIN' ? '#818cf8' : '#34d399',
              fontWeight: 700,
              fontSize: '0.88rem'
            }}>
              {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
            </div>

            <div style={{ display: 'none', mdDisplay: 'block' }}>
              <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#f8fafc', lineHeight: 1.2 }}>
                {user.full_name || user.email}
              </div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                <span style={{
                  color: user.role === 'ADMIN' ? '#818cf8' : '#34d399',
                  fontWeight: 600
                }}>
                  {user.role}
                </span>
                {user.employee_code && ` • ${user.employee_code}`}
              </div>
            </div>
          </div>
        )}

        {/* Logout Button */}
        <button
          onClick={logout}
          title="Logout"
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            color: '#f87171',
            borderRadius: '10px',
            padding: '8px 14px',
            fontSize: '0.85rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
            transition: 'all 0.2s ease'
          }}
        >
          <LogOut size={16} />
          <span style={{ display: 'inline' }}>Logout</span>
        </button>
      </div>
    </header>
  );
}
