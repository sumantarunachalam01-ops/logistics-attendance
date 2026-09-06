import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiRequest } from '../../services/api';
import {
  FileSpreadsheet,
  Download,
  Calendar,
  ExternalLink,
  Users
} from 'lucide-react';

export default function AdminReports() {
  const navigate = useNavigate();
  const [selectedMonth, setSelectedMonth] = useState('2026-09');
  const [reportData, setReportData] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchMonthlyReport = async (month) => {
    setLoading(true);
    try {
      const res = await apiRequest(`/reports/monthly?month=${month}`);
      if (res.success && res.data) {
        setReportData(res.data.records || []);
      }
    } catch (err) {
      console.error("Failed to load monthly company report:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonthlyReport(selectedMonth);
  }, [selectedMonth]);

  const handleExportCsv = () => {
    const token = localStorage.getItem('logitrack_token');
    window.open(`/api/reports/monthly?month=${selectedMonth}&format=csv&token=${token}`, '_blank');
  };

  const getMonthDisplayName = (monthStr) => {
    const [y, m] = monthStr.split('-').map(Number);
    const d = new Date(y, m - 1, 1);
    return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  return (
    <div style={{ padding: '28px', maxWidth: '1280px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc' }}>
            Monthly Company Attendance Report
          </h1>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
            Consolidated staff attendance totals, working hours, and overtime breakdown
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Month Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Calendar size={18} style={{ color: '#38bdf8' }} />
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

          {/* Export CSV Button */}
          <button
            onClick={handleExportCsv}
            style={{
              background: '#1e293b',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#f1f5f9',
              borderRadius: '10px',
              padding: '9px 16px',
              fontSize: '0.88rem',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer'
            }}
          >
            <Download size={16} /> Export CSV
          </button>
        </div>
      </div>

      {/* Report Table */}
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
          <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
            Company Overview — {getMonthDisplayName(selectedMonth)}
          </h2>
          <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
            Click an employee row to view complete day-by-day logs
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ background: '#0f172a', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Employee</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600, textAlign: 'right' }}>Present</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600, textAlign: 'right' }}>Absent</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600, textAlign: 'right' }}>Leave</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600, textAlign: 'right' }}>Total Hours</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600, textAlign: 'right' }}>Overtime</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600, textAlign: 'center' }}>Details</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
                    Calculating consolidated monthly totals...
                  </td>
                </tr>
              ) : reportData.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
                    No employee attendance data found for this month.
                  </td>
                </tr>
              ) : (
                reportData.map((row) => (
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

                    {/* Present */}
                    <td style={{ padding: '16px 20px', textAlign: 'right', fontWeight: 700, color: '#34d399' }}>
                      {row.present_days}
                    </td>

                    {/* Absent */}
                    <td style={{ padding: '16px 20px', textAlign: 'right', fontWeight: 700, color: '#f87171' }}>
                      {row.absent_days}
                    </td>

                    {/* Leave */}
                    <td style={{ padding: '16px 20px', textAlign: 'right', fontWeight: 700, color: '#fbbf24' }}>
                      {row.leave_days}
                    </td>

                    {/* Total Hours */}
                    <td style={{ padding: '16px 20px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 800, color: '#38bdf8' }}>
                      {row.total_hours_formatted}
                    </td>

                    {/* Overtime */}
                    <td style={{ padding: '16px 20px', textAlign: 'right', fontFamily: 'monospace', fontWeight: 700, color: '#c084fc' }}>
                      {row.overtime_formatted}
                    </td>

                    {/* Action */}
                    <td style={{ padding: '16px 20px', textAlign: 'center' }}>
                      <button
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#38bdf8',
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          fontSize: '0.8rem',
                          fontWeight: 600
                        }}
                      >
                        <span>View</span>
                        <ExternalLink size={14} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
