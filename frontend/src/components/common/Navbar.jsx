import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { LogOut, Clock, Menu, X } from 'lucide-react';

export default function Navbar({ onToggleMobileMenu, isMobileMenuOpen }) {
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
      height: '60px',
      background: '#111827',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 16px',
      position: 'sticky',
      top: 0,
      zIndex: 40
    }}>
      {/* Left: Mobile Toggle + Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {onToggleMobileMenu && (
          <button
            onClick={onToggleMobileMenu}
            className="mobile-only"
            aria-label="Toggle navigation menu"
            style={{
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#f8fafc',
              padding: '7px',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: '2px'
            }}
          >
            {isMobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        )}

        <div style={{
          width: '34px',
          height: '34px',
          borderRadius: '9px',
          background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(37, 99, 235, 0.35)',
          color: '#ffffff',
          fontWeight: 800,
          fontSize: '16px',
          flexShrink: 0
        }}>
          📍
        </div>
        <div style={{ overflow: 'hidden' }}>
          <span style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '-0.01em', whiteSpace: 'nowrap' }}>
            Attendance Portal
          </span>
          <span
            className="desktop-only"
            style={{
              display: 'block',
              fontSize: '0.68rem',
              color: '#38bdf8',
              fontWeight: 500,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              whiteSpace: 'nowrap'
            }}
          >
            GPS Location & Selfie Verification
          </span>
        </div>
      </div>

      {/* Right Items */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Live IST Clock */}
        <div
          className="desktop-only"
          style={{
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '9999px',
            padding: '5px 12px',
            fontSize: '0.82rem',
            color: '#94a3b8'
          }}
        >
          <Clock size={14} style={{ color: '#38bdf8' }} />
          <span style={{ fontWeight: 600, color: '#f1f5f9' }}>{currentTime || 'Loading...'}</span>
          <span style={{ fontSize: '0.7rem', color: '#64748b' }}>IST</span>
        </div>

        {/* User Badge */}
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              background: user.role === 'ADMIN' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(16, 185, 129, 0.2)',
              border: `1px solid ${user.role === 'ADMIN' ? 'rgba(99, 102, 241, 0.4)' : 'rgba(16, 185, 129, 0.4)'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: user.role === 'ADMIN' ? '#818cf8' : '#34d399',
              fontWeight: 700,
              fontSize: '0.82rem',
              flexShrink: 0
            }}>
              {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
            </div>

            <div className="desktop-only">
              <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#f8fafc', lineHeight: 1.2, maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.full_name || user.email}
              </div>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
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
            borderRadius: '9px',
            padding: '7px 12px',
            fontSize: '0.82rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            flexShrink: 0
          }}
        >
          <LogOut size={15} />
          <span className="desktop-only">Logout</span>
        </button>
      </div>
    </header>
  );
}

