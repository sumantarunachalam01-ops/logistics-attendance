import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  Home,
  CalendarCheck,
  User,
  LayoutDashboard,
  Users,
  FileSpreadsheet,
  Settings
} from 'lucide-react';

export default function BottomNav() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';

  const staffItems = [
    { to: '/staff/dashboard', icon: Home, label: 'Home' },
    { to: '/staff/attendance', icon: CalendarCheck, label: 'Attendance' },
    { to: '/staff/profile', icon: User, label: 'Profile' },
  ];

  const adminItems = [
    { to: '/admin/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/admin/attendance', icon: CalendarCheck, label: 'Attendance' },
    { to: '/admin/employees', icon: Users, label: 'Staff' },
    { to: '/admin/reports', icon: FileSpreadsheet, label: 'Reports' },
    { to: '/admin/settings', icon: Settings, label: 'Settings' },
  ];

  const navItems = isAdmin ? adminItems : staffItems;

  return (
    <nav
      className="mobile-bottom-nav"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        height: '60px',
        background: '#0f172a',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-around',
        zIndex: 50,
        padding: '0 4px',
        backdropFilter: 'blur(12px)',
      }}
    >
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
              gap: '3px',
              color: isActive ? '#38bdf8' : '#94a3b8',
              textDecoration: 'none',
              padding: '5px 8px',
              borderRadius: '10px',
              background: isActive ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
              fontSize: '0.7rem',
              fontWeight: isActive ? 600 : 500,
              transition: 'all 0.15s ease',
              minWidth: '54px'
            })}
          >
            <Icon size={18} />
            <span style={{ whiteSpace: 'nowrap' }}>{item.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );
}

