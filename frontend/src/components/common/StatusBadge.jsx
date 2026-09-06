import React from 'react';

export default function StatusBadge({ status }) {
  const norm = (status || 'UNKNOWN').toUpperCase();

  const configMap = {
    PRESENT: { label: 'Present', className: 'badge-present' },
    ABSENT: { label: 'Absent', className: 'badge-absent' },
    LEAVE: { label: 'On Leave', className: 'badge-leave' },
    LATE: { label: 'Late', className: 'badge-late' },
    HALF_DAY: { label: 'Half Day', className: 'badge-late' },
    IN_PROGRESS: { label: 'In Progress', className: 'badge-in_progress' },
    COMPLETED: { label: 'Completed', className: 'badge-completed' },
    ASSIGNED: { label: 'Assigned', className: 'badge-not_started' },
    ACCEPTED: { label: 'Accepted', className: 'badge-in_progress' },
    CANCELLED: { label: 'Cancelled', className: 'badge-absent' },
    NOT_STARTED: { label: 'Not Started', className: 'badge-not_started' },
    URGENT: { label: 'Urgent', className: 'badge-absent' },
    HIGH: { label: 'High', className: 'badge-late' },
    MEDIUM: { label: 'Medium', className: 'badge-in_progress' },
    LOW: { label: 'Low', className: 'badge-not_started' },
  };

  const current = configMap[norm] || { label: status, className: 'badge-not_started' };

  return (
    <span className={`badge ${current.className}`}>
      {current.label}
    </span>
  );
}
