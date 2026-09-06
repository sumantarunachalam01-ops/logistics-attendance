import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../services/api';
import LocationModal from '../../components/common/LocationModal';
import SelfieModal from '../../components/common/SelfieModal';
import {
  Calendar,
  Clock,
  MapPin,
  Camera,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  AlertCircle
} from 'lucide-react';

export default function StaffAttendance() {
  const [currentMonth, setCurrentMonth] = useState('2026-09');
  const [summary, setSummary] = useState(null);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  // Modals
  const [mapModal, setMapModal] = useState({ open: false, lat: null, lng: null, acc: null, title: '', time: '' });
  const [selfieModal, setSelfieModal] = useState({ open: false, filename: null, title: '', time: '' });

  const fetchAttendance = async (month) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await apiRequest(`/attendance/my?month=${month}`);
      if (res.success && res.data) {
        setSummary(res.data.summary);
        setRecords(res.data.records || []);
      }
    } catch (err) {
      console.error("Failed to fetch my attendance:", err);
      setErrorMsg(err.message || "Failed to load attendance records.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttendance(currentMonth);
  }, [currentMonth]);

  const handlePrevMonth = () => {
    const [y, m] = currentMonth.split('-').map(Number);
    const prevDate = new Date(y, m - 2, 1);
    const newMonth = `${prevDate.getFullYear()}-${String(prevDate.getMonth() + 1).padStart(2, '0')}`;
    setCurrentMonth(newMonth);
  };

  const handleNextMonth = () => {
    const [y, m] = currentMonth.split('-').map(Number);
    const nextDate = new Date(y, m, 1);
    const newMonth = `${nextDate.getFullYear()}-${String(nextDate.getMonth() + 1).padStart(2, '0')}`;
    setCurrentMonth(newMonth);
  };

  const getMonthDisplayName = (monthStr) => {
    const [y, m] = monthStr.split('-').map(Number);
    const d = new Date(y, m - 1, 1);
    return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  return (
    <div style={{
      maxWidth: '560px',
      margin: '0 auto',
      padding: '24px 16px 80px 16px',
      display: 'flex',
      flexDirection: 'column',
      gap: '20px'
    }}>
      {/* Page Title & Month Selector */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc' }}>
            My Attendance
          </h1>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
            Personal monthly attendance & GPS logs
          </p>
        </div>

        {/* Month Navigation */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: '#1e293b',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '12px',
          padding: '4px 8px'
        }}>
          <button
            onClick={handlePrevMonth}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '6px'
            }}
          >
            <ChevronLeft size={18} />
          </button>
          <span style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f1f5f9', minWidth: '130px', textAlign: 'center' }}>
            {getMonthDisplayName(currentMonth)}
          </span>
          <button
            onClick={handleNextMonth}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '6px'
            }}
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      {/* Summary Card */}
      {summary && (
        <div style={{
          background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '18px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)'
        }}>
          <div>
            <div style={{ fontSize: '0.78rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
              Total Worked ({getMonthDisplayName(currentMonth)})
            </div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#38bdf8', fontFamily: 'monospace', marginTop: '2px' }}>
              {summary.total_work_formatted}
            </div>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '8px',
            paddingTop: '12px',
            borderTop: '1px solid rgba(255, 255, 255, 0.08)'
          }}>
            <div style={{
              background: 'rgba(16, 185, 129, 0.1)',
              borderRadius: '10px',
              padding: '8px 10px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Present</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#34d399' }}>{summary.present_days}</div>
            </div>
            <div style={{
              background: 'rgba(239, 68, 68, 0.1)',
              borderRadius: '10px',
              padding: '8px 10px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Absent</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f87171' }}>{summary.absent_days}</div>
            </div>
            <div style={{
              background: 'rgba(245, 158, 11, 0.1)',
              borderRadius: '10px',
              padding: '8px 10px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Overtime</div>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#fbbf24' }}>{summary.total_overtime_formatted}</div>
            </div>
          </div>
        </div>
      )}

      {/* Daily Records List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <h2 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
          Daily Records
        </h2>

        {loading ? (
          <div style={{ padding: '30px', textAlign: 'center', color: '#94a3b8' }}>
            Loading attendance records...
          </div>
        ) : errorMsg ? (
          <div style={{ padding: '20px', color: '#fca5a5', background: 'rgba(239, 68, 68, 0.15)', borderRadius: '12px' }}>
            {errorMsg}
          </div>
        ) : records.length === 0 ? (
          <div style={{
            padding: '36px 20px',
            textAlign: 'center',
            color: '#94a3b8',
            background: '#111827',
            borderRadius: '16px',
            border: '1px solid rgba(255, 255, 255, 0.06)'
          }}>
            No attendance records found for {getMonthDisplayName(currentMonth)}.
          </div>
        ) : (
          records.map((rec) => {
            const isPresent = rec.status === 'PRESENT';
            const isAbsent = rec.status === 'ABSENT';
            const isLeave = rec.status === 'LEAVE';

            return (
              <div
                key={rec.id}
                style={{
                  background: '#111827',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: '16px',
                  padding: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)'
                }}
              >
                {/* Card Top: Date & Status */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <span style={{ fontSize: '0.98rem', fontWeight: 700, color: '#f8fafc' }}>
                      {rec.date_short}
                    </span>
                    <span style={{ fontSize: '0.8rem', color: '#94a3b8', marginLeft: '6px' }}>
                      ({rec.day_name})
                    </span>
                  </div>

                  <span style={{
                    fontSize: '0.78rem',
                    fontWeight: 700,
                    padding: '3px 10px',
                    borderRadius: '9999px',
                    background: isPresent ? 'rgba(16, 185, 129, 0.15)' : isLeave ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                    color: isPresent ? '#34d399' : isLeave ? '#fbbf24' : '#f87171',
                    border: `1px solid ${isPresent ? 'rgba(16, 185, 129, 0.3)' : isLeave ? 'rgba(245, 158, 11, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                  }}>
                    {rec.status}
                  </span>
                </div>

                {/* Card Body: Time Range & Duration */}
                {isPresent && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    borderRadius: '10px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    fontSize: '0.88rem'
                  }}>
                    <div style={{ color: '#cbd5e1' }}>
                      <span>{rec.check_in_formatted}</span>
                      <span style={{ margin: '0 6px', color: '#64748b' }}>→</span>
                      <span>{rec.check_out_formatted || 'Working'}</span>
                    </div>
                    <div style={{ fontWeight: 700, color: '#38bdf8', fontFamily: 'monospace' }}>
                      {rec.duration_formatted}
                    </div>
                  </div>
                )}

                {/* Card Actions: Location & Selfie Buttons */}
                {isPresent && (
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', paddingTop: '4px' }}>
                    {rec.check_in_latitude && (
                      <button
                        onClick={() => setMapModal({
                          open: true,
                          lat: rec.check_in_latitude,
                          lng: rec.check_in_longitude,
                          acc: rec.check_in_accuracy,
                          title: `Location - ${rec.date_short}`,
                          time: rec.check_in_formatted
                        })}
                        style={{
                          background: 'rgba(56, 189, 248, 0.1)',
                          border: '1px solid rgba(56, 189, 248, 0.25)',
                          color: '#38bdf8',
                          padding: '6px 12px',
                          borderRadius: '8px',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '5px',
                          cursor: 'pointer'
                        }}
                      >
                        <MapPin size={13} /> GPS Location
                      </button>
                    )}

                    {rec.check_in_selfie && (
                      <button
                        onClick={() => setSelfieModal({
                          open: true,
                          filename: rec.check_in_selfie,
                          title: `Check-In Selfie - ${rec.date_short}`,
                          time: rec.check_in_formatted
                        })}
                        style={{
                          background: 'rgba(16, 185, 129, 0.1)',
                          border: '1px solid rgba(16, 185, 129, 0.25)',
                          color: '#34d399',
                          padding: '6px 12px',
                          borderRadius: '8px',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '5px',
                          cursor: 'pointer'
                        }}
                      >
                        <Camera size={13} /> In Selfie
                      </button>
                    )}

                    {rec.check_out_selfie && (
                      <button
                        onClick={() => setSelfieModal({
                          open: true,
                          filename: rec.check_out_selfie,
                          title: `Check-Out Selfie - ${rec.date_short}`,
                          time: rec.check_out_formatted
                        })}
                        style={{
                          background: 'rgba(168, 85, 247, 0.1)',
                          border: '1px solid rgba(168, 85, 247, 0.25)',
                          color: '#c084fc',
                          padding: '6px 12px',
                          borderRadius: '8px',
                          fontSize: '0.78rem',
                          fontWeight: 600,
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '5px',
                          cursor: 'pointer'
                        }}
                      >
                        <Camera size={13} /> Out Selfie
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Modals */}
      <LocationModal
        isOpen={mapModal.open}
        onClose={() => setMapModal(prev => ({ ...prev, open: false }))}
        latitude={mapModal.lat}
        longitude={mapModal.lng}
        accuracy={mapModal.acc}
        title={mapModal.title}
        time={mapModal.time}
      />

      <SelfieModal
        isOpen={selfieModal.open}
        onClose={() => setSelfieModal(prev => ({ ...prev, open: false }))}
        filename={selfieModal.filename}
        title={selfieModal.title}
        time={selfieModal.time}
      />
    </div>
  );
}
