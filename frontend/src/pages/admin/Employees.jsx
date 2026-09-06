import React, { useState, useEffect } from 'react';
import { apiRequest } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import {
  Users,
  UserPlus,
  Search,
  Edit2,
  Key,
  Trash2,
  CheckCircle,
  XCircle,
  AlertCircle,
  AlertTriangle,
  X,
  Shield,
  Phone,
  Mail
} from 'lucide-react';

export default function AdminEmployees() {
  const { user: currentUser } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Modals
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  const [selectedEmp, setSelectedEmp] = useState(null);
  const [empToDelete, setEmpToDelete] = useState(null);

  // Form states
  const [formData, setFormData] = useState({
    full_name: '',
    employee_code: '',
    email: '',
    password: '',
    phone: '',
    department: 'Customs Clearance',
    designation: 'Field Executive',
    employment_type: 'FULL_TIME'
  });

  const [resetPassword, setResetPassword] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [msg, setMsg] = useState({ type: '', text: '' });

  const fetchEmployees = async () => {
    try {
      setLoading(true);
      const query = search ? `?search=${encodeURIComponent(search)}` : '';
      const res = await apiRequest(`/employees${query}`);
      if (res.success && res.data) {
        setEmployees(res.data.employees || []);
      }
    } catch (err) {
      console.error("Failed to fetch employees:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchEmployees();
  };

  // Add Employee
  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    setMsg({ type: '', text: '' });

    try {
      const res = await apiRequest('/employees', {
        method: 'POST',
        body: JSON.stringify(formData)
      });
      if (res.success) {
        setMsg({ type: 'success', text: res.message || "Employee created successfully." });
        setAddModalOpen(false);
        setFormData({
          full_name: '',
          employee_code: '',
          email: '',
          password: '',
          phone: '',
          department: 'Operations',
          designation: 'Field Executive',
          employment_type: 'FULL_TIME'
        });
        fetchEmployees();
      }
    } catch (err) {
      setMsg({ type: 'error', text: err.message || "Failed to create employee." });
    } finally {
      setActionLoading(false);
    }
  };

  // Edit Employee
  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!selectedEmp) return;
    setActionLoading(true);

    try {
      const res = await apiRequest(`/employees/${selectedEmp.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          full_name: selectedEmp.full_name,
          phone: selectedEmp.phone,
          email: selectedEmp.email,
          department: selectedEmp.department,
          designation: selectedEmp.designation
        })
      });
      if (res.success) {
        setMsg({ type: 'success', text: "Employee updated successfully." });
        setEditModalOpen(false);
        fetchEmployees();
      }
    } catch (err) {
      setMsg({ type: 'error', text: err.message || "Failed to update employee." });
    } finally {
      setActionLoading(false);
    }
  };

  // Reset Password
  const handleResetPasswordSubmit = async (e) => {
    e.preventDefault();
    if (!selectedEmp || !resetPassword) return;
    setActionLoading(true);

    try {
      const res = await apiRequest(`/employees/${selectedEmp.id}/reset-password`, {
        method: 'POST',
        body: JSON.stringify({ new_password: resetPassword })
      });
      if (res.success) {
        setMsg({ type: 'success', text: res.message || "Password reset successfully." });
        setPasswordModalOpen(false);
        setResetPassword('');
      }
    } catch (err) {
      setMsg({ type: 'error', text: err.message || "Failed to reset password." });
    } finally {
      setActionLoading(false);
    }
  };

  // Delete Employee Confirmation
  const handleDeleteSubmit = async () => {
    if (!empToDelete) return;
    setActionLoading(true);
    setMsg({ type: '', text: '' });

    try {
      const res = await apiRequest(`/employees/${empToDelete.id}`, {
        method: 'DELETE'
      });
      if (res.success) {
        setMsg({ type: 'success', text: res.message || `Employee '${empToDelete.full_name}' deleted successfully.` });
        setDeleteModalOpen(false);
        setEmpToDelete(null);
        fetchEmployees();
      }
    } catch (err) {
      setMsg({ type: 'error', text: err.message || "Failed to delete employee." });
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div style={{ padding: '28px', maxWidth: '1280px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc' }}>
            Employees
          </h1>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
            Manage staff profiles, active status, credentials, and records
          </p>
        </div>

        <button
          onClick={() => { setMsg({ type: '', text: '' }); setAddModalOpen(true); }}
          style={{
            background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
            color: '#ffffff',
            border: 'none',
            borderRadius: '12px',
            padding: '11px 20px',
            fontSize: '0.92rem',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer',
            boxShadow: '0 4px 14px rgba(37, 99, 235, 0.4)'
          }}
        >
          <UserPlus size={18} /> Add Employee
        </button>
      </div>

      {/* Alert Messages */}
      {msg.text && (
        <div style={{
          background: msg.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          border: `1px solid ${msg.type === 'success' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
          borderRadius: '12px',
          padding: '12px 16px',
          color: msg.type === 'success' ? '#34d399' : '#f87171',
          fontSize: '0.88rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span>{msg.text}</span>
          <button
            onClick={() => setMsg({ type: '', text: '' })}
            style={{ background: 'transparent', border: 'none', color: 'inherit', cursor: 'pointer' }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Filter Row */}
      <div style={{
        background: '#111827',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '16px',
        padding: '16px 20px',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '14px'
      }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: '240px' }}>
          <div style={{ position: 'relative', width: '100%', maxWidth: '380px' }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by name, ID, or email..."
              style={{
                width: '100%',
                padding: '9px 12px 9px 36px',
                borderRadius: '10px',
                background: '#1e293b',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#f8fafc',
                fontSize: '0.88rem'
              }}
            />
          </div>
          <button
            type="submit"
            style={{
              padding: '9px 16px',
              borderRadius: '10px',
              background: '#1e293b',
              border: '1px solid rgba(255, 255, 255, 0.15)',
              color: '#f1f5f9',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Search
          </button>
        </form>
      </div>

      {/* Employees Table */}
      <div style={{
        background: '#111827',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
        overflow: 'hidden',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)'
      }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ background: '#0f172a', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Employee ID</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Name</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Phone</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Email</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Department</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600 }}>Designation</th>
                <th style={{ padding: '14px 20px', color: '#94a3b8', fontWeight: 600, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
                    Loading employee roster...
                  </td>
                </tr>
              ) : employees.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
                    No employees matching criteria.
                  </td>
                </tr>
              ) : (
                employees.map((emp) => {
                  const isSelf = currentUser && (emp.id === currentUser.employee_id || emp.user_id === currentUser.id);

                  return (
                    <tr
                      key={emp.id}
                      style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                        transition: 'background 0.15s ease'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    >
                      {/* Employee ID */}
                      <td style={{ padding: '16px 20px', fontFamily: 'monospace', fontWeight: 700, color: '#38bdf8' }}>
                        {emp.employee_code}
                      </td>

                      {/* Name */}
                      <td style={{ padding: '16px 20px', fontWeight: 600, color: '#f8fafc' }}>
                        {emp.full_name}
                      </td>

                      {/* Phone */}
                      <td style={{ padding: '16px 20px', color: '#94a3b8', fontSize: '0.85rem' }}>
                        {emp.phone || '—'}
                      </td>

                      {/* Email */}
                      <td style={{ padding: '16px 20px', color: '#cbd5e1' }}>
                        {emp.email}
                      </td>

                      {/* Department */}
                      <td style={{ padding: '16px 20px', color: '#94a3b8' }}>
                        {emp.department}
                      </td>

                      {/* Designation */}
                      <td style={{ padding: '16px 20px', color: '#94a3b8' }}>
                        {emp.designation}
                      </td>

                      {/* Actions */}
                      <td style={{ padding: '16px 20px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                        <div style={{ display: 'inline-flex', gap: '8px', alignItems: 'center', justifyContent: 'flex-end' }}>
                          <button
                            onClick={() => { setSelectedEmp(emp); setEditModalOpen(true); }}
                            title="Edit Employee"
                            style={{
                              background: 'rgba(255, 255, 255, 0.08)',
                              border: '1px solid rgba(255, 255, 255, 0.12)',
                              color: '#cbd5e1',
                              padding: '6px 10px',
                              borderRadius: '8px',
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '5px',
                              fontSize: '0.8rem',
                              fontWeight: 500
                            }}
                          >
                            <Edit2 size={13} /> Edit
                          </button>

                          <button
                            onClick={() => { setSelectedEmp(emp); setResetPassword(''); setPasswordModalOpen(true); }}
                            title="Reset Password"
                            style={{
                              background: 'rgba(56, 189, 248, 0.1)',
                              border: '1px solid rgba(56, 189, 248, 0.25)',
                              color: '#38bdf8',
                              padding: '6px 10px',
                              borderRadius: '8px',
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '5px',
                              fontSize: '0.8rem',
                              fontWeight: 500
                            }}
                          >
                            <Key size={13} /> Password
                          </button>

                          {/* Delete Employee Button */}
                          {isSelf ? (
                            <span style={{ fontSize: '0.78rem', color: '#64748b', fontStyle: 'italic', padding: '0 6px' }}>
                              (Active Admin)
                            </span>
                          ) : (
                            <button
                              onClick={() => { setEmpToDelete(emp); setDeleteModalOpen(true); }}
                              title="Delete Employee Permanently"
                              style={{
                                background: 'rgba(239, 68, 68, 0.15)',
                                border: '1px solid rgba(239, 68, 68, 0.35)',
                                color: '#f87171',
                                padding: '6px 12px',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '5px',
                                fontSize: '0.8rem',
                                fontWeight: 700,
                                transition: 'all 0.15s ease'
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.background = 'rgba(239, 68, 68, 0.28)';
                                e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.6)';
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.background = 'rgba(239, 68, 68, 0.15)';
                                e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.35)';
                              }}
                            >
                              <Trash2 size={13} /> Delete
                            </button>
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

      {/* ADD EMPLOYEE MODAL */}
      {addModalOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(8px)',
          padding: '16px'
        }}>
          <div style={{
            background: '#111827',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '20px',
            width: '100%',
            maxWidth: '520px',
            overflow: 'hidden',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{
              padding: '18px 24px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc' }}>
                Add New Staff Member
              </h2>
              <button
                onClick={() => setAddModalOpen(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleAddSubmit} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Full Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    placeholder="e.g. Ramesh Kumar"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', background: '#1e293b', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', fontSize: '0.88rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Employee Code *</label>
                  <input
                    type="text"
                    required
                    value={formData.employee_code}
                    onChange={(e) => setFormData({ ...formData, employee_code: e.target.value })}
                    placeholder="e.g. EMP-1006"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', background: '#1e293b', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', fontSize: '0.88rem' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Email (Login Username) *</label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="staff@logistics.com"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', background: '#1e293b', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', fontSize: '0.88rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Initial Password *</label>
                  <input
                    type="password"
                    required
                    minLength={6}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="Minimum 6 chars"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', background: '#1e293b', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', fontSize: '0.88rem' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Phone Number</label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="+91 98400 XXXXX"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', background: '#1e293b', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', fontSize: '0.88rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Department</label>
                  <input
                    type="text"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    placeholder="Operations"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', background: '#1e293b', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', fontSize: '0.88rem' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Designation</label>
                <input
                  type="text"
                  value={formData.designation}
                  onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                  placeholder="Field Executive"
                  style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', background: '#1e293b', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', fontSize: '0.88rem' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
                <button
                  type="button"
                  onClick={() => setAddModalOpen(false)}
                  style={{ padding: '10px 16px', borderRadius: '8px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8', cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  style={{ padding: '10px 20px', borderRadius: '8px', background: '#2563eb', border: 'none', color: '#ffffff', fontWeight: 600, cursor: actionLoading ? 'not-allowed' : 'pointer' }}
                >
                  {actionLoading ? 'Creating...' : 'Create Employee'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT EMPLOYEE MODAL */}
      {editModalOpen && selectedEmp && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(8px)',
          padding: '16px'
        }}>
          <div style={{
            background: '#111827',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '20px',
            width: '100%',
            maxWidth: '520px',
            overflow: 'hidden',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{
              padding: '18px 24px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <h2 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc' }}>
                Edit Employee ({selectedEmp.employee_code})
              </h2>
              <button
                onClick={() => setEditModalOpen(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleEditSubmit} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Full Name</label>
                <input
                  type="text"
                  required
                  value={selectedEmp.full_name}
                  onChange={(e) => setSelectedEmp({ ...selectedEmp, full_name: e.target.value })}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', background: '#1e293b', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', fontSize: '0.88rem' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Phone</label>
                  <input
                    type="text"
                    value={selectedEmp.phone || ''}
                    onChange={(e) => setSelectedEmp({ ...selectedEmp, phone: e.target.value })}
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', background: '#1e293b', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', fontSize: '0.88rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Email</label>
                  <input
                    type="email"
                    required
                    value={selectedEmp.email}
                    onChange={(e) => setSelectedEmp({ ...selectedEmp, email: e.target.value })}
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', background: '#1e293b', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', fontSize: '0.88rem' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Department</label>
                  <input
                    type="text"
                    value={selectedEmp.department}
                    onChange={(e) => setSelectedEmp({ ...selectedEmp, department: e.target.value })}
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', background: '#1e293b', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', fontSize: '0.88rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>Designation</label>
                  <input
                    type="text"
                    value={selectedEmp.designation}
                    onChange={(e) => setSelectedEmp({ ...selectedEmp, designation: e.target.value })}
                    style={{ width: '100%', padding: '9px 12px', borderRadius: '8px', background: '#1e293b', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', fontSize: '0.88rem' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', marginTop: '12px' }}>
                <div>
                  {!(currentUser && (selectedEmp.id === currentUser.employee_id || selectedEmp.user_id === currentUser.id)) && (
                    <button
                      type="button"
                      onClick={() => {
                        const target = selectedEmp;
                        setEditModalOpen(false);
                        setEmpToDelete(target);
                        setDeleteModalOpen(true);
                      }}
                      style={{
                        padding: '9px 14px',
                        borderRadius: '8px',
                        background: 'rgba(239, 68, 68, 0.12)',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        color: '#f87171',
                        fontSize: '0.84rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(239, 68, 68, 0.22)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'rgba(239, 68, 68, 0.12)';
                      }}
                    >
                      <Trash2 size={15} /> Delete Employee
                    </button>
                  )}
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    type="button"
                    onClick={() => setEditModalOpen(false)}
                    style={{ padding: '10px 16px', borderRadius: '8px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8', cursor: 'pointer' }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={actionLoading}
                    style={{ padding: '10px 20px', borderRadius: '8px', background: '#2563eb', border: 'none', color: '#ffffff', fontWeight: 600, cursor: actionLoading ? 'not-allowed' : 'pointer' }}
                  >
                    {actionLoading ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* RESET PASSWORD MODAL */}
      {passwordModalOpen && selectedEmp && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(8px)',
          padding: '16px'
        }}>
          <div style={{
            background: '#111827',
            border: '1px solid rgba(255, 255, 255, 0.15)',
            borderRadius: '20px',
            width: '100%',
            maxWidth: '440px',
            overflow: 'hidden',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{
              padding: '18px 24px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                Reset Password for {selectedEmp.full_name}
              </h2>
              <button
                onClick={() => setPasswordModalOpen(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleResetPasswordSubmit} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', color: '#94a3b8', marginBottom: '6px' }}>New Password</label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={resetPassword}
                  onChange={(e) => setResetPassword(e.target.value)}
                  placeholder="Minimum 6 characters"
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', background: '#1e293b', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#f8fafc', fontSize: '0.9rem' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={() => setPasswordModalOpen(false)}
                  style={{ padding: '10px 16px', borderRadius: '8px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8', cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={actionLoading}
                  style={{ padding: '10px 20px', borderRadius: '8px', background: '#2563eb', border: 'none', color: '#ffffff', fontWeight: 600, cursor: actionLoading ? 'not-allowed' : 'pointer' }}
                >
                  {actionLoading ? 'Updating...' : 'Set New Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DELETE EMPLOYEE CONFIRMATION MODAL */}
      {deleteModalOpen && empToDelete && (
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
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '20px',
            width: '100%',
            maxWidth: '460px',
            overflow: 'hidden',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.8)',
            display: 'flex',
            flexDirection: 'column'
          }}>
            <div style={{
              padding: '18px 24px',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  background: 'rgba(239, 68, 68, 0.2)',
                  color: '#f87171',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <AlertTriangle size={20} />
                </div>
                <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                  Confirm Employee Deletion
                </h2>
              </div>
              <button
                onClick={() => { setDeleteModalOpen(false); setEmpToDelete(null); }}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <p style={{ margin: 0, fontSize: '0.92rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                Are you sure you want to permanently delete <strong style={{ color: '#f8fafc' }}>{empToDelete.full_name}</strong> (<span style={{ fontFamily: 'monospace', color: '#38bdf8' }}>{empToDelete.employee_code}</span>)?
              </p>

              <div style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                borderRadius: '12px',
                padding: '12px 14px',
                color: '#fca5a5',
                fontSize: '0.82rem',
                lineHeight: 1.4
              }}>
                ⚠️ <strong>Warning:</strong> This will permanently remove the employee's profile, portal login account, and all associated attendance records. This action cannot be undone.
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '6px' }}>
                <button
                  type="button"
                  onClick={() => { setDeleteModalOpen(false); setEmpToDelete(null); }}
                  disabled={actionLoading}
                  style={{
                    padding: '10px 18px',
                    borderRadius: '10px',
                    background: 'transparent',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    color: '#94a3b8',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleDeleteSubmit}
                  disabled={actionLoading}
                  style={{
                    padding: '10px 20px',
                    borderRadius: '10px',
                    background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                    border: 'none',
                    color: '#ffffff',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    cursor: actionLoading ? 'not-allowed' : 'pointer',
                    opacity: actionLoading ? 0.7 : 1,
                    boxShadow: '0 4px 14px rgba(239, 68, 68, 0.4)'
                  }}
                >
                  <Trash2 size={16} />
                  <span>{actionLoading ? 'Deleting...' : 'Permanently Delete'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
