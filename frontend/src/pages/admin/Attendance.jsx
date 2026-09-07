import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiRequest, getSelfieUrl } from '../../services/api';
import LocationModal from '../../components/common/LocationModal';
import SelfieModal from '../../components/common/SelfieModal';
import {
  Calendar,
  Users,
  MapPin,
  Camera,
  Clock,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  X,
  Eye,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

export default function AdminAttendance() {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlEmpId = searchParams.get('employee_id');

  const [employees, setEmployees] = useState([]);
  const [selectedEmpId, setSelectedEmpId] = useState(urlEmpId ? parseInt(urlEmpId) : null);
  const [selectedMonth, setSelectedMonth] = useState('2026-09');

  const [attendanceData, setAttendanceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Selected Day Details Modal
  const [dayDetails, setDayDetails] = useState(null);

  // Map & Selfie Modals
  const [mapModal, setMapModal] = useState({ open: false, lat: null, lng: null, acc: null, title: '', time: '' });
  const [selfieModal, setSelfieModal] = useState({ open: false, filename: null, title: '', time: '', employeeName: '' });

  // Fetch employees for dropdown
  useEffect(() => {
    const loadEmployees = async () => {
      try {
        const res = await apiRequest('/employees');
        if (res.success && res.data) {
          const staffEmps = res.data.employees.filter(e => e.role === 'STAFF' || e.user_active);
          setEmployees(staffEmps);
          if (!selectedEmpId && staffEmps.length > 0) {
            setSelectedEmpId(staffEmps[0].id);
          }
        }
      } catch (err) {
        console.error("Failed to load employees dropdown:", err);
      }
    };
    loadEmployees();
  }, []);

  // Update selectedEmpId when URL param changes
  useEffect(() => {
    if (urlEmpId) {
      setSelectedEmpId(parseInt(urlEmpId));
    }
  }, [urlEmpId]);

  // Fetch Monthly Attendance for selected employee
  const fetchMonthlyAttendance = async (empId, month) => {
    if (!empId) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await apiRequest(`/attendance/employee/${empId}/monthly?month=${month}`);
      if (res.success && res.data) {
        setAttendanceData(res.data);
      }
    } catch (err) {
      console.error("Failed to load monthly attendance:", err);
      setErrorMsg(err.message || "Failed to load monthly attendance.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedEmpId) {
      fetchMonthlyAttendance(selectedEmpId, selectedMonth);
    }
  }, [selectedEmpId, selectedMonth]);

  const handleEmployeeChange = (e) => {
    const id = parseInt(e.target.value);
    setSelectedEmpId(id);
    setSearchParams({ employee_id: id });
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'PRESENT':
        return (
          <span style={{
            background: 'rgba(16, 185, 129, 0.15)',
            color: '#34d399',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            padding: '2px 8px',
            borderRadius: '9999px',
            fontSize: '0.78rem',
            fontWeight: 700
          }}>
            PRESENT
          </span>
        );
      case 'ABSENT':
        return (
          <span style={{
            background: 'rgba(239, 68, 68, 0.15)',
            color: '#f87171',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            padding: '2px 8px',
            borderRadius: '9999px',
            fontSize: '0.78rem',
            fontWeight: 700
          }}>
            ABSENT
          </span>
        );
      case 'LEAVE':
        return (
          <span style={{
            background: 'rgba(245, 158, 11, 0.15)',
            color: '#fbbf24',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            padding: '2px 8px',
            borderRadius: '9999px',
            fontSize: '0.78rem',
            fontWeight: 700
          }}>
            LEAVE
          </span>
        );
      case 'WEEK_OFF':
        return (
          <span style={{
            background: 'rgba(148, 163, 184, 0.15)',
            color: '#94a3b8',
            border: '1px solid rgba(148, 163, 184, 0.3)',
            padding: '2px 8px',
            borderRadius: '9999px',
            fontSize: '0.78rem',
            fontWeight: 600
          }}>
            WEEK OFF
          </span>
        );
      default:
        return (
          <span style={{
            background: 'rgba(148, 163, 184, 0.1)',
            color: '#64748b',
            padding: '2px 8px',
            borderRadius: '9999px',
            fontSize: '0.78rem'
          }}>
            {status}
          </span>
        );
    }
  };

  const selectedEmpName = attendanceData?.summary?.employee?.full_name || employees.find(e => e.id === selectedEmpId)?.full_name || 'Employee';

  return (
    <div className="admin-page-container">
      {/* Top Filter Bar */}
      <div style={{
        background: '#111827',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '18px',
        padding: '20px 24px',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        boxShadow: '0 4px 14px rgba(0, 0, 0, 0.25)'
      }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc' }}>
            Monthly Attendance Verification
          </h1>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
            Inspect daily clock times, GPS locations, and live selfie photos
          </p>
        </div>

        {/* Selectors */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          {/* Employee Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600 }}>Employee:</label>
            <select
              value={selectedEmpId || ''}
              onChange={handleEmployeeChange}
              style={{
                background: '#1e293b',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                color: '#f8fafc',
                padding: '9px 14px',
                borderRadius: '10px',
                fontSize: '0.9rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              {employees.map(emp => (
                <option key={emp.id} value={emp.id}>
                  {emp.full_name} ({emp.employee_code})
                </option>
              ))}
            </select>
          </div>

          {/* Month Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <label style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600 }}>Month:</label>
            <select
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(e.target.value)}
              style={{
                background: '#1e293b',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                color: '#f8fafc',
                padding: '9px 14px',
                borderRadius: '10px',
                fontSize: '0.9rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <option value="2026-09">September 2026</option>
              <option value="2026-08">August 2026</option>
              <option value="2026-07">July 2026</option>
              <option value="2026-06">June 2026</option>
            </select>
          </div>
        </div>
      </div>

      {/* Header Banner */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
        <h2 style={{ margin: 0, fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc' }}>
          {selectedEmpName} — {attendanceData?.summary?.month_formatted || 'September 2026'}
        </h2>
        {attendanceData?.summary?.employee?.department && (
          <span style={{ fontSize: '0.9rem', color: '#38bdf8', fontWeight: 600 }}>
            {attendanceData.summary.employee.department} • {attendanceData.summary.employee.designation}
          </span>
        )}
      </div>

      {/* Summary Cards */}
      {attendanceData?.summary && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
          gap: '14px'
        }}>
          {/* Present Days */}
          <div style={{
            background: '#111827',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '14px',
            padding: '16px',
            borderLeft: '4px solid #10b981'
          }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Present Days</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#34d399', marginTop: '2px' }}>
              {attendanceData.summary.present_days}
            </div>
          </div>

          {/* Absent Days */}
          <div style={{
            background: '#111827',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '14px',
            padding: '16px',
            borderLeft: '4px solid #ef4444'
          }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Absent Days</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f87171', marginTop: '2px' }}>
              {attendanceData.summary.absent_days}
            </div>
          </div>

          {/* Leave Days */}
          <div style={{
            background: '#111827',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '14px',
            padding: '16px',
            borderLeft: '4px solid #f59e0b'
          }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Leave Days</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fbbf24', marginTop: '2px' }}>
              {attendanceData.summary.leave_days}
            </div>
          </div>

          {/* Total Hours */}
          <div style={{
            background: '#111827',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '14px',
            padding: '16px',
            borderLeft: '4px solid #38bdf8'
          }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Total Hours</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#38bdf8', marginTop: '2px', fontFamily: 'monospace' }}>
              {attendanceData.summary.total_hours_formatted}
            </div>
          </div>

          {/* Average Hours/Day */}
          <div style={{
            background: '#111827',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '14px',
            padding: '16px',
            borderLeft: '4px solid #818cf8'
          }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Average Hours/Day</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#818cf8', marginTop: '2px', fontFamily: 'monospace' }}>
              {attendanceData.summary.average_hours_formatted}
            </div>
          </div>

          {/* Total Overtime */}
          <div style={{
            background: '#111827',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '14px',
            padding: '16px',
            borderLeft: '4px solid #a855f7'
          }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Total Overtime</div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#c084fc', marginTop: '2px', fontFamily: 'monospace' }}>
              {attendanceData.summary.total_overtime_formatted}
            </div>
          </div>
        </div>
      )}

      {/* Daily Breakdown Table */}
      <div style={{
        background: '#111827',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
        overflow: 'hidden',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)'
      }}>
        <div style={{
          padding: '18px 24px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
            Daily Attendance Log
          </h3>
          <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
            Click any row to open the complete Verification view with GPS map and full-resolution selfies
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ background: '#0f172a', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Date</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>In Time</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Out Time</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Hours</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600, textAlign: 'center' }}>In Location</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600, textAlign: 'center' }}>Out Location</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600, textAlign: 'center' }}>Selfies</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
                    Loading monthly attendance log...
                  </td>
                </tr>
              ) : attendanceData?.days?.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
                    No records found for this month.
                  </td>
                </tr>
              ) : (
                attendanceData?.days?.map((day) => {
                  const hasRecord = !!day.id;
                  const isPresent = day.status === 'PRESENT';

                  return (
                    <tr
                      key={day.date}
                      style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                        cursor: hasRecord ? 'pointer' : 'default',
                        transition: 'background 0.15s ease'
                      }}
                      onMouseEnter={(e) => hasRecord && (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)')}
                      onMouseLeave={(e) => hasRecord && (e.currentTarget.style.background = 'transparent')}
                      onClick={() => hasRecord && setDayDetails(day)}
                    >
                      {/* Date */}
                      <td style={{ padding: '14px 20px' }}>
                        <div style={{ fontWeight: 600, color: '#f8fafc' }}>{day.date_short}</div>
                        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{day.day_name}</div>
                      </td>

                      {/* Status */}
                      <td style={{ padding: '14px 20px' }}>
                        {getStatusBadge(day.status)}
                      </td>

                      {/* In Time */}
                      <td style={{ padding: '14px 20px', color: '#f1f5f9', fontFamily: 'monospace' }}>
                        {day.check_in_time}
                      </td>

                      {/* Out Time */}
                      <td style={{ padding: '14px 20px', color: '#f1f5f9', fontFamily: 'monospace' }}>
                        {day.check_out_time}
                      </td>

                      {/* Hours */}
                      <td style={{ padding: '14px 20px', fontFamily: 'monospace', fontWeight: 600, color: isPresent ? '#38bdf8' : '#94a3b8' }}>
                        {day.duration_formatted}
                      </td>

                      {/* In Location */}
                      <td style={{ padding: '14px 20px', textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                        {day.check_in_latitude ? (
                          <button
                            onClick={() => setMapModal({
                              open: true,
                              lat: day.check_in_latitude,
                              lng: day.check_in_longitude,
                              acc: day.check_in_accuracy,
                              title: `${selectedEmpName} — Check-In (${day.date_short})`,
                              time: day.check_in_time
                            })}
                            style={{
                              background: 'rgba(56, 189, 248, 0.12)',
                              border: '1px solid rgba(56, 189, 248, 0.3)',
                              color: '#38bdf8',
                              padding: '5px 10px',
                              borderRadius: '8px',
                              fontSize: '0.78rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}
                          >
                            <MapPin size={13} /> View
                          </button>
                        ) : (
                          <span style={{ color: '#64748b' }}>—</span>
                        )}
                      </td>

                      {/* Out Location */}
                      <td style={{ padding: '14px 20px', textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                        {day.check_out_latitude ? (
                          <button
                            onClick={() => setMapModal({
                              open: true,
                              lat: day.check_out_latitude,
                              lng: day.check_out_longitude,
                              acc: day.check_out_accuracy,
                              title: `${selectedEmpName} — Check-Out (${day.date_short})`,
                              time: day.check_out_time
                            })}
                            style={{
                              background: 'rgba(168, 85, 247, 0.12)',
                              border: '1px solid rgba(168, 85, 247, 0.3)',
                              color: '#c084fc',
                              padding: '5px 10px',
                              borderRadius: '8px',
                              fontSize: '0.78rem',
                              fontWeight: 600,
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px'
                            }}
                          >
                            <MapPin size={13} /> View
                          </button>
                        ) : (
                          <span style={{ color: '#64748b' }}>—</span>
                        )}
                      </td>

                      {/* Selfies */}
                      <td style={{ padding: '14px 20px', textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                        <div style={{ display: 'inline-flex', gap: '6px' }}>
                          {day.check_in_selfie && (
                            <button
                              onClick={() => setSelfieModal({
                                open: true,
                                filename: day.check_in_selfie,
                                title: `Check-In Selfie (${day.date_short})`,
                                time: day.check_in_time,
                                employeeName: selectedEmpName
                              })}
                              title="Check-In Selfie"
                              style={{
                                background: 'rgba(16, 185, 129, 0.12)',
                                border: '1px solid rgba(16, 185, 129, 0.3)',
                                color: '#34d399',
                                padding: '5px 8px',
                                borderRadius: '8px',
                                fontSize: '0.78rem',
                                fontWeight: 600,
                                cursor: 'pointer'
                              }}
                            >
                              📷 In
                            </button>
                          )}
                          {day.check_out_selfie && (
                            <button
                              onClick={() => setSelfieModal({
                                open: true,
                                filename: day.check_out_selfie,
                                title: `Check-Out Selfie (${day.date_short})`,
                                time: day.check_out_time,
                                employeeName: selectedEmpName
                              })}
                              title="Check-Out Selfie"
                              style={{
                                background: 'rgba(168, 85, 247, 0.12)',
                                border: '1px solid rgba(168, 85, 247, 0.3)',
                                color: '#c084fc',
                                padding: '5px 8px',
                                borderRadius: '8px',
                                fontSize: '0.78rem',
                                fontWeight: 600,
                                cursor: 'pointer'
                              }}
                            >
                              📷 Out
                            </button>
                          )}
                          {!day.check_in_selfie && !day.check_out_selfie && (
                            <span style={{ color: '#64748b' }}>—</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* DETAILED ATTENDANCE VIEW MODAL (Section 12 Specification) */}
      {dayDetails && (
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
            borderRadius: '22px',
            width: '100%',
            maxWidth: '680px',
            maxHeight: '90vh',
            overflowY: 'auto',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
            display: 'flex',
            flexDirection: 'column'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '20px 24px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              position: 'sticky',
              top: 0,
              background: '#111827',
              zIndex: 10
            }}>
              <div>
                <h2 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800, color: '#f8fafc' }}>
                  {selectedEmpName} — {dayDetails.date_display}
                </h2>
                <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                  Attendance Verification Record
                </span>
              </div>
              <button
                onClick={() => setDayDetails(null)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  padding: '6px'
                }}
              >
                <X size={22} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '22px' }}>
              {/* Overall Attendance Summary Box */}
              <div style={{
                background: '#0f172a',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '16px',
                padding: '18px 22px',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
                gap: '14px'
              }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Status</div>
                  <div style={{ marginTop: '4px' }}>{getStatusBadge(dayDetails.status)}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Check In</div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f1f5f9', fontFamily: 'monospace' }}>
                    {dayDetails.check_in_exact || dayDetails.check_in_time}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Check Out</div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f1f5f9', fontFamily: 'monospace' }}>
                    {dayDetails.check_out_exact || dayDetails.check_out_time}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Total Worked</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#38bdf8', fontFamily: 'monospace' }}>
                    {dayDetails.duration_formatted}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Overtime</div>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: '#fbbf24', fontFamily: 'monospace' }}>
                    {dayDetails.overtime_formatted}
                  </div>
                </div>
              </div>

              {/* Check-In Verification Section */}
              <div style={{
                background: '#0f172a',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '16px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <h3 style={{ margin: 0, fontSize: '1.08rem', fontWeight: 700, color: '#34d399', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <ShieldCheck size={18} /> Check-In Verification
                  </h3>
                  <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                    {dayDetails.check_in_exact || dayDetails.check_in_time}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  {/* Location column */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ fontSize: '0.82rem', color: '#94a3b8', fontWeight: 600 }}>GPS Location</div>
                    {dayDetails.check_in_latitude ? (
                      <>
                        <div style={{ fontSize: '0.88rem', color: '#f1f5f9', fontFamily: 'monospace' }}>
                          Latitude: {Number(dayDetails.check_in_latitude).toFixed(6)}<br />
                          Longitude: {Number(dayDetails.check_in_longitude).toFixed(6)}<br />
                          Accuracy: {Number(dayDetails.check_in_accuracy).toFixed(0)} meters
                        </div>

                        <button
                          onClick={() => setMapModal({
                            open: true,
                            lat: dayDetails.check_in_latitude,
                            lng: dayDetails.check_in_longitude,
                            acc: dayDetails.check_in_accuracy,
                            title: `Check-In Location (${dayDetails.date_short})`,
                            time: dayDetails.check_in_time
                          })}
                          style={{
                            alignSelf: 'flex-start',
                            background: '#2563eb',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '8px',
                            padding: '8px 14px',
                            fontSize: '0.82rem',
                            fontWeight: 600,
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            cursor: 'pointer',
                            marginTop: '6px'
                          }}
                        >
                          <MapPin size={14} /> VIEW CHECK-IN LOCATION
                        </button>
                      </>
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '0.85rem' }}>No location recorded.</span>
                    )}
                  </div>

                  {/* Selfie column */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ fontSize: '0.82rem', color: '#94a3b8', fontWeight: 600 }}>Check-in Selfie</div>
                    {dayDetails.check_in_selfie ? (
                      <div
                        onClick={() => setSelfieModal({
                          open: true,
                          filename: dayDetails.check_in_selfie,
                          title: `Check-In Selfie (${dayDetails.date_short})`,
                          time: dayDetails.check_in_time,
                          employeeName: selectedEmpName
                        })}
                        style={{
                          width: '120px',
                          height: '120px',
                          borderRadius: '12px',
                          overflow: 'hidden',
                          border: '2px solid rgba(16, 185, 129, 0.4)',
                          cursor: 'pointer',
                          position: 'relative'
                        }}
                      >
                        <img
                          src={getSelfieUrl(dayDetails.check_in_selfie)}
                          alt="Check-in selfie"
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                            if (e.currentTarget.nextSibling) {
                              e.currentTarget.parentElement.style.display = 'flex';
                              e.currentTarget.parentElement.style.alignItems = 'center';
                              e.currentTarget.parentElement.style.justifyContent = 'center';
                              e.currentTarget.parentElement.style.background = '#1e293b';
                            }
                          }}
                        />
                        <div style={{
                          position: 'absolute',
                          inset: 0,
                          background: 'rgba(0, 0, 0, 0.3)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#ffffff',
                          opacity: 0,
                          transition: 'opacity 0.2s ease'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                        onMouseLeave={(e) => e.currentTarget.style.opacity = '0'}
                        >
                          <Eye size={20} />
                        </div>
                      </div>
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '0.85rem' }}>No selfie recorded.</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Check-Out Verification Section */}
              <div style={{
                background: '#0f172a',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '16px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '14px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <h3 style={{ margin: 0, fontSize: '1.08rem', fontWeight: 700, color: '#c084fc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <ShieldCheck size={18} /> Check-Out Verification
                  </h3>
                  <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                    {dayDetails.check_out_exact || dayDetails.check_out_time}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  {/* Location column */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ fontSize: '0.82rem', color: '#94a3b8', fontWeight: 600 }}>GPS Location</div>
                    {dayDetails.check_out_latitude ? (
                      <>
                        <div style={{ fontSize: '0.88rem', color: '#f1f5f9', fontFamily: 'monospace' }}>
                          Latitude: {Number(dayDetails.check_out_latitude).toFixed(6)}<br />
                          Longitude: {Number(dayDetails.check_out_longitude).toFixed(6)}<br />
                          Accuracy: {Number(dayDetails.check_out_accuracy).toFixed(0)} meters
                        </div>

                        <button
                          onClick={() => setMapModal({
                            open: true,
                            lat: dayDetails.check_out_latitude,
                            lng: dayDetails.check_out_longitude,
                            acc: dayDetails.check_out_accuracy,
                            title: `Check-Out Location (${dayDetails.date_short})`,
                            time: dayDetails.check_out_time
                          })}
                          style={{
                            alignSelf: 'flex-start',
                            background: '#7c3aed',
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '8px',
                            padding: '8px 14px',
                            fontSize: '0.82rem',
                            fontWeight: 600,
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            cursor: 'pointer',
                            marginTop: '6px'
                          }}
                        >
                          <MapPin size={14} /> VIEW CHECK-OUT LOCATION
                        </button>
                      </>
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '0.85rem' }}>No checkout location recorded.</span>
                    )}
                  </div>

                  {/* Selfie column */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ fontSize: '0.82rem', color: '#94a3b8', fontWeight: 600 }}>Check-out Selfie</div>
                    {dayDetails.check_out_selfie ? (
                      <div
                        onClick={() => setSelfieModal({
                          open: true,
                          filename: dayDetails.check_out_selfie,
                          title: `Check-Out Selfie (${dayDetails.date_short})`,
                          time: dayDetails.check_out_time,
                          employeeName: selectedEmpName
                        })}
                        style={{
                          width: '120px',
                          height: '120px',
                          borderRadius: '12px',
                          overflow: 'hidden',
                          border: '2px solid rgba(168, 85, 247, 0.4)',
                          cursor: 'pointer',
                          position: 'relative'
                        }}
                      >
                        <img
                          src={getSelfieUrl(dayDetails.check_out_selfie)}
                          alt="Check-out selfie"
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                            if (e.currentTarget.nextSibling) {
                              e.currentTarget.parentElement.style.display = 'flex';
                              e.currentTarget.parentElement.style.alignItems = 'center';
                              e.currentTarget.parentElement.style.justifyContent = 'center';
                              e.currentTarget.parentElement.style.background = '#1e293b';
                            }
                          }}
                        />
                        <div style={{
                          position: 'absolute',
                          inset: 0,
                          background: 'rgba(0, 0, 0, 0.3)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#ffffff',
                          opacity: 0,
                          transition: 'opacity 0.2s ease'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                        onMouseLeave={(e) => e.currentTarget.style.opacity = '0'}
                        >
                          <Eye size={20} />
                        </div>
                      </div>
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '0.85rem' }}>No checkout selfie recorded.</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Map Modal */}
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
