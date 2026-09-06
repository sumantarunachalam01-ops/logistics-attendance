-- =====================================================================
-- Staff Attendance, GPS Location & Selfie Portal
-- Seed Data: database/seed.sql
-- =====================================================================

USE logistics_attendance;

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE attendance;
TRUNCATE TABLE employees;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. USERS
-- Passwords:
-- Admin: admin123 -> $2b$12$X2.N3beehNcUkFjtLm3o5.0lwnrOn58DNoIKAF4CSW8P13bPNULMG
-- Staff: staff123 -> $2b$12$cfYsLZQ66YjNQmcBf8IVoebUXZpStujN1Jg7uDnxd4DoOpW2hg9JG
INSERT INTO users (id, email, password_hash, role, is_active)
VALUES
  (1, 'arunachalam@sevenstarslogistics.com', '$2b$12$X2.N3beehNcUkFjtLm3o5.0lwnrOn58DNoIKAF4CSW8P13bPNULMG', 'ADMIN', TRUE),
  (2, 'admin@sevenstarslogistics.com', '$2b$12$X2.N3beehNcUkFjtLm3o5.0lwnrOn58DNoIKAF4CSW8P13bPNULMG', 'ADMIN', TRUE),
  (3, 'arun@logistics.com', '$2b$12$cfYsLZQ66YjNQmcBf8IVoebUXZpStujN1Jg7uDnxd4DoOpW2hg9JG', 'STAFF', TRUE),
  (4, 'priya@logistics.com', '$2b$12$cfYsLZQ66YjNQmcBf8IVoebUXZpStujN1Jg7uDnxd4DoOpW2hg9JG', 'STAFF', TRUE),
  (5, 'rahul@logistics.com', '$2b$12$cfYsLZQ66YjNQmcBf8IVoebUXZpStujN1Jg7uDnxd4DoOpW2hg9JG', 'STAFF', TRUE),
  (6, 'karthik@logistics.com', '$2b$12$cfYsLZQ66YjNQmcBf8IVoebUXZpStujN1Jg7uDnxd4DoOpW2hg9JG', 'STAFF', TRUE),
  (7, 'suresh@logistics.com', '$2b$12$cfYsLZQ66YjNQmcBf8IVoebUXZpStujN1Jg7uDnxd4DoOpW2hg9JG', 'STAFF', TRUE),
  (8, 'hr@logistics.com', '$2b$12$cfYsLZQ66YjNQmcBf8IVoebUXZpStujN1Jg7uDnxd4DoOpW2hg9JG', 'STAFF', TRUE);

-- 2. EMPLOYEES
INSERT INTO employees (id, user_id, employee_code, full_name, phone, email, department, designation, joining_date, employment_type, status)
VALUES
  (1, 1, 'ADM-001', 'Arunachalam RG', '+91 98400 11223', 'arunachalam@sevenstarslogistics.com', 'Operations Management', 'Director & Operations Head', '2023-01-10', 'FULL_TIME', 'ACTIVE'),
  (2, 2, 'ADM-002', 'Logistics Admin', '+91 98400 00002', 'admin@sevenstarslogistics.com', 'Administration', 'Portal Administrator', '2023-01-15', 'FULL_TIME', 'ACTIVE'),
  (3, 3, 'EMP-1001', 'Arun Kumar', '+91 98401 33445', 'arun@logistics.com', 'Customs Clearance', 'Senior Field Executive', '2024-02-01', 'FULL_TIME', 'ACTIVE'),
  (4, 4, 'EMP-1002', 'Priya Sundaram', '+91 98404 66778', 'priya@logistics.com', 'CFS Operations', 'Documentation Specialist', '2024-06-01', 'FULL_TIME', 'ACTIVE'),
  (5, 5, 'EMP-1003', 'Rahul Verma', '+91 98402 44556', 'rahul@logistics.com', 'Port Logistics', 'Field Inspector', '2024-04-10', 'FULL_TIME', 'ACTIVE'),
  (6, 6, 'EMP-1004', 'Karthik Raja', '+91 98403 55667', 'karthik@logistics.com', 'Air Cargo', 'Cargo Officer', '2024-05-15', 'FULL_TIME', 'ACTIVE'),
  (7, 7, 'EMP-1005', 'Suresh Nair', '+91 98405 77889', 'suresh@logistics.com', 'Warehousing', 'Warehouse Supervisor', '2024-07-20', 'FULL_TIME', 'ACTIVE'),
  (8, 8, 'HR-002', 'Sneha Sharma', '+91 98400 22334', 'hr@logistics.com', 'Human Resources', 'HR Operations Specialist', '2023-03-01', 'FULL_TIME', 'ACTIVE');

-- 3. ATTENDANCE HISTORY (September 2026)
-- Arun Kumar (EMP-1001 / ID: 3)
INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, check_in_latitude, check_in_longitude, check_in_accuracy, check_out_latitude, check_out_longitude, check_out_accuracy, check_in_selfie, check_out_selfie, total_work_minutes, overtime_minutes, status, remarks)
VALUES
  (3, '2026-09-01', '2026-09-01 09:02:14', '2026-09-01 18:15:42', 13.0883100, 80.2925200, 15.00, 13.0883500, 80.2925400, 21.00, 'emp_arun_in.jpg', 'emp_arun_out.jpg', 553, 73, 'PRESENT', 'Full day customs clearing'),
  (3, '2026-09-02', '2026-09-02 08:58:20', '2026-09-02 17:52:10', 13.0883200, 80.2925100, 12.00, 13.0883300, 80.2925300, 18.00, 'emp_arun_in.jpg', 'emp_arun_out.jpg', 533, 53, 'PRESENT', 'Customs documentation complete'),
  (3, '2026-09-03', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, 'ABSENT', 'Unplanned absence'),
  (3, '2026-09-04', '2026-09-04 09:05:00', '2026-09-04 18:35:00', 13.0883000, 80.2925000, 14.00, 13.0883200, 80.2925100, 16.00, 'emp_arun_in.jpg', 'emp_arun_out.jpg', 570, 90, 'PRESENT', 'High volume clearance'),
  (3, '2026-09-05', '2026-09-05 09:10:15', '2026-09-05 18:10:20', 13.0883400, 80.2925500, 16.00, 13.0883100, 80.2925000, 19.00, 'emp_arun_in.jpg', 'emp_arun_out.jpg', 540, 60, 'PRESENT', 'Regular shift'),
  (3, '2026-09-06', '2026-09-06 09:04:12', NULL, 13.0883100, 80.2925200, 18.00, NULL, NULL, NULL, 'emp_arun_in.jpg', NULL, 0, 0, 'PRESENT', 'Checked in at Chennai Customs');

-- Priya Sundaram (EMP-1002 / ID: 4)
INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, check_in_latitude, check_in_longitude, check_in_accuracy, check_out_latitude, check_out_longitude, check_out_accuracy, check_in_selfie, check_out_selfie, total_work_minutes, overtime_minutes, status, remarks)
VALUES
  (4, '2026-09-01', '2026-09-01 08:50:00', '2026-09-01 17:55:00', 13.1670100, 80.2600200, 10.00, 13.1670300, 80.2600400, 14.00, 'emp_priya_in.jpg', 'emp_priya_out.jpg', 545, 65, 'PRESENT', 'CFS gate processing'),
  (4, '2026-09-02', '2026-09-02 08:55:00', '2026-09-02 18:00:00', 13.1670200, 80.2600300, 12.00, 13.1670100, 80.2600100, 15.00, 'emp_priya_in.jpg', 'emp_priya_out.jpg', 545, 65, 'PRESENT', 'Container verification'),
  (4, '2026-09-03', '2026-09-03 09:00:00', '2026-09-03 18:10:00', 13.1670000, 80.2600000, 11.00, 13.1670200, 80.2600300, 13.00, 'emp_priya_in.jpg', 'emp_priya_out.jpg', 550, 70, 'PRESENT', 'Manifest checks'),
  (4, '2026-09-04', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, 'LEAVE', 'Approved personal leave'),
  (4, '2026-09-05', '2026-09-05 08:52:00', '2026-09-05 18:05:00', 13.1670400, 80.2600500, 15.00, 13.1670000, 80.2600000, 18.00, 'emp_priya_in.jpg', 'emp_priya_out.jpg', 553, 73, 'PRESENT', 'CFS verification'),
  (4, '2026-09-06', '2026-09-06 08:55:00', '2026-09-06 18:10:00', 13.1670100, 80.2600200, 12.00, 13.1670300, 80.2600400, 14.00, 'emp_priya_in.jpg', 'emp_priya_out.jpg', 555, 75, 'PRESENT', 'Completed attendance at Manali CFS');

-- Rahul Verma (EMP-1003 / ID: 5)
INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, check_in_latitude, check_in_longitude, check_in_accuracy, check_out_latitude, check_out_longitude, check_out_accuracy, check_in_selfie, check_out_selfie, total_work_minutes, overtime_minutes, status, remarks)
VALUES
  (5, '2026-09-01', '2026-09-01 09:12:00', '2026-09-01 18:20:00', 13.0970200, 80.2980100, 20.00, 13.0970300, 80.2980500, 22.00, 'emp_rahul_in.jpg', 'emp_rahul_out.jpg', 548, 68, 'PRESENT', 'Harbour inspection'),
  (5, '2026-09-02', '2026-09-02 09:08:00', '2026-09-02 18:15:00', 13.0970100, 80.2980200, 18.00, 13.0970400, 80.2980600, 20.00, 'emp_rahul_in.jpg', 'emp_rahul_out.jpg', 547, 67, 'PRESENT', 'Reefer container audit'),
  (5, '2026-09-05', '2026-09-05 09:15:00', '2026-09-05 18:30:00', 13.0970500, 80.2980700, 25.00, 13.0970100, 80.2980200, 19.00, 'emp_rahul_in.jpg', 'emp_rahul_out.jpg', 555, 75, 'PRESENT', 'Port clearance gate 1'),
  (5, '2026-09-06', '2026-09-06 09:12:45', NULL, 13.0970200, 80.2980100, 22.00, NULL, NULL, NULL, 'emp_rahul_in.jpg', NULL, 0, 0, 'PRESENT', 'Working at Harbour Gate 1');

-- Karthik Raja (EMP-1004 / ID: 6)
INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, check_in_latitude, check_in_longitude, check_in_accuracy, check_out_latitude, check_out_longitude, check_out_accuracy, check_in_selfie, check_out_selfie, total_work_minutes, overtime_minutes, status, remarks)
VALUES
  (6, '2026-09-01', '2026-09-01 08:45:00', '2026-09-01 17:45:00', 12.9815000, 80.1636000, 14.00, 12.9815200, 80.1636200, 16.00, 'emp_karthik_in.jpg', 'emp_karthik_out.jpg', 540, 60, 'PRESENT', 'Airport dispatch cargo'),
  (6, '2026-09-02', '2026-09-02 08:50:00', '2026-09-02 18:00:00', 12.9815100, 80.1636100, 15.00, 12.9815300, 80.1636300, 17.00, 'emp_karthik_in.jpg', 'emp_karthik_out.jpg', 550, 70, 'PRESENT', 'Export airway bill docs'),
  (6, '2026-09-06', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, 'ABSENT', 'Not reported for attendance');

-- Suresh Nair (EMP-1005 / ID: 7)
INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, check_in_latitude, check_in_longitude, check_in_accuracy, check_out_latitude, check_out_longitude, check_out_accuracy, check_in_selfie, check_out_selfie, total_work_minutes, overtime_minutes, status, remarks)
VALUES
  (7, '2026-09-01', '2026-09-01 08:30:00', '2026-09-01 17:15:00', 12.9720300, 79.9480400, 12.00, 12.9720100, 79.9480200, 14.00, 'emp_suresh_in.jpg', 'emp_suresh_out.jpg', 525, 45, 'PRESENT', 'Warehouse inventory'),
  (7, '2026-09-02', '2026-09-02 08:40:00', '2026-09-02 17:30:00', 12.9720200, 79.9480300, 13.00, 12.9720400, 79.9480500, 15.00, 'emp_suresh_in.jpg', 'emp_suresh_out.jpg', 530, 50, 'PRESENT', 'Unloading cargo check'),
  (7, '2026-09-06', '2026-09-06 08:45:00', '2026-09-06 17:00:00', 12.9720300, 79.9480400, 15.00, 12.9720500, 79.9480600, 16.00, 'emp_suresh_in.jpg', 'emp_suresh_out.jpg', 495, 15, 'PRESENT', 'Completed warehouse shift');

-- Sneha Sharma (HR-002 / ID: 8)
INSERT INTO attendance (employee_id, attendance_date, check_in_time, check_out_time, check_in_latitude, check_in_longitude, check_in_accuracy, check_out_latitude, check_out_longitude, check_out_accuracy, check_in_selfie, check_out_selfie, total_work_minutes, overtime_minutes, status, remarks)
VALUES
  (8, '2026-09-01', '2026-09-01 09:00:00', '2026-09-01 18:00:00', 13.0100000, 80.2100000, 10.00, 13.0100200, 80.2100300, 12.00, 'emp_sneha_in.jpg', 'emp_sneha_out.jpg', 540, 60, 'PRESENT', 'Corporate HR documentation'),
  (8, '2026-09-02', '2026-09-02 08:55:00', '2026-09-02 17:50:00', 13.0100100, 80.2100200, 11.00, 13.0100300, 80.2100100, 14.00, 'emp_sneha_in.jpg', 'emp_sneha_out.jpg', 535, 55, 'PRESENT', 'Staff onboarding review'),
  (8, '2026-09-05', '2026-09-05 09:05:00', '2026-09-05 18:05:00', 13.0100000, 80.2100000, 15.00, 13.0100200, 80.2100200, 18.00, 'emp_sneha_in.jpg', 'emp_sneha_out.jpg', 540, 60, 'PRESENT', 'Monthly payroll processing'),
  (8, '2026-09-06', '2026-09-06 09:00:00', NULL, 13.0100000, 80.2100000, 12.00, NULL, NULL, NULL, 'emp_sneha_in.jpg', NULL, 0, 0, 'PRESENT', 'Staff attendance audit');

