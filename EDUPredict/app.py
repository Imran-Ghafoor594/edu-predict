# ============================================
#   EduPredict Portal — Main App
# ============================================

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from database import *
from database import (
    get_student_details, add_student_details,
    get_all_fee_structures, add_fee_structure,
    get_all_student_fees, get_student_fee,
    generate_student_fee,
    add_fee_payment, get_payment_history, get_all_payments,
    create_installments, get_installments, get_student_installments,
    pay_installment, get_all_installments,
    add_scholarship, get_all_scholarships, get_student_scholarship
)


app = Flask(__name__)
app.secret_key = 'edupredict-secret-2024'

# ── Auth Helper ──
def is_admin():
    return session.get('role') == 'admin'

def is_student():
    return session.get('role') == 'student'

def login_required(role=None):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if role and session.get('role') != role:
        return redirect(url_for('login'))
    return None

# ============================================
#   AUTH ROUTES
# ============================================

@app.route('/', methods=['GET','POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard') if is_admin() else url_for('student_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        user = get_user(username, password)

        if user:
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['role']     = user['role']

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                student = get_student_by_user_id(user['id'])
                if student:
                    session['student_id'] = student['id']
                    session['name']       = student['name']
                    session['semester']   = student['semester']
                return redirect(url_for('student_dashboard'))
        else:
            flash('Galat username ya password!', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ============================================
#   ADMIN ROUTES
# ============================================

@app.route('/admin')
def admin_dashboard():
    if r := login_required('admin'): return r
    stats = get_dashboard_stats()
    return render_template('admin/dashboard.html', stats=stats)

# ── Students ──
@app.route('/admin/students')
def admin_students():
    if r := login_required('admin'): return r
    return render_template('admin/students.html', students=get_all_students())

@app.route('/admin/students/add', methods=['POST'])
def admin_add_student():
    if r := login_required('admin'): return r
    result = add_student(
        name     = request.form.get('name','').strip(),
        email    = request.form.get('email','').strip(),
        roll_no  = request.form.get('roll_no','').strip(),
        semester = int(request.form.get('semester',1)),
        username = request.form.get('username','').strip(),
        password = request.form.get('password','').strip(),
    )
    flash('Student added successfully!' if result else 'Error! Username/Email already exists.', 'success' if result else 'error')
    return redirect(url_for('admin_students'))

@app.route('/admin/students/<int:sid>/delete')
def admin_delete_student(sid):
    if r := login_required('admin'): return r
    delete_student(sid)
    flash('Student deleted.', 'success')
    return redirect(url_for('admin_students'))

# ── Courses ──
@app.route('/admin/courses')
def admin_courses():
    if r := login_required('admin'): return r
    return render_template('admin/courses.html', courses=get_all_courses())

@app.route('/admin/courses/add', methods=['POST'])
def admin_add_course():
    if r := login_required('admin'): return r
    result = add_course(
        code       = request.form.get('code','').strip(),
        name       = request.form.get('name','').strip(),
        credit_hrs = int(request.form.get('credit_hrs',3)),
        semester   = int(request.form.get('semester',1)),
        instructor = request.form.get('instructor','').strip(),
    )
    flash('Course added!' if result else 'Error! Code already exists.', 'success' if result else 'error')
    return redirect(url_for('admin_courses'))

@app.route('/admin/courses/<int:cid>/delete')
def admin_delete_course(cid):
    if r := login_required('admin'): return r
    delete_course(cid)
    flash('Course deleted.', 'success')
    return redirect(url_for('admin_courses'))

# ── Marks ──
@app.route('/admin/marks')
def admin_marks():
    if r := login_required('admin'): return r
    return render_template('admin/marks.html',
        results  = get_all_results(),
        students = get_all_students(),
        courses  = get_all_courses()
    )

@app.route('/admin/marks/add', methods=['POST'])
def admin_add_marks():
    if r := login_required('admin'): return r
    result = add_result(
        student_id   = int(request.form.get('student_id')),
        course_id    = int(request.form.get('course_id')),
        assignment   = float(request.form.get('assignment_score',0)),
        midterm      = float(request.form.get('midterm_score',0)),
        final_score  = float(request.form.get('final_score',0)),
    )
    flash('Marks added successfully!' if result else 'Error adding marks.', 'success' if result else 'error')
    return redirect(url_for('admin_marks'))

@app.route('/admin/marks/publish/<int:rid>')
def admin_publish_result(rid):
    if r := login_required('admin'): return r
    publish_result(rid)
    flash('Result published!', 'success')
    return redirect(url_for('admin_marks'))

@app.route('/admin/marks/publish/all')
def admin_publish_all():
    if r := login_required('admin'): return r
    publish_all_results()
    flash('All results published!', 'success')
    return redirect(url_for('admin_marks'))



# ============================================
#   STUDENT ROUTES
# ============================================

@app.route('/student')
def student_dashboard():
    if r := login_required('student'): return r
    sid     = session.get('student_id')
    results = get_student_results(sid)
    cgpa    = get_student_cgpa(sid)
    enrolled = get_student_enrollments(sid)
    return render_template('student/dashboard.html',
        results=results, cgpa=cgpa, enrolled=enrolled)

# ── Enrollment ──
@app.route('/student/enroll')
def student_enroll():
    if r := login_required('student'): return r
    sid      = session.get('student_id')
    sem      = session.get('semester', 1)
    enrolled = get_student_enrollments(sid)
    available= get_available_courses(sid, sem)
    return render_template('student/enroll.html',
        enrolled=enrolled, available=available)

@app.route('/student/enroll/add/<int:cid>')
def student_enroll_add(cid):
    if r := login_required('student'): return r
    enroll_student(session.get('student_id'), cid)
    flash('Course enrolled successfully!', 'success')
    return redirect(url_for('student_enroll'))

@app.route('/student/enroll/drop/<int:eid>')
def student_enroll_drop(eid):
    if r := login_required('student'): return r
    unenroll_student(eid)
    flash('Course dropped.', 'success')
    return redirect(url_for('student_enroll'))

# ── Results ──
@app.route('/student/results')
def student_results():
    if r := login_required('student'): return r
    sid     = session.get('student_id')
    results = get_student_results(sid)
    cgpa    = get_student_cgpa(sid)
    return render_template('student/results.html', results=results, cgpa=cgpa)

@app.route('/admin/fee')
def admin_fee():
    if r := login_required('admin'): return r
    return render_template('admin/fee.html',
        fee_structures = get_all_fee_structures(),
        student_fees   = get_all_student_fees(),
        payments       = get_all_payments(),
        students       = get_all_students(),
        installments   = get_all_installments(),
        scholarships   = get_all_scholarships()
    )

@app.route('/admin/fee/structure/add', methods=['POST'])
def admin_add_fee_structure():
    if r := login_required('admin'): return r
    add_fee_structure(
        semester        = int(request.form.get('semester', 1)),
        fee_per_credit  = float(request.form.get('fee_per_credit_hour', 0)),
        reg_fee         = float(request.form.get('registration_fee', 0)),
        exam_fee        = float(request.form.get('exam_fee', 0)),
        other_charges   = float(request.form.get('other_charges', 0)),
        academic_year   = request.form.get('academic_year', ''),
        due_date        = request.form.get('due_date', '')
    )
    flash('Fee structure added!', 'success')
    return redirect(url_for('admin_fee'))

@app.route('/admin/fee/generate', methods=['POST'])
def admin_generate_fee():
    if r := login_required('admin'): return r
    student_id = int(request.form.get('student_id'))
    semester   = int(request.form.get('semester', 1))
    result = generate_student_fee(student_id, semester)
    if result:
        flash('Fee generated successfully!', 'success')
    else:
        flash('Error! Fee structure nahi mili ya already generated hai.', 'error')
    return redirect(url_for('admin_fee'))

@app.route('/admin/fee/payment/add', methods=['POST'])
def admin_add_payment():
    if r := login_required('admin'): return r
    add_fee_payment(
        student_fee_id = int(request.form.get('student_fee_id')),
        student_id     = int(request.form.get('student_id', 0)),
        amount         = float(request.form.get('amount_paid', 0)),
        payment_date   = request.form.get('payment_date'),
        method         = request.form.get('payment_method', 'Cash'),
        transaction_id = request.form.get('transaction_id', ''),
        remarks        = request.form.get('remarks', ''),
        received_by    = request.form.get('received_by', '')
    )
    flash('Payment recorded!', 'success')
    return redirect(url_for('admin_fee'))

@app.route('/admin/fee/installment/create', methods=['POST'])
def admin_create_installment():
    if r := login_required('admin'): return r
    student_fee_id  = int(request.form.get('student_fee_id'))
    num             = int(request.form.get('num_installments', 2))
    due_dates       = request.form.getlist('due_date[]')
    created_by      = request.form.get('created_by', 'Admin')
    if len(due_dates) != num:
        flash('Due dates theek se fill karo!', 'error')
        return redirect(url_for('admin_fee'))
    result = create_installments(student_fee_id, num, due_dates, created_by)
    flash('Installment plan bana diya!' if result else 'Error! Installment nahi bani.', 'success' if result else 'error')
    return redirect(url_for('admin_fee'))

@app.route('/admin/fee/installment/pay', methods=['POST'])
def admin_pay_installment():
    if r := login_required('admin'): return r
    result = pay_installment(
        installment_id = int(request.form.get('installment_id')),
        payment_date   = request.form.get('payment_date'),
        method         = request.form.get('payment_method', 'Cash'),
        transaction_id = request.form.get('transaction_id', ''),
        received_by    = request.form.get('received_by', '')
    )
    flash('Installment paid mark kar di!' if result else 'Error ya pehle se paid hai.', 'success' if result else 'error')
    return redirect(url_for('admin_fee'))

@app.route('/admin/fee/scholarship/add', methods=['POST'])
def admin_add_scholarship():
    if r := login_required('admin'): return r
    result = add_scholarship(
        student_id     = int(request.form.get('student_id')),
        label          = request.form.get('label', 'Scholarship'),
        discount_type  = request.form.get('discount_type', 'percent'),
        discount_value = float(request.form.get('discount_value', 0)),
        applied_by     = request.form.get('applied_by', 'Admin')
    )
    flash('Scholarship apply ho gayi!' if result else 'Error! Scholarship apply nahi hui.', 'success' if result else 'error')
    return redirect(url_for('admin_fee'))

@app.route('/admin/fee/installment/get/<int:fee_id>')
def admin_get_installments(fee_id):
    if r := login_required('admin'): return r
    return jsonify(get_installments(fee_id))


# ── STUDENT FEE ROUTE ──

@app.route('/student/fee')
def student_fee():
    if r := login_required('student'): return r
    sid = session.get('student_id')
    return render_template('student/fee.html',
        fees         = get_student_fee(sid),
        payments     = get_payment_history(sid),
        installments = get_student_installments(sid),
        scholarship  = get_student_scholarship(sid)
    )

@app.route('/student/fee/installment/request', methods=['POST'])
def student_request_installment():
    if r := login_required('student'): return r
    sid            = session.get('student_id')
    student_fee_id = int(request.form.get('student_fee_id'))
    due1           = request.form.get('due_date_1')
    due2           = request.form.get('due_date_2')
    # Student can only request 2 installments
    result = create_installments(student_fee_id, 2, [due1, due2], created_by=f'Student:{sid}')
    flash('Installment request bhej di! Admin approve kare ga.' if result else 'Error! Dobara try karo.', 'success' if result else 'error')
    return redirect(url_for('student_fee'))

@app.route('/student/fee/challan/<int:fee_id>')
def student_challan(fee_id):
    if r := login_required('student'): return r
    sid = session.get('student_id')
    fees = get_student_fee(sid)
    fee  = next((f for f in fees if f['id'] == fee_id), None)
    if not fee:
        flash('Fee record nahi mila!', 'error')
        return redirect(url_for('student_fee'))
    student  = get_student_by_user_id(session.get('user_id'))
    details  = get_student_details(sid)
    installments = get_installments(fee_id)
    return render_template('student/challan.html',
        fee=fee, student=student, details=details, installments=installments)


# ── STUDENT PROFILE ROUTES ──

@app.route('/student/profile')
def student_profile():
    if r := login_required('student'): return r
    sid = session.get('student_id')
    student = get_student_by_user_id(session.get('user_id'))
    details = get_student_details(sid)
    return render_template('student/profile.html',
        student=student,
        details=details
    )

@app.route('/student/profile/update', methods=['POST'])
def student_profile_update():
    if r := login_required('student'): return r
    sid = session.get('student_id')
    add_student_details(
        student_id     = sid,
        father_name    = request.form.get('father_name', ''),
        cnic           = request.form.get('cnic', ''),
        phone          = request.form.get('phone', ''),
        address        = request.form.get('address', ''),
        city           = request.form.get('city', ''),
        dob            = request.form.get('date_of_birth') or None,
        gender         = request.form.get('gender', ''),
        blood_group    = request.form.get('blood_group', ''),
        program        = request.form.get('program', ''),
        admission_year = request.form.get('admission_year') or None
    )
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('student_profile'))

# ============================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)