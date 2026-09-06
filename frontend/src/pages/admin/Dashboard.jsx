import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiRequest } from '../../services/api';
import LocationModal from '../../components/common/LocationModal';
import SelfieModal from '../../components/common/SelfieModal';
import {
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  CheckCheck,
  MapPin,
  Camera,
  RefreshCw,
  Eye,
  Calendar,
  ExternalLink
} from 'lucide-react';

export default function AdminDashboard() {
  const navigate = useNavigate();

  const [stats, setStats] = useState(null);
  const [roster, setRoster] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Modals
  const [mapModal, setMapModal] = useState({ open: false, lat: null, lng: null, acc: null, title: '', time: '' });
  const [selfieModal, setSelfieModal] = useState({ open: false, filename: null, title: '', time: '', employeeName: '' });

  const fetchDashboardData = async () => {
    try {
      const res = await apiRequest('/dashboard/today');
      if (res.success && res.data) {
        setStats(res.data.stats);
        setRoster(res.data.roster || []);
      }
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    // Auto refresh every 30 seconds for live roster updates
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchDashboardData();
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'WORKING':
        return (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(16, 185, 129, 0.15)',
            color: '#34d399',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            padding: '3px 10px',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontWeight: 700
          }}>
            🟢 Working
          </span>
        );
      case 'COMPLETED':
        return (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(59, 130, 246, 0.15)',
            color: '#60a5fa',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            padding: '3px 10px',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontWeight: 700
          }}>
            🔵 Completed
          </span>
        );
      case 'LEAVE':
        return (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(245, 158, 11, 0.15)',
            color: '#fbbf24',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            padding: '3px 10px',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontWeight: 700
          }}>
            🟡 Leave
          </span>
        );
      default:
        return (
          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(239, 68, 68, 0.15)',
            color: '#f87171',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            padding: '3px 10px',
            borderRadius: '9999px',
            fontSize: '0.8rem',
            fontWeight: 700
          }}>
            🔴 Absent
          </span>
        );
    }
  };

  return (
    <div style={{ padding: '28px', maxWidth: '1280px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            Today's Attendance
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94a3b8', fontSize: '0.9rem', marginTop: '4px' }}>
            <Calendar size={15} style={{ color: '#38bdf8' }} />
            <span>{stats?.today_formatted || 'Sunday, September 6, 2026'}</span>
            <span>•</span>
            <span>Live IST Roster</span>
          </div>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: '#1e293b',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            color: '#f1f5f9',
            padding: '9px 16px',
            borderRadius: '10px',
            fontSize: '0.88rem',
            fontWeight: 600,
            cursor: refreshing ? 'not-allowed' : 'pointer'
          }}
        >
          <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
          <span>{refreshing ? 'Refreshing...' : 'Refresh Live Status'}</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
        gap: '16px'
      }}>
        {/* Total Staff */}
        <div style={{
          background: '#111827',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '16px',
          padding: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          boxShadow: '0 4px 14px rgba(0, 0, 0, 0.25)'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'rgba(99, 102, 241, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#818cf8'
          }}>
            <Users size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Total Staff</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', lineHeight: 1.1 }}>
              {stats?.total_staff ?? '—'}
            </div>
          </div>
        </div>

        {/* Present */}
        <div style={{
          background: '#111827',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '16px',
          padding: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          boxShadow: '0 4px 14px rgba(0, 0, 0, 0.25)'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'rgba(16, 185, 129, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#34d399'
          }}>
            <CheckCircle2 size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Present</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#34d399', lineHeight: 1.1 }}>
              {stats?.present ?? '—'}
            </div>
          </div>
        </div>

        {/* Absent */}
        <div style={{
          background: '#111827',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '16px',
          padding: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          boxShadow: '0 4px 14px rgba(0, 0, 0, 0.25)'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'rgba(239, 68, 68, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#f87171'
          }}>
            <XCircle size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Absent</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f87171', lineHeight: 1.1 }}>
              {stats?.absent ?? '—'}
            </div>
          </div>
        </div>

        {/* Currently Working */}
        <div style={{
          background: '#111827',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '16px',
          padding: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          boxShadow: '0 4px 14px rgba(0, 0, 0, 0.25)'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'rgba(56, 189, 248, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#38bdf8'
          }}>
            <Clock size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Currently Working</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#38bdf8', lineHeight: 1.1 }}>
              {stats?.currently_working ?? '—'}
            </div>
          </div>
        </div>

        {/* Completed Attendance */}
        <div style={{
          background: '#111827',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '16px',
          padding: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          boxShadow: '0 4px 14px rgba(0, 0, 0, 0.25)'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'rgba(168, 85, 247, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#c084fc'
          }}>
            <CheckCheck size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>Completed</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#c084fc', lineHeight: 1.1 }}>
              {stats?.completed ?? '—'}
            </div>
          </div>
        </div>
      </div>

      {/* Today's Roster Table */}
      <div style={{
        background: '#111827',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
        overflow: 'hidden',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)'
      }}>
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
            Staff Today's Roster
          </h2>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Click an employee to open their monthly attendance record
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ background: '#0f172a', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Employee</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Check In</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Check Out</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Hours</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600, textAlign: 'center' }}>Location</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600, textAlign: 'center' }}>Selfie</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
                    Loading today's attendance roster...
                  </td>
                </tr>
              ) : roster.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
                    No staff members found.
                  </td>
                </tr>
              ) : (
                roster.map((row) => (
                  <tr
                    key={row.employee_id}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                      transition: 'background 0.15s ease',
                      cursor: 'pointer'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    onClick={() => navigate(`/admin/attendance?employee_id=${row.employee_id}`)}
                  >
                    {/* Employee */}
                    <td style={{ padding: '16px 20px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{
                          width: '34px',
                          height: '34px',
                          borderRadius: '50%',
                          background: 'rgba(37, 99, 235, 0.15)',
                          color: '#38bdf8',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 700,
                          fontSize: '0.85rem'
                        }}>
                          {row.full_name.charAt(0)}
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, color: '#f1f5f9' }}>{row.full_name}</div>
                          <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                            {row.employee_code} • {row.department}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Status */}
                    <td style={{ padding: '16px 20px' }}>
                      {getStatusBadge(row.status)}
                    </td>

                    {/* Check In */}
                    <td style={{ padding: '16px 20px', color: '#f1f5f9', fontFamily: 'monospace', fontWeight: 600 }}>
                      {row.check_in_formatted}
                    </td>

                    {/* Check Out */}
                    <td style={{ padding: '16px 20px', color: '#f1f5f9', fontFamily: 'monospace', fontWeight: 600 }}>
                      {row.check_out_formatted}
                    </td>

                    {/* Hours */}
                    <td style={{ padding: '16px 20px' }}>
                      <span style={{
                        fontFamily: 'monospace',
                        fontWeight: 700,
                        color: row.status === 'WORKING' ? '#34d399' : row.status === 'COMPLETED' ? '#38bdf8' : '#94a3b8'
                      }}>
                        {row.hours_formatted}
                      </span>
                    </td>

                    {/* Location Pin Trigger */}
                    <td style={{ padding: '16px 20px', textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                      {row.check_in_latitude ? (
                        <button
                          onClick={() => setMapModal({
                            open: true,
                            lat: row.check_in_latitude,
                            lng: row.check_in_longitude,
                            acc: row.check_in_accuracy,
                            title: `${row.full_name} — Check-In Location`,
                            time: row.check_in_formatted
                          })}
                          title="View Check-In Coordinates on Map"
                          style={{
                            background: 'rgba(56, 189, 248, 0.12)',
                            border: '1px solid rgba(56, 189, 248, 0.3)',
                            color: '#38bdf8',
                            padding: '6px 10px',
                            borderRadius: '8px',
                            fontSize: '0.82rem',
                            fontWeight: 600,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            cursor: 'pointer'
                          }}
                        >
                          <MapPin size={14} /> 📍
                        </button>
                      ) : (
                        <span style={{ color: '#64748b' }}>—</span>
                      )}
                    </td>

                    {/* Selfie Trigger */}
                    <td style={{ padding: '16px 20px', textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                      {row.check_in_selfie ? (
                        <button
                          onClick={() => setSelfieModal({
                            open: true,
                            filename: row.check_in_selfie,
                            title: `${row.full_name} — Check-In Selfie`,
                            time: row.check_in_formatted,
                            employeeName: row.full_name
                          })}
                          title="View Verified Check-In Selfie"
                          style={{
                            background: 'rgba(16, 185, 129, 0.12)',
                            border: '1px solid rgba(16, 185, 129, 0.3)',
                            color: '#34d399',
                            padding: '6px 10px',
                            borderRadius: '8px',
                            fontSize: '0.82rem',
                            fontWeight: 600,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            cursor: 'pointer'
                          }}
                        >
                          <Camera size={14} /> 📷
                        </button>
                      ) : (
                        <span style={{ color: '#64748b' }}>—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Location Modal */}
      <LocationModal
        isOpen={mapModal.open}
        onClose={() => setMapModal(prev => ({ ...prev, open: false }))}
        latitude={mapModal.lat}
        longitude={mapModal.lng}
        accuracy={mapModal.acc}
        title={mapModal.title}
        time={mapModal.time}
      />

      {/* Selfie Modal */}
      <SelfieModal
        isOpen={selfieModal.open}
        onClose={() => setSelfieModal(prev => ({ ...prev, open: false }))}
        filename={selfieModal.filename}
        title={selfieModal.title}
        time={selfieModal.time}
        employeeName={selfieModal.employeeName}
      />
    </div>
  );
}
