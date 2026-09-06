-- =====================================================================
-- Staff Attendance, GPS Location & Selfie Portal
-- Database Schema: logistics_attendance
-- Compatible with: MySQL 8.0+ / Community Edition
-- =====================================================================

CREATE DATABASE IF NOT EXISTS logistics_attendance
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE logistics_attendance;

-- Drop legacy tables if they exist
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS leaves;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS shifts;
DROP TABLE IF EXISTS holidays;
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. USERS TABLE
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(191) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('ADMIN', 'STAFF') NOT NULL DEFAULT 'STAFF',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. EMPLOYEES TABLE
CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    employee_code VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(150) NOT NULL,
    phone VARCHAR(25) NULL,
    email VARCHAR(191) NOT NULL,
    department VARCHAR(100) NOT NULL DEFAULT 'Operations',
    designation VARCHAR(100) NOT NULL DEFAULT 'Field Executive',
    joining_date DATE NOT NULL,
    employment_type ENUM('FULL_TIME', 'PART_TIME', 'CONTRACT') NOT NULL DEFAULT 'FULL_TIME',
    status ENUM('ACTIVE', 'INACTIVE') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_employees_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_employees_code (employee_code),
    INDEX idx_employees_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. ATTENDANCE TABLE
CREATE TABLE attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    check_in_time DATETIME NULL,
    check_out_time DATETIME NULL,
    check_in_latitude DECIMAL(10, 7) NULL,
    check_in_longitude DECIMAL(10, 7) NULL,
    check_in_accuracy DECIMAL(8, 2) NULL,
    check_out_latitude DECIMAL(10, 7) NULL,
    check_out_longitude DECIMAL(10, 7) NULL,
    check_out_accuracy DECIMAL(8, 2) NULL,
    check_in_selfie VARCHAR(255) NULL,
    check_out_selfie VARCHAR(255) NULL,
    total_work_minutes INT NOT NULL DEFAULT 0,
    overtime_minutes INT NOT NULL DEFAULT 0,
    status ENUM('PRESENT', 'ABSENT', 'LEAVE', 'HALF_DAY', 'WEEK_OFF', 'HOLIDAY') NOT NULL DEFAULT 'PRESENT',
    remarks TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_attendance_employee FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    CONSTRAINT uq_employee_date UNIQUE (employee_id, attendance_date),
    INDEX idx_attendance_date (attendance_date),
    INDEX idx_attendance_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. SYSTEM SETTINGS TABLE
CREATE TABLE IF NOT EXISTS system_settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

