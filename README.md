# Apex Student Attendance Management System

An enterprise-grade, responsive, multi-page **Student Attendance Management System** engineered for schools, colleges, and universities. Built with a modern commercial administrative UI (Bootstrap 5, Chart.js, Font Awesome) and powered by Python Flask with a robust, thread-safe Microsoft Excel (`.xlsx`) data engine.

---

## 🌟 Executive Overview

Unlike standard student projects, this system is designed as a commercial institutional SaaS product. It operates entirely on structured Microsoft Excel workbooks using **Pandas** and **OpenPyXL**, eliminating the requirement for external SQL database servers while ensuring thread-safe concurrency, atomic write-replace safeguards, automatic timestamped backups, and CSV/Excel formula injection prevention.

---

## 🚀 Key Features

### 1. Executive Dashboard
- **Real-Time KPIs**: Total active students, today's present count, absent count, late arrivals, approved leaves, and percentage attendance rate.
- **Dynamic Date Switcher**: Inspect attendance statistics for any historical or future date with live recalculation.
- **Visual Analytics**: Interactive 7-day attendance trend line chart, doughnut breakdown, and class-by-class comparison bars powered by Chart.js.
- **Activity Feed**: Live audit stream of the latest attendance submissions recorded into `attendance.xlsx`.

### 2. Daily Attendance Marking Roster
- **Class & Period Selector**: Select Date, Class, Section, Subject, and Period (Periods 1 to 8).
- **Roster Controls**: Quick-action **"Mark All Present"** and **"Mark All Absent"** buttons with live client-side counter badges.
- **Duplicate Prevention**: Intelligently detects if attendance was already recorded for that slot. Pre-populates existing entries and prompts for confirmation before an overwrite.
- **Granular Statuses**: Supports `Present`, `Absent`, `Late`, and `Leave` with individual per-student remark notes.

### 3. Comprehensive Student Directory & 360° Profile
- **Full Student Management**: Add, edit, filter, search (by name, ID, roll number, email), and paginate student records.
- **Batch Excel Import/Export**: Upload class spreadsheets (`.xlsx`) with row-level validation; download pre-formatted blank import templates.
- **Student 360° Profile**:
  - Academic & contact information overview.
  - Cumulative attendance statistics and compliance rate.
  - **Configurable Low-Attendance Warning**: Highlights students falling below institutional thresholds (e.g., < 75%).
  - **Monthly Attendance Heatmap**: Color-coded calendar days (Green = Present, Red = Absent, Amber = Late, Blue = Leave).
  - Downloadable **Individual Attendance PDF Report** generated via ReportLab.

### 4. Advanced Attendance Reports & Analytics
- **Multi-Category Aggregations**:
  - **Student Summary**: Cumulative totals, individual attendance rate, and good-standing status.
  - **Low Attendance Report**: Instant filter of all at-risk students below threshold for academic review.
  - **Class-Wise Report**: Cohort comparison metrics with assigned class advisors.
  - **Subject-Wise Report**: Course-level attendance tracking.
- **Multi-Format Export**: One-click export of any filtered report to styled **Microsoft Excel (.xlsx)** or **PDF Document (.pdf)**.

### 5. Academic Structure & Faculty Management
- **Class & Section Manager**: Manage cohorts, streams/majors, room numbers, and track live student enrollment counts.
- **Faculty Directory**: Manage instructors, designations, departments, and class/subject assignments.

### 6. Dedicated Excel Data Center
- **Workbook Health Dashboard**: Inspect status, file size, last modified timestamp, and total row count across all 7 Excel workbooks.
- **Direct Workbook Downloads**: Download live copies of `students.xlsx`, `attendance.xlsx`, `teachers.xlsx`, etc.
- **Template Generator**: Download blank schema templates for every system table.
- **Disaster Recovery & Snapshots**: Trigger on-demand backups or restore any workbook from a previous snapshot with automated rollback protection.

### 7. User & Role Management (RBAC)
- Three access levels:
  - **Admin**: Unrestricted control across all settings, user accounts, and Excel Data Center.
  - **Teacher**: Mark roster attendance, manage assigned classes, view reports, and edit student profiles.
  - **Attendance Staff**: Daily attendance capture and record searching.
- Secure session cookies, CSRF protection, and Werkzeug-salted password hashing.

### 8. System & Formula Configuration
- Configure institution name and academic year.
- Customize low-attendance alert percentage (e.g., `75%`).
- **Configurable Formula Weighting**: Specify credit for late arrivals (e.g., `0.5` half credit vs `0.0` absent).
- **Approved Leave Policy**: Configure whether excused medical leaves count against or are exempted from the attendance session denominator.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.10+ / Flask 3.x | Lightweight, modular blueprint architecture |
| **Data Storage Engine** | Microsoft Excel (`.xlsx`) | Zero-database architecture powered by OpenPyXL & Pandas |
| **Concurrency & Safety** | Threading RLock & Atomic Replace | Prevents workbook corruption and race conditions |
| **PDF Generation** | ReportLab 5.x | High-resolution institutional attendance transcripts |
| **UI Framework** | Bootstrap 5.3 & Custom CSS | Clean, commercial administrative design system |
| **Charts & Visuals** | Chart.js 4.4 | Smooth canvas-rendered analytics and trends |
| **Iconography** | Font Awesome 6 Pro | Consistent vector icons throughout all navigation |
| **Testing** | Pytest 9.x | 20+ automated unit and integration test suites |
| **Production WSGI** | Waitress 3.x | Multi-threaded production WSGI server for Windows/Linux |

---

## 📂 Project Architecture

```
student-attendance-system/
│
├── app.py                     # Flask application factory and lifecycle entrypoint
├── config.py                  # Environment configuration, file paths, and security limits
├── wsgi.py                    # Multi-threaded Waitress WSGI production server
├── manage.py                  # CLI utility for initialization, backups, and user management
├── requirements.txt           # Python package dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules for virtual environments and temporary files
├── README.md                  # Comprehensive documentation
│
├── data/                      # Live Production Excel Workbooks
│   ├── students.xlsx          # Enrolled student directory
│   ├── attendance.xlsx        # Daily session attendance records
│   ├── teachers.xlsx          # Faculty and instructor details
│   ├── classes.xlsx           # Classes, sections, streams, and room assignments
│   ├── users.xlsx             # User credentials, roles, and password hashes
│   ├── holidays.xlsx          # Academic calendar holidays and non-instructional days
│   └── settings.xlsx          # Institutional preferences, weights, and thresholds
│
├── backups/                   # Timestamped Excel snapshots before writes and restorations
│
├── services/                  # Business Logic & Data Access Layer
│   ├── excel_service.py       # Thread-safe read/writes, atomic replaces, formula sanitization
│   ├── auth_service.py        # Authentication, session helpers, password hashing
│   ├── student_service.py     # Student CRUD, Excel imports/exports, profile metrics
│   ├── attendance_service.py  # Roster marking, duplicate prevention, dashboard metrics
│   ├── report_service.py      # Statistical aggregations, Excel and ReportLab PDF generators
│   ├── class_service.py       # Cohort and section management
│   ├── teacher_service.py     # Faculty assignments
│   ├── backup_service.py      # Automated snapshots and restore verification
│   └── settings_service.py    # System preferences and calculation rules
│
├── routes/                    # Modular Flask Blueprints (Controllers)
│   ├── auth.py                # Login, logout, profile update
│   ├── dashboard.py           # Dashboard analytics and JSON stats endpoint
│   ├── students.py            # Student directory, import, export, CRUD
│   ├── student_profile.py     # Student 360 profile and individual PDF report
│   ├── attendance.py          # Roster attendance marking, log records, record editing
│   ├── reports.py             # Multi-tab reports, Excel export, PDF export
│   ├── classes.py             # Class & section administration
│   ├── teachers.py            # Faculty administration
│   ├── excel_manager.py       # Excel Data Center console
│   ├── users.py               # User and role administration
│   └── settings.py            # System configuration settings
│
├── templates/                 # Jinja2 HTML5 Templates
│   ├── base.html              # Shared layout: sidebar, navbar, toasts, modal containers
│   ├── login.html             # Login card with quick demo credential buttons
│   ├── profile.html           # User profile and password reset
│   ├── dashboard.html         # Rich metrics, Chart.js graphs, activity feed
│   ├── students/
│   │   ├── index.html         # Student data table, filters, import modal
│   │   ├── form.html          # Add / edit student enrollment form
│   │   └── profile.html       # Student 360 profile with attendance calendar heatmap
│   ├── attendance/
│   │   ├── mark.html          # Class roster marking with "Mark All Present"
│   │   └── records.html       # Searchable attendance log with filters
│   ├── reports/
│   │   └── index.html         # Interactive report generator
│   ├── classes/
│   │   └── index.html         # Classes and sections manager
│   ├── teachers/
│   │   └── index.html         # Faculty directory manager
│   ├── excel_center/
│   │   └── index.html         # Excel Data Center console and disaster recovery
│   ├── users/
│   │   └── index.html         # User & role administration
│   ├── settings/
│   │   └── index.html         # System configuration settings
│   └── errors/
│       ├── 403.html           # Forbidden error page
│       ├── 404.html           # Not found error page
│       └── 500.html           # Internal server error page
│
├── static/
│   ├── css/
│   │   └── style.css          # Modern commercial UI stylesheet
│   └── js/
│       ├── main.js            # Sidebar toggle, tooltips, auto-dismiss alerts
│       ├── dashboard.js       # Chart.js initialization & live date triggers
│       └── attendance.js      # Live roster counter & quick status toggles
│
└── tests/                     # Automated Pytest Suite
    ├── conftest.py            # Temporary isolated Excel data fixture
    ├── test_auth.py           # Login, logout, hashing, authorization tests
    ├── test_students.py       # Student CRUD, validation, import/export tests
    ├── test_attendance.py     # Attendance marking, duplicate prevention, calculations
    └── test_excel.py          # Atomic writes, formula sanitization, concurrency locking
```

---

## 📊 Excel Workbook Schemas

All 7 workbooks are automatically generated upon first boot inside `data/` if missing:

| Workbook | Primary Key | Key Columns |
| :--- | :--- | :--- |
| `students.xlsx` | `Student_ID` | `Student_ID, Roll_No, Full_Name, Email, Phone, Class, Section, Course, Admission_Date, Status` |
| `attendance.xlsx` | `Attendance_ID` | `Attendance_ID, Student_ID, Student_Name, Date, Class, Section, Subject, Period, Status, Marked_By, Remarks, Timestamp` |
| `teachers.xlsx` | `Teacher_ID` | `Teacher_ID, Full_Name, Email, Phone, Department, Designation, Assigned_Classes, Assigned_Subjects, Status` |
| `classes.xlsx` | `Class_ID` | `Class_ID, Class_Name, Section, Stream_or_Course, Room_No, Class_Teacher, Status` |
| `users.xlsx` | `User_ID` | `User_ID, Username, Password_Hash, Full_Name, Email, Role, Status, Created_At, Last_Login` |
| `holidays.xlsx` | `Holiday_ID` | `Holiday_ID, Holiday_Name, Start_Date, End_Date, Type, Description` |
| `settings.xlsx` | `Key` | `Key, Value, Category, Description, Updated_At` |

---

## 🧮 Attendance Calculation Rules

The system provides consistent, transparent attendance metrics computed via:

$$\text{Attendance Rate (\%)} = \frac{\text{Present Sessions} + (\text{Late Sessions} \times \text{Late Weight})}{\text{Total Applicable Sessions}} \times 100$$

### Configuration Options:
1. **Late Weight**: Configurable under **Settings** (`0.5` = half-credit, `1.0` = full present, `0.0` = counted as absent).
2. **Approved Leave Policy**:
   - If `leave_counted_in_total = "no"` (Standard Academic Rule):
     $$\text{Total Applicable Sessions} = \text{Total Marked Sessions} - \text{Approved Leaves}$$
   - If `leave_counted_in_total = "yes"`:
     $$\text{Total Applicable Sessions} = \text{Total Marked Sessions}$$
3. **Low-Attendance Threshold**: Default is set to **75.0%**. Any student below this triggers warning badges on their profile, class lists, and the Low Attendance report.

---

## 🔐 Excel Safety & Security Architecture

1. **Thread-Safe Synchronization**: All read, write, and batch append operations pass through an internal `threading.RLock()` object and `ExcelService.transactional_update()` to guarantee synchronization across concurrent HTTP requests.
2. **Atomic Write-Replace (Crash Resistance)**:
   - When updating a workbook, the application writes to a temporary file (`temp_xxxx.tmp.xlsx`) first.
   - Once successfully flushed and closed by OpenPyXL, `os.replace()` is executed atomically to overwrite the destination workbook.
   - If a sudden power outage or OS process termination occurs during serialization, the existing live workbook remains completely intact.
3. **Automatic Timestamped Backups**: Every write or restore operation automatically preserves a snapshot in `backups/<workbook>_<timestamp>.xlsx`.
4. **Formula Injection Sanitization**: Any user-submitted input starting with `=`, `+`, `-`, `@`, `\t`, or `\r` is escaped with a leading apostrophe (`'`) prior to saving into Excel.
5. **Secure Credential Storage**: Passwords are never stored in plaintext; they are hashed using PBKDF2 with SHA-256 via Werkzeug.

---

## 💻 Installation & Setup Instructions (Windows)

### Prerequisites
- Python 3.10+ (Python 3.14 compatible)
- PowerShell or Command Prompt

### Step 1: Clone or Navigate to Project
```powershell
cd "c:\Users\Nitesh Prajapati\Desktop\Student Attendance Management System"
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

*(If script execution is disabled in PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Verify and Initialize Excel Workbooks
```powershell
python manage.py init
python manage.py check
```

---

## 🔑 Default Login Accounts

The system is pre-seeded with ready-to-use institutional accounts:

| Role | Username | Password | Access Privileges |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin` | `Admin@123` | Full access to all modules, settings, user roles, and Excel Data Center |
| **Faculty / Teacher** | `teacher` | `Teacher@123` | Mark attendance, manage students, view reports and class rosters |
| **Attendance Staff** | `staff` | `Staff@123` | Daily roster attendance marking and record lookups |

*(Tip: On the login screen, click any of the "Quick Demo Accounts" pill buttons to auto-fill credentials instantly!)*

---

## 🏃 Running the Application

### Option A: Development Server (with Auto-Reload)
```powershell
python app.py
```
Open your browser and navigate to: **`http://localhost:5000`**

### Option B: Production WSGI Server (Waitress)
```powershell
python wsgi.py
```
Waitress launches a multi-threaded, robust WSGI production server listening on **`http://0.0.0.0:5000`**.

---

## 🧪 Running Automated Tests

Run the complete test suite covering authentication, student operations, duplicate prevention, Excel locking, atomic writes, and PDF generation:

```powershell
python -m pytest -v
```

All 20 test cases run against isolated temporary Excel files (`tmp_path`), guaranteeing that your live production workbooks in `data/` are never modified during test execution.

---

## 🌐 Production & Cloud Deployment Guide

When deploying this Excel-backed attendance system to cloud environments (e.g., AWS EC2, Azure VMs, DigitalOcean, or Docker containers):

1. **Persistent Storage Requirement**:
   - Because all application data resides in `data/*.xlsx`, you **must** mount a persistent volume (e.g., AWS EBS volume, Azure Managed Disk, or Docker persistent volume bind-mount).
   - Ephemeral container filesystems (such as default Heroku dynos) will erase Excel workbooks on restart if persistent storage is not attached.
2. **Reverse Proxy Configuration (Nginx / IIS)**:
   - Place Nginx or IIS in front of Waitress to handle HTTPS/TLS termination, static file caching, and rate limiting.
3. **Backup Retention**:
   - Regularly sync the `backups/` directory to an off-site cloud object storage bucket (e.g., AWS S3, Cloudflare R2, Google Cloud Storage).

---

## ⚖️ Excel Storage Considerations & Scalability Limits

| Parameter | Excel Storage Capacity | Recommendation |
| :--- | :--- | :--- |
| **Optimal Institution Size** | 100 to 5,000 enrolled students | Ideal for single campus schools, polytechnics, colleges |
| **Concurrent Write Load** | 10 to 50 concurrent teachers marking attendance | Internal `RLock` serializes writes smoothly with sub-second execution |
| **Row Limits per Sheet** | 1,048,576 rows per Excel sheet | At 1,000 attendance records/day, one workbook holds over 3 years of daily logs |
| **When to Migrate to SQL?** | Multi-campus universities with 20,000+ students and 500+ simultaneous real-time writes | Easily migrate the modular `services/` layer to SQLAlchemy or PostgreSQL |

---

## 📄 License & Credits

Developed with precision and enterprise standards by the Senior Engineering Pair.
Designed with Bootstrap 5, Font Awesome, Chart.js, Flask, and OpenPyXL.
