import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, CalendarCheck, User } from 'lucide-react';

export default function BottomNav() {
  const navItems = [
    { to: '/staff/dashboard', icon: Home, label: 'Home' },
    { to: '/staff/attendance', icon: CalendarCheck, label: 'My Attendance' },
    { to: '/staff/profile', icon: User, label: 'Profile' },
  ];

  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      height: '64px',
      background: '#0f172a',
      borderTop: '1px solid rgba(255, 255, 255, 0.1)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-around',
      zIndex: 50,
      padding: '0 8px',
      backdropFilter: 'blur(12px)',
    }}>
      {navItems.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            style={({ isActive }) => ({
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '4px',
              color: isActive ? '#38bdf8' : '#94a3b8',
              textDecoration: 'none',
              padding: '6px 16px',
              borderRadius: '12px',
              background: isActive ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
              fontSize: '0.75rem',
              fontWeight: isActive ? 600 : 500,
              transition: 'all 0.15s ease'
            })}
          >
            <Icon size={20} />
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}
