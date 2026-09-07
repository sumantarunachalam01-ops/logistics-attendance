import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  Users,
  CalendarCheck,
  FileSpreadsheet,
  Settings,
  Home,
  User,
  LogOut,
  X
} from 'lucide-react';

export default function Sidebar({ isMobileOpen = false, onClose = () => {} }) {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === 'ADMIN';

  const adminLinks = [
    { to: '/admin/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/admin/employees', icon: Users, label: 'Employees' },
    { to: '/admin/attendance', icon: CalendarCheck, label: 'Attendance' },
    { to: '/admin/reports', icon: FileSpreadsheet, label: 'Monthly Reports' },
    { to: '/admin/settings', icon: Settings, label: 'Settings' },
  ];

  const staffLinks = [
    { to: '/staff/dashboard', icon: Home, label: 'Home' },
    { to: '/staff/attendance', icon: CalendarCheck, label: 'My Attendance' },
    { to: '/staff/profile', icon: User, label: 'Profile' },
  ];

  const links = isAdmin ? adminLinks : staffLinks;

  const renderNavContent = (isMobile = false) => (
    <>
      <div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 12px 16px 12px'
        }}>
          <span style={{
            fontSize: '0.72rem',
            fontWeight: 700,
            color: '#64748b',
            textTransform: 'uppercase',
            letterSpacing: '0.08em'
          }}>
            {isAdmin ? 'Administration' : 'Staff Portal'}
          </span>
          {isMobile && (
            <button
              onClick={onClose}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                border: 'none',
                color: '#94a3b8',
                cursor: 'pointer',
                padding: '5px',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <X size={18} />
            </button>
          )}
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {links.map((link) => {
            const Icon = link.icon;
            return (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={isMobile ? onClose : undefined}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 14px',
                  borderRadius: '12px',
                  fontSize: '0.92rem',
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? '#ffffff' : '#94a3b8',
                  background: isActive ? 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)' : 'transparent',
                  boxShadow: isActive ? '0 4px 12px rgba(37, 99, 235, 0.35)' : 'none',
                  textDecoration: 'none',
                  transition: 'all 0.15s ease'
                })}
              >
                <Icon size={19} />
                <span>{link.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Bottom User Card & Logout */}
      <div style={{
        paddingTop: '16px',
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px'
      }}>
        <div style={{
          padding: '10px 12px',
          borderRadius: '10px',
          background: 'rgba(255, 255, 255, 0.04)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: isAdmin ? 'rgba(99, 102, 241, 0.2)' : 'rgba(16, 185, 129, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: isAdmin ? '#818cf8' : '#34d399',
            fontWeight: 700,
            fontSize: '0.85rem',
            flexShrink: 0
          }}>
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
          </div>
          <div style={{ overflow: 'hidden' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
              {user?.full_name || user?.email}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
              {user?.employee_code || user?.role}
            </div>
          </div>
        </div>

        <button
          onClick={() => { if (isMobile) onClose(); logout(); }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '10px 12px',
            borderRadius: '10px',
            background: 'transparent',
            border: 'none',
            color: '#ef4444',
            fontSize: '0.88rem',
            fontWeight: 500,
            cursor: 'pointer',
            textAlign: 'left'
          }}
        >
          <LogOut size={17} />
          <span>Sign Out</span>
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* 1. Desktop Persistent Sidebar */}
      <aside
        className="desktop-sidebar"
        style={{
          width: '240px',
          background: '#0f172a',
          borderRight: '1px solid rgba(255, 255, 255, 0.08)',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '20px 14px',
          flexShrink: 0,
          minHeight: 'calc(100vh - 60px)',
          position: 'sticky',
          top: '60px'
        }}
      >
        {renderNavContent(false)}
      </aside>

      {/* 2. Mobile Slide-out Drawer */}
      {isMobileOpen && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 1000,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(6px)',
            display: 'flex',
            animation: 'fadeIn 0.15s ease'
          }}
        >
          <aside
            onClick={(e) => e.stopPropagation()}
            style={{
              width: '280px',
              maxWidth: '85vw',
              height: '100%',
              background: '#0f172a',
              borderRight: '1px solid rgba(255, 255, 255, 0.12)',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              padding: '20px 16px',
              animation: 'slideInLeft 0.25s ease-out'
            }}
          >
            {renderNavContent(true)}
          </aside>
        </div>
      )}
    </>
  );
}

