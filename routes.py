from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, Response
from flask_login import login_user, login_required, logout_user, current_user
from app import app, db
from models import (Patient, Treatment, Medication, BloodTest, ImagingRecord, PatientEvent, 
                   MedicationSchedule, Appointment, User, TreatmentEvent, SurgeryEvent, 
                   RadiationEvent, HormoneTherapyEvent, ChemotherapyEvent, SystemicTherapyEvent, AdverseEvent)
from forms import (PatientForm, TreatmentForm, MedicationForm, BloodTestForm, ImagingForm, 
                  EventForm, MedicationScheduleForm, AppointmentForm, LoginForm, UserForm, 
                  UserEditForm, ChangePasswordForm, ExcelImportForm, LabIntegrationForm, LabImportForm)
from followup_forms import (FollowUpScheduleForm, PSAAnalysisForm, AdverseEventForm, 
                           NotificationSettingsForm, FollowUpReportForm, get_adverse_events_for_treatment)
from followup_management import (get_patient_psa_analysis, get_patient_followup_schedule, 
                                send_followup_reminders, check_and_alert_psa_changes)
from adverse_events import (AdverseEventManager, AdverseEventAnalyzer, get_treatment_adverse_events_summary)
from ai_prediction import (get_patient_bcr_prediction, get_patient_adt_prediction, 
                          get_adverse_event_prediction, get_comprehensive_ai_dashboard)
from ai_prediction_forms import (BCRPredictionForm, ADTPredictionForm, AdverseEventPredictionForm, 
                                ComprehensivePredictionForm, PredictionConfigForm)
from treatment_forms import (SurgeryEventForm, RadiationEventForm, HormoneTherapyEventForm, 
                            ChemotherapyEventForm, SystemicTherapyEventForm)
from translations import TRANSLATIONS
from sqlalchemy import func, desc, text
from datetime import datetime, timedelta
import json
import pandas as pd
import io
from werkzeug.utils import secure_filename
from urllib.parse import urlparse
import os
import logging
from flask import send_file
from pdf_generator import generate_patient_report

@app.context_processor
def inject_translations():
    """Make translations available in all templates"""
    return dict(t=TRANSLATIONS)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Trang đăng nhập - Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.active:
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('dashboard')
            flash(f'Chào mừng {user.full_name}!', 'success')
            return redirect(next_page)
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Đăng xuất - Logout"""
    logout_user()
    flash('Bạn đã đăng xuất thành công.', 'info')
    return redirect(url_for('login'))

# User management routes
@app.route('/users')
@login_required
def user_list():
    """Danh sách người dùng - User list"""
    if not current_user.has_permission('manage_users'):
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.full_name).all()
    return render_template('user_list.html', users=users)

@app.route('/user/new', methods=['GET', 'POST'])
@login_required
def user_new():
    """Tạo người dùng mới - Create new user"""
    if not current_user.has_permission('manage_users'):
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('dashboard'))
    
    form = UserForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('Tên đăng nhập hoặc email đã tồn tại.', 'error')
        else:
            user = User(
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data,
                phone=form.phone.data,
                role=form.role.data,
                department=form.department.data,
                employee_id=form.employee_id.data,
                active=form.active.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash(f'Người dùng {user.full_name} đã được tạo thành công.', 'success')
            return redirect(url_for('user_list'))
    
    return render_template('user_form.html', form=form, title='Tạo người dùng mới')

@app.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(user_id):
    """Sửa người dùng - Edit user"""
    if not current_user.has_permission('manage_users'):
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    
    if form.validate_on_submit():
        # Check if username or email already exists (excluding current user)
        existing_user = User.query.filter(
            ((User.username == form.username.data) | 
             (User.email == form.email.data)) &
            (User.id != user_id)
        ).first()
        
        if existing_user:
            flash('Tên đăng nhập hoặc email đã tồn tại.', 'error')
        else:
            user.username = form.username.data
            user.email = form.email.data
            user.full_name = form.full_name.data
            user.phone = form.phone.data
            user.role = form.role.data
            user.department = form.department.data
            user.employee_id = form.employee_id.data
            user.active = form.active.data
            
            db.session.commit()
            
            flash(f'Người dùng {user.full_name} đã được cập nhật thành công.', 'success')
            return redirect(url_for('user_list'))
    
    return render_template('user_form.html', form=form, title='Sửa người dùng', user=user)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Đổi mật khẩu - Change password"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            
            flash('Mật khẩu đã được thay đổi thành công.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Mật khẩu hiện tại không đúng.', 'error')
    
    return render_template('change_password.html', form=form)

@app.route('/')
@login_required
def dashboard():
    """Trang chủ - Dashboard"""
    # Thống kê tổng quan - General statistics
    total_patients = Patient.query.count()
    active_treatments = Treatment.query.filter_by(is_active=True).count()
    recent_blood_tests = BloodTest.query.filter(
        BloodTest.test_date >= datetime.now().date() - timedelta(days=30)
    ).count()
    urgent_events = PatientEvent.query.filter_by(
        priority='URGENT', 
        status='OPEN'
    ).count()
    
    # Lịch hẹn tuần tới - Upcoming appointments this week
    today = datetime.now().date()
    week_end = today + timedelta(days=7)
    upcoming_appointments = Appointment.query.filter(
        Appointment.status == 'SCHEDULED',
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= week_end
    ).order_by(Appointment.appointment_date).all()
    
    # Thuốc sắp đến hạn - Medications due soon
    medications_due_soon = MedicationSchedule.query.filter(
        MedicationSchedule.status == 'PENDING',
        MedicationSchedule.scheduled_date <= today + timedelta(days=1)
    ).order_by(MedicationSchedule.scheduled_date).all()
    
    # Bệnh nhân mới nhất - Recent patients
    recent_patients = Patient.query.order_by(desc(Patient.created_at)).limit(5).all()
    
    # Sự kiện quan trọng - Important events
    important_events = PatientEvent.query.filter(
        PatientEvent.priority.in_(['HIGH', 'URGENT']),
        PatientEvent.status != 'RESOLVED'
    ).order_by(desc(PatientEvent.event_date)).limit(5).all()
    
    return render_template('dashboard.html',
                         total_patients=total_patients,
                         active_treatments=active_treatments,
                         recent_blood_tests=recent_blood_tests,
                         urgent_events=urgent_events,
                         upcoming_appointments=upcoming_appointments,
                         medications_due_soon=medications_due_soon,
                         recent_patients=recent_patients,
                         important_events=important_events)

@app.route('/patients')
@login_required
def patient_list():
    """Danh sách bệnh nhân - Patient list"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = Patient.query
    
    if search:
        query = query.filter(
            db.or_(
                Patient.full_name.contains(search),
                Patient.patient_code.contains(search)
            )
        )
    
    patients = query.order_by(desc(Patient.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Create a form for CSRF token
    from forms import PatientForm
    dummy_form = PatientForm()
    
    return render_template('patient_list.html', patients=patients, search=search, csrf_token=dummy_form.csrf_token)

@app.route('/patient/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    """Chi tiết bệnh nhân - Patient detail"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Lấy dữ liệu cho biểu đồ PSA - Get PSA chart data
    blood_tests = BloodTest.query.filter_by(patient_id=patient_id).order_by(BloodTest.test_date).all()
    
    # Xét nghiệm máu gần nhất - Recent blood tests
    recent_blood_tests = BloodTest.query.filter_by(patient_id=patient_id).order_by(desc(BloodTest.test_date)).limit(5).all()
    
    # Điều trị hiện tại - Current treatment
    current_treatment = Treatment.query.filter_by(patient_id=patient_id, is_active=True).first()
    
    # Thuốc hiện tại - Current medications
    current_medications = []
    if current_treatment:
        current_medications = Medication.query.filter_by(treatment_id=current_treatment.id, is_active=True).all()
    
    # Chẩn đoán hình ảnh gần nhất - Recent imaging
    recent_imaging = ImagingRecord.query.filter_by(patient_id=patient_id).order_by(desc(ImagingRecord.imaging_date)).limit(3).all()
    
    # Sự kiện gần nhất - Recent events
    recent_events = PatientEvent.query.filter_by(patient_id=patient_id).order_by(desc(PatientEvent.event_date)).limit(5).all()
    
    return render_template('patient_detail.html',
                         patient=patient,
                         blood_tests=blood_tests,
                         recent_blood_tests=recent_blood_tests,
                         current_treatment=current_treatment,
                         current_medications=current_medications,
                         recent_imaging=recent_imaging,
                         recent_events=recent_events,
                         today=datetime.now().date())

@app.route('/patient/new', methods=['GET', 'POST'])
@login_required
def patient_new():
    """Tạo bệnh nhân mới - Create new patient"""
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền tạo bệnh nhân mới.', 'error')
        return redirect(url_for('patient_list'))
    
    form = PatientForm()
    
    if form.validate_on_submit():
        # Kiểm tra mã bệnh nhân trùng lặp - Check duplicate patient code
        existing = Patient.query.filter_by(patient_code=form.patient_code.data).first()
        if existing:
            flash('Mã bệnh nhân đã tồn tại!', 'error')
            return render_template('patient_form.html', form=form, title='Thêm bệnh nhân mới')
        
        # Handle pathology image upload
        pathology_image_path = None
        pathology_image_filename = None
        
        if form.pathology_image.data:
            try:
                file = form.pathology_image.data
                # Create filename: name + birth_year + upload_datetime
                name_part = form.full_name.data.replace(' ', '_')
                birth_year = form.date_of_birth.data.year
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                
                new_filename = f"{name_part}_{birth_year}_{timestamp}.{file_extension}"
                file_path = os.path.join('images', 'pathology', new_filename)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Save file
                file.save(file_path)
                pathology_image_path = file_path
                pathology_image_filename = file.filename
                
            except Exception as e:
                flash(f'Lỗi khi tải hình ảnh: {str(e)}', 'error')
                return render_template('patient_form.html', form=form, title='Thêm bệnh nhân mới')
        
        # Create patient with all fields including TNM staging
        patient = Patient(
            patient_code=form.patient_code.data,
            full_name=form.full_name.data,
            date_of_birth=form.date_of_birth.data,
            phone=form.phone.data,
            address=form.address.data,
            insurance_number=form.insurance_number.data,
            diagnosis_date=form.diagnosis_date.data,
            gleason_score=form.gleason_score.data,
            cancer_stage=form.cancer_stage.data,
            initial_psa=form.initial_psa.data,
            sampling_method=form.sampling_method.data,
            sampling_date=form.sampling_date.data,
            # TNM staging fields
            clinical_t=form.clinical_t.data or None,
            clinical_n=form.clinical_n.data or None,
            clinical_m=form.clinical_m.data or None,
            pathological_t=form.pathological_t.data or None,
            pathological_n=form.pathological_n.data or None,
            pathological_m=form.pathological_m.data or None,
            # Pathology image fields
            pathology_image_path=pathology_image_path,
            pathology_image_filename=pathology_image_filename
        )
        
        db.session.add(patient)
        db.session.commit()
        
        # Perform AI risk assessment after patient creation
        try:
            from gemini_ai import evaluate_prostate_cancer_risk
            
            # Prepare data for AI assessment
            patient_data = {
                'age': patient.age,
                'initial_psa': patient.initial_psa,
                'gleason_score': patient.gleason_score,
                'clinical_t': patient.clinical_t,
                'clinical_n': patient.clinical_n,
                'clinical_m': patient.clinical_m,
                'pathological_t': patient.pathological_t,
                'pathological_n': patient.pathological_n,
                'pathological_m': patient.pathological_m,
                'sampling_method': patient.sampling_method
            }
            
            # Get AI assessment
            ai_result = evaluate_prostate_cancer_risk(patient_data)
            
            # Update patient with AI results
            patient.ai_risk_score = ai_result['risk_score']
            patient.ai_staging_result = ai_result['assessment_summary']
            patient.ai_assessment_date = ai_result['assessment_date']
            
            db.session.commit()
            
            flash('Đã thêm bệnh nhân và hoàn tất đánh giá nguy cơ tự động bằng AI!', 'success')
            
        except Exception as e:
            # AI assessment failed, but patient was created successfully
            flash('Đã thêm bệnh nhân thành công! Tuy nhiên không thể thực hiện đánh giá nguy cơ tự động.', 'warning')
            logging.error(f'AI assessment failed: {str(e)}')
        
        return redirect(url_for('dashboard'))
    
    return render_template('patient_form.html', form=form, title='Thêm bệnh nhân mới')

@app.route('/patient/wizard', methods=['GET', 'POST'])
@login_required
def patient_onboarding_wizard():
    """Hướng dẫn thêm bệnh nhân mới - Patient onboarding wizard"""
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền tạo bệnh nhân mới.', 'error')
        return redirect(url_for('patient_list'))
    
    form = PatientForm()
    
    if form.validate_on_submit():
        try:
            # Check for duplicate patient code
            existing = Patient.query.filter_by(patient_code=form.patient_code.data).first()
            if existing:
                flash('Mã bệnh nhân đã tồn tại!', 'error')
                return render_template('patient_onboarding_wizard.html', form=form)
            
            # Create new patient from wizard
            patient = Patient(
                patient_code=form.patient_code.data,
                full_name=form.full_name.data,
                date_of_birth=form.date_of_birth.data,
                phone=form.phone.data,
                address=form.address.data,
                insurance_number=form.insurance_number.data,
                diagnosis_date=form.diagnosis_date.data,
                initial_psa=form.initial_psa.data,
                gleason_score=form.gleason_score.data,
                cancer_stage=form.cancer_stage.data,
                clinical_t=form.clinical_t.data or None,
                clinical_n=form.clinical_n.data or None,
                clinical_m=form.clinical_m.data or None,
                pathological_t=form.pathological_t.data or None,
                pathological_n=form.pathological_n.data or None,
                pathological_m=form.pathological_m.data or None,
                sampling_method=form.sampling_method.data,
                sampling_date=form.sampling_date.data
            )
            
            db.session.add(patient)
            db.session.commit()
            
            # Add initial blood test if provided
            initial_test_date = request.form.get('initial_test_date')
            initial_total_psa = request.form.get('initial_total_psa')
            initial_free_psa = request.form.get('initial_free_psa')
            initial_testosterone = request.form.get('initial_testosterone')
            
            if initial_test_date and (initial_total_psa or initial_free_psa or initial_testosterone):
                try:
                    test_date = datetime.strptime(initial_test_date, '%Y-%m-%d').date()
                    blood_test = BloodTest(
                        patient_id=patient.id,
                        test_date=test_date,
                        total_psa=float(initial_total_psa) if initial_total_psa else None,
                        free_psa=float(initial_free_psa) if initial_free_psa else None,
                        testosterone=int(initial_testosterone) if initial_testosterone else None,
                        notes='Xét nghiệm ban đầu từ hướng dẫn'
                    )
                    blood_test.calculate_psa_ratio()
                    db.session.add(blood_test)
                    db.session.commit()
                except Exception as e:
                    logging.error(f'Error adding initial blood test: {str(e)}')
            
            # AI Assessment if enabled
            enable_ai = request.form.get('enable_ai_assessment') == 'on'
            
            if enable_ai:
                try:
                    from gemini_ai import evaluate_prostate_cancer_risk
                    
                    # Prepare data for AI assessment
                    patient_data = {
                        'age': patient.age,
                        'initial_psa': patient.initial_psa,
                        'gleason_score': patient.gleason_score,
                        'clinical_t': patient.clinical_t,
                        'clinical_n': patient.clinical_n,
                        'clinical_m': patient.clinical_m,
                        'pathological_t': patient.pathological_t,
                        'pathological_n': patient.pathological_n,
                        'pathological_m': patient.pathological_m,
                        'sampling_method': patient.sampling_method
                    }
                    
                    # Get AI assessment
                    ai_result = evaluate_prostate_cancer_risk(patient_data)
                    
                    # Update patient with AI results
                    patient.ai_risk_score = ai_result['risk_score']
                    patient.ai_staging_result = ai_result['assessment_summary']
                    patient.ai_assessment_date = ai_result['assessment_date']
                    
                    db.session.commit()
                    
                    flash('Đã tạo hồ sơ bệnh nhân với đánh giá nguy cơ AI hoàn tất!', 'success')
                    
                except Exception as e:
                    flash('Đã tạo hồ sơ bệnh nhân thành công! Đánh giá AI sẽ được thực hiện sau.', 'warning')
                    logging.error(f'AI assessment failed: {str(e)}')
            else:
                flash('Đã tạo hồ sơ bệnh nhân thành công!', 'success')
            
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi tạo hồ sơ bệnh nhân: {str(e)}', 'error')
            logging.error(f'Error creating patient via wizard: {str(e)}')
    
    return render_template('patient_onboarding_wizard.html', form=form)

@app.route('/patient/<int:patient_id>/edit', methods=['GET', 'POST'])
def patient_edit(patient_id):
    """Sửa thông tin bệnh nhân - Edit patient"""
    patient = Patient.query.get_or_404(patient_id)
    form = PatientForm(obj=patient)
    
    if form.validate_on_submit():
        # Kiểm tra mã bệnh nhân trùng lặp (trừ chính nó) - Check duplicate code except itself
        existing = Patient.query.filter(
            Patient.patient_code == form.patient_code.data,
            Patient.id != patient_id
        ).first()
        if existing:
            flash('Mã bệnh nhân đã tồn tại!', 'error')
            return render_template('patient_form.html', form=form, title='Sửa thông tin bệnh nhân', patient=patient)
        
        form.populate_obj(patient)
        patient.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Đã cập nhật thông tin bệnh nhân!', 'success')
        return redirect(url_for('patient_detail', patient_id=patient.id))
    
    return render_template('patient_form.html', form=form, title='Sửa thông tin bệnh nhân', patient=patient)

@app.route('/patient/<int:patient_id>/blood_test/new', methods=['GET', 'POST'])
def blood_test_new(patient_id):
    """Thêm xét nghiệm máu mới - Add new blood test"""
    patient = Patient.query.get_or_404(patient_id)
    form = BloodTestForm()
    
    if form.validate_on_submit():
        blood_test = BloodTest(
            patient_id=patient_id,
            test_date=form.test_date.data,
            free_psa=form.free_psa.data,
            total_psa=form.total_psa.data,
            testosterone=form.testosterone.data,
            notes=form.notes.data
        )
        
        # Tính tỷ lệ PSA - Calculate PSA ratio
        blood_test.calculate_psa_ratio()
        
        db.session.add(blood_test)
        db.session.commit()
        
        flash('Đã thêm kết quả xét nghiệm máu!', 'success')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    return render_template('blood_test_form.html', form=form, patient=patient, title='Thêm xét nghiệm máu')

@app.route('/patient/<int:patient_id>/treatment/new', methods=['GET', 'POST'])
def treatment_new(patient_id):
    """Thêm điều trị mới - Add new treatment"""
    patient = Patient.query.get_or_404(patient_id)
    form = TreatmentForm()
    
    if form.validate_on_submit():
        # Nếu điều trị mới được đặt là active, deactivate các điều trị khác
        # If new treatment is set as active, deactivate other treatments
        if form.is_active.data:
            Treatment.query.filter_by(patient_id=patient_id, is_active=True).update({'is_active': False})
        
        treatment = Treatment(
            patient_id=patient_id,
            treatment_name=form.treatment_name.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_active=form.is_active.data,
            notes=form.notes.data
        )
        
        db.session.add(treatment)
        db.session.commit()
        
        flash('Đã thêm phác đồ điều trị!', 'success')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    return render_template('treatment_form.html', form=form, patient=patient, title='Thêm điều trị')

@app.route('/patient/<int:patient_id>/imaging/new', methods=['GET', 'POST'])
def imaging_new(patient_id):
    """Thêm chẩn đoán hình ảnh mới - Add new imaging record"""
    patient = Patient.query.get_or_404(patient_id)
    form = ImagingForm()
    
    if form.validate_on_submit():
        imaging = ImagingRecord(
            patient_id=patient_id,
            imaging_type=form.imaging_type.data,
            imaging_date=form.imaging_date.data,
            findings=form.findings.data,
            impression=form.impression.data,
            contrast_used=form.contrast_used.data,
            radiologist=form.radiologist.data
        )
        
        db.session.add(imaging)
        db.session.commit()
        
        flash('Đã thêm kết quả chẩn đoán hình ảnh!', 'success')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    return render_template('imaging_form.html', form=form, patient=patient, title='Thêm chẩn đoán hình ảnh')

@app.route('/patient/<int:patient_id>/event/new', methods=['GET', 'POST'])
def event_new(patient_id):
    """Thêm sự kiện mới - Add new event"""
    patient = Patient.query.get_or_404(patient_id)
    form = EventForm()
    
    if form.validate_on_submit():
        event = PatientEvent(
            patient_id=patient_id,
            event_date=form.event_date.data,
            event_type=form.event_type.data,
            title=form.title.data,
            description=form.description.data,
            priority=form.priority.data,
            status=form.status.data
        )
        
        db.session.add(event)
        db.session.commit()
        
        flash('Đã thêm sự kiện!', 'success')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    return render_template('event_form.html', form=form, patient=patient, title='Thêm sự kiện')

@app.route('/api/patient/<int:patient_id>/blood_test_chart')
def blood_test_chart_data(patient_id):
    """API endpoint cho dữ liệu biểu đồ xét nghiệm máu - Blood test chart data API"""
    blood_tests = BloodTest.query.filter_by(patient_id=patient_id).order_by(BloodTest.test_date).all()
    
    data = {
        'dates': [bt.test_date.strftime('%Y-%m-%d') for bt in blood_tests],
        'free_psa': [bt.free_psa if bt.free_psa else None for bt in blood_tests],
        'total_psa': [bt.total_psa if bt.total_psa else None for bt in blood_tests],
        'testosterone': [bt.testosterone if bt.testosterone else None for bt in blood_tests]
    }
    
    return jsonify(data)

@app.route('/treatment/<int:treatment_id>/medication/new', methods=['GET', 'POST'])
def medication_new(treatment_id):
    """Thêm thuốc mới cho điều trị - Add new medication to treatment"""
    treatment = Treatment.query.get_or_404(treatment_id)
    form = MedicationForm()
    
    if form.validate_on_submit():
        medication = Medication(
            treatment_id=treatment_id,
            drug_name=form.drug_name.data,
            dosage=form.dosage.data,
            frequency=form.frequency.data,
            route=form.route.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_active=form.is_active.data,
            notes=form.notes.data
        )
        
        db.session.add(medication)
        db.session.commit()
        
        flash('Đã thêm thuốc!', 'success')
        return redirect(url_for('patient_detail', patient_id=treatment.patient_id))
    
    return render_template('medication_form.html', form=form, treatment=treatment, title='Thêm thuốc')

# Excel Import/Export Functions

@app.route('/export/patients')
def export_patients():
    """Xuất danh sách bệnh nhân ra Excel - Export patients to Excel"""
    patients = Patient.query.all()
    
    # Tạo DataFrame
    data = []
    for patient in patients:
        current_treatment = patient.get_current_treatment()
        latest_blood_test = patient.get_latest_blood_test()
        
        data.append({
            'Mã bệnh nhân': patient.patient_code,
            'Họ và tên': patient.full_name,
            'Ngày sinh': patient.date_of_birth.strftime('%d/%m/%Y') if patient.date_of_birth else '',
            'Tuổi': patient.age,
            'Số điện thoại': patient.phone or '',
            'Địa chỉ': patient.address or '',
            'Số BHYT': patient.insurance_number or '',
            'Ngày chẩn đoán': patient.diagnosis_date.strftime('%d/%m/%Y') if patient.diagnosis_date else '',
            'Điểm Gleason': patient.gleason_score or '',
            'Giai đoạn': patient.cancer_stage or '',
            'PSA ban đầu': patient.initial_psa or '',
            'Phương pháp lấy mẫu': patient.sampling_method or '',
            'Ngày lấy mẫu': patient.sampling_date.strftime('%d/%m/%Y') if patient.sampling_date else '',
            'Điều trị hiện tại': current_treatment.treatment_name if current_treatment else '',
            'PSA gần nhất': latest_blood_test.total_psa if latest_blood_test else '',
            'Ngày XN gần nhất': latest_blood_test.test_date.strftime('%d/%m/%Y') if latest_blood_test else '',
            'Ngày tạo': patient.created_at.strftime('%d/%m/%Y %H:%M') if patient.created_at else 'N/A'
        })
    
    df = pd.DataFrame(data)
    
    # Tạo file Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Danh sách bệnh nhân', index=False)
        
        # Định dạng
        workbook = writer.book
        worksheet = writer.sheets['Danh sách bệnh nhân']
        
        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#2E7D9A',
            'font_color': 'white',
            'border': 1
        })
        
        # Apply header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Auto-adjust column widths
        for i, col in enumerate(df.columns):
            max_len = max(df[col].astype(str).str.len().max(), len(str(col))) + 2
            worksheet.set_column(i, i, min(max_len, 50))
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'danh_sach_benh_nhan_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    )

@app.route('/export/blood_tests/<int:patient_id>')
def export_blood_tests(patient_id):
    """Xuất xét nghiệm máu của bệnh nhân ra Excel"""
    patient = Patient.query.get_or_404(patient_id)
    blood_tests = BloodTest.query.filter_by(patient_id=patient_id).order_by(BloodTest.test_date.desc()).all()
    
    data = []
    for test in blood_tests:
        data.append({
            'Ngày xét nghiệm': test.test_date.strftime('%d/%m/%Y') if test.test_date else '',
            'FREE PSA (ng/mL)': test.free_psa or '',
            'TOTAL PSA (ng/mL)': test.total_psa or '',
            'Tỷ lệ PSA (%)': f"{test.psa_ratio:.1f}" if test.psa_ratio else '',
            'Testosterone (ng/dL)': test.testosterone or '',
            'Ghi chú': test.notes or '',
            'Ngày tạo': test.created_at.strftime('%d/%m/%Y %H:%M') if test.created_at else 'N/A'
        })
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Xét nghiệm máu', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Xét nghiệm máu']
        
        # Thêm thông tin bệnh nhân
        patient_info = [
            ['Mã bệnh nhân:', patient.patient_code],
            ['Họ tên:', patient.full_name],
            ['Ngày sinh:', patient.date_of_birth.strftime('%d/%m/%Y')],
            ['', '']  # Empty row
        ]
        
        for i, info in enumerate(patient_info):
            worksheet.write(i, 0, info[0] if len(info) > 0 else '')
            worksheet.write(i, 1, info[1] if len(info) > 1 else '')
        
        # Di chuyển dữ liệu xuống
        df.to_excel(writer, sheet_name='Xét nghiệm máu', startrow=len(patient_info), index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'xet_nghiem_mau_{patient.patient_code}_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@app.route('/import/blood_tests/<int:patient_id>', methods=['GET', 'POST'])
def import_blood_tests(patient_id):
    """Nhập xét nghiệm máu từ Excel"""
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Vui lòng chọn file Excel!', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('Vui lòng chọn file Excel!', 'error')
            return redirect(request.url)
        
        if file and file.filename.lower().endswith(('.xlsx', '.xls')):
            try:
                # Đọc file Excel
                df = pd.read_excel(file)
                
                # Mapping columns
                required_columns = {
                    'Ngày xét nghiệm': 'test_date',
                    'FREE PSA (ng/mL)': 'free_psa',
                    'TOTAL PSA (ng/mL)': 'total_psa',
                    'Testosterone (ng/dL)': 'testosterone',
                    'Ghi chú': 'notes'
                }
                
                imported_count = 0
                errors = []
                
                for index, row in df.iterrows():
                    try:
                        # Parse date
                        test_date = pd.to_datetime(row['Ngày xét nghiệm']).date()
                        
                        # Check if test already exists
                        existing = BloodTest.query.filter_by(
                            patient_id=patient_id,
                            test_date=test_date
                        ).first()
                        
                        if existing:
                            errors.append(f"Dòng {index + 2}: Đã có xét nghiệm ngày {test_date.strftime('%d/%m/%Y')}")
                            continue
                        
                        blood_test = BloodTest(
                            patient_id=patient_id,
                            test_date=test_date,
                            free_psa=float(row['FREE PSA (ng/mL)']) if pd.notna(row['FREE PSA (ng/mL)']) and row['FREE PSA (ng/mL)'] != '' else None,
                            total_psa=float(row['TOTAL PSA (ng/mL)']) if pd.notna(row['TOTAL PSA (ng/mL)']) and row['TOTAL PSA (ng/mL)'] != '' else None,
                            testosterone=float(row['Testosterone (ng/dL)']) if pd.notna(row['Testosterone (ng/dL)']) and row['Testosterone (ng/dL)'] != '' else None,
                            notes=str(row['Ghi chú']) if pd.notna(row['Ghi chú']) else None
                        )
                        
                        # Calculate PSA ratio
                        blood_test.calculate_psa_ratio()
                        
                        db.session.add(blood_test)
                        imported_count += 1
                        
                    except Exception as e:
                        errors.append(f"Dòng {index + 2}: {str(e)}")
                
                if imported_count > 0:
                    db.session.commit()
                    flash(f'Đã nhập thành công {imported_count} xét nghiệm!', 'success')
                
                if errors:
                    for error in errors:
                        flash(error, 'warning')
                
                return redirect(url_for('patient_detail', patient_id=patient_id))
                
            except Exception as e:
                flash(f'Lỗi đọc file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Vui lòng chọn file Excel (.xlsx hoặc .xls)!', 'error')
            return redirect(request.url)
    
    return render_template('import_blood_tests.html', patient=patient)

# Enhanced Blood Test Management

@app.route('/patient/<int:patient_id>/blood_tests')
def blood_tests_list(patient_id):
    """Danh sách xét nghiệm máu của bệnh nhân"""
    patient = Patient.query.get_or_404(patient_id)
    page = request.args.get('page', 1, type=int)
    
    blood_tests = BloodTest.query.filter_by(patient_id=patient_id).order_by(desc(BloodTest.test_date)).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('blood_tests_list.html', 
                         patient=patient, 
                         blood_tests=blood_tests)

@app.route('/blood_test/<int:test_id>/edit', methods=['GET', 'POST'])
def blood_test_edit(test_id):
    """Sửa xét nghiệm máu"""
    blood_test = BloodTest.query.get_or_404(test_id)
    form = BloodTestForm(obj=blood_test)
    
    if form.validate_on_submit():
        form.populate_obj(blood_test)
        blood_test.calculate_psa_ratio()
        
        db.session.commit()
        flash('Đã cập nhật xét nghiệm máu!', 'success')
        return redirect(url_for('patient_detail', patient_id=blood_test.patient_id))
    
    return render_template('blood_test_form.html', 
                         form=form, 
                         patient=blood_test.patient, 
                         title='Sửa xét nghiệm máu',
                         blood_test=blood_test)

@app.route('/blood_test/<int:test_id>/delete', methods=['POST'])
def blood_test_delete(test_id):
    """Xóa xét nghiệm máu"""
    blood_test = BloodTest.query.get_or_404(test_id)
    patient_id = blood_test.patient_id
    
    db.session.delete(blood_test)
    db.session.commit()
    
    flash('Đã xóa xét nghiệm máu!', 'success')
    return redirect(url_for('patient_detail', patient_id=patient_id))

# Enhanced Imaging Management

@app.route('/patient/<int:patient_id>/imaging')
def imaging_list(patient_id):
    """Danh sách chẩn đoán hình ảnh của bệnh nhân"""
    patient = Patient.query.get_or_404(patient_id)
    page = request.args.get('page', 1, type=int)
    
    imaging_records = ImagingRecord.query.filter_by(patient_id=patient_id).order_by(desc(ImagingRecord.imaging_date)).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('imaging_list.html', 
                         patient=patient, 
                         imaging_records=imaging_records)

@app.route('/imaging/<int:imaging_id>/edit', methods=['GET', 'POST'])
def imaging_edit(imaging_id):
    """Sửa chẩn đoán hình ảnh"""
    imaging = ImagingRecord.query.get_or_404(imaging_id)
    form = ImagingForm(obj=imaging)
    
    if form.validate_on_submit():
        form.populate_obj(imaging)
        
        db.session.commit()
        flash('Đã cập nhật chẩn đoán hình ảnh!', 'success')
        return redirect(url_for('patient_detail', patient_id=imaging.patient_id))
    
    return render_template('imaging_form.html', 
                         form=form, 
                         patient=imaging.patient, 
                         title='Sửa chẩn đoán hình ảnh',
                         imaging=imaging)

@app.route('/imaging/<int:imaging_id>/delete', methods=['POST'])
def imaging_delete(imaging_id):
    """Xóa chẩn đoán hình ảnh"""
    imaging = ImagingRecord.query.get_or_404(imaging_id)
    patient_id = imaging.patient_id
    
    db.session.delete(imaging)
    db.session.commit()
    
    flash('Đã xóa chẩn đoán hình ảnh!', 'success')
    return redirect(url_for('patient_detail', patient_id=patient_id))

# Enhanced Medication Management

@app.route('/patient/<int:patient_id>/medications')
def medications_list(patient_id):
    """Danh sách thuốc của bệnh nhân"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Lấy tất cả thuốc theo điều trị
    treatments = Treatment.query.filter_by(patient_id=patient_id).order_by(desc(Treatment.start_date)).all()
    
    return render_template('medications_list.html', 
                         patient=patient, 
                         treatments=treatments)

@app.route('/medication/<int:medication_id>/edit', methods=['GET', 'POST'])
def medication_edit(medication_id):
    """Sửa thuốc"""
    medication = Medication.query.get_or_404(medication_id)
    form = MedicationForm(obj=medication)
    
    if form.validate_on_submit():
        form.populate_obj(medication)
        
        db.session.commit()
        flash('Đã cập nhật thuốc!', 'success')
        return redirect(url_for('patient_detail', patient_id=medication.treatment.patient_id))
    
    return render_template('medication_form.html', 
                         form=form, 
                         treatment=medication.treatment, 
                         title='Sửa thuốc',
                         medication=medication)

@app.route('/medication/<int:medication_id>/delete', methods=['POST'])
def medication_delete(medication_id):
    """Xóa thuốc"""
    medication = Medication.query.get_or_404(medication_id)
    patient_id = medication.treatment.patient_id
    
    db.session.delete(medication)
    db.session.commit()
    
    flash('Đã xóa thuốc!', 'success')
    return redirect(url_for('patient_detail', patient_id=patient_id))

# Medication Scheduling Routes

@app.route('/medication/<int:medication_id>/schedule')
def medication_schedule_list(medication_id):
    """Danh sách lịch trình thuốc"""
    medication = Medication.query.get_or_404(medication_id)
    schedules = MedicationSchedule.query.filter_by(medication_id=medication_id).order_by(desc(MedicationSchedule.scheduled_date)).all()
    
    return render_template('medication_schedule_list.html', 
                         medication=medication, 
                         schedules=schedules)

@app.route('/medication/<int:medication_id>/schedule/new', methods=['GET', 'POST'])
def medication_schedule_new(medication_id):
    """Tạo lịch trình thuốc mới"""
    medication = Medication.query.get_or_404(medication_id)
    form = MedicationScheduleForm()
    
    if form.validate_on_submit():
        schedule = MedicationSchedule(
            medication_id=medication_id,
            patient_id=medication.treatment.patient_id,
            scheduled_date=form.scheduled_date.data,
            administered_date=form.administered_date.data,
            status=form.status.data,
            postpone_reason=form.postpone_reason.data,
            dosage_given=form.dosage_given.data,
            administration_notes=form.administration_notes.data
        )
        
        db.session.add(schedule)
        
        # Tự động tạo lịch hẹn tái khám nếu chưa có
        if form.status.data == 'PENDING':
            existing_appointment = Appointment.query.filter_by(
                patient_id=medication.treatment.patient_id,
                appointment_date=form.scheduled_date.data,
                status='SCHEDULED'
            ).first()
            
            if not existing_appointment:
                appointment = Appointment(
                    patient_id=medication.treatment.patient_id,
                    medication_schedule_id=schedule.id,
                    appointment_date=form.scheduled_date.data,
                    appointment_type='MEDICATION',
                    purpose=f'Tái khám và sử dụng {medication.drug_name}',
                    status='SCHEDULED'
                )
                db.session.add(appointment)
        
        db.session.commit()
        flash('Đã tạo lịch trình thuốc!', 'success')
        return redirect(url_for('patient_detail', patient_id=medication.treatment.patient_id))
    
    return render_template('medication_schedule_form.html', 
                         form=form, 
                         medication=medication, 
                         title='Tạo lịch trình thuốc')

@app.route('/schedule/<int:schedule_id>/edit', methods=['GET', 'POST'])
def medication_schedule_edit(schedule_id):
    """Sửa lịch trình thuốc"""
    schedule = MedicationSchedule.query.get_or_404(schedule_id)
    form = MedicationScheduleForm(obj=schedule)
    
    if form.validate_on_submit():
        form.populate_obj(schedule)
        schedule.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Đã cập nhật lịch trình thuốc!', 'success')
        return redirect(url_for('patient_detail', patient_id=schedule.patient_id))
    
    return render_template('medication_schedule_form.html', 
                         form=form, 
                         medication=schedule.medication, 
                         title='Sửa lịch trình thuốc',
                         schedule=schedule)

@app.route('/schedule/<int:schedule_id>/complete', methods=['POST'])
def medication_schedule_complete(schedule_id):
    """Đánh dấu hoàn thành lịch trình thuốc"""
    schedule = MedicationSchedule.query.get_or_404(schedule_id)
    
    schedule.status = 'COMPLETED'
    schedule.administered_date = datetime.now().date()
    schedule.updated_at = datetime.utcnow()
    
    # Tự động tạo lịch trình tiếp theo (1 tháng sau)
    next_date = schedule.scheduled_date + timedelta(days=30)
    next_schedule = MedicationSchedule(
        medication_id=schedule.medication_id,
        patient_id=schedule.patient_id,
        scheduled_date=next_date,
        status='PENDING'
    )
    
    # Tạo lịch hẹn cho lần tiếp theo
    next_appointment = Appointment(
        patient_id=schedule.patient_id,
        medication_schedule_id=next_schedule.id,
        appointment_date=next_date,
        appointment_type='MEDICATION',
        purpose=f'Tái khám và sử dụng {schedule.medication.drug_name}',
        status='SCHEDULED'
    )
    
    db.session.add(next_schedule)
    db.session.add(next_appointment)
    db.session.commit()
    
    flash(f'Đã hoàn thành và tạo lịch tiếp theo ({next_date.strftime("%d/%m/%Y")})!', 'success')
    return redirect(url_for('patient_detail', patient_id=schedule.patient_id))

# Appointment Management Routes

@app.route('/appointments')
def appointment_list():
    """Danh sách tất cả lịch hẹn"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '', type=str)
    
    query = Appointment.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    appointments = query.order_by(Appointment.appointment_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('appointment_list.html', 
                         appointments=appointments, 
                         status_filter=status_filter)

@app.route('/patient/<int:patient_id>/appointments')
def patient_appointments(patient_id):
    """Lịch hẹn của bệnh nhân"""
    patient = Patient.query.get_or_404(patient_id)
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(desc(Appointment.appointment_date)).all()
    
    return render_template('patient_appointments.html', 
                         patient=patient, 
                         appointments=appointments)

@app.route('/patient/<int:patient_id>/appointment/new', methods=['GET', 'POST'])
def appointment_new(patient_id):
    """Tạo lịch hẹn mới"""
    patient = Patient.query.get_or_404(patient_id)
    form = AppointmentForm()
    
    if form.validate_on_submit():
        # Combine date and time into datetime
        appointment_datetime = datetime.combine(form.appointment_date.data, form.appointment_time.data)
        
        appointment = Appointment(
            patient_id=patient_id,
            appointment_date=appointment_datetime,
            appointment_time=form.appointment_time.data,
            appointment_type=form.appointment_type.data,
            purpose=form.purpose.data,
            description=form.description.data,
            notes=form.notes.data,
            status=form.status.data,
            created_by=current_user.id
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        flash('Đã tạo lịch hẹn!', 'success')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    return render_template('appointment_form.html', 
                         form=form, 
                         patient=patient, 
                         title='Tạo lịch hẹn')

@app.route('/appointment/<int:appointment_id>/edit', methods=['GET', 'POST'])
def appointment_edit(appointment_id):
    """Sửa lịch hẹn"""
    appointment = Appointment.query.get_or_404(appointment_id)
    
    # Pre-populate form with existing data
    form = AppointmentForm()
    if request.method == 'GET':
        form.appointment_date.data = appointment.appointment_date.date() if appointment.appointment_date else None
        form.appointment_time.data = appointment.appointment_time or (appointment.appointment_date.time() if appointment.appointment_date else None)
        form.appointment_type.data = appointment.appointment_type
        form.purpose.data = appointment.purpose
        form.description.data = appointment.description
        form.notes.data = appointment.notes
        form.status.data = appointment.status
    
    if form.validate_on_submit():
        # Combine date and time into datetime
        appointment_datetime = datetime.combine(form.appointment_date.data, form.appointment_time.data)
        
        appointment.appointment_date = appointment_datetime
        appointment.appointment_time = form.appointment_time.data
        appointment.appointment_type = form.appointment_type.data
        appointment.purpose = form.purpose.data
        appointment.description = form.description.data
        appointment.notes = form.notes.data
        appointment.status = form.status.data
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Đã cập nhật lịch hẹn!', 'success')
        return redirect(url_for('patient_detail', patient_id=appointment.patient_id))
    
    return render_template('appointment_form.html', 
                         form=form, 
                         patient=appointment.patient, 
                         title='Sửa lịch hẹn',
                         appointment=appointment)

# Excel Export for Medication Schedules

@app.route('/export/medication_schedules/<int:patient_id>')
def export_medication_schedules(patient_id):
    """Xuất lịch trình thuốc ra Excel"""
    patient = Patient.query.get_or_404(patient_id)
    schedules = MedicationSchedule.query.filter_by(patient_id=patient_id).order_by(MedicationSchedule.scheduled_date.desc()).all()
    
    data = []
    for schedule in schedules:
        data.append({
            'Tên thuốc': schedule.medication.drug_name,
            'Ngày dự kiến': schedule.scheduled_date.strftime('%d/%m/%Y'),
            'Ngày thực tế': schedule.administered_date.strftime('%d/%m/%Y') if schedule.administered_date else '',
            'Trạng thái': 'Chờ xử lý' if schedule.status == 'PENDING' else 'Đã xử lý' if schedule.status == 'COMPLETED' else 'Hoãn',
            'Liều lượng': schedule.dosage_given or schedule.medication.dosage or '',
            'Lý do hoãn': schedule.postpone_reason or '',
            'Ghi chú': schedule.administration_notes or '',
            'Ngày tạo': schedule.created_at.strftime('%d/%m/%Y %H:%M')
        })
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Lịch trình thuốc', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Lịch trình thuốc']
        
        # Thêm thông tin bệnh nhân
        patient_info = [
            ['Mã bệnh nhân:', patient.patient_code],
            ['Họ tên:', patient.full_name],
            ['Ngày sinh:', patient.date_of_birth.strftime('%d/%m/%Y')],
            ['', '']  # Empty row
        ]
        
        for i, info in enumerate(patient_info):
            worksheet.write(i, 0, info[0] if len(info) > 0 else '')
            worksheet.write(i, 1, info[1] if len(info) > 1 else '')
        
        # Di chuyển dữ liệu xuống
        df.to_excel(writer, sheet_name='Lịch trình thuốc', startrow=len(patient_info), index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'lich_trinh_thuoc_{patient.patient_code}_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/patient/<int:patient_id>/ai_assess', methods=['POST'])
@login_required
def ai_assess_patient(patient_id):
    """Đánh giá nguy cơ bằng AI - AI risk assessment"""
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền thực hiện đánh giá AI.', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    patient = Patient.query.get_or_404(patient_id)
    
    try:
        from gemini_ai import evaluate_prostate_cancer_risk
        
        # Prepare data for AI assessment
        patient_data = {
            'age': patient.age,
            'initial_psa': patient.initial_psa,
            'gleason_score': patient.gleason_score,
            'clinical_t': patient.clinical_t,
            'clinical_n': patient.clinical_n,
            'clinical_m': patient.clinical_m,
            'pathological_t': patient.pathological_t,
            'pathological_n': patient.pathological_n,
            'pathological_m': patient.pathological_m,
            'sampling_method': patient.sampling_method
        }
        
        # Get AI assessment
        ai_result = evaluate_prostate_cancer_risk(patient_data)
        
        # Update patient with AI results
        patient.ai_risk_score = ai_result['risk_score']
        patient.ai_staging_result = ai_result['assessment_summary']
        patient.ai_assessment_date = ai_result['assessment_date']
        
        db.session.commit()
        
        flash('Đã hoàn tất đánh giá nguy cơ tự động bằng AI!', 'success')
        
    except Exception as e:
        flash(f'Không thể thực hiện đánh giá AI: {str(e)}', 'error')
        logging.error(f'AI assessment failed: {str(e)}')
    
    return redirect(url_for('patient_detail', patient_id=patient_id) + '#ai-assessment-tab')

@app.route('/patients/excel_import', methods=['GET', 'POST'])
@login_required
def excel_import():
    """Nhập dữ liệu bệnh nhân từ Excel - Import patient data from Excel"""
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền nhập dữ liệu.', 'error')
        return redirect(url_for('patient_list'))
    
    form = ExcelImportForm()
    import_results = None
    
    if form.validate_on_submit():
        try:
            # Read Excel file
            excel_file = form.excel_file.data
            df = pd.read_excel(excel_file)
            
            # Process import
            import_results = process_excel_import(df)
            
            if import_results['success'] > 0:
                flash(f'Đã nhập thành công {import_results["success"]} bệnh nhân!', 'success')
            if import_results['errors'] > 0:
                flash(f'Có {import_results["errors"]} lỗi xảy ra.', 'warning')
                
        except Exception as e:
            flash(f'Lỗi đọc tệp Excel: {str(e)}', 'error')
            logging.error(f'Excel import error: {str(e)}')
    
    return render_template('excel_import.html', form=form, import_results=import_results)

@app.route('/patients/excel_template')
def download_excel_template():
    """Tải mẫu Excel - Download Excel template"""
    
    # Create template data
    template_data = {
        'patient_code': ['BN001', 'BN002'],
        'full_name': ['Nguyễn Văn A', 'Trần Thị B'],
        'date_of_birth': ['01/01/1970', '15/06/1965'],
        'phone': ['0901234567', '0987654321'],
        'address': ['123 Đường ABC, TP.HCM', '456 Đường XYZ, Hà Nội'],
        'insurance_number': ['DN1234567890', 'HN0987654321'],
        'diagnosis_date': ['01/01/2024', '15/02/2024'],
        'initial_psa': [8.5, 12.3],
        'gleason_score': ['3+4=7', '4+3=7'],
        'cancer_stage': ['T2a', 'T2b'],
        'clinical_t': ['T2a', 'T2b'],
        'clinical_n': ['N0', 'N0'],
        'clinical_m': ['M0', 'M0'],
        'pathological_t': ['T2a', 'T2b'],
        'pathological_n': ['N0', 'N0'],
        'pathological_m': ['M0', 'M0'],
        'sampling_method': ['TRUS_BIOPSY', 'TRANSPERINEAL_BIOPSY'],
        'sampling_date': ['20/12/2023', '10/01/2024']
    }
    
    df = pd.DataFrame(template_data)
    
    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Danh sách bệnh nhân', index=False)
        
        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Danh sách bệnh nhân']
        
        # Add header formatting
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Apply header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Adjust column widths
        worksheet.set_column('A:A', 12)  # patient_code
        worksheet.set_column('B:B', 20)  # full_name
        worksheet.set_column('C:C', 15)  # date_of_birth
        worksheet.set_column('D:D', 15)  # phone
        worksheet.set_column('E:E', 30)  # address
        worksheet.set_column('F:F', 20)  # insurance_number
        worksheet.set_column('G:G', 15)  # diagnosis_date
        worksheet.set_column('H:H', 12)  # initial_psa
        worksheet.set_column('I:I', 15)  # gleason_score
        worksheet.set_column('J:J', 12)  # cancer_stage
        worksheet.set_column('K:S', 10)  # TNM columns
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'mau_benh_nhan_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

def process_excel_import(df):
    """Xử lý nhập dữ liệu từ Excel - Process Excel import"""
    results = {
        'total': len(df),
        'success': 0,
        'skipped': 0,
        'errors': 0,
        'error_details': []
    }
    
    # Required columns mapping
    required_columns = {
        'patient_code': 'patient_code',
        'full_name': 'full_name', 
        'date_of_birth': 'date_of_birth',
        'diagnosis_date': 'diagnosis_date',
        'initial_psa': 'initial_psa',
        'gleason_score': 'gleason_score'
    }
    
    # Check required columns
    missing_columns = []
    for col in required_columns.keys():
        if col not in df.columns:
            missing_columns.append(col)
    
    if missing_columns:
        results['errors'] = results['total']
        results['error_details'].append(f'Thiếu các cột bắt buộc: {", ".join(missing_columns)}')
        return results
    
    for index, row in df.iterrows():
        try:
            # Check if patient already exists
            existing_patient = Patient.query.filter_by(patient_code=row['patient_code']).first()
            if existing_patient:
                results['skipped'] += 1
                continue
            
            # Parse dates
            try:
                date_of_birth = pd.to_datetime(row['date_of_birth'], format='%d/%m/%Y').date()
                diagnosis_date = pd.to_datetime(row['diagnosis_date'], format='%d/%m/%Y').date()
                sampling_date = pd.to_datetime(row.get('sampling_date'), format='%d/%m/%Y').date() if pd.notna(row.get('sampling_date')) else None
            except:
                results['errors'] += 1
                results['error_details'].append(f'Dòng {index + 2}: Lỗi định dạng ngày')
                continue
            
            # Create new patient
            patient = Patient(
                patient_code=row['patient_code'],
                full_name=row['full_name'],
                date_of_birth=date_of_birth,
                phone=row.get('phone'),
                address=row.get('address'),
                insurance_number=row.get('insurance_number'),
                diagnosis_date=diagnosis_date,
                initial_psa=float(row['initial_psa']) if pd.notna(row['initial_psa']) else None,
                gleason_score=str(row['gleason_score']) if pd.notna(row['gleason_score']) else None,
                cancer_stage=row.get('cancer_stage'),
                clinical_t=row.get('clinical_t'),
                clinical_n=row.get('clinical_n'),
                clinical_m=row.get('clinical_m'),
                pathological_t=row.get('pathological_t'),
                pathological_n=row.get('pathological_n'),
                pathological_m=row.get('pathological_m'),
                sampling_method=row.get('sampling_method'),
                sampling_date=sampling_date
            )
            
            db.session.add(patient)
            db.session.commit()
            results['success'] += 1
            
        except Exception as e:
            results['errors'] += 1
            results['error_details'].append(f'Dòng {index + 2}: {str(e)}')
            db.session.rollback()
    
    return results

@app.route('/patient/<int:patient_id>/report/pdf')
@login_required
def patient_report_pdf(patient_id):
    """Tạo báo cáo PDF cho bệnh nhân - Generate PDF report for patient"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Get blood tests for chart
    blood_tests = BloodTest.query.filter_by(patient_id=patient_id).order_by(BloodTest.test_date).all()
    
    try:
        # Generate PDF report
        pdf_path = generate_patient_report(patient, blood_tests)
        
        # Return PDF file
        filename = f"bao_cao_{patient.patient_code}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        response = send_file(
            pdf_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
        # Schedule cleanup of temp file after response is sent
        @response.call_on_close
        def cleanup_temp_file():
            try:
                import os
                if os.path.exists(pdf_path):
                    os.unlink(pdf_path)
            except Exception as e:
                print(f"Could not cleanup temp file: {e}")
            
        return response
        
    except Exception as e:
        flash(f'Không thể tạo báo cáo PDF: {str(e)}', 'error')
        logging.error(f'PDF generation failed: {str(e)}')
        return redirect(url_for('patient_detail', patient_id=patient_id))

@app.route('/blood_tests/template/<int:patient_id>')
def download_blood_test_template(patient_id):
    """Tải mẫu Excel xét nghiệm máu - Download blood test Excel template"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Create template data
    template_data = {
        'test_date': ['01/01/2024', '01/02/2024', '01/03/2024'],
        'free_psa': [1.2, 1.1, 1.0],
        'total_psa': [8.5, 7.8, 7.2],
        'testosterone': [450, 440, 430],
        'notes': ['Kết quả bình thường', 'Giảm nhẹ', 'Ổn định']
    }
    
    df = pd.DataFrame(template_data)
    
    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Xét nghiệm máu', index=False)
        
        # Get workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Xét nghiệm máu']
        
        # Add header formatting
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Apply header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Adjust column widths
        worksheet.set_column('A:A', 15)  # test_date
        worksheet.set_column('B:B', 15)  # free_psa
        worksheet.set_column('C:C', 15)  # total_psa
        worksheet.set_column('D:D', 15)  # testosterone
        worksheet.set_column('E:E', 30)  # notes
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'mau_xet_nghiem_mau_{patient.patient_code}_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@app.route('/blood_tests/import/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def blood_test_import(patient_id):
    """Nhập dữ liệu xét nghiệm máu từ Excel - Import blood test data from Excel"""
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền nhập dữ liệu.', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    patient = Patient.query.get_or_404(patient_id)
    form = ExcelImportForm()
    import_results = None
    
    if form.validate_on_submit():
        try:
            # Read Excel file
            excel_file = form.excel_file.data
            df = pd.read_excel(excel_file)
            
            # Process import
            import_results = process_blood_test_import(df, patient_id)
            
            if import_results['success'] > 0:
                flash(f'Đã nhập thành công {import_results["success"]} kết quả xét nghiệm!', 'success')
            if import_results['errors'] > 0:
                flash(f'Có {import_results["errors"]} lỗi xảy ra.', 'warning')
                
        except Exception as e:
            flash(f'Lỗi đọc tệp Excel: {str(e)}', 'error')
            logging.error(f'Blood test Excel import error: {str(e)}')
    
    return render_template('blood_test_import.html', form=form, import_results=import_results, patient=patient)

def process_blood_test_import(df, patient_id):
    """Xử lý nhập dữ liệu xét nghiệm máu từ Excel - Process blood test Excel import"""
    results = {
        'total': len(df),
        'success': 0,
        'skipped': 0,
        'errors': 0,
        'error_details': []
    }
    
    # Required columns mapping
    required_columns = {
        'test_date': 'test_date',
        'free_psa': 'free_psa',
        'total_psa': 'total_psa'
    }
    
    # Check required columns
    missing_columns = []
    for col in required_columns.keys():
        if col not in df.columns:
            missing_columns.append(col)
    
    if missing_columns:
        results['errors'] = results['total']
        results['error_details'].append(f'Thiếu các cột bắt buộc: {", ".join(missing_columns)}')
        return results
    
    for index, row in df.iterrows():
        try:
            # Parse test date
            try:
                test_date = pd.to_datetime(row['test_date'], format='%d/%m/%Y').date()
            except:
                try:
                    test_date = pd.to_datetime(row['test_date']).date()
                except:
                    results['errors'] += 1
                    results['error_details'].append(f'Dòng {index + 2}: Lỗi định dạng ngày xét nghiệm')
                    continue
            
            # Check if blood test already exists for this date
            existing_test = BloodTest.query.filter_by(
                patient_id=patient_id,
                test_date=test_date
            ).first()
            if existing_test:
                results['skipped'] += 1
                continue
            
            # Create new blood test
            blood_test = BloodTest(
                patient_id=patient_id,
                test_date=test_date,
                free_psa=float(row['free_psa']) if pd.notna(row['free_psa']) else None,
                total_psa=float(row['total_psa']) if pd.notna(row['total_psa']) else None,
                testosterone=float(row.get('testosterone')) if pd.notna(row.get('testosterone')) else None,
                notes=str(row.get('notes')) if pd.notna(row.get('notes')) else None
            )
            
            # Calculate PSA ratio
            blood_test.calculate_psa_ratio()
            
            db.session.add(blood_test)
            db.session.commit()
            results['success'] += 1
            
        except Exception as e:
            results['errors'] += 1
            results['error_details'].append(f'Dòng {index + 2}: {str(e)}')
            db.session.rollback()
    
    return results


# Lab Integration Routes

@app.route('/lab_integration')
@login_required
def lab_integration_dashboard():
    """Lab integration dashboard - Bảng điều khiển tích hợp lab"""
    if not current_user.has_permission('system_config'):
        flash('Bạn không có quyền truy cập chức năng này.', 'error')
        return redirect(url_for('index'))
    
    from lab_integration import lab_manager
    
    # Test connections to all configured lab systems
    connection_status = lab_manager.test_all_connections()
    available_systems = lab_manager.get_available_systems()
    
    # Get patients with lab integration configured
    patients_with_lab = Patient.query.filter(Patient.external_lab_id.isnot(None)).all()
    
    return render_template('lab_integration_dashboard.html',
                         connection_status=connection_status,
                         available_systems=available_systems,
                         patients_with_lab=patients_with_lab)

@app.route('/patient/<int:patient_id>/lab_config', methods=['GET', 'POST'])
@login_required
def patient_lab_config(patient_id):
    """Configure lab integration for patient - Cấu hình tích hợp lab cho bệnh nhân"""
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền sửa đổi thông tin bệnh nhân.', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    patient = Patient.query.get_or_404(patient_id)
    form = LabIntegrationForm()
    
    if form.validate_on_submit():
        patient.external_lab_id = form.external_lab_id.data
        patient.lab_system_type = form.lab_system_type.data
        
        try:
            db.session.commit()
            flash('Đã cập nhật cấu hình tích hợp lab!', 'success')
            return redirect(url_for('patient_detail', patient_id=patient_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi cập nhật: {str(e)}', 'error')
    
    # Pre-populate form with existing data
    if request.method == 'GET':
        form.external_lab_id.data = patient.external_lab_id
        form.lab_system_type.data = patient.lab_system_type
    
    return render_template('patient_lab_config.html', patient=patient, form=form)

@app.route('/patient/<int:patient_id>/lab_import', methods=['GET', 'POST'])
@login_required
def patient_lab_import(patient_id):
    """Import lab results for specific patient - Nhập kết quả lab cho bệnh nhân"""
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền nhập dữ liệu.', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    patient = Patient.query.get_or_404(patient_id)
    form = LabImportForm()
    import_results = None
    
    # Pre-populate with patient's configured lab system
    if patient.lab_system_type and request.method == 'GET':
        form.lab_system.data = patient.lab_system_type
        form.patient_lab_id.data = patient.external_lab_id
    
    if form.validate_on_submit():
        try:
            from lab_integration import lab_manager
            from datetime import timedelta
            
            lab_system = form.lab_system.data
            patient_lab_id = form.patient_lab_id.data
            import_days = int(form.import_days.data)
            
            # Import results
            imported_count, errors = lab_manager.import_for_patient(
                patient_id, lab_system, patient_lab_id
            )
            
            # Update patient's lab configuration if not set
            if not patient.external_lab_id:
                patient.external_lab_id = patient_lab_id
                patient.lab_system_type = lab_system
            
            # Update last import time
            patient.last_lab_import = datetime.now()
            db.session.commit()
            
            import_results = {
                'imported_count': imported_count,
                'errors': errors,
                'lab_system': lab_system
            }
            
            if imported_count > 0:
                flash(f'Đã nhập thành công {imported_count} kết quả xét nghiệm từ {lab_system.upper()}!', 'success')
            if errors:
                for error in errors:
                    flash(error, 'warning')
                    
        except Exception as e:
            flash(f'Lỗi nhập dữ liệu từ lab: {str(e)}', 'error')
            logging.error(f'Lab import error: {str(e)}')
    
    return render_template('patient_lab_import.html', 
                         patient=patient, 
                         form=form, 
                         import_results=import_results)

# Treatment Event Management Routes

@app.route('/patient/<int:patient_id>/treatment_events')
@login_required
def patient_treatment_timeline(patient_id):
    """Comprehensive treatment timeline for patient - Dòng thời gian điều trị toàn diện"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Get treatment timeline from patient helper method
    treatment_timeline = patient.get_treatment_timeline()
    
    return render_template('treatment_timeline.html', 
                         patient=patient, 
                         treatment_timeline=treatment_timeline)

# Surgery Event Routes

@app.route('/patient/<int:patient_id>/surgery/add', methods=['GET', 'POST'])
@login_required
def add_surgery_event(patient_id):
    """Thêm sự kiện phẫu thuật - Add surgery event"""
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền thêm thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    patient = Patient.query.get_or_404(patient_id)
    form = SurgeryEventForm()
    
    if form.validate_on_submit():
        surgery_event = SurgeryEvent(patient_id=patient_id)
        form.populate_obj(surgery_event)
        
        db.session.add(surgery_event)
        db.session.commit()
        flash('Đã thêm thông tin phẫu thuật!', 'success')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    return render_template('treatment_forms/surgery_form.html', 
                         form=form, 
                         patient=patient, 
                         title='Thêm phẫu thuật')

@app.route('/surgery/<int:surgery_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_surgery_event(surgery_id):
    """Sửa sự kiện phẫu thuật - Edit surgery event"""
    surgery = SurgeryEvent.query.get_or_404(surgery_id)
    
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền sửa thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=surgery.patient_id))
    
    form = SurgeryEventForm(obj=surgery)
    
    if form.validate_on_submit():
        form.populate_obj(surgery)
        db.session.commit()
        flash('Đã cập nhật thông tin phẫu thuật!', 'success')
        return redirect(url_for('patient_detail', patient_id=surgery.patient_id))
    
    return render_template('treatment_forms/surgery_form.html', 
                         form=form, 
                         patient=surgery.patient, 
                         title='Sửa phẫu thuật',
                         surgery=surgery)

@app.route('/surgery/<int:surgery_id>/delete', methods=['POST'])
@login_required
def delete_surgery_event(surgery_id):
    """Xóa sự kiện phẫu thuật - Delete surgery event"""
    surgery = SurgeryEvent.query.get_or_404(surgery_id)
    
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền xóa thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=surgery.patient_id))
    
    patient_id = surgery.patient_id
    db.session.delete(surgery)
    db.session.commit()
    
    flash('Đã xóa thông tin phẫu thuật!', 'success')
    return redirect(url_for('patient_detail', patient_id=patient_id))

# Radiation Event Routes

@app.route('/patient/<int:patient_id>/radiation/add', methods=['GET', 'POST'])
@login_required
def add_radiation_event(patient_id):
    """Thêm sự kiện xạ trị - Add radiation event"""
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền thêm thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    patient = Patient.query.get_or_404(patient_id)
    form = RadiationEventForm()
    
    if form.validate_on_submit():
        radiation_event = RadiationEvent(patient_id=patient_id)
        form.populate_obj(radiation_event)
        
        db.session.add(radiation_event)
        db.session.commit()
        flash('Đã thêm thông tin xạ trị!', 'success')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    return render_template('treatment_forms/radiation_form.html', 
                         form=form, 
                         patient=patient, 
                         title='Thêm xạ trị')

@app.route('/radiation/<int:radiation_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_radiation_event(radiation_id):
    """Sửa sự kiện xạ trị - Edit radiation event"""
    radiation = RadiationEvent.query.get_or_404(radiation_id)
    
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền sửa thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=radiation.patient_id))
    
    form = RadiationEventForm(obj=radiation)
    
    if form.validate_on_submit():
        form.populate_obj(radiation)
        db.session.commit()
        flash('Đã cập nhật thông tin xạ trị!', 'success')
        return redirect(url_for('patient_detail', patient_id=radiation.patient_id))
    
    return render_template('treatment_forms/radiation_form.html', 
                         form=form, 
                         patient=radiation.patient, 
                         title='Sửa xạ trị',
                         radiation=radiation)

@app.route('/radiation/<int:radiation_id>/delete', methods=['POST'])
@login_required
def delete_radiation_event(radiation_id):
    """Xóa sự kiện xạ trị - Delete radiation event"""
    radiation = RadiationEvent.query.get_or_404(radiation_id)
    
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền xóa thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=radiation.patient_id))
    
    patient_id = radiation.patient_id
    db.session.delete(radiation)
    db.session.commit()
    
    flash('Đã xóa thông tin xạ trị!', 'success')
    return redirect(url_for('patient_detail', patient_id=patient_id))

# Hormone Therapy Event Routes

@app.route('/patient/<int:patient_id>/hormone_therapy/add', methods=['GET', 'POST'])
@login_required
def add_hormone_therapy_event(patient_id):
    """Thêm sự kiện liệu pháp nội tiết - Add hormone therapy event"""
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền thêm thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    patient = Patient.query.get_or_404(patient_id)
    form = HormoneTherapyEventForm()
    
    if form.validate_on_submit():
        hormone_therapy_event = HormoneTherapyEvent(patient_id=patient_id)
        form.populate_obj(hormone_therapy_event)
        
        db.session.add(hormone_therapy_event)
        db.session.commit()
        flash('Đã thêm thông tin liệu pháp nội tiết!', 'success')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    return render_template('treatment_forms/hormone_therapy_form.html', 
                         form=form, 
                         patient=patient, 
                         title='Thêm liệu pháp nội tiết')

@app.route('/hormone_therapy/<int:hormone_therapy_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_hormone_therapy_event(hormone_therapy_id):
    """Sửa sự kiện liệu pháp nội tiết - Edit hormone therapy event"""
    hormone_therapy = HormoneTherapyEvent.query.get_or_404(hormone_therapy_id)
    
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền sửa thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=hormone_therapy.patient_id))
    
    form = HormoneTherapyEventForm(obj=hormone_therapy)
    
    if form.validate_on_submit():
        form.populate_obj(hormone_therapy)
        db.session.commit()
        flash('Đã cập nhật thông tin liệu pháp nội tiết!', 'success')
        return redirect(url_for('patient_detail', patient_id=hormone_therapy.patient_id))
    
    return render_template('treatment_forms/hormone_therapy_form.html', 
                         form=form, 
                         patient=hormone_therapy.patient, 
                         title='Sửa liệu pháp nội tiết',
                         hormone_therapy=hormone_therapy)

@app.route('/hormone_therapy/<int:hormone_therapy_id>/delete', methods=['POST'])
@login_required
def delete_hormone_therapy_event(hormone_therapy_id):
    """Xóa sự kiện liệu pháp nội tiết - Delete hormone therapy event"""
    hormone_therapy = HormoneTherapyEvent.query.get_or_404(hormone_therapy_id)
    
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền xóa thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=hormone_therapy.patient_id))
    
    patient_id = hormone_therapy.patient_id
    db.session.delete(hormone_therapy)
    db.session.commit()
    
    flash('Đã xóa thông tin liệu pháp nội tiết!', 'success')
    return redirect(url_for('patient_detail', patient_id=patient_id))

# Chemotherapy Event Routes

@app.route('/patient/<int:patient_id>/chemotherapy/add', methods=['GET', 'POST'])
@login_required
def add_chemotherapy_event(patient_id):
    """Thêm sự kiện hóa trị - Add chemotherapy event"""
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền thêm thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    patient = Patient.query.get_or_404(patient_id)
    form = ChemotherapyEventForm()
    
    if form.validate_on_submit():
        chemotherapy_event = ChemotherapyEvent(patient_id=patient_id)
        form.populate_obj(chemotherapy_event)
        
        db.session.add(chemotherapy_event)
        db.session.commit()
        flash('Đã thêm thông tin hóa trị!', 'success')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    return render_template('treatment_forms/chemotherapy_form.html', 
                         form=form, 
                         patient=patient, 
                         title='Thêm hóa trị')

@app.route('/chemotherapy/<int:chemotherapy_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_chemotherapy_event(chemotherapy_id):
    """Sửa sự kiện hóa trị - Edit chemotherapy event"""
    chemotherapy = ChemotherapyEvent.query.get_or_404(chemotherapy_id)
    
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền sửa thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=chemotherapy.patient_id))
    
    form = ChemotherapyEventForm(obj=chemotherapy)
    
    if form.validate_on_submit():
        form.populate_obj(chemotherapy)
        db.session.commit()
        flash('Đã cập nhật thông tin hóa trị!', 'success')
        return redirect(url_for('patient_detail', patient_id=chemotherapy.patient_id))
    
    return render_template('treatment_forms/chemotherapy_form.html', 
                         form=form, 
                         patient=chemotherapy.patient, 
                         title='Sửa hóa trị',
                         chemotherapy=chemotherapy)

@app.route('/chemotherapy/<int:chemotherapy_id>/delete', methods=['POST'])
@login_required
def delete_chemotherapy_event(chemotherapy_id):
    """Xóa sự kiện hóa trị - Delete chemotherapy event"""
    chemotherapy = ChemotherapyEvent.query.get_or_404(chemotherapy_id)
    
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền xóa thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=chemotherapy.patient_id))
    
    patient_id = chemotherapy.patient_id
    db.session.delete(chemotherapy)
    db.session.commit()
    
    flash('Đã xóa thông tin hóa trị!', 'success')
    return redirect(url_for('patient_detail', patient_id=patient_id))

# Systemic Therapy Event Routes

@app.route('/patient/<int:patient_id>/systemic_therapy/add', methods=['GET', 'POST'])
@login_required
def add_systemic_therapy_event(patient_id):
    """Thêm sự kiện liệu pháp toàn thân - Add systemic therapy event"""
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền thêm thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    patient = Patient.query.get_or_404(patient_id)
    form = SystemicTherapyEventForm()
    
    if form.validate_on_submit():
        systemic_therapy_event = SystemicTherapyEvent(patient_id=patient_id)
        form.populate_obj(systemic_therapy_event)
        
        db.session.add(systemic_therapy_event)
        db.session.commit()
        flash('Đã thêm thông tin liệu pháp toàn thân!', 'success')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    return render_template('treatment_forms/systemic_therapy_form.html', 
                         form=form, 
                         patient=patient, 
                         title='Thêm liệu pháp toàn thân')

@app.route('/systemic_therapy/<int:systemic_therapy_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_systemic_therapy_event(systemic_therapy_id):
    """Sửa sự kiện liệu pháp toàn thân - Edit systemic therapy event"""
    systemic_therapy = SystemicTherapyEvent.query.get_or_404(systemic_therapy_id)
    
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền sửa thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=systemic_therapy.patient_id))
    
    form = SystemicTherapyEventForm(obj=systemic_therapy)
    
    if form.validate_on_submit():
        form.populate_obj(systemic_therapy)
        db.session.commit()
        flash('Đã cập nhật thông tin liệu pháp toàn thân!', 'success')
        return redirect(url_for('patient_detail', patient_id=systemic_therapy.patient_id))
    
    return render_template('treatment_forms/systemic_therapy_form.html', 
                         form=form, 
                         patient=systemic_therapy.patient, 
                         title='Sửa liệu pháp toàn thân',
                         systemic_therapy=systemic_therapy)

@app.route('/systemic_therapy/<int:systemic_therapy_id>/delete', methods=['POST'])
@login_required
def delete_systemic_therapy_event(systemic_therapy_id):
    """Xóa sự kiện liệu pháp toàn thân - Delete systemic therapy event"""
    systemic_therapy = SystemicTherapyEvent.query.get_or_404(systemic_therapy_id)
    
    if not current_user.can_modify_patient():
        flash('Bạn không có quyền xóa thông tin điều trị.', 'error')
        return redirect(url_for('patient_detail', patient_id=systemic_therapy.patient_id))
    
    patient_id = systemic_therapy.patient_id
    db.session.delete(systemic_therapy)
    db.session.commit()
    
    flash('Đã xóa thông tin liệu pháp toàn thân!', 'success')
    return redirect(url_for('patient_detail', patient_id=patient_id))

# ============================================================================
# FOLLOW-UP AND ADVERSE EVENT MANAGEMENT ROUTES
# ============================================================================

@app.route('/patient/<int:patient_id>/followup')
@login_required
def patient_followup_dashboard(patient_id):
    """Trang tổng quan theo dõi bệnh nhân"""
    patient = Patient.query.get_or_404(patient_id)
    
    # Get PSA analysis
    psa_analysis = get_patient_psa_analysis(patient_id)
    
    # Get follow-up schedule
    followup_schedule = get_patient_followup_schedule(patient_id)
    
    # Get adverse events summary
    adverse_events_summary = get_treatment_adverse_events_summary(patient_id)
    
    # Get recent adverse events
    recent_adverse_events = AdverseEvent.query.filter_by(patient_id=patient_id)\
                                             .order_by(AdverseEvent.onset_date.desc())\
                                             .limit(5).all()
    
    return render_template('followup/dashboard.html',
                         patient=patient,
                         psa_analysis=psa_analysis,
                         followup_schedule=followup_schedule,
                         adverse_events_summary=adverse_events_summary,
                         recent_adverse_events=recent_adverse_events)

@app.route('/patient/<int:patient_id>/psa_analysis', methods=['GET', 'POST'])
@login_required
def psa_analysis(patient_id):
    """Phân tích PSA chi tiết"""
    patient = Patient.query.get_or_404(patient_id)
    form = PSAAnalysisForm()
    
    analysis_result = None
    
    if form.validate_on_submit():
        # Perform PSA analysis based on form parameters
        analysis_result = get_patient_psa_analysis(patient_id)
        
        # Check for alerts if enabled
        if form.enable_alerts.data:
            alert_result = check_and_alert_psa_changes(patient_id)
            if alert_result.get('alert_sent'):
                flash('Đã gửi cảnh báo PSA cho bệnh nhân và nhóm y tế.', 'info')
        
        flash('Phân tích PSA đã hoàn thành.', 'success')
    
    # Get current analysis if no form submission
    if not analysis_result:
        analysis_result = get_patient_psa_analysis(patient_id)
    
    return render_template('followup/psa_analysis.html',
                         patient=patient,
                         form=form,
                         analysis_result=analysis_result)

@app.route('/patient/<int:patient_id>/adverse_events')
@login_required
def adverse_events_list(patient_id):
    """Danh sách biến cố bất lợi"""
    patient = Patient.query.get_or_404(patient_id)
    page = request.args.get('page', 1, type=int)
    
    adverse_events = AdverseEvent.query.filter_by(patient_id=patient_id)\
                                      .order_by(AdverseEvent.onset_date.desc())\
                                      .paginate(page=page, per_page=10, error_out=False)
    
    # Get safety summary
    safety_summary = AdverseEventAnalyzer.analyze_treatment_safety_profile(patient_id)
    
    return render_template('followup/adverse_events_list.html',
                         patient=patient,
                         adverse_events=adverse_events,
                         safety_summary=safety_summary)

@app.route('/patient/<int:patient_id>/adverse_event/add', methods=['GET', 'POST'])
@login_required
def add_adverse_event(patient_id):
    """Thêm biến cố bất lợi"""
    patient = Patient.query.get_or_404(patient_id)
    form = AdverseEventForm()
    
    if form.validate_on_submit():
        # Determine event name
        event_name = form.event_name.data
        if event_name == 'other' and form.custom_event_name.data:
            event_name = form.custom_event_name.data
        
        event_data = {
            'treatment_type': form.treatment_type.data,
            'treatment_event_id': form.treatment_event_id.data or None,
            'event_name': event_name,
            'ctcae_term': event_name,  # Use event name as CTCAE term for custom events
            'category': form.category.data,
            'ctcae_grade': form.ctcae_grade.data,
            'grade_description': form.grade_description.data,
            'onset_date': form.onset_date.data,
            'resolution_date': form.resolution_date.data,
            'is_ongoing': form.is_ongoing.data,
            'severity_assessment': form.severity_assessment.data,
            'causality_assessment': form.causality_assessment.data,
            'action_taken': form.action_taken.data,
            'outcome': form.outcome.data,
            'treatment_modification': form.treatment_modification.data,
            'concomitant_medication': form.concomitant_medication.data,
            'notes': form.notes.data
        }
        
        try:
            adverse_event = AdverseEventManager.create_adverse_event(patient_id, event_data)
            flash('Đã thêm biến cố bất lợi thành công.', 'success')
            return redirect(url_for('adverse_events_list', patient_id=patient_id))
        except Exception as e:
            flash(f'Lỗi khi thêm biến cố: {str(e)}', 'error')
    
    return render_template('followup/adverse_event_form.html',
                         patient=patient,
                         form=form,
                         title='Thêm biến cố bất lợi')

# API endpoints for PSA trend data
@app.route('/api/patient/<int:patient_id>/psa_trend')
@login_required
def get_psa_trend_data(patient_id):
    """API endpoint để lấy dữ liệu xu hướng PSA"""
    analysis = get_patient_psa_analysis(patient_id)
    return jsonify(analysis)

# ============================================================================
# AI PREDICTION ROUTES
# ============================================================================

@app.route('/patient/<int:patient_id>/ai_predictions')
@login_required
def ai_predictions_dashboard(patient_id):
    """AI Prediction Dashboard cho bệnh nhân - Tối ưu hóa tốc độ"""
    patient = Patient.query.get_or_404(patient_id)
    
    try:
        # Import AI prediction functions với caching
        from ai_prediction import prediction_dashboard
        
        # Lấy tất cả dự báo với cache enabled
        start_time = datetime.now()
        predictions = prediction_dashboard.get_comprehensive_prediction(patient_id, use_cache=True)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Thêm thông tin hiệu suất
        predictions['total_processing_time'] = processing_time
        predictions['cache_status'] = prediction_dashboard.get_cache_status()
        
        return render_template('ai_predictions/dashboard.html',
                             patient=patient,
                             predictions=predictions)
                             
    except Exception as e:
        logger.error(f"Lỗi AI prediction dashboard: {str(e)}")
        flash(f'Lỗi tải dashboard AI: {str(e)}', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))

@app.route('/patient/<int:patient_id>/bcr_prediction', methods=['GET', 'POST'])
@login_required
def bcr_prediction(patient_id):
    """Dự báo nguy cơ tái phát sinh hóa"""
    patient = Patient.query.get_or_404(patient_id)
    form = BCRPredictionForm()
    
    prediction_result = None
    
    if form.validate_on_submit():
        # Thực hiện dự báo BCR với tối ưu hóa
        from ai_prediction import bcr_predictor
        prediction_result = bcr_predictor.predict_bcr_risk(patient_id)
        
        if prediction_result.get('status') == 'success':
            flash('Đã hoàn thành phân tích nguy cơ tái phát sinh hóa.', 'success')
        else:
            flash(f'Lỗi dự báo: {prediction_result.get("message", "Không xác định")}', 'error')
    
    return render_template('ai_predictions/bcr_prediction.html',
                         patient=patient,
                         form=form,
                         prediction_result=prediction_result)

@app.route('/patient/<int:patient_id>/adt_prediction', methods=['GET', 'POST'])
@login_required
def adt_prediction(patient_id):
    """Dự báo lợi ích từ liệu pháp nội tiết"""
    patient = Patient.query.get_or_404(patient_id)
    form = ADTPredictionForm()
    
    prediction_result = None
    
    if form.validate_on_submit():
        # Thực hiện dự báo ADT với tối ưu hóa
        from ai_prediction import adt_predictor
        prediction_result = adt_predictor.predict_adt_benefit(patient_id)
        
        if prediction_result.get('status') == 'success':
            flash('Đã hoàn thành phân tích lợi ích liệu pháp nội tiết.', 'success')
        else:
            flash(f'Lỗi dự báo: {prediction_result.get("message", "Không xác định")}', 'error')
    
    return render_template('ai_predictions/adt_prediction.html',
                         patient=patient,
                         form=form,
                         prediction_result=prediction_result)

@app.route('/patient/<int:patient_id>/adverse_event_prediction', methods=['GET', 'POST'])
@login_required
def adverse_event_prediction(patient_id):
    """Dự báo nguy cơ biến cố bất lợi"""
    patient = Patient.query.get_or_404(patient_id)
    form = AdverseEventPredictionForm()
    
    prediction_result = None
    
    if form.validate_on_submit():
        # Chuẩn bị chi tiết điều trị từ form
        treatment_details = {
            'treatment_type': form.treatment_type.data,
            'surgery_type': form.surgery_type.data,
            'radiation_type': form.radiation_type.data,
            'radiation_dose': form.radiation_dose.data,
            'hormone_drug': form.hormone_drug.data,
            'chemo_regimen': form.chemo_regimen.data,
            'age_group': form.age_group.data,
            'cardiovascular_risk': form.cardiovascular_risk.data,
            'diabetes_status': form.diabetes_status.data,
            'bone_health_status': form.bone_health_status.data,
            'previous_ae_concern': form.previous_ae_concern.data,
            'prediction_timeframe': form.prediction_timeframe.data
        }
        
        # Thực hiện dự báo
        prediction_result = get_adverse_event_prediction(
            patient_id, 
            form.treatment_type.data, 
            treatment_details
        )
        
        if prediction_result.get('status') == 'success':
            flash('Đã hoàn thành phân tích nguy cơ biến cố bất lợi.', 'success')
        else:
            flash(f'Lỗi dự báo: {prediction_result.get("message", "Không xác định")}', 'error')
    
    return render_template('ai_predictions/adverse_event_prediction.html',
                         patient=patient,
                         form=form,
                         prediction_result=prediction_result)

@app.route('/patient/<int:patient_id>/comprehensive_prediction', methods=['GET', 'POST'])
@login_required
def comprehensive_prediction(patient_id):
    """Phân tích dự báo tổng hợp"""
    patient = Patient.query.get_or_404(patient_id)
    form = ComprehensivePredictionForm()
    
    prediction_results = None
    
    if form.validate_on_submit():
        # Thực hiện các dự báo theo lựa chọn
        prediction_results = {}
        
        if form.include_bcr.data:
            prediction_results['bcr'] = get_patient_bcr_prediction(patient_id)
        
        if form.include_adt.data:
            prediction_results['adt'] = get_patient_adt_prediction(patient_id)
        
        # Có thể thêm adverse event prediction nếu cần
        
        flash('Đã hoàn thành phân tích dự báo tổng hợp.', 'success')
    
    return render_template('ai_predictions/comprehensive_prediction.html',
                         patient=patient,
                         form=form,
                         prediction_results=prediction_results)

@app.route('/ai_predictions/config', methods=['GET', 'POST'])
@login_required
def ai_prediction_config():
    """Cấu hình hệ thống dự báo AI"""
    if not current_user.has_permission('manage_system'):
        flash('Bạn không có quyền truy cập trang này.', 'error')
        return redirect(url_for('dashboard'))
    
    form = PredictionConfigForm()
    
    if form.validate_on_submit():
        # Lưu cấu hình (có thể lưu vào database hoặc file config)
        flash('Đã lưu cấu hình hệ thống dự báo AI.', 'success')
        return redirect(url_for('ai_prediction_config'))
    
    return render_template('ai_predictions/config.html', form=form)

# API endpoints cho AJAX requests
@app.route('/api/patient/<int:patient_id>/ai_predictions/bcr')
@login_required
def api_bcr_prediction(patient_id):
    """API endpoint cho dự báo BCR"""
    result = get_patient_bcr_prediction(patient_id)
    return jsonify(result)

@app.route('/api/patient/<int:patient_id>/ai_predictions/adt')
@login_required
def api_adt_prediction(patient_id):
    """API endpoint cho dự báo ADT"""
    result = get_patient_adt_prediction(patient_id)
    return jsonify(result)

@app.route('/api/ai_predictions/treatment_adverse_events/<treatment_type>')
@login_required
def api_treatment_adverse_events(treatment_type):
    """API endpoint để lấy danh sách biến cố bất lợi theo loại điều trị"""
    # Mapping các biến cố bất lợi phổ biến theo loại điều trị
    adverse_events_map = {
        'surgery': [
            'Tiểu không tự chủ', 'Rối loạn cương dương', 'Đau vết mổ',
            'Nhiễm trùng vết mổ', 'Chảy máu', 'Hẹp niệu đạo'
        ],
        'radiation': [
            'Viêm bàng quang xạ', 'Viêm trực tràng xạ', 'Mệt mỏi',
            'Rối loạn cương dương', 'Tiểu buốt', 'Đi ngoài máu'
        ],
        'hormone_therapy': [
            'Bốc hỏa', 'Giảm ham muốn tình dục', 'Mệt mỏi',
            'Loãng xương', 'Tăng cân', 'Trầm cảm'
        ],
        'chemotherapy': [
            'Buồn nôn và nôn', 'Rụng tóc', 'Giảm bạch cầu',
            'Mệt mỏi', 'Tê bì đầu ngón tay chân', 'Nhiễm trùng'
        ]
    }
    
    events = adverse_events_map.get(treatment_type, [])
    return jsonify({'events': events})

# Patient Deletion Route (Admin Only)
@app.route('/patient/<int:patient_id>/delete', methods=['POST'])
@login_required
def patient_delete(patient_id):
    """Xóa bệnh nhân - Admin only"""
    if not current_user.can_delete_patient():
        flash('Chỉ admin mới có quyền xóa bệnh nhân.', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    patient = Patient.query.get_or_404(patient_id)
    patient_name = patient.full_name
    
    try:
        # Delete all related records (cascade will handle most)
        # Delete blood tests
        BloodTest.query.filter_by(patient_id=patient_id).delete()
        
        # Delete imaging records
        ImagingRecord.query.filter_by(patient_id=patient_id).delete()
        
        # Delete patient events
        PatientEvent.query.filter_by(patient_id=patient_id).delete()
        
        # Delete adverse events
        AdverseEvent.query.filter_by(patient_id=patient_id).delete()
        
        # Delete follow-up schedules (if the model exists)
        try:
            from followup_management import FollowUpSchedule
            FollowUpSchedule.query.filter_by(patient_id=patient_id).delete()
        except ImportError:
            pass  # FollowUpSchedule model not available
        
        # Delete treatment events
        SurgeryEvent.query.filter_by(patient_id=patient_id).delete()
        RadiationEvent.query.filter_by(patient_id=patient_id).delete()
        HormoneTherapyEvent.query.filter_by(patient_id=patient_id).delete()
        ChemotherapyEvent.query.filter_by(patient_id=patient_id).delete()
        SystemicTherapyEvent.query.filter_by(patient_id=patient_id).delete()
        
        # Delete appointments
        Appointment.query.filter_by(patient_id=patient_id).delete()
        
        # Delete medication schedules for medications belonging to this patient's treatments
        for treatment in patient.treatments:
            for medication in treatment.medications:
                MedicationSchedule.query.filter_by(medication_id=medication.id).delete()
            # Delete medications
            Medication.query.filter_by(treatment_id=treatment.id).delete()
        
        # Delete treatments
        Treatment.query.filter_by(patient_id=patient_id).delete()
        
        # Finally delete the patient
        db.session.delete(patient)
        db.session.commit()
        
        flash(f'Đã xóa bệnh nhân {patient_name} và tất cả dữ liệu liên quan.', 'success')
        return redirect(url_for('patient_list'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa bệnh nhân: {str(e)}', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))

@app.route('/patient/<int:patient_id>/delete_confirm')
@login_required
def patient_delete_confirm(patient_id):
    """Trang xác nhận xóa bệnh nhân - Admin only"""
    if not current_user.can_delete_patient():
        flash('Chỉ admin mới có quyền xóa bệnh nhân.', 'error')
        return redirect(url_for('patient_detail', patient_id=patient_id))
    
    patient = Patient.query.get_or_404(patient_id)
    
    # Count related records
    blood_tests_count = BloodTest.query.filter_by(patient_id=patient_id).count()
    treatments_count = Treatment.query.filter_by(patient_id=patient_id).count()
    events_count = PatientEvent.query.filter_by(patient_id=patient_id).count()
    adverse_events_count = AdverseEvent.query.filter_by(patient_id=patient_id).count()
    appointments_count = Appointment.query.filter_by(patient_id=patient_id).count()
    
    related_data = {
        'blood_tests': blood_tests_count,
        'treatments': treatments_count,
        'events': events_count,
        'adverse_events': adverse_events_count,
        'appointments': appointments_count
    }
    
    # Create a form for CSRF token
    from forms import PatientForm
    dummy_form = PatientForm()
    
    return render_template('patient_delete_confirm.html', 
                         patient=patient, 
                         related_data=related_data,
                         csrf_token=dummy_form.csrf_token)

@app.route('/patients/bulk_delete', methods=['POST'])
@login_required
def bulk_delete_patients():
    """Xóa nhiều bệnh nhân cùng lúc - Admin only"""
    if not current_user.can_delete_patient():
        flash('Chỉ admin mới có quyền xóa bệnh nhân.', 'error')
        return redirect(url_for('patient_list'))
    
    patient_ids = request.form.getlist('patient_ids')
    
    if not patient_ids:
        flash('Vui lòng chọn ít nhất một bệnh nhân để xóa.', 'error')
        return redirect(url_for('patient_list'))
    
    try:
        deleted_count = 0
        deleted_names = []
        
        for patient_id in patient_ids:
            patient = Patient.query.get(patient_id)
            if patient:
                # Delete related data first
                BloodTest.query.filter_by(patient_id=patient_id).delete()
                Treatment.query.filter_by(patient_id=patient_id).delete()
                PatientEvent.query.filter_by(patient_id=patient_id).delete()
                AdverseEvent.query.filter_by(patient_id=patient_id).delete()
                Appointment.query.filter_by(patient_id=patient_id).delete()
                ImagingRecord.query.filter_by(patient_id=patient_id).delete()
                
                # Delete all treatment events
                SurgeryEvent.query.filter_by(patient_id=patient_id).delete()
                RadiationEvent.query.filter_by(patient_id=patient_id).delete()
                HormoneTherapyEvent.query.filter_by(patient_id=patient_id).delete()
                ChemotherapyEvent.query.filter_by(patient_id=patient_id).delete()
                SystemicTherapyEvent.query.filter_by(patient_id=patient_id).delete()
                
                # Delete follow-up schedules and PSA analysis
                FollowUpSchedule.query.filter_by(patient_id=patient_id).delete()
                PSAAnalysis.query.filter_by(patient_id=patient_id).delete()
                
                deleted_names.append(f"{patient.patient_code} - {patient.full_name}")
                
                # Finally delete the patient
                db.session.delete(patient)
                deleted_count += 1
        
        db.session.commit()
        
        if deleted_count > 0:
            flash(f'Đã xóa thành công {deleted_count} bệnh nhân và toàn bộ dữ liệu liên quan.', 'success')
            
            # Log deleted patients for admin reference
            app.logger.info(f"Admin {current_user.username} deleted {deleted_count} patients: {', '.join(deleted_names)}")
        else:
            flash('Không có bệnh nhân nào được xóa.', 'warning')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi xóa bệnh nhân: {str(e)}', 'error')
        app.logger.error(f"Error in bulk delete patients: {str(e)}")
    
    return redirect(url_for('patient_list'))

@app.route('/admin/clear_all_data', methods=['GET', 'POST'])
@login_required
def clear_all_data():
    """Xóa toàn bộ dữ liệu bệnh nhân - Admin only"""
    if not current_user.can_delete_patient():
        flash('Chỉ admin mới có quyền thực hiện chức năng này.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        confirm = request.form.get('confirm')
        if confirm == 'DELETE_ALL_DATA':
            try:
                # Count existing data before deletion
                patient_count = Patient.query.count()
                
                # Delete all related data first (in correct order to avoid foreign key constraints)
                # Delete appointments first (they reference medication_schedule)
                db.session.execute(text("DELETE FROM appointment"))
                
                # Delete medication_schedule and related data
                db.session.execute(text("DELETE FROM medication_schedule"))
                db.session.execute(text("DELETE FROM medication"))
                db.session.execute(text("DELETE FROM blood_test"))
                db.session.execute(text("DELETE FROM imaging_record"))
                db.session.execute(text("DELETE FROM patient_event"))
                
                # Delete adverse events (note: table name is adverse_events, not adverse_event)
                db.session.execute(text("DELETE FROM adverse_events"))
                
                # Delete treatment events
                db.session.execute(text("DELETE FROM surgery_event"))
                db.session.execute(text("DELETE FROM radiation_event"))
                db.session.execute(text("DELETE FROM hormone_therapy_event"))
                db.session.execute(text("DELETE FROM chemotherapy_event"))
                db.session.execute(text("DELETE FROM systemic_therapy_event"))
                db.session.execute(text("DELETE FROM treatment_event"))
                
                # Delete treatments
                db.session.execute(text("DELETE FROM treatment"))
                
                # Finally delete patients
                db.session.execute(text("DELETE FROM patient"))
                
                db.session.commit()
                
                flash(f'Đã xóa thành công toàn bộ {patient_count} bệnh nhân và tất cả dữ liệu liên quan.', 'success')
                app.logger.info(f"Admin {current_user.username} cleared all patient data ({patient_count} patients)")
                
            except Exception as e:
                db.session.rollback()
                flash(f'Lỗi khi xóa dữ liệu: {str(e)}', 'error')
                app.logger.error(f"Error clearing all data: {str(e)}")
        else:
            flash('Vui lòng nhập đúng mã xác nhận để tiếp tục.', 'error')
    
    # Get current data count
    patient_count = Patient.query.count()
    blood_test_count = BloodTest.query.count()
    treatment_count = Treatment.query.count()
    appointment_count = Appointment.query.count()
    
    return render_template('admin_clear_data.html',
                         patient_count=patient_count,
                         blood_test_count=blood_test_count,
                         treatment_count=treatment_count,
                         appointment_count=appointment_count)



# Create appointment from AI recommendations
@app.route('/patient/<int:patient_id>/create_appointment_from_ai', methods=['POST'])
@login_required
def create_appointment_from_ai(patient_id):
    """Tạo lịch hẹn dựa trên khuyến nghị AI"""
    patient = Patient.query.get_or_404(patient_id)
    
    recommendation_type = request.form.get('recommendation_type')
    prediction_data = request.form.get('prediction_data')
    
    try:
        import json
        pred_data = json.loads(prediction_data) if prediction_data else {}
    except:
        pred_data = {}
    
    # Determine appointment details based on recommendation type
    appointment_details = {}
    
    if recommendation_type == 'bcr_followup':
        # BCR follow-up appointment
        appointment_details = {
            'appointment_type': 'Tái khám theo dõi BCR',
            'description': 'Theo dõi nguy cơ tái phát sinh hóa dựa trên phân tích AI',
            'recommended_date': datetime.now() + timedelta(days=30),  # 1 month follow-up
            'notes': 'Khuyến nghị từ phân tích AI BCR: Theo dõi PSA định kỳ'
        }
        
    elif recommendation_type == 'blood_test':
        # Blood test appointment  
        appointment_details = {
            'appointment_type': 'Xét nghiệm máu',
            'description': 'Xét nghiệm PSA và các chỉ số liên quan theo khuyến nghị AI',
            'recommended_date': datetime.now() + timedelta(days=14),  # 2 weeks for blood test
            'notes': 'Khuyến nghị xét nghiệm từ phân tích AI: PSA, Testosterone, CBC'
        }
        
    elif recommendation_type == 'adt_monitoring':
        # ADT monitoring appointment
        appointment_details = {
            'appointment_type': 'Theo dõi điều trị nội tiết',
            'description': 'Theo dõi hiệu quả và tác dụng phụ của liệu pháp nội tiết',
            'recommended_date': datetime.now() + timedelta(days=90),  # 3 months for ADT monitoring
            'notes': 'Khuyến nghị từ phân tích ADT AI: Theo dõi PSA, Testosterone, tác dụng phụ'
        }
        
    elif recommendation_type == 'followup':
        # General follow-up
        appointment_details = {
            'appointment_type': 'Tái khám tổng quát',
            'description': 'Tái khám theo khuyến nghị tổng hợp từ phân tích AI',
            'recommended_date': datetime.now() + timedelta(days=60),  # 2 months general follow-up
            'notes': 'Khuyến nghị từ dashboard AI: Đánh giá tổng quan tình trạng bệnh nhân'
        }
        
    else:
        flash('Loại khuyến nghị không hợp lệ.', 'error')
        return redirect(url_for('ai_predictions_dashboard', patient_id=patient_id))
    
    # Create new appointment
    appointment = Appointment(
        patient_id=patient_id,
        appointment_date=appointment_details['recommended_date'],
        appointment_type=appointment_details['appointment_type'],
        description=appointment_details['description'],
        status='scheduled',
        notes=appointment_details['notes'],
        created_by=current_user.id,
        ai_generated=True,
        recommendation_source=recommendation_type
    )
    
    try:
        db.session.add(appointment)
        db.session.commit()
        
        flash(f'Đã tạo lịch hẹn {appointment_details["appointment_type"]} thành công cho ngày {appointment_details["recommended_date"].strftime("%d/%m/%Y")}.', 'success')
        
        # Redirect back to referrer or AI dashboard if no referrer
        next_page = request.form.get('next') or request.referrer
        if next_page and 'ai_predictions' in next_page:
            return redirect(next_page)
        else:
            return redirect(url_for('ai_predictions_dashboard', patient_id=patient_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi khi tạo lịch hẹn: {str(e)}', 'error')
        return redirect(url_for('ai_predictions_dashboard', patient_id=patient_id))

# Enhanced appointment creation with AI integration
@app.route('/patient/<int:patient_id>/smart_appointment', methods=['GET', 'POST'])
@login_required
def smart_appointment_creation(patient_id):
    """Tạo lịch hẹn thông minh dựa trên AI và lịch sử bệnh nhân"""
    patient = Patient.query.get_or_404(patient_id)
    form = AppointmentForm()
    
    # Get AI recommendations for this patient
    try:
        from ai_prediction import prediction_dashboard
        ai_recommendations = prediction_dashboard.get_comprehensive_prediction(patient_id, use_cache=True)
    except:
        ai_recommendations = None
    
    # Get recent appointments and blood tests for context
    recent_appointments = Appointment.query.filter_by(patient_id=patient_id)\
                                          .order_by(Appointment.appointment_date.desc())\
                                          .limit(5).all()
    
    recent_blood_tests = BloodTest.query.filter_by(patient_id=patient_id)\
                                       .order_by(BloodTest.test_date.desc())\
                                       .limit(3).all()
    
    if form.validate_on_submit():
        appointment = Appointment(
            patient_id=patient_id,
            appointment_date=form.appointment_date.data,
            appointment_type=form.appointment_type.data,
            description=form.description.data,
            status='scheduled',
            notes=form.notes.data,
            created_by=current_user.id
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        flash('Đã tạo lịch hẹn thành công.', 'success')
        return redirect(url_for('patient_appointments', patient_id=patient_id))
    
    return render_template('smart_appointment_form.html',
                         patient=patient,
                         form=form,
                         ai_recommendations=ai_recommendations,
                         recent_appointments=recent_appointments,
                         recent_blood_tests=recent_blood_tests)

# Health check endpoint for Google Cloud deployment
@app.route("/health")
def health_check():
    """Health check endpoint for deployment monitoring"""
    try:
        # Check database connection
        db.session.execute("SELECT 1")
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0",
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "database": "disconnected"
        }), 503

