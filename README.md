# EduPredict —  Student Performance Portal

A full-stack web application which uses **Database Systems** 
for students record saving

---

## Project Overview

EduPredict is a university portal where:
- **Admin** manages students, courses, marks, and set semester
 fee 

- **Students** enroll in courses, view results, view & edit his profile, and view his semester fee

---

## Features

### Admin Portal
- Secure login system
- Add / delete students with login credentials
- Add / delete courses (with credit hours, semester, instructor)
- Add marks (assignment, midterm, final) — auto grade calculation
- Publish results for students
- Set & view Semester fee 

### Student Portal
- Secure login system
- Enroll / drop courses by semester
- View published results and CGPA
- View & edit his profile
- View his semester fee summary


---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Auth | Flask Sessions |

---

## 📁 Project Structure

```
EduPredict/
├── app.py                  # Main Flask application
├── database.py             # MySQL connection & queries
├── schema.sql              # Database tables & default admin
├── requirements.txt        # Python dependencies
└── templates/
    ├── login.html          # Login page
    ├── admin/
    │   ├── base.html       # Admin layout
    │   ├── dashboard.html  # Admin dashboard
    │   ├── students.html   # Manage students
    │   ├── courses.html    # Manage courses
    │   ├── marks.html      # Add & publish marks
    │   └── fee.html        # Fee structure
    └── student/
        ├── base.html       # Student layout
        ├── dashboard.html  # Student dashboard
        ├── profile.html    # Student profile
        ├── enroll.html     # Course enrollment
        ├── results.html    # View results & CGPA
        └── fee.html        # Fee payment
```

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL Server
- pip

### Step 1 — Clone / Download the project
```
Place all files in your project folder e.g. F:\EDUPredict\
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Setup Database
Open MySQL Workbench and run:
```sql
source path/to/schema.sql
```
Or open `schema.sql` in Workbench via **File → Open SQL Script** then press **Ctrl+Shift+Enter**

### Step 4 — Configure Database 

EduPredict uses MySQL for storing student, course, and enrollment data.

#### 1. Create your `.env` file

Copy the `.env.example` file and rename the copy to `.env`.

**Windows:**

```bash
copy .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

#### 2. Configure your MySQL credentials

Open the newly created `.env` file and update the values according to your local MySQL setup:

```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=edupredict
MYSQL_PORT=3306
```

Replace `your_mysql_password` with your actual MySQL password.

#### 3. Make sure the database exists

Create a MySQL database named:

```text
edupredict
```

Then run the provided database/schema setup if included in the project.


### Step 5 — Run the Application
```bash
python app.py
```

### Step 6 — Open in Browser
```
http://localhost:5000
```

---

## Default Login

| Role | Username | Password |
|---|---|---|
| Admin | admin | admin123 |
| Student | Created by Admin | Set by Admin |

---

## Mobile Access

### Same WiFi Network
1. Find PC IP address: `ipconfig` in CMD
2. Change in `app.py`: `app.run(host='0.0.0.0', port=5000)`
3. Open on mobile: `http://YOUR_PC_IP:5000`

### Via Ngrok (Anywhere)
1. Install Ngrok from ngrok.com
2. Run: `ngrok http 5000`
3. Use the generated `https://` link on any device


## License
This project is developed for academic purposes.
