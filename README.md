# Staff Attendance, GPS Location & Selfie Portal

A dedicated, mobile-first employee attendance and location verification portal built for logistics operations. The portal replaces task management with a focused, streamlined attendance verification workflow:

`STAFF → LOGIN → GPS + CAMERA SELFIE → START ATTENDANCE → WORK → GPS + SELFIE → END ATTENDANCE`
`ADMIN → LOGIN → SEE STAFF → TODAY'S ATTENDANCE → MONTHLY ATTENDANCE → TIME, GPS MAP & SELFIE INSPECTION`

---

## 1. Features

### Staff Experience (Mobile-First)
- **Minimal, Distraction-Free Mobile Dashboard**: Greeting, live date, real-time Indian Standard Time clock (`Asia/Kolkata`).
- **Start Attendance Flow**:
  1. Requests device GPS location (latitude, longitude, accuracy).
  2. Opens live device camera viewfinder for real-time selfie capture.
  3. Official check-in timestamp generated on the server using IST.
  4. Status automatically becomes `🟢 WORKING` with a live elapsed duration counter.
- **End Attendance Flow**:
  1. Captures checkout GPS coordinates and accuracy.
  2. Captures checkout camera selfie.
  3. Server automatically calculates `total_work_minutes` and `overtime_minutes` (hours above standard 8-hour workday).
  4. Status becomes `🔵 COMPLETED` with check-in, check-out, duration, and overtime summary.
- **My Attendance**: Personal calendar history showing total worked hours in the selected month, daily start/end times, GPS location preview, and verified selfies.
- **Profile & Security**: Employee details and password reset.

### Admin Experience (Desktop & Tablet)
- **Today's Attendance Dashboard**:
  - Top KPI cards: Total Staff, Present, Absent, Currently Working, Completed Attendance.
  - Live Staff Roster Table: Employee, Status badge, Check In, Check Out, Hours, 📍 Location Map trigger, 📷 Selfie trigger.
- **Monthly Attendance Drill-Down**:
  - Select Employee dropdown (`[ Arun Kumar ▼ ]`) and Month dropdown (`[ September 2026 ▼ ]`).
  - Summary Cards: Present Days, Absent Days, Leave Days, Total Hours, Average Hours/Day, Total Overtime.
  - Daily Calendar Table: Date, Status, In Time, Out Time, Duration, In Location (📍 View), Out Location (📍 View), Selfies (📷 In, 📷 Out).
  - Detailed Day Verification View: Click any row to inspect check-in/out exact timestamps, GPS coordinates with accuracy, Leaflet + OpenStreetMap modal, and full-resolution selfie photos.
- **Monthly Company Report**:
  - Consolidated table of all employees for any month with Present, Absent, Leave days, Total Hours, and Overtime.
  - One-click export to CSV.
  - Direct drill-down into any employee's monthly attendance.
- **Employee Management**: Add, edit, activate, deactivate employees, and reset staff passwords.
- **Settings**: Configurable standard daily work hours (default 8 hours) and timezone indicator.

---

## 2. Technology Stack

- **Frontend**: React 18, Vite, React Router v6, Leaflet (OpenStreetMap Carto Voyager), Lucide React.
- **Backend**: Python 3.14 + Flask 3.x REST API, PyJWT, bcrypt, Flask-CORS, PyMySQL.
- **Database**: MySQL Community Edition (`logistics_attendance`).
- **Timezone**: Indian Standard Time (`Asia/Kolkata` - UTC+05:30).

---

## 3. Database Schema

The database has been simplified to 3 core tables:

### `users`
- `id` (INT PRIMARY KEY AUTO_INCREMENT)
- `email` (VARCHAR(191) UNIQUE NOT NULL)
- `password_hash` (VARCHAR(255) NOT NULL)
- `role` (ENUM('ADMIN', 'STAFF') NOT NULL)
- `is_active` (BOOLEAN DEFAULT TRUE)
- `created_at`, `updated_at` (TIMESTAMP)

### `employees`
- `id` (INT PRIMARY KEY AUTO_INCREMENT)
- `user_id` (INT UNIQUE, FK -> users.id)
- `employee_code` (VARCHAR(50) UNIQUE NOT NULL)
- `full_name` (VARCHAR(150) NOT NULL)
- `phone` (VARCHAR(25))
- `email` (VARCHAR(191) NOT NULL)
- `department` (VARCHAR(100) DEFAULT 'Operations')
- `designation` (VARCHAR(100) DEFAULT 'Field Executive')
- `joining_date` (DATE NOT NULL)
- `employment_type` (ENUM('FULL_TIME', 'PART_TIME', 'CONTRACT'))
- `status` (ENUM('ACTIVE', 'INACTIVE'))
- `created_at`, `updated_at` (TIMESTAMP)

### `attendance`
- `id` (INT PRIMARY KEY AUTO_INCREMENT)
- `employee_id` (INT, FK -> employees.id)
- `attendance_date` (DATE NOT NULL)
- `check_in_time` (DATETIME)
- `check_out_time` (DATETIME)
- `check_in_latitude`, `check_in_longitude` (DECIMAL(10, 7))
- `check_in_accuracy` (DECIMAL(8, 2))
- `check_out_latitude`, `check_out_longitude` (DECIMAL(10, 7))
- `check_out_accuracy` (DECIMAL(8, 2))
- `check_in_selfie`, `check_out_selfie` (VARCHAR(255))
- `total_work_minutes` (INT DEFAULT 0)
- `overtime_minutes` (INT DEFAULT 0)
- `status` (ENUM('PRESENT', 'ABSENT', 'LEAVE', 'HALF_DAY', 'WEEK_OFF', 'HOLIDAY'))
- `remarks` (TEXT)
- `created_at`, `updated_at` (TIMESTAMP)
- Unique Constraint: `(employee_id, attendance_date)`

---

## 4. REST API Endpoints

### Authentication
- `POST /api/auth/login`: Login by email or employee code. Returns JWT and user profile.
- `GET /api/auth/me`: Get active session.
- `POST /api/auth/logout`: Invalidate session.
- `POST /api/auth/change-password`: Update authenticated user password.

### Attendance
- `POST /api/attendance/start`: Start attendance with GPS coordinates, accuracy, and live camera selfie.
- `POST /api/attendance/end`: End attendance with GPS coordinates, accuracy, and checkout selfie.
- `GET /api/attendance/today`: Retrieve today's attendance status and live elapsed time.
- `GET /api/attendance/my?month=YYYY-MM`: Retrieve authenticated staff member's monthly attendance logs.
- `GET /api/attendance/employee/:id/monthly?month=YYYY-MM`: Admin/owner view of complete monthly attendance logs.
- `GET /api/attendance/selfie/:filename`: Secure authenticated endpoint for serving attendance selfie images.

### Dashboard & Reports
- `GET /api/dashboard/today`: Admin today's KPI counts and staff roster with live working times.
- `GET /api/reports/monthly?month=YYYY-MM`: Monthly company attendance overview report (supports `&format=csv`).

### Employees
- `GET /api/employees`: List employees with search and status filters.
- `POST /api/employees`: Create new employee account.
- `GET /api/employees/:id`: Retrieve single employee profile.
- `PUT /api/employees/:id`: Update employee details.
- `PUT /api/employees/:id/toggle-status`: Toggle ACTIVE / INACTIVE status.
- `POST /api/employees/:id/reset-password`: Reset employee password.

### Health
- `GET /api/health`: Service health status.

---

## 5. Setup & Running Instructions

### Prerequisites
- Python 3.9+ (Tested on Python 3.14)
- Node.js 18+ (with npm)
- MySQL 8.0+ Community Edition

### Database Setup
1. Configure credentials in `backend/.env` (default: `root:admin` on `localhost:3306`).
2. Apply schema and seed data:
```powershell
# From backend/ directory
python -c "import pymysql; conn=pymysql.connect(host='localhost', user='root', password='admin', autocommit=True); cur=conn.cursor(); sql=open('../database/schema.sql').read(); [cur.execute(s) for s in sql.split(';') if s.strip()]; print('Schema migrated')"
python -c "import pymysql; conn=pymysql.connect(host='localhost', user='root', password='admin', database='logistics_attendance', autocommit=True); cur=conn.cursor(); sql=open('../database/seed.sql').read(); [cur.execute(s) for s in sql.split(';') if s.strip()]; print('Seed data loaded')"
```

### Start Backend
```powershell
cd backend
python run.py
# Backend runs on http://127.0.0.1:5000
```

### Start Frontend
```powershell
cd frontend
npm.cmd run dev
# Frontend runs on http://localhost:5173
```

---

## 6. Demo Credentials

| Role | Email / Employee ID | Password | Notes |
|---|---|---|---|
| **Admin** | `admin@sevenstarslogistics.com` | `admin123` | Full administrative oversight |
| **Admin** | `arunachalam@sevenstarslogistics.com` | `admin123` | Managing Director account |
| **Staff** | `arun@logistics.com` (or `EMP-1001`) | `staff123` | Senior Customs Executive (Currently Working) |
| **Staff** | `priya@logistics.com` (or `EMP-1002`) | `staff123` | CFS Specialist (Completed Attendance) |
| **Staff** | `rahul@logistics.com` (or `EMP-1003`) | `staff123` | Port Inspector (Currently Working) |
| **Staff** | `karthik@logistics.com` (or `EMP-1004`) | `staff123` | Cargo Officer (Status: Not Started / Ready to Start) |
| **Staff** | `suresh@logistics.com` (or `EMP-1005`) | `staff123` | Warehouse Supervisor (Completed Attendance) |

---

## 7. Running Automated Backend Tests

```powershell
cd backend
python test_attendance_portal.py
```
All 9 core security and flow tests verify authentication, start/end attendance, GPS coordinates, IST timestamps, duration & overtime calculations, selfie access permissions, and report generation.
