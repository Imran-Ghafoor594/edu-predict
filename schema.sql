-- ============================================
--   EduPredict Portal — MySQL Schema
-- ============================================

CREATE DATABASE IF NOT EXISTS edupredict;
USE edupredict;

-- ── 1. USERS TABLE (Admin + Students login) ──
CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(50)  UNIQUE NOT NULL,
    password   VARCHAR(255) NOT NULL,
    role       ENUM('admin','student') NOT NULL DEFAULT 'student',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── 2. STUDENTS TABLE ──
CREATE TABLE IF NOT EXISTS students (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT UNIQUE,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(100) UNIQUE NOT NULL,
    roll_no    VARCHAR(30)  UNIQUE NOT NULL,
    semester   TINYINT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ── 3. COURSES TABLE ──
CREATE TABLE IF NOT EXISTS courses (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(20)  UNIQUE NOT NULL,
    name        VARCHAR(100) NOT NULL,
    credit_hrs  TINYINT NOT NULL DEFAULT 3,
    semester    TINYINT NOT NULL DEFAULT 1,
    instructor  VARCHAR(100),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── 4. ENROLLMENTS TABLE ──
CREATE TABLE IF NOT EXISTS enrollments (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id  INT NOT NULL,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses(id)  ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment (student_id, course_id)
);

-- ── 5. RESULTS TABLE ──
CREATE TABLE IF NOT EXISTS results (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    student_id       INT NOT NULL,
    course_id        INT NOT NULL,
    assignment_score FLOAT DEFAULT 0,
    midterm_score    FLOAT DEFAULT 0,
    final_score      FLOAT DEFAULT 0,
    grade            VARCHAR(5),
    is_published     TINYINT DEFAULT 0,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses(id)  ON DELETE CASCADE
);


-- ── 6. Student Details  ──
CREATE TABLE IF NOT EXISTS student_details (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT UNIQUE NOT NULL,
    father_name     VARCHAR(100),
    cnic            VARCHAR(15),           -- 13 digit CNIC
    phone           VARCHAR(15),
    address         TEXT,
    city            VARCHAR(50),
    date_of_birth   DATE,
    gender          ENUM('Male','Female','Other'),
    blood_group     VARCHAR(5),
    program         VARCHAR(100),          -- e.g. BS Computer Science
    admission_year  YEAR,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- ── 7. FEE STRUCTURE (Admin sets this) ──
CREATE TABLE IF NOT EXISTS fee_structure (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    semester            TINYINT NOT NULL,
    fee_per_credit_hour DECIMAL(10,2) NOT NULL,     -- e.g. 5000.00
    registration_fee    DECIMAL(10,2) DEFAULT 0,    -- fixed per semester
    exam_fee            DECIMAL(10,2) DEFAULT 0,    -- fixed per semester
    other_charges       DECIMAL(10,2) DEFAULT 0,    -- misc charges
    academic_year       VARCHAR(20),                -- e.g. 2025-2026
    due_date            DATE,                       -- last date to pay
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── 8. STUDENT FEES (Generated per student) ──
CREATE TABLE IF NOT EXISTS student_fees (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    student_id          INT NOT NULL,
    fee_structure_id    INT NOT NULL,
    semester            TINYINT NOT NULL,
    total_credit_hours  INT NOT NULL,               -- from enrolled courses
    tuition_fee         DECIMAL(10,2) NOT NULL,     -- credit hrs × fee per hr
    registration_fee    DECIMAL(10,2) DEFAULT 0,
    exam_fee            DECIMAL(10,2) DEFAULT 0,
    other_charges       DECIMAL(10,2) DEFAULT 0,
    total_amount        DECIMAL(10,2) NOT NULL,     -- sum of all
    paid_amount         DECIMAL(10,2) DEFAULT 0,
    remaining_amount    DECIMAL(10,2),              -- total - paid
    status              ENUM('Unpaid','Partial','Paid') DEFAULT 'Unpaid',
    generated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id)       REFERENCES students(id)       ON DELETE CASCADE,
    FOREIGN KEY (fee_structure_id) REFERENCES fee_structure(id)  ON DELETE CASCADE
);

-- ── 9. FEE PAYMENTS (Payment history) ──
CREATE TABLE IF NOT EXISTS fee_payments (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_fee_id  INT NOT NULL,
    student_id      INT NOT NULL,
    amount_paid     DECIMAL(10,2) NOT NULL,
    payment_date    DATE NOT NULL,
    payment_method  ENUM('Cash','Bank Transfer','Online','Cheque') DEFAULT 'Cash',
    transaction_id  VARCHAR(100),                  -- bank ref number
    remarks         TEXT,
    received_by     VARCHAR(100),                  -- admin name
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_fee_id) REFERENCES student_fees(id)  ON DELETE CASCADE,
    FOREIGN KEY (student_id)     REFERENCES students(id)       ON DELETE CASCADE
);

-- ── 10. FEE INSTALLMENTS ──
CREATE TABLE IF NOT EXISTS fee_installments (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_fee_id  INT NOT NULL,
    student_id      INT NOT NULL,
    installment_no  TINYINT NOT NULL,
    amount          DECIMAL(10,2) NOT NULL,
    due_date        DATE NOT NULL,
    status          ENUM('Unpaid','Paid') DEFAULT 'Unpaid',
    payment_date    DATE,
    payment_method  ENUM('Cash','Bank Transfer','Online','Cheque') DEFAULT 'Cash',
    transaction_id  VARCHAR(100),
    received_by     VARCHAR(100),
    created_by      VARCHAR(100) DEFAULT 'admin',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_fee_id) REFERENCES student_fees(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id)     REFERENCES students(id)     ON DELETE CASCADE
);

-- ── 11. SCHOLARSHIPS ──
CREATE TABLE IF NOT EXISTS scholarships (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    student_id      INT NOT NULL,
    label           VARCHAR(100) NOT NULL,       -- e.g. "Merit 50%"
    discount_type   ENUM('percent','fixed') NOT NULL,
    discount_value  DECIMAL(10,2) NOT NULL,      -- 50 or 5000
    applied_by      VARCHAR(100) DEFAULT 'admin',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);


-- ============================================
--   DEFAULT ADMIN ACCOUNT
INSERT INTO users (username, password, role) VALUES
('admin', 'admin123', 'admin');
