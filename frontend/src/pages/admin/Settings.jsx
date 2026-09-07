import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import {
  Settings,
  Clock,
  Building,
  Lock,
  CheckCircle,
  AlertCircle,
  Activity,
  Globe,
  HardDrive,
  Trash2,
  Database,
  RefreshCw,
  Save,
  User,
  ShieldCheck
} from 'lucide-react';

export default function AdminSettings() {
  const { user } = useAuth();

  // General Settings
  const [companyName, setCompanyName] = useState(() => localStorage.getItem('company_name') || 'Seven Stars Logistics Private Limited');
  const [workHours, setWorkHours] = useState(() => parseInt(localStorage.getItem('system_work_hours')) || 8);
  const [timezone, setTimezone] = useState('Asia/Kolkata (IST +05:30)');
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsMsg, setSettingsMsg] = useState({ type: '', text: '' });

  // Change password
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordMsg, setPasswordMsg] = useState({ type: '', text: '' });

  // System Health
  const [healthStatus, setHealthStatus] = useState(null);
  const [healthLoading, setHealthLoading] = useState(false);

  // Storage Stats & Cleanup
  const [storageStats, setStorageStats] = useState(null);
  const [retentionDays, setRetentionDays] = useState(90);
  const [cleanupLoading, setCleanupLoading] = useState(false);
  const [cleanupMsg, setCleanupMsg] = useState({ type: '', text: '' });

  const fetchGeneralSettings = async () => {
    try {
      const res = await apiRequest('/settings/general');
      if (res.success && res.data) {
        if (res.data.company_name) {
          setCompanyName(res.data.company_name);
          localStorage.setItem('company_name', res.data.company_name);
        }
        if (res.data.work_hours) {
          const wh = parseInt(res.data.work_hours) || 8;
          setWorkHours(wh);
          localStorage.setItem('system_work_hours', wh.toString());
        }
        if (res.data.timezone) {
          setTimezone(`${res.data.timezone} (IST +05:30)`);
        }
      }
    } catch (err) {
      console.warn("Could not fetch remote settings, using local defaults:", err);
    }
  };

  const handleSaveGeneralSettings = async (e) => {
    e.preventDefault();
    setSettingsSaving(true);
    setSettingsMsg({ type: '', text: '' });

    try {
      const res = await apiRequest('/settings/general', {
        method: 'PUT',
        body: JSON.stringify({
          company_name: companyName,
          work_hours: workHours
        })
      });

      if (res.success) {
        localStorage.setItem('company_name', companyName);
        localStorage.setItem('system_work_hours', workHours.toString());
        setSettingsMsg({ type: 'success', text: 'Company & work configuration saved successfully!' });
      } else {
        throw new Error(res.message || 'Failed to save settings.');
      }
    } catch (err) {
      // Fallback save to localStorage if backend offline
      localStorage.setItem('company_name', companyName);
      localStorage.setItem('system_work_hours', workHours.toString());
      setSettingsMsg({ type: 'success', text: 'Saved configuration to local browser cache.' });
    } finally {
      setSettingsSaving(false);
    }
  };

  const checkHealth = async () => {
    setHealthLoading(true);
    try {
      const res = await apiRequest('/health');
      if (res.success && res.data) {
        setHealthStatus(res.data);
      }
    } catch (err) {
      setHealthStatus({ status: 'DOWN', error: err.message });
    } finally {
      setHealthLoading(false);
    }
  };

  const fetchStorageStats = async () => {
    try {
      const res = await apiRequest('/settings/storage');
      if (res.success && res.data) {
        setStorageStats(res.data);
        if (res.data.retention_days) {
          setRetentionDays(res.data.retention_days);
        }
      }
    } catch (err) {
      console.error("Failed to fetch storage stats:", err);
    }
  };

  useEffect(() => {
    checkHealth();
    fetchGeneralSettings();
    fetchStorageStats();
  }, []);

  const handleRunCleanup = async () => {
    if (!window.confirm(`Are you sure you want to clean up records older than ${retentionDays} days? This will permanently delete records and photos older than this date across all staff.`)) {
      return;
    }

    setCleanupLoading(true);
    setCleanupMsg({ type: '', text: '' });

    try {
      const res = await apiRequest('/settings/cleanup', {
        method: 'POST',
        body: JSON.stringify({ retention_days: retentionDays })
      });
      if (res.success) {
        setCleanupMsg({ type: 'success', text: res.message || 'Storage cleanup executed successfully.' });
        fetchStorageStats();
      }
    } catch (err) {
      setCleanupMsg({ type: 'error', text: err.message || 'Failed to run storage cleanup.' });
    } finally {
      setCleanupLoading(false);
    }
  };

  const handleRunFullPrunerTest = async () => {
    if (!window.confirm("Test Full-Storage Auto-Pruner: This will prune the oldest recorded date across ALL staff members simultaneously. Are you sure you want to run this test?")) {
      return;
    }

    setCleanupLoading(true);
    setCleanupMsg({ type: '', text: '' });

    try {
      const res = await apiRequest('/settings/cleanup-on-full-test', {
        method: 'POST',
        body: JSON.stringify({ target_free_mb: 50.0 })
      });
      if (res.success) {
        setCleanupMsg({ type: 'success', text: res.message || 'Full-storage pruning test completed successfully.' });
        fetchStorageStats();
      }
    } catch (err) {
      setCleanupMsg({ type: 'error', text: err.message || 'Failed to execute storage pruning test.' });
    } finally {
      setCleanupLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordMsg({ type: '', text: '' });

    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: 'error', text: 'New passwords do not match.' });
      return;
    }

    if (newPassword.length < 6) {
      setPasswordMsg({ type: 'error', text: 'New password must be at least 6 characters.' });
      return;
    }

    setPasswordLoading(true);
    try {
      const res = await apiRequest('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
      });
      if (res.success) {
        setPasswordMsg({ type: 'success', text: 'Password updated successfully. Please remember your new password.' });
        setOldPassword('');
        setNewPassword('');
        setConfirmPassword('');
      }
    } catch (err) {
      setPasswordMsg({ type: 'error', text: err.message || 'Failed to update password.' });
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div className="admin-page-container" style={{ maxWidth: '840px' }}>
      <div>
        <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc' }}>
          System Settings
        </h1>
        <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: '#94a3b8' }}>
          Manage working hour thresholds, company localization, cloud storage, and administrator security
        </p>
      </div>

      {/* 1. Working Hours & Company Profile */}
      <div style={{
        background: '#111827',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '18px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'rgba(56, 189, 248, 0.15)',
              color: '#38bdf8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Building size={20} />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                Company Profile & Work Hours
              </h2>
              <p style={{ margin: 0, fontSize: '0.82rem', color: '#94a3b8' }}>
                Operational parameters and standard daily work calculation
              </p>
            </div>
          </div>

          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.78rem',
            fontWeight: 700,
            padding: '4px 12px',
            borderRadius: '9999px',
            background: 'rgba(56, 189, 248, 0.12)',
            color: '#38bdf8',
            border: '1px solid rgba(56, 189, 248, 0.25)'
          }}>
            <Clock size={13} /> Active Standard Rule
          </span>
        </div>

        {settingsMsg.text && (
          <div style={{
            background: settingsMsg.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${settingsMsg.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            borderRadius: '10px',
            padding: '10px 14px',
            color: settingsMsg.type === 'success' ? '#34d399' : '#f87171',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            {settingsMsg.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
            <span>{settingsMsg.text}</span>
          </div>
        )}

        <form onSubmit={handleSaveGeneralSettings} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
              Company / Organization Name
            </label>
            <input
              type="text"
              required
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="Seven Stars Logistics Private Limited"
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '10px',
                background: '#1e293b',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#f8fafc',
                fontSize: '0.92rem',
                fontWeight: 600
              }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                Standard Daily Working Hours
              </label>
              <input
                type="number"
                min="1"
                max="24"
                required
                value={workHours}
                onChange={(e) => setWorkHours(parseInt(e.target.value) || 8)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  background: '#1e293b',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: '#f8fafc',
                  fontSize: '0.92rem',
                  fontWeight: 600
                }}
              />
              <span style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '4px', display: 'block' }}>
                Default: 8 hours ({workHours * 60} minutes) per workday
              </span>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                Overtime Calculation Rule
              </label>
              <div style={{
                padding: '10px 14px',
                borderRadius: '10px',
                background: '#0f172a',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                color: '#34d399',
                fontSize: '0.88rem',
                fontWeight: 600,
                minHeight: '42px',
                display: 'flex',
                alignItems: 'center'
              }}>
                Work &gt; {workHours} hrs is auto-credited as Overtime
              </div>
              <span style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '4px', display: 'block' }}>
                Example: {String(workHours + 1).padStart(2, '0')}h 30m worked = 01h 30m overtime
              </span>
            </div>
          </div>

          <button
            type="submit"
            disabled={settingsSaving}
            style={{
              alignSelf: 'flex-start',
              padding: '10px 20px',
              borderRadius: '10px',
              background: '#2563eb',
              color: '#ffffff',
              border: 'none',
              fontSize: '0.88rem',
              fontWeight: 600,
              cursor: settingsSaving ? 'not-allowed' : 'pointer',
              opacity: settingsSaving ? 0.7 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginTop: '4px'
            }}
          >
            <Save size={16} />
            <span>{settingsSaving ? 'Saving Configuration...' : 'Save Configuration'}</span>
          </button>
        </form>
      </div>

      {/* 2. Localization & Timezone */}
      <div style={{
        background: '#111827',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '18px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'rgba(16, 185, 129, 0.15)',
            color: '#34d399',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Globe size={20} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
              Localization & Server Timezone
            </h2>
            <p style={{ margin: 0, fontSize: '0.82rem', color: '#94a3b8' }}>Strict Indian Standard Time enforcement</p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
              Official Timezone
            </label>
            <input
              type="text"
              readOnly
              value={timezone}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '10px',
                background: '#0f172a',
                border: '1px solid rgba(255, 255, 255, 0.06)',
                color: '#38bdf8',
                fontSize: '0.92rem',
                fontWeight: 600
              }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                Backend API Status
              </label>
              <button
                type="button"
                onClick={checkHealth}
                disabled={healthLoading}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#38bdf8',
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: 0
                }}
              >
                <RefreshCw size={12} style={{ animation: healthLoading ? 'spin 1s linear infinite' : 'none' }} />
                <span>Re-check</span>
              </button>
            </div>

            <div style={{
              padding: '10px 14px',
              borderRadius: '10px',
              background: '#0f172a',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              color: healthStatus?.status === 'UP' ? '#34d399' : '#f87171',
              fontSize: '0.88rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <Activity size={16} />
              <span>{healthStatus?.status === 'UP' ? 'Flask Cloud API Online (v2.0.0)' : 'API Connecting...'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Cloud Storage & Auto-Cleanup */}
      <div style={{
        background: '#111827',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '18px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'rgba(168, 85, 247, 0.15)',
              color: '#c084fc',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <HardDrive size={20} />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                Cloud Storage & Auto-Cleanup
              </h2>
              <p style={{ margin: 0, fontSize: '0.82rem', color: '#94a3b8' }}>
                Manage 5 GB cloud storage quota and automatic retention pruning
              </p>
            </div>
          </div>

          <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.78rem',
            fontWeight: 700,
            padding: '4px 12px',
            borderRadius: '9999px',
            background: 'rgba(16, 185, 129, 0.15)',
            color: '#34d399',
            border: '1px solid rgba(16, 185, 129, 0.3)'
          }}>
            <CheckCircle size={14} /> Clean Only When Storage Full Active
          </span>
        </div>

        {cleanupMsg.text && (
          <div style={{
            background: cleanupMsg.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${cleanupMsg.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            borderRadius: '10px',
            padding: '10px 14px',
            color: cleanupMsg.type === 'success' ? '#34d399' : '#f87171',
            fontSize: '0.85rem'
          }}>
            {cleanupMsg.text}
          </div>
        )}

        {/* Policy Summary Banner */}
        <div style={{
          background: 'rgba(56, 189, 248, 0.08)',
          border: '1px solid rgba(56, 189, 248, 0.2)',
          borderRadius: '12px',
          padding: '12px 16px',
          fontSize: '0.82rem',
          color: '#cbd5e1',
          lineHeight: 1.5
        }}>
          🛡️ <strong>Permanent Cloud Retention Rule:</strong> All employee attendance records and selfie photos are <strong>preserved permanently</strong> without scheduled deletion. Old data is <em>only</em> automatically deleted if cloud storage reaches <strong>90% capacity (4,608 MB of 5,120 MB)</strong>. When triggered, it prunes the oldest recorded date across <strong>all staff simultaneously</strong>, freeing 500 MB headroom so new attendance and photos can always be input smoothly.
        </div>

        {/* Storage Metric Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
          <div style={{ background: '#0f172a', padding: '14px 16px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Total Records</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#f8fafc', marginTop: '4px' }}>
              {storageStats ? storageStats.total_records.toLocaleString() : '—'}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '2px' }}>
              {storageStats?.oldest_record_date ? `Since ${storageStats.oldest_record_date}` : 'No records yet'}
            </div>
          </div>

          <div style={{ background: '#0f172a', padding: '14px 16px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Selfie Photos</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#38bdf8', marginTop: '4px' }}>
              {storageStats ? storageStats.selfie_files_count.toLocaleString() : '—'}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '2px' }}>
              {storageStats ? `${storageStats.selfies_storage_mb} MB stored` : '—'}
            </div>
          </div>

          <div style={{ background: '#0f172a', padding: '14px 16px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
            <div style={{ fontSize: '0.75rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Quota Used</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: '#34d399', marginTop: '4px' }}>
              {storageStats ? `${storageStats.storage_used_percentage}%` : '0%'}
            </div>
            <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '2px' }}>
              {storageStats ? `${storageStats.storage_free_mb || 5120} MB free` : '5,120 MB free limit'}
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: '#94a3b8', marginBottom: '6px' }}>
            <span>Cloud Storage Usage</span>
            <span>{storageStats ? `${storageStats.selfies_storage_mb} MB / 5,120 MB (5 GB Free Plan)` : '0 MB / 5 GB'}</span>
          </div>
          <div style={{ height: '8px', background: '#1e293b', borderRadius: '9999px', overflow: 'hidden' }}>
            <div style={{
              height: '100%',
              width: `${Math.max(1, storageStats?.storage_used_percentage || 1)}%`,
              background: 'linear-gradient(90deg, #10b981, #06b6d4)',
              borderRadius: '9999px'
            }} />
          </div>
        </div>

        {/* Action Controls */}
        <div style={{
          background: '#0f172a',
          borderRadius: '12px',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
          border: '1px solid rgba(255, 255, 255, 0.06)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.86rem', fontWeight: 600, color: '#f8fafc' }}>
                Storage Pruning Engine Controls
              </label>
              <p style={{ margin: '2px 0 0 0', fontSize: '0.76rem', color: '#94a3b8' }}>
                Auto-prune triggers automatically at 90% full. You can also manually test or prune below.
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={handleRunFullPrunerTest}
                disabled={cleanupLoading}
                style={{
                  background: 'rgba(56, 189, 248, 0.15)',
                  border: '1px solid rgba(56, 189, 248, 0.35)',
                  color: '#38bdf8',
                  borderRadius: '10px',
                  padding: '9px 16px',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  cursor: cleanupLoading ? 'not-allowed' : 'pointer'
                }}
              >
                <RefreshCw size={15} style={{ animation: cleanupLoading ? 'spin 1s linear infinite' : 'none' }} />
                <span>Test Full-Storage Pruner</span>
              </button>

              <select
                value={retentionDays}
                onChange={(e) => setRetentionDays(parseInt(e.target.value))}
                style={{
                  padding: '9px 12px',
                  borderRadius: '10px',
                  background: '#1e293b',
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  color: '#f8fafc',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <option value={30}>Older than 30 Days</option>
                <option value={60}>Older than 60 Days</option>
                <option value={90}>Older than 90 Days</option>
                <option value={180}>Older than 180 Days</option>
              </select>

              <button
                type="button"
                onClick={handleRunCleanup}
                disabled={cleanupLoading}
                style={{
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.35)',
                  color: '#f87171',
                  borderRadius: '10px',
                  padding: '9px 14px',
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  cursor: cleanupLoading ? 'not-allowed' : 'pointer'
                }}
              >
                <Trash2 size={14} />
                <span>Manual Prune</span>
              </button>
            </div>
          </div>

          <div style={{ fontSize: '0.75rem', color: '#64748b', lineHeight: 1.4 }}>
            ℹ️ <strong>Simultaneous Guarantee:</strong> Every pruning operation (automatic on full storage or manual) cleans records and selfie files for <strong>all staff members up to the exact same date</strong>. No staff member will have mismatched history.
          </div>
        </div>
      </div>

      {/* 4. Admin Account Security */}
      <div style={{
        background: '#111827',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '18px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'rgba(99, 102, 241, 0.15)',
              color: '#818cf8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Lock size={20} />
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                Admin Account Security
              </h2>
              <p style={{ margin: 0, fontSize: '0.82rem', color: '#94a3b8' }}>Update administrator credentials</p>
            </div>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(255, 255, 255, 0.04)',
            padding: '6px 12px',
            borderRadius: '10px',
            border: '1px solid rgba(255, 255, 255, 0.08)'
          }}>
            <User size={15} style={{ color: '#818cf8' }} />
            <span style={{ fontSize: '0.82rem', color: '#cbd5e1' }}>
              Logged in as: <strong style={{ color: '#f8fafc' }}>{user?.email || 'Admin'}</strong>
            </span>
          </div>
        </div>

        {passwordMsg.text && (
          <div style={{
            background: passwordMsg.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${passwordMsg.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            borderRadius: '10px',
            padding: '10px 14px',
            color: passwordMsg.type === 'success' ? '#34d399' : '#f87171',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            {passwordMsg.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
            <span>{passwordMsg.text}</span>
          </div>
        )}

        <form onSubmit={handleChangePassword} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
              Current Password
            </label>
            <input
              type="password"
              required
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '10px',
                background: '#1e293b',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#f8fafc',
                fontSize: '0.9rem'
              }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                New Password
              </label>
              <input
                type="password"
                required
                minLength={6}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Minimum 6 characters"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  background: '#1e293b',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: '#f8fafc',
                  fontSize: '0.9rem'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>
                Confirm New Password
              </label>
              <input
                type="password"
                required
                minLength={6}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '10px',
                  background: '#1e293b',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: '#f8fafc',
                  fontSize: '0.9rem'
                }}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={passwordLoading}
            style={{
              alignSelf: 'flex-start',
              padding: '10px 20px',
              borderRadius: '10px',
              background: '#2563eb',
              color: '#ffffff',
              border: 'none',
              fontSize: '0.9rem',
              fontWeight: 600,
              cursor: passwordLoading ? 'not-allowed' : 'pointer',
              opacity: passwordLoading ? 0.7 : 1,
              marginTop: '4px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <ShieldCheck size={16} />
            <span>{passwordLoading ? 'Updating Password...' : 'Save Password'}</span>
          </button>
        </form>
      </div>
    </div>
  );
}
