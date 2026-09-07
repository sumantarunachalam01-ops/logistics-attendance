import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { apiRequest } from '../../services/api';
import CameraModal from '../../components/common/CameraModal';
import LocationModal from '../../components/common/LocationModal';
import SelfieModal from '../../components/common/SelfieModal';
import {
  Play,
  Square,
  MapPin,
  Camera,
  CheckCircle2,
  Clock,
  Calendar,
  AlertCircle,
  Loader2,
  Eye,
  ShieldCheck
} from 'lucide-react';

export default function StaffDashboard() {
  const { user } = useAuth();

  const [todayData, setTodayData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Live IST Clock
  const [liveTime, setLiveTime] = useState('');
  const [liveDate, setLiveDate] = useState('');

  // Live timer for currently working
  const [liveWorkMinutes, setLiveWorkMinutes] = useState(0);

  // Modals
  const [cameraOpen, setCameraOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState(null); // 'START' | 'END'
  const [pendingLocation, setPendingLocation] = useState(null);

  const [mapModal, setMapModal] = useState({ open: false, lat: null, lng: null, acc: null, title: '', time: '' });
  const [selfieModal, setSelfieModal] = useState({ open: false, filename: null, title: '', time: '' });

  // Confirmation screen state
  const [confirmation, setConfirmation] = useState(null); // { type: 'START' | 'END', ... }

  // Update live clock
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setLiveTime(now.toLocaleTimeString('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }));
      setLiveDate(now.toLocaleDateString('en-IN', {
        timeZone: 'Asia/Kolkata',
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      }));
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Fetch today's status
  const fetchTodayAttendance = async () => {
    try {
      setErrorMsg(null);
      const res = await apiRequest('/attendance/today');
      if (res.success && res.data) {
        setTodayData(res.data.attendance);
        setLiveWorkMinutes(res.data.live_work_minutes || 0);
      }
    } catch (err) {
      console.error("Failed to fetch today's attendance:", err);
      setErrorMsg(err.message || "Failed to load today's attendance.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTodayAttendance();
  }, []);

  // Live elapsed counter if currently working
  useEffect(() => {
    if (!todayData?.check_in_time || todayData?.check_out_time) return;

    const interval = setInterval(() => {
      setLiveWorkMinutes(prev => prev + 1);
    }, 60000); // every minute

    return () => clearInterval(interval);
  }, [todayData]);

  // Greeting helper
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  // Format minutes into Xh Ym
  const formatHm = (min) => {
    if (!min || min <= 0) return '00h 00m';
    const h = Math.floor(min / 60);
    const m = min % 60;
    return `${String(h).padStart(2, '0')}h ${String(m).padStart(2, '0')}m`;
  };

  // Step 1: Capture GPS position
  const initiateAttendanceFlow = (actionType) => {
    setErrorMsg(null);
    setConfirmation(null);
    setActionLoading(true);

    if (!navigator.geolocation) {
      setActionLoading(false);
      setErrorMsg("Geolocation is not supported by your browser/device.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setActionLoading(false);
        setPendingLocation({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy || 15.0,
        });
        setPendingAction(actionType);
        setCameraOpen(true);
      },
      (err) => {
        setActionLoading(false);
        console.warn("Geolocation prompt error:", err);
        // If permission prompt fails or in simulated environment, allow fallback coordinates for smooth demo
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
          setPendingLocation({
            latitude: 13.0827,
            longitude: 80.2707,
            accuracy: 18.0
          });
          setPendingAction(actionType);
          setCameraOpen(true);
        } else {
          setErrorMsg("Location access denied or unavailable. Please enable GPS location permission.");
        }
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
    );
  };

  // Step 3: Handle Selfie captured -> Send to backend
  const handleSelfieCaptured = async (selfieBase64) => {
    if (!pendingAction || !pendingLocation) return;

    setActionLoading(true);
    setErrorMsg(null);

    const endpoint = pendingAction === 'START' ? '/attendance/start' : '/attendance/end';

    try {
      const payload = {
        latitude: pendingLocation.latitude,
        longitude: pendingLocation.longitude,
        accuracy: pendingLocation.accuracy,
        selfie: selfieBase64
      };

      const res = await apiRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (res.success && res.data) {
        if (pendingAction === 'START') {
          setConfirmation({
            type: 'START',
            time: res.data.check_in_formatted,
            lat: res.data.latitude,
            lng: res.data.longitude,
            acc: res.data.accuracy,
            selfie: res.data.selfie_filename,
            message: "You are now marked as PRESENT."
          });
        } else {
          setConfirmation({
            type: 'END',
            checkIn: res.data.check_in_formatted,
            checkOut: res.data.check_out_formatted,
            duration: res.data.duration_formatted,
            overtime: res.data.overtime_formatted,
            lat: res.data.latitude || pendingLocation.latitude,
            lng: res.data.longitude || pendingLocation.longitude,
            acc: res.data.accuracy || pendingLocation.accuracy,
            selfie: res.data.selfie_filename,
            message: `Today's working time: ${res.data.duration_formatted}`
          });
        }
        // Refresh today data
        await fetchTodayAttendance();
      }
    } catch (err) {
      console.error("Attendance submission error:", err);
      setErrorMsg(err.message || "Failed to record attendance. Please try again.");
    } finally {
      setActionLoading(false);
      setPendingAction(null);
      setPendingLocation(null);
    }
  };

  const isWorking = todayData?.check_in_time && !todayData?.check_out_time;
  const isCompleted = todayData?.check_in_time && todayData?.check_out_time;
  const isNotStarted = !todayData?.check_in_time;

  return (
    <div style={{
      maxWidth: '560px',
      margin: '0 auto',
      padding: '24px 16px 80px 16px',
      display: 'flex',
      flexDirection: 'column',
      gap: '20px'
    }}>
      {/* Header Greeting */}
      <div style={{
        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
        padding: '24px',
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.4)'
      }}>
        <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc', marginBottom: '4px' }}>
          {getGreeting()}, {user?.full_name || 'Staff'}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94a3b8', fontSize: '0.9rem', marginBottom: '14px' }}>
          <Calendar size={16} style={{ color: '#38bdf8' }} />
          <span>{liveDate || 'Loading date...'}</span>
        </div>

        <div style={{
          background: 'rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          borderRadius: '12px',
          padding: '10px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Current IST Time</span>
          <span style={{ fontSize: '1.2rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.02em', fontFamily: 'monospace' }}>
            {liveTime || '—'}
          </span>
        </div>
      </div>

      {/* Error Alert */}
      {errorMsg && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '14px',
          padding: '14px 16px',
          color: '#fca5a5',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '10px',
          fontSize: '0.9rem'
        }}>
          <AlertCircle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div style={{ flex: 1 }}>{errorMsg}</div>
        </div>
      )}

      {/* Confirmation Card (Shown immediately after check-in or check-out) */}
      {confirmation && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.1) 100%)',
          border: '1px solid rgba(16, 185, 129, 0.4)',
          borderRadius: '18px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          boxShadow: '0 8px 24px rgba(16, 185, 129, 0.2)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <CheckCircle2 size={24} style={{ color: '#34d399' }} />
            <div>
              <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                {confirmation.type === 'START' ? 'Attendance Started Successfully' : 'Attendance Completed Successfully'}
              </div>
              <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Official server timestamp recorded in IST</div>
            </div>
          </div>

          {confirmation.type === 'START' ? (
            <div style={{
              background: 'rgba(0, 0, 0, 0.25)',
              borderRadius: '12px',
              padding: '14px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              fontSize: '0.92rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#f1f5f9', fontWeight: 600 }}>
                <span>Start Time:</span>
                <span style={{ color: '#34d399' }}>{confirmation.time}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#38bdf8', fontSize: '0.85rem' }}>
                <MapPin size={15} /> <span>Location Captured (±{confirmation.acc}m)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#34d399', fontSize: '0.85rem' }}>
                <Camera size={15} /> <span>Selfie Captured & Verified</span>
              </div>
              <div style={{ marginTop: '6px', color: '#34d399', fontWeight: 600, fontSize: '0.88rem' }}>
                ✓ {confirmation.message}
              </div>
            </div>
          ) : (
            <div style={{
              background: 'rgba(0, 0, 0, 0.25)',
              borderRadius: '12px',
              padding: '14px',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              fontSize: '0.92rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span>Check In:</span>
                <span style={{ color: '#f1f5f9', fontWeight: 600 }}>{confirmation.checkIn}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8' }}>
                <span>Check Out:</span>
                <span style={{ color: '#f1f5f9', fontWeight: 600 }}>{confirmation.checkOut}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#c084fc', fontSize: '0.85rem' }}>
                <MapPin size={15} /> <span>Out Location Captured (±{confirmation.acc || 15}m)</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#c084fc', fontSize: '0.85rem' }}>
                <Camera size={15} /> <span>Out Selfie Captured & Verified</span>
              </div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                color: '#34d399',
                fontWeight: 700,
                fontSize: '1rem',
                paddingTop: '6px',
                borderTop: '1px solid rgba(255, 255, 255, 0.08)'
              }}>
                <span>Total Worked:</span>
                <span>{confirmation.duration}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Main Attendance Status Card */}
      <div style={{
        background: '#111827',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '20px',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.35)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <span style={{ fontSize: '0.78rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
              Today's Attendance
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
              {isWorking ? (
                <span style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  color: '#34d399',
                  padding: '4px 12px',
                  borderRadius: '9999px',
                  fontWeight: 700,
                  fontSize: '0.88rem'
                }}>
                  🟢 WORKING
                </span>
              ) : isCompleted ? (
                <span style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'rgba(59, 130, 246, 0.15)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  color: '#60a5fa',
                  padding: '4px 12px',
                  borderRadius: '9999px',
                  fontWeight: 700,
                  fontSize: '0.88rem'
                }}>
                  🔵 COMPLETED
                </span>
              ) : (
                <span style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'rgba(148, 163, 184, 0.15)',
                  border: '1px solid rgba(148, 163, 184, 0.3)',
                  color: '#cbd5e1',
                  padding: '4px 12px',
                  borderRadius: '9999px',
                  fontWeight: 700,
                  fontSize: '0.88rem'
                }}>
                  ⚪ Not Started
                </span>
              )}
            </div>
          </div>

          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: isWorking ? 'rgba(16, 185, 129, 0.15)' : 'rgba(37, 99, 235, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: isWorking ? '#34d399' : '#38bdf8'
          }}>
            <Clock size={24} />
          </div>
        </div>

        {/* STATE 1: NOT STARTED */}
        {isNotStarted && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Ready to begin your work day? Press below to verify your GPS location and live camera selfie.
            </p>

            <button
              onClick={() => initiateAttendanceFlow('START')}
              disabled={actionLoading}
              style={{
                width: '100%',
                padding: '20px',
                borderRadius: '16px',
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                color: '#ffffff',
                border: 'none',
                fontSize: '1.15rem',
                fontWeight: 800,
                letterSpacing: '0.03em',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '12px',
                cursor: actionLoading ? 'not-allowed' : 'pointer',
                opacity: actionLoading ? 0.7 : 1,
                boxShadow: '0 8px 24px rgba(16, 185, 129, 0.4)',
                transition: 'all 0.2s ease'
              }}
            >
              {actionLoading ? (
                <>
                  <Loader2 size={24} className="animate-spin" />
                  <span>Requesting GPS & Camera...</span>
                </>
              ) : (
                <>
                  <Play size={24} fill="#ffffff" />
                  <span>START ATTENDANCE</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* STATE 2: WORKING */}
        {isWorking && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div style={{
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              borderRadius: '14px',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '10px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Started:</span>
                <span style={{ fontSize: '0.98rem', fontWeight: 700, color: '#f1f5f9' }}>
                  {todayData.check_in_formatted}
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Current working time:</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#34d399', fontFamily: 'monospace' }}>
                  {formatHm(liveWorkMinutes)}
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Location:</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.85rem', color: '#38bdf8', fontWeight: 500 }}>
                    Location captured (±{todayData.check_in_accuracy || 15}m)
                  </span>
                  <button
                    onClick={() => setMapModal({
                      open: true,
                      lat: todayData.check_in_latitude,
                      lng: todayData.check_in_longitude,
                      acc: todayData.check_in_accuracy,
                      title: 'Check-In Location',
                      time: todayData.check_in_formatted
                    })}
                    style={{
                      background: 'rgba(56, 189, 248, 0.15)',
                      border: 'none',
                      color: '#38bdf8',
                      padding: '4px 8px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <Eye size={12} /> View
                  </button>
                </div>
              </div>

              {todayData.check_in_selfie && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Selfie:</span>
                  <button
                    onClick={() => setSelfieModal({
                      open: true,
                      filename: todayData.check_in_selfie,
                      title: 'Check-In Selfie',
                      time: todayData.check_in_formatted
                    })}
                    style={{
                      background: 'rgba(16, 185, 129, 0.15)',
                      border: 'none',
                      color: '#34d399',
                      padding: '4px 8px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <Camera size={12} /> View Photo
                  </button>
                </div>
              )}
            </div>

            <button
              onClick={() => initiateAttendanceFlow('END')}
              disabled={actionLoading}
              style={{
                width: '100%',
                padding: '20px',
                borderRadius: '16px',
                background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                color: '#ffffff',
                border: 'none',
                fontSize: '1.15rem',
                fontWeight: 800,
                letterSpacing: '0.03em',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '12px',
                cursor: actionLoading ? 'not-allowed' : 'pointer',
                opacity: actionLoading ? 0.7 : 1,
                boxShadow: '0 8px 24px rgba(239, 68, 68, 0.4)',
                transition: 'all 0.2s ease'
              }}
            >
              {actionLoading ? (
                <>
                  <Loader2 size={24} className="animate-spin" />
                  <span>Requesting GPS & Camera...</span>
                </>
              ) : (
                <>
                  <Square size={22} fill="#ffffff" />
                  <span>END ATTENDANCE</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* STATE 3: COMPLETED */}
        {isCompleted && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              borderRadius: '14px',
              padding: '18px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Check In:</span>
                <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f1f5f9' }}>{todayData.check_in_formatted}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Check Out:</span>
                <span style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f1f5f9' }}>{todayData.check_out_formatted}</span>
              </div>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                paddingTop: '8px',
                borderTop: '1px solid rgba(255, 255, 255, 0.08)'
              }}>
                <span style={{ fontSize: '0.9rem', color: '#94a3b8' }}>Total Worked:</span>
                <span style={{ fontSize: '1.2rem', fontWeight: 800, color: '#38bdf8', fontFamily: 'monospace' }}>
                  {formatHm(todayData.total_work_minutes)}
                </span>
              </div>
              {todayData.overtime_minutes > 0 && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.85rem', color: '#f59e0b' }}>Overtime:</span>
                  <span style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fbbf24' }}>
                    {formatHm(todayData.overtime_minutes)}
                  </span>
                </div>
              )}

              {/* View Verification Buttons */}
              <div style={{
                display: 'flex',
                gap: '8px',
                flexWrap: 'wrap',
                paddingTop: '10px',
                borderTop: '1px solid rgba(255, 255, 255, 0.08)'
              }}>
                {todayData.check_in_latitude && (
                  <button
                    onClick={() => setMapModal({
                      open: true,
                      lat: todayData.check_in_latitude,
                      lng: todayData.check_in_longitude,
                      acc: todayData.check_in_accuracy,
                      title: 'Check-In Location',
                      time: todayData.check_in_formatted
                    })}
                    style={{
                      flex: '1 1 calc(50% - 4px)',
                      minWidth: '100px',
                      background: 'rgba(56, 189, 248, 0.1)',
                      border: '1px solid rgba(56, 189, 248, 0.25)',
                      color: '#38bdf8',
                      padding: '8px',
                      borderRadius: '8px',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    <MapPin size={13} /> In Map
                  </button>
                )}

                {todayData.check_out_latitude && (
                  <button
                    onClick={() => setMapModal({
                      open: true,
                      lat: todayData.check_out_latitude,
                      lng: todayData.check_out_longitude,
                      acc: todayData.check_out_accuracy,
                      title: 'Check-Out Location',
                      time: todayData.check_out_formatted
                    })}
                    style={{
                      flex: '1 1 calc(50% - 4px)',
                      minWidth: '100px',
                      background: 'rgba(168, 85, 247, 0.1)',
                      border: '1px solid rgba(168, 85, 247, 0.25)',
                      color: '#c084fc',
                      padding: '8px',
                      borderRadius: '8px',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    <MapPin size={13} /> Out Map
                  </button>
                )}

                {todayData.check_in_selfie && (
                  <button
                    onClick={() => setSelfieModal({
                      open: true,
                      filename: todayData.check_in_selfie,
                      title: 'Check-In Selfie',
                      time: todayData.check_in_formatted
                    })}
                    style={{
                      flex: '1 1 calc(50% - 4px)',
                      minWidth: '100px',
                      background: 'rgba(16, 185, 129, 0.1)',
                      border: '1px solid rgba(16, 185, 129, 0.25)',
                      color: '#34d399',
                      padding: '8px',
                      borderRadius: '8px',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    <Camera size={13} /> In Selfie
                  </button>
                )}

                {todayData.check_out_selfie && (
                  <button
                    onClick={() => setSelfieModal({
                      open: true,
                      filename: todayData.check_out_selfie,
                      title: 'Check-Out Selfie',
                      time: todayData.check_out_formatted
                    })}
                    style={{
                      flex: '1 1 calc(50% - 4px)',
                      minWidth: '100px',
                      background: 'rgba(168, 85, 247, 0.1)',
                      border: '1px solid rgba(168, 85, 247, 0.25)',
                      color: '#c084fc',
                      padding: '8px',
                      borderRadius: '8px',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    <Camera size={13} /> Out Selfie
                  </button>
                )}
              </div>
            </div>

            <div style={{
              background: 'rgba(16, 185, 129, 0.1)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              borderRadius: '12px',
              padding: '12px 16px',
              color: '#34d399',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              justifyContent: 'center'
            }}>
              <ShieldCheck size={16} /> Attendance marked and closed for today.
            </div>
          </div>
        )}
      </div>

      {/* Camera Capture Modal */}
      <CameraModal
        isOpen={cameraOpen}
        onClose={() => { setCameraOpen(false); setPendingAction(null); setPendingLocation(null); }}
        onCapture={handleSelfieCaptured}
        title={pendingAction === 'START' ? 'Check-In Selfie Verification' : 'Check-Out Selfie Verification'}
      />

      {/* Map Location Modal */}
      <LocationModal
        isOpen={mapModal.open}
        onClose={() => setMapModal(prev => ({ ...prev, open: false }))}
        latitude={mapModal.lat}
        longitude={mapModal.lng}
        accuracy={mapModal.acc}
        title={mapModal.title}
        time={mapModal.time}
      />

      {/* Selfie Preview Modal */}
      <SelfieModal
        isOpen={selfieModal.open}
        onClose={() => setSelfieModal(prev => ({ ...prev, open: false }))}
        filename={selfieModal.filename}
        title={selfieModal.title}
        time={selfieModal.time}
        employeeName={user?.full_name}
      />
    </div>
  );
}
