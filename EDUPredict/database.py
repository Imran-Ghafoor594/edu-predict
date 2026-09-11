# ============================================
#   EduPredict Portal — Database Layer
# ============================================

import pymysql
import pymysql.cursors
from pymysql import Error
import os


DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'cursorclass': pymysql.cursors.DictCursor
}


def get_connection():
    try:
        return pymysql.connect(**DB_CONFIG)
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None

def execute_query(query, params=None, fetch=False):
    conn = get_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        if fetch:
            return cursor.fetchall()
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None
    finally:
        cursor.close()
        conn.close()

# ── AUTH ──
def get_user(username, password):
    rows = execute_query(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, password), fetch=True
    )
    return rows[0] if rows else None

def get_student_by_user_id(user_id):
    rows = execute_query(
        "SELECT * FROM students WHERE user_id=%s", (user_id,), fetch=True
    )
    return rows[0] if rows else None

# ── ADMIN: STUDENTS ──
def get_all_students():
    return execute_query(
        "SELECT s.*, u.username FROM students s LEFT JOIN users u ON s.user_id=u.id ORDER BY s.name",
        fetch=True
    ) or []

def add_student(name, email, roll_no, semester, username, password):
    # Create user first
    user_id = execute_query(
        "INSERT INTO users (username, password, role) VALUES (%s,%s,'student')",
        (username, password)
    )
    if not user_id: return None
    return execute_query(
        "INSERT INTO students (user_id, name, email, roll_no, semester) VALUES (%s,%s,%s,%s,%s)",
        (user_id, name, email, roll_no, semester)
    )

def delete_student(student_id):
    # Get user_id first
    rows = execute_query("SELECT user_id FROM students WHERE id=%s", (student_id,), fetch=True)
    if rows and rows[0]['user_id']:
        execute_query("DELETE FROM users WHERE id=%s", (rows[0]['user_id'],))
    return execute_query("DELETE FROM students WHERE id=%s", (student_id,))

# ── ADMIN: COURSES ──
def get_all_courses():
    return execute_query("SELECT * FROM courses ORDER BY semester, code", fetch=True) or []

def get_courses_by_semester(semester):
    return execute_query(
        "SELECT * FROM courses WHERE semester=%s ORDER BY code",
        (semester,), fetch=True
    ) or []

def add_course(code, name, credit_hrs, semester, instructor):
    return execute_query(
        "INSERT INTO courses (code,name,credit_hrs,semester,instructor) VALUES (%s,%s,%s,%s,%s)",
        (code, name, credit_hrs, semester, instructor)
    )

def delete_course(course_id):
    return execute_query("DELETE FROM courses WHERE id=%s", (course_id,))

# ── ADMIN: MARKS ──
def get_all_results():
    return execute_query(
        """SELECT r.*, s.name as student_name, s.roll_no,
                  c.name as course_name, c.code
           FROM results r
           JOIN students s ON r.student_id=s.id
           JOIN courses  c ON r.course_id=c.id
           ORDER BY s.name""",
        fetch=True
    ) or []

def add_result(student_id, course_id, assignment, midterm, final_score):
    avg = assignment*0.2 + midterm*0.3 + final_score*0.5
    if   avg >= 90: grade='A+'
    elif avg >= 85: grade='A'
    elif avg >= 80: grade='A-'
    elif avg >= 75: grade='B+'
    elif avg >= 70: grade='B'
    elif avg >= 65: grade='B-'
    elif avg >= 60: grade='C+'
    elif avg >= 55: grade='C'
    elif avg >= 50: grade='D'
    else:           grade='F'
    return execute_query(
        """INSERT INTO results (student_id,course_id,assignment_score,midterm_score,final_score,grade)
           VALUES (%s,%s,%s,%s,%s,%s)
           ON DUPLICATE KEY UPDATE
           assignment_score=%s, midterm_score=%s, final_score=%s, grade=%s""",
        (student_id, course_id, assignment, midterm, final_score, grade,
         assignment, midterm, final_score, grade)
    )

def publish_result(result_id):
    return execute_query("UPDATE results SET is_published=1 WHERE id=%s", (result_id,))

def publish_all_results():
    return execute_query("UPDATE results SET is_published=1")

# ── ADMIN: DASHBOARD STATS ──
def get_dashboard_stats():
    try:
        r1 = execute_query("SELECT COUNT(*) as c FROM students", fetch=True)
        r2 = execute_query("SELECT COUNT(*) as c FROM courses", fetch=True)
        r3 = execute_query("SELECT COUNT(*) as c FROM results WHERE is_published=1", fetch=True)
        r4 = execute_query("SELECT COUNT(*) as c FROM students s JOIN results r ON s.id=r.student_id WHERE r.grade='F'", fetch=True)
        return {
            'total_students': r1[0]['c'] if r1 else 0,
            'total_courses':  r2[0]['c'] if r2 else 0,
            'published_results': r3[0]['c'] if r3 else 0,
            'failed_students':   r4[0]['c'] if r4 else 0,
        }
    except:
        return {'total_students':0,'total_courses':0,'published_results':0,'failed_students':0}

# ── STUDENT: ENROLLMENT ──
def get_student_enrollments(student_id):
    return execute_query(
        """SELECT c.*, e.id as enrollment_id, e.enrolled_at
           FROM enrollments e
           JOIN courses c ON e.course_id=c.id
           WHERE e.student_id=%s ORDER BY c.code""",
        (student_id,), fetch=True
    ) or []

def get_available_courses(student_id, semester):
    return execute_query(
        """SELECT * FROM courses
           WHERE semester=%s
           AND id NOT IN (
               SELECT course_id FROM enrollments WHERE student_id=%s
           ) ORDER BY code""",
        (semester, student_id), fetch=True
    ) or []

def enroll_student(student_id, course_id):
    return execute_query(
        "INSERT IGNORE INTO enrollments (student_id, course_id) VALUES (%s,%s)",
        (student_id, course_id)
    )

def unenroll_student(enrollment_id):
    return execute_query("DELETE FROM enrollments WHERE id=%s", (enrollment_id,))

# ── STUDENT: RESULTS ──
def get_student_results(student_id):
    return execute_query(
        """SELECT r.*, c.name as course_name, c.code, c.credit_hrs
           FROM results r
           JOIN courses c ON r.course_id=c.id
           WHERE r.student_id=%s AND r.is_published=1
           ORDER BY c.code""",
        (student_id,), fetch=True
    ) or []

def get_student_cgpa(student_id):
    results = get_student_results(student_id)
    if not results: return 0.0
    grade_points = {'A+':4.0,'A':4.0,'A-':3.7,'B+':3.3,'B':3.0,'B-':2.7,
                    'C+':2.3,'C':2.0,'D':1.0,'F':0.0}
    total_points = sum(grade_points.get(r['grade'],0) * r['credit_hrs'] for r in results)
    total_hrs    = sum(r['credit_hrs'] for r in results)
    return round(total_points/total_hrs, 2) if total_hrs else 0.0

# ── STUDENT PERSONAL DETAILS ──

def get_student_details(student_id):
    rows = execute_query(
        "SELECT * FROM student_details WHERE student_id = %s",
        (student_id,), fetch=True
    )
    return rows[0] if rows else None

def add_student_details(student_id, father_name, cnic, phone,
                        address, city, dob, gender, blood_group,
                        program, admission_year):
    return execute_query(
        """INSERT INTO student_details
           (student_id, father_name, cnic, phone, address, city,
            date_of_birth, gender, blood_group, program, admission_year)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           ON DUPLICATE KEY UPDATE
           father_name=%s, cnic=%s, phone=%s, address=%s, city=%s,
           date_of_birth=%s, gender=%s, blood_group=%s, program=%s,
           admission_year=%s""",
        (student_id, father_name, cnic, phone, address, city,
         dob, gender, blood_group, program, admission_year,
         father_name, cnic, phone, address, city,
         dob, gender, blood_group, program, admission_year)
    )


# ── FEE STRUCTURE (Admin) ──

def get_all_fee_structures():
    return execute_query(
        "SELECT * FROM fee_structure ORDER BY semester",
        fetch=True
    ) or []

def get_fee_structure_by_semester(semester):
    rows = execute_query(
        "SELECT * FROM fee_structure WHERE semester = %s",
        (semester,), fetch=True
    )
    return rows[0] if rows else None

def add_fee_structure(semester, fee_per_credit, reg_fee,
                      exam_fee, other_charges, academic_year, due_date):
    return execute_query(
        """INSERT INTO fee_structure
           (semester, fee_per_credit_hour, registration_fee,
            exam_fee, other_charges, academic_year, due_date)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (semester, fee_per_credit, reg_fee,
         exam_fee, other_charges, academic_year, due_date)
    )


# ── STUDENT FEES ──

def generate_student_fee(student_id, semester):
    """
    Auto-calculate fee based on enrolled courses
    and fee structure for that semester
    """
    # Get fee structure
    fs = get_fee_structure_by_semester(semester)
    if not fs:
        return None

    # Get enrolled courses credit hours
    rows = execute_query(
        """SELECT SUM(c.credit_hrs) as total_hrs
           FROM enrollments e
           JOIN courses c ON e.course_id = c.id
           WHERE e.student_id = %s AND c.semester = %s""",
        (student_id, semester), fetch=True
    )
    total_hrs = rows[0]['total_hrs'] if rows and rows[0]['total_hrs'] else 0

    tuition    = float(total_hrs) * float(fs['fee_per_credit_hour'])
    reg_fee    = float(fs['registration_fee'])
    exam_fee   = float(fs['exam_fee'])
    other      = float(fs['other_charges'])
    total      = tuition + reg_fee + exam_fee + other

    return execute_query(
        """INSERT INTO student_fees
           (student_id, fee_structure_id, semester, total_credit_hours,
            tuition_fee, registration_fee, exam_fee, other_charges,
            total_amount, remaining_amount)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (student_id, fs['id'], semester, total_hrs,
         tuition, reg_fee, exam_fee, other, total, total)
    )

def get_all_student_fees():
    return execute_query(
        """SELECT sf.*, s.name as student_name, s.roll_no
           FROM student_fees sf
           JOIN students s ON sf.student_id = s.id
           ORDER BY sf.generated_at DESC""",
        fetch=True
    ) or []

def get_student_fee(student_id):
    return execute_query(
        """SELECT sf.*, fs.due_date, fs.academic_year
           FROM student_fees sf
           JOIN fee_structure fs ON sf.fee_structure_id = fs.id
           WHERE sf.student_id = %s
           ORDER BY sf.semester DESC""",
        (student_id,), fetch=True
    ) or []


# ── FEE PAYMENTS ──

def add_fee_payment(student_fee_id, student_id, amount,
                    payment_date, method, transaction_id, remarks, received_by):
    # Insert payment
    result = execute_query(
        """INSERT INTO fee_payments
           (student_fee_id, student_id, amount_paid, payment_date,
            payment_method, transaction_id, remarks, received_by)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        (student_fee_id, student_id, amount, payment_date,
         method, transaction_id, remarks, received_by)
    )

    if result:
        # Update paid_amount, remaining, and status
        execute_query(
            """UPDATE student_fees
               SET paid_amount    = paid_amount + %s,
                   remaining_amount = total_amount - (paid_amount + %s),
                   status = CASE
                     WHEN (paid_amount + %s) >= total_amount THEN 'Paid'
                     WHEN (paid_amount + %s) > 0             THEN 'Partial'
                     ELSE 'Unpaid'
                   END
               WHERE id = %s""",
            (amount, amount, amount, amount, student_fee_id)
        )
    return result

def get_payment_history(student_id):
    return execute_query(
        """SELECT fp.*, sf.semester, sf.total_amount
           FROM fee_payments fp
           JOIN student_fees sf ON fp.student_fee_id = sf.id
           WHERE fp.student_id = %s
           ORDER BY fp.payment_date DESC""",
        (student_id,), fetch=True
    ) or []

def get_all_payments():
    return execute_query(
        """SELECT fp.*, s.name as student_name, s.roll_no, sf.semester
           FROM fee_payments fp
           JOIN students s  ON fp.student_id = s.id
           JOIN student_fees sf ON fp.student_fee_id = sf.id
           ORDER BY fp.payment_date DESC""",
        fetch=True
    ) or []


# ── INSTALLMENTS ──

def create_installments(student_fee_id, num_installments, due_dates, created_by='admin'):
    """
    Create installment plan for a student fee.
    Splits total_amount equally into num_installments.
    due_dates: list of date strings (len == num_installments)
    """
    conn = get_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        # Get fee info
        cursor.execute("SELECT * FROM student_fees WHERE id=%s", (student_fee_id,))
        fee = cursor.fetchone()
        if not fee: return None

        total = float(fee['total_amount'])
        per_inst = round(total / num_installments, 2)
        # Last installment covers rounding
        amounts = [per_inst] * num_installments
        amounts[-1] = round(total - per_inst * (num_installments - 1), 2)

        # Delete old installments for this fee
        cursor.execute("DELETE FROM fee_installments WHERE student_fee_id=%s", (student_fee_id,))

        for i, (amt, due) in enumerate(zip(amounts, due_dates), start=1):
            cursor.execute(
                """INSERT INTO fee_installments
                   (student_fee_id, student_id, installment_no, amount, due_date, created_by)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (student_fee_id, fee['student_id'], i, amt, due, created_by)
            )
        conn.commit()
        return True
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_installments(student_fee_id):
    return execute_query(
        "SELECT * FROM fee_installments WHERE student_fee_id=%s ORDER BY installment_no",
        (student_fee_id,), fetch=True
    ) or []

def get_student_installments(student_id):
    return execute_query(
        """SELECT fi.*, sf.semester, sf.total_amount
           FROM fee_installments fi
           JOIN student_fees sf ON fi.student_fee_id = sf.id
           WHERE fi.student_id=%s ORDER BY sf.semester, fi.installment_no""",
        (student_id,), fetch=True
    ) or []

def pay_installment(installment_id, payment_date, method, transaction_id='', received_by=''):
    """Mark installment as paid and update student_fees paid/remaining."""
    conn = get_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fee_installments WHERE id=%s", (installment_id,))
        inst = cursor.fetchone()
        if not inst or inst['status'] == 'Paid': return None

        # Mark installment paid
        cursor.execute(
            """UPDATE fee_installments SET status='Paid', payment_date=%s,
               payment_method=%s, transaction_id=%s, received_by=%s WHERE id=%s""",
            (payment_date, method, transaction_id, received_by, installment_id)
        )
        # Update student_fees
        amt = float(inst['amount'])
        cursor.execute(
            """UPDATE student_fees
               SET paid_amount = paid_amount + %s,
                   remaining_amount = remaining_amount - %s,
                   status = CASE
                     WHEN (paid_amount + %s) >= total_amount THEN 'Paid'
                     WHEN (paid_amount + %s) > 0             THEN 'Partial'
                     ELSE 'Unpaid'
                   END
               WHERE id=%s""",
            (amt, amt, amt, amt, inst['student_fee_id'])
        )
        conn.commit()
        return True
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_all_installments():
    return execute_query(
        """SELECT fi.*, s.name as student_name, s.roll_no, sf.semester
           FROM fee_installments fi
           JOIN student_fees sf ON fi.student_fee_id = sf.id
           JOIN students s ON fi.student_id = s.id
           ORDER BY fi.due_date""",
        fetch=True
    ) or []


# ── SCHOLARSHIP ──

def add_scholarship(student_id, label, discount_type, discount_value, applied_by='admin'):
    """
    discount_type: 'percent' or 'fixed'
    discount_value: e.g. 50 (for 50%) or 5000 (for Rs.5000)
    Apply discount to ALL unpaid/partial student_fees for this student.
    """
    conn = get_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO scholarships (student_id, label, discount_type, discount_value, applied_by)
               VALUES (%s,%s,%s,%s,%s)""",
            (student_id, label, discount_type, discount_value, applied_by)
        )
        schol_id = cursor.lastrowid

        # Apply to student_fees that are not fully paid
        cursor.execute(
            "SELECT * FROM student_fees WHERE student_id=%s AND status != 'Paid'",
            (student_id,)
        )
        fees = cursor.fetchall()
        for fee in fees:
            total = float(fee['total_amount'])
            paid  = float(fee['paid_amount'])
            if discount_type == 'percent':
                discount = round(total * float(discount_value) / 100, 2)
            else:
                discount = float(discount_value)
            new_total     = max(0, total - discount)
            new_remaining = max(0, new_total - paid)
            new_status = 'Paid' if new_remaining <= 0 else ('Partial' if paid > 0 else 'Unpaid')
            cursor.execute(
                """UPDATE student_fees SET total_amount=%s, remaining_amount=%s,
                   status=%s, scholarship_id=%s WHERE id=%s""",
                (new_total, new_remaining, new_status, schol_id, fee['id'])
            )
        conn.commit()
        return schol_id
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_all_scholarships():
    return execute_query(
        """SELECT sc.*, s.name as student_name, s.roll_no
           FROM scholarships sc
           JOIN students s ON sc.student_id = s.id
           ORDER BY sc.created_at DESC""",
        fetch=True
    ) or []

def get_student_scholarship(student_id):
    return execute_query(
        "SELECT * FROM scholarships WHERE student_id=%s ORDER BY created_at DESC",
        (student_id,), fetch=True
    ) or []