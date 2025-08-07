from datetime import datetime, date, timedelta
from app import db
from sqlalchemy import func
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """Người dùng hệ thống - System user model"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Thông tin đăng nhập - Login information
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Thông tin cá nhân - Personal information
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15))
    role = db.Column(db.String(20), nullable=False, default='nurse')  # doctor, nurse, admin
    department = db.Column(db.String(50))  # Khoa
    employee_id = db.Column(db.String(20), unique=True)  # Mã nhân viên
    
    # Trạng thái tài khoản - Account status
    active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        permissions = {
            'admin': ['read', 'write', 'delete', 'manage_users', 'export_data', 'system_config'],
            'doctor': ['read', 'write', 'delete', 'export_data'],
            'nurse': ['read', 'write']
        }
        return permission in permissions.get(self.role, [])
    
    def can_modify_patient(self):
        """Check if user can modify patient data"""
        return self.role in ['doctor', 'admin']
    
    def can_delete_records(self):
        """Check if user can delete records"""
        return self.role in ['doctor', 'admin']
    
    def can_manage_medications(self):
        """Check if user can manage medications"""
        return self.role in ['doctor', 'nurse', 'admin']
    
    def can_delete_patient(self):
        """Check if user can delete patients - Admin only"""
        return self.role == 'admin'
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}: {self.full_name} ({self.role})>'

class Patient(db.Model):
    """Bệnh nhân - Patient model"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Thông tin hành chính - Administrative information
    patient_code = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(15))
    
    @property
    def phone_number(self):
        """Alias for phone for compatibility"""
        return self.phone
    email = db.Column(db.String(120))  # For email notifications
    address = db.Column(db.Text)
    insurance_number = db.Column(db.String(20))
    
    # Thông tin chẩn đoán ban đầu - Initial diagnosis information
    diagnosis_date = db.Column(db.Date, nullable=False)
    gleason_score = db.Column(db.String(10))  # e.g., "3+4=7"
    cancer_stage = db.Column(db.String(10))   # e.g., "T2a", "T3b"
    initial_psa = db.Column(db.Float)
    
    # Phương pháp lấy mẫu tế bào - Cell sampling method
    sampling_method = db.Column(db.String(20))  # TURP or TRUS_BIOPSY
    sampling_date = db.Column(db.Date)
    
    # TNM Staging - Phân giai đoạn TNM
    clinical_t = db.Column(db.String(10))  # Clinical T stage
    clinical_n = db.Column(db.String(10))  # Clinical N stage  
    clinical_m = db.Column(db.String(10))  # Clinical M stage
    pathological_t = db.Column(db.String(10))  # Pathological T stage
    pathological_n = db.Column(db.String(10))  # Pathological N stage
    pathological_m = db.Column(db.String(10))  # Pathological M stage
    
    # Pathology Images - Hình ảnh giải phẫu bệnh
    pathology_image_path = db.Column(db.String(255))  # Path to uploaded image
    pathology_image_filename = db.Column(db.String(255))  # Original filename
    
    # AI Risk Assessment - Đánh giá nguy cơ bằng AI
    ai_risk_score = db.Column(db.String(20))  # LOW, MEDIUM, HIGH, VERY_HIGH
    ai_staging_result = db.Column(db.Text)  # AI analysis result
    ai_assessment_date = db.Column(db.DateTime)  # When AI assessment was performed
    
    # Lab Integration - Tích hợp hệ thống xét nghiệm
    external_lab_id = db.Column(db.String(50))  # External lab system patient ID
    lab_system_type = db.Column(db.String(20))  # labcorp, quest, etc.
    last_lab_import = db.Column(db.DateTime)  # Last successful lab import timestamp
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    treatments = db.relationship('Treatment', backref='patient', lazy=True, cascade='all, delete-orphan')
    treatment_events = db.relationship('TreatmentEvent', backref='patient', lazy=True, cascade='all, delete-orphan')
    surgery_events = db.relationship('SurgeryEvent', backref='patient', lazy=True, cascade='all, delete-orphan')
    radiation_events = db.relationship('RadiationEvent', backref='patient', lazy=True, cascade='all, delete-orphan')
    hormone_therapy_events = db.relationship('HormoneTherapyEvent', backref='patient', lazy=True, cascade='all, delete-orphan')
    chemotherapy_events = db.relationship('ChemotherapyEvent', backref='patient', lazy=True, cascade='all, delete-orphan')
    systemic_therapy_events = db.relationship('SystemicTherapyEvent', backref='patient', lazy=True, cascade='all, delete-orphan')
    blood_tests = db.relationship('BloodTest', backref='patient', lazy=True, cascade='all, delete-orphan')
    imaging_records = db.relationship('ImagingRecord', backref='patient', lazy=True, cascade='all, delete-orphan')
    events = db.relationship('PatientEvent', backref='patient', lazy=True, cascade='all, delete-orphan')
    medication_schedules = db.relationship('MedicationSchedule', back_populates='patient', lazy=True, cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', back_populates='patient', lazy=True, cascade='all, delete-orphan')
    adverse_events = db.relationship('AdverseEvent', backref='patient', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Patient {self.patient_code}: {self.full_name}>'
    
    @property
    def age(self):
        """Calculate current age"""
        today = datetime.now().date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def get_latest_blood_test(self):
        """Get most recent blood test"""
        return BloodTest.query.filter_by(patient_id=self.id).order_by(BloodTest.test_date.desc()).first()
    
    def get_current_treatment(self):
        """Get active treatment (legacy)"""
        return Treatment.query.filter_by(patient_id=self.id, is_active=True).first()
    
    def get_treatment_timeline(self):
        """Get comprehensive treatment timeline from all modalities"""
        # Collect all treatment events from different tables
        all_events = []
        
        # Add surgery events
        surgeries = SurgeryEvent.query.filter_by(patient_id=self.id).all()
        for surgery in surgeries:
            all_events.append({
                'type': 'SURGERY',
                'event': surgery,
                'start_date': surgery.start_date,
                'name': surgery.treatment_name,
                'status': surgery.status
            })
        
        # Add radiation events
        radiations = RadiationEvent.query.filter_by(patient_id=self.id).all()
        for radiation in radiations:
            all_events.append({
                'type': 'RADIATION',
                'event': radiation,
                'start_date': radiation.start_date,
                'name': radiation.treatment_name,
                'status': radiation.status
            })
        
        # Add hormone therapy events
        hormone_therapies = HormoneTherapyEvent.query.filter_by(patient_id=self.id).all()
        for ht in hormone_therapies:
            all_events.append({
                'type': 'HORMONE_THERAPY',
                'event': ht,
                'start_date': ht.start_date,
                'name': ht.treatment_name,
                'status': ht.status
            })
        
        # Add chemotherapy events
        chemotherapies = ChemotherapyEvent.query.filter_by(patient_id=self.id).all()
        for chemo in chemotherapies:
            all_events.append({
                'type': 'CHEMOTHERAPY',
                'event': chemo,
                'start_date': chemo.start_date,
                'name': chemo.treatment_name,
                'status': chemo.status
            })
        
        # Add systemic therapy events
        systemic_therapies = SystemicTherapyEvent.query.filter_by(patient_id=self.id).all()
        for st in systemic_therapies:
            all_events.append({
                'type': 'SYSTEMIC_THERAPY',
                'event': st,
                'start_date': st.start_date,
                'name': st.treatment_name,
                'status': st.status
            })
        
        # Sort by start date (most recent first)
        all_events.sort(key=lambda x: x['start_date'], reverse=True)
        return all_events
    
    def get_active_treatments(self):
        """Get currently active treatment events from all modalities"""
        active_events = []
        
        # Check all treatment types for active status
        for surgery in SurgeryEvent.query.filter_by(patient_id=self.id, status='ACTIVE').all():
            active_events.append(('SURGERY', surgery))
        
        for radiation in RadiationEvent.query.filter_by(patient_id=self.id, status='ACTIVE').all():
            active_events.append(('RADIATION', radiation))
        
        for ht in HormoneTherapyEvent.query.filter_by(patient_id=self.id, status='ACTIVE').all():
            active_events.append(('HORMONE_THERAPY', ht))
        
        for chemo in ChemotherapyEvent.query.filter_by(patient_id=self.id, status='ACTIVE').all():
            active_events.append(('CHEMOTHERAPY', chemo))
        
        for st in SystemicTherapyEvent.query.filter_by(patient_id=self.id, status='ACTIVE').all():
            active_events.append(('SYSTEMIC_THERAPY', st))
        
        return active_events
    
    def get_surgery_history(self):
        """Get all surgery events"""
        return SurgeryEvent.query.filter_by(patient_id=self.id).order_by(SurgeryEvent.start_date.desc()).all()
    
    def get_radiation_history(self):
        """Get all radiation therapy events"""
        return RadiationEvent.query.filter_by(patient_id=self.id).order_by(RadiationEvent.start_date.desc()).all()
    
    def get_hormone_therapy_history(self):
        """Get all hormone therapy events"""
        return HormoneTherapyEvent.query.filter_by(patient_id=self.id).order_by(HormoneTherapyEvent.start_date.desc()).all()
    
    def get_chemotherapy_history(self):
        """Get all chemotherapy events"""
        return ChemotherapyEvent.query.filter_by(patient_id=self.id).order_by(ChemotherapyEvent.start_date.desc()).all()
    
    def get_systemic_therapy_history(self):
        """Get all systemic therapy events"""
        return SystemicTherapyEvent.query.filter_by(patient_id=self.id).order_by(SystemicTherapyEvent.start_date.desc()).all()

class TreatmentEvent(db.Model):
    """Sự kiện điều trị - Treatment event base model"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    
    # Thông tin cơ bản - Basic information
    event_type = db.Column(db.String(30), nullable=False)  # SURGERY, RADIATION, ADT, CHEMOTHERAPY, SYSTEMIC
    treatment_name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    
    # Trạng thái - Status
    status = db.Column(db.String(20), default='PLANNED')  # PLANNED, ACTIVE, COMPLETED, CANCELLED
    
    # Metadata
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Polymorphic relationship
    __mapper_args__ = {
        'polymorphic_identity': 'base',
        'polymorphic_on': event_type
    }
    
    def __repr__(self):
        return f'<TreatmentEvent {self.treatment_name} for Patient {self.patient_id}>'

class SurgeryEvent(db.Model):
    """Phẫu thuật - Surgery event model"""
    __tablename__ = 'surgery_event'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    
    # Basic information inherited from TreatmentEvent concept
    treatment_name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='PLANNED')
    notes = db.Column(db.Text)
    
    # Thông tin phẫu thuật - Surgery details
    surgery_type = db.Column(db.String(50), nullable=False)  # OPEN, LAPAROSCOPIC, ROBOTIC
    procedure_name = db.Column(db.String(200), nullable=False)  # e.g., "Cắt tuyến tiền liệt hoàn toàn"
    surgeon = db.Column(db.String(100))
    
    # Kết quả giải phẫu bệnh - Pathology results
    pathology_date = db.Column(db.Date)
    surgical_margin_status = db.Column(db.String(20))  # NEGATIVE, POSITIVE, CLOSE
    lymph_node_status = db.Column(db.String(50))  # e.g., "0/12 hạch dương tính"
    extracapsular_extension = db.Column(db.Boolean)
    seminal_vesicle_invasion = db.Column(db.Boolean)
    
    # Thông tin bổ sung - Additional info
    operative_time = db.Column(db.Integer)  # minutes
    blood_loss = db.Column(db.Integer)  # mL
    complications = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SurgeryEvent {self.treatment_name} for Patient {self.patient_id}>'

class RadiationEvent(db.Model):
    """Xạ trị - Radiation therapy event model"""
    __tablename__ = 'radiation_event'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    
    # Basic information
    treatment_name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='PLANNED')
    notes = db.Column(db.Text)
    
    # Thông tin xạ trị - Radiation details
    radiation_type = db.Column(db.String(30), nullable=False)  # EXTERNAL, BRACHYTHERAPY, SBRT
    technique = db.Column(db.String(50))  # IMRT, VMAT, 3D-CRT, HDR, LDR
    
    # Liều lượng - Dosage
    total_dose = db.Column(db.Float)  # Gy
    dose_per_fraction = db.Column(db.Float)  # Gy
    number_of_fractions = db.Column(db.Integer)
    
    # Vùng chiếu xạ - Treatment areas
    treatment_areas = db.Column(db.Text)  # JSON or comma-separated
    planning_target_volume = db.Column(db.Float)  # cc
    
    # Thiết bị và kỹ thuật - Equipment and technique
    machine_type = db.Column(db.String(50))
    image_guidance = db.Column(db.String(50))  # IGRT technique
    
    # Tác dụng phụ - Side effects
    acute_toxicity = db.Column(db.Text)
    late_toxicity = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<RadiationEvent {self.treatment_name} for Patient {self.patient_id}>'

class HormoneTherapyEvent(db.Model):
    """Liệu pháp nội tiết (ADT) - Hormone therapy event model"""
    __tablename__ = 'hormone_therapy_event'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    
    # Basic information
    treatment_name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='PLANNED')
    notes = db.Column(db.Text)
    
    # Thông tin ADT - ADT details
    therapy_type = db.Column(db.String(30), nullable=False)  # CONTINUOUS, INTERMITTENT
    drug_class = db.Column(db.String(50))  # LHRH_AGONIST, LHRH_ANTAGONIST, ANTIANDROGEN
    
    # Thông tin thuốc - Drug information
    drug_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50))
    administration_route = db.Column(db.String(30))  # IM, SC, ORAL
    frequency = db.Column(db.String(50))  # "Mỗi 3 tháng", "Hàng ngày"
    
    # Chu kỳ điều trị - Treatment cycles
    cycle_length = db.Column(db.Integer)  # months
    off_treatment_period = db.Column(db.Integer)  # months for intermittent therapy
    
    # Theo dõi - Monitoring
    baseline_testosterone = db.Column(db.Float)  # ng/dL
    castration_achieved = db.Column(db.Boolean)
    castration_date = db.Column(db.Date)
    
    # Tác dụng phụ - Side effects
    side_effects = db.Column(db.Text)
    quality_of_life_impact = db.Column(db.String(20))  # MINIMAL, MODERATE, SEVERE
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<HormoneTherapyEvent {self.treatment_name} for Patient {self.patient_id}>'

class ChemotherapyEvent(db.Model):
    """Hóa trị - Chemotherapy event model"""
    __tablename__ = 'chemotherapy_event'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    
    # Basic information
    treatment_name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='PLANNED')
    notes = db.Column(db.Text)
    
    # Thông tin hóa trị - Chemotherapy details
    regimen_name = db.Column(db.String(100), nullable=False)  # e.g., "Docetaxel + Prednisone"
    indication = db.Column(db.String(100))  # e.g., "mCRPC", "Adjuvant"
    
    # Chu kỳ điều trị - Treatment cycles
    planned_cycles = db.Column(db.Integer)
    completed_cycles = db.Column(db.Integer, default=0)
    cycle_length = db.Column(db.Integer)  # days
    
    # Thông tin thuốc chính - Primary drug information
    primary_drug = db.Column(db.String(100))
    dose_per_cycle = db.Column(db.String(100))
    dose_modifications = db.Column(db.Text)
    
    # Đáp ứng điều trị - Treatment response
    response_evaluation = db.Column(db.String(30))  # CR, PR, SD, PD
    response_date = db.Column(db.Date)
    
    # Độc tính - Toxicity
    grade_3_4_toxicity = db.Column(db.Text)
    dose_delays = db.Column(db.Integer, default=0)
    dose_reductions = db.Column(db.Integer, default=0)
    
    # Nguyên nhân dừng điều trị - Discontinuation reason
    discontinuation_reason = db.Column(db.String(100))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ChemotherapyEvent {self.treatment_name} for Patient {self.patient_id}>'

class SystemicTherapyEvent(db.Model):
    """Liệu pháp toàn thân khác - Other systemic therapy event model"""
    __tablename__ = 'systemic_therapy_event'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    
    # Basic information
    treatment_name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='PLANNED')
    notes = db.Column(db.Text)
    
    # Thông tin liệu pháp - Therapy details
    therapy_class = db.Column(db.String(50), nullable=False)  # IMMUNOTHERAPY, TARGETED, BONE_TARGETED
    drug_name = db.Column(db.String(100), nullable=False)
    mechanism_of_action = db.Column(db.String(200))
    
    # Thông tin liều lượng - Dosing information
    dosage = db.Column(db.String(100))
    administration_route = db.Column(db.String(30))  # IV, SC, ORAL
    frequency = db.Column(db.String(50))
    
    # Theo dõi hiệu quả - Efficacy monitoring
    biomarkers_monitored = db.Column(db.Text)  # JSON or comma-separated
    response_criteria = db.Column(db.String(50))
    best_response = db.Column(db.String(30))
    
    # Quản lý tác dụng phụ - Adverse event management
    adverse_events = db.Column(db.Text)
    dose_modifications_required = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemicTherapyEvent {self.treatment_name} for Patient {self.patient_id}>'

# Keep the old Treatment model for backward compatibility but mark as deprecated
class Treatment(db.Model):
    """DEPRECATED - Điều trị cũ - Legacy treatment model - Use TreatmentEvent instead"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    
    # Thông tin điều trị - Treatment information
    treatment_name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    
    # Ghi chú - Notes
    notes = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    medications = db.relationship('Medication', backref='treatment', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Treatment {self.treatment_name} for Patient {self.patient_id}>'

class Medication(db.Model):
    """Thuốc - Medication model"""
    id = db.Column(db.Integer, primary_key=True)
    treatment_id = db.Column(db.Integer, db.ForeignKey('treatment.id'), nullable=False)
    
    # Thông tin thuốc - Medication information
    drug_name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50))  # e.g., "50mg"
    frequency = db.Column(db.String(50))  # e.g., "2 lần/ngày"
    route = db.Column(db.String(30))  # e.g., "Uống", "Tiêm"
    
    # Thời gian - Timing
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    
    # Ghi chú - Notes
    notes = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    schedules = db.relationship('MedicationSchedule', back_populates='medication', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Medication {self.drug_name} - {self.dosage}>'

class BloodTest(db.Model):
    """Xét nghiệm máu - Blood test model"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    
    # Thông tin xét nghiệm - Test information
    test_date = db.Column(db.Date, nullable=False)
    
    # Các chỉ số xét nghiệm - Test values
    free_psa = db.Column(db.Float)  # FREE PSA (ng/mL)
    total_psa = db.Column(db.Float)  # TOTAL PSA (ng/mL)
    testosterone = db.Column(db.Float)  # BLOOD TESTOSTERONE CONCENTRATION (ng/dL)
    
    # Tỷ lệ PSA - PSA ratio
    psa_ratio = db.Column(db.Float)  # Free/Total PSA ratio
    
    @property
    def psa_level(self):
        """Alias for total_psa for compatibility"""
        return self.total_psa
    
    # Ghi chú - Notes
    notes = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BloodTest {self.test_date} for Patient {self.patient_id}>'
    
    def calculate_psa_ratio(self):
        """Calculate PSA ratio if both values exist"""
        if self.free_psa and self.total_psa and self.total_psa > 0:
            self.psa_ratio = (self.free_psa / self.total_psa) * 100
        return self.psa_ratio

class ImagingRecord(db.Model):
    """Chẩn đoán hình ảnh - Imaging record model"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    
    # Thông tin chẩn đoán - Imaging information
    imaging_type = db.Column(db.String(20), nullable=False)  # CT, MRI, BONE_SCAN
    imaging_date = db.Column(db.Date, nullable=False)
    
    # Kết quả - Results
    findings = db.Column(db.Text)
    impression = db.Column(db.Text)
    
    # Thông tin kỹ thuật - Technical information
    contrast_used = db.Column(db.Boolean, default=False)
    radiologist = db.Column(db.String(100))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ImagingRecord {self.imaging_type} {self.imaging_date} for Patient {self.patient_id}>'

class PatientEvent(db.Model):
    """Sự kiện bệnh nhân - Patient event model"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    
    # Thông tin sự kiện - Event information
    event_date = db.Column(db.Date, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # e.g., "Khám định kỳ", "Biến chứng", "Thay đổi điều trị"
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Mức độ quan trọng - Priority level
    priority = db.Column(db.String(20), default='NORMAL')  # LOW, NORMAL, HIGH, URGENT
    
    # Trạng thái - Status
    status = db.Column(db.String(20), default='OPEN')  # OPEN, IN_PROGRESS, RESOLVED
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PatientEvent {self.title} for Patient {self.patient_id}>'

class MedicationSchedule(db.Model):
    """Lịch trình thuốc hàng tháng - Monthly medication schedule"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    
    # Thông tin lịch trình - Schedule information
    scheduled_date = db.Column(db.Date, nullable=False)  # Ngày dự kiến sử dụng thuốc
    administered_date = db.Column(db.Date)  # Ngày thực tế sử dụng thuốc
    
    # Trạng thái - Status
    status = db.Column(db.String(20), default='PENDING')  # PENDING, COMPLETED, POSTPONED
    postpone_reason = db.Column(db.Text)  # Lý do hoãn (nếu có)
    
    # Thông tin thuốc - Medication details
    dosage_given = db.Column(db.String(50))  # Liều lượng thực tế
    administration_notes = db.Column(db.Text)  # Ghi chú khi sử dụng thuốc
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='medication_schedules')
    medication = db.relationship('Medication', back_populates='schedules')
    
    def __repr__(self):
        return f'<MedicationSchedule {self.medication.drug_name if self.medication else "Unknown"} - {self.scheduled_date}>'
    
    @property
    def is_due_soon(self):
        """Check if medication is due within 1 day"""
        if self.status != 'PENDING':
            return False
        today = date.today()
        return (self.scheduled_date - today).days <= 1
    
    @property
    def is_overdue(self):
        """Check if medication is overdue"""
        if self.status != 'PENDING':
            return False
        return self.scheduled_date < date.today()

class Appointment(db.Model):
    """Lịch hẹn tái khám - Appointment model"""
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    medication_schedule_id = db.Column(db.Integer, db.ForeignKey('medication_schedule.id'))
    
    # Thông tin lịch hẹn - Appointment information
    appointment_date = db.Column(db.DateTime, nullable=False)  # Changed to DateTime for better compatibility
    appointment_type = db.Column(db.String(100), default='Tái khám')  # Support Vietnamese appointment types
    
    # Mục đích - Purpose and description
    description = db.Column(db.String(500))  # Description for AI-generated appointments
    purpose = db.Column(db.String(200))  # Backward compatibility
    notes = db.Column(db.Text)
    
    # Trạng thái - Status
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, rescheduled
    
    # AI Integration - Track if created by AI
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # User who created the appointment
    ai_generated = db.Column(db.Boolean, default=False)  # Track AI-generated appointments
    recommendation_source = db.Column(db.String(50))  # bcr, adt, followup, blood_test
    
    # Thông báo - Notification
    notification_sent = db.Column(db.Boolean, default=False)
    reminder_sent = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', back_populates='appointments')
    medication_schedule = db.relationship('MedicationSchedule', backref='appointment')
    creator = db.relationship('User', backref='created_appointments')
    
    def __repr__(self):
        return f'<Appointment {self.appointment_date} - {self.appointment_type} for Patient {self.patient_id}>'

class AdverseEvent(db.Model):
    """Biến cố bất lợi - Adverse Event model with CTCAE Integration"""
    __tablename__ = 'adverse_events'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    
    # Treatment correlation
    treatment_type = db.Column(db.String(50), nullable=False)  # surgery, radiation, hormone_therapy, etc.
    treatment_event_id = db.Column(db.Integer, nullable=True)  # ID of specific treatment event
    
    # Event details
    event_name = db.Column(db.String(200), nullable=False)
    ctcae_term = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(50), nullable=False)
    
    # CTCAE Grading
    ctcae_grade = db.Column(db.String(1), nullable=False)  # 1-5
    grade_description = db.Column(db.Text, nullable=True)
    
    # Timeline
    onset_date = db.Column(db.Date, nullable=False)
    resolution_date = db.Column(db.Date, nullable=True)
    is_ongoing = db.Column(db.Boolean, default=True)
    
    # Clinical details
    severity_assessment = db.Column(db.String(20), nullable=True)  # mild, moderate, severe
    causality_assessment = db.Column(db.String(30), nullable=True)  # definite, probable, possible, unlikely
    action_taken = db.Column(db.String(100), nullable=True)  # dose_reduction, treatment_delay, discontinuation
    outcome = db.Column(db.String(50), nullable=True)  # resolved, ongoing, worsened
    
    # Management
    treatment_modification = db.Column(db.Text, nullable=True)
    concomitant_medication = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AdverseEvent {self.event_name} Grade {self.ctcae_grade} for Patient {self.patient_id}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'treatment_type': self.treatment_type,
            'treatment_event_id': self.treatment_event_id,
            'event_name': self.event_name,
            'ctcae_term': self.ctcae_term,
            'category': self.category,
            'ctcae_grade': self.ctcae_grade,
            'grade_description': self.grade_description,
            'onset_date': self.onset_date.isoformat() if self.onset_date else None,
            'resolution_date': self.resolution_date.isoformat() if self.resolution_date else None,
            'is_ongoing': self.is_ongoing,
            'severity_assessment': self.severity_assessment,
            'causality_assessment': self.causality_assessment,
            'action_taken': self.action_taken,
            'outcome': self.outcome,
            'treatment_modification': self.treatment_modification,
            'concomitant_medication': self.concomitant_medication,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def is_upcoming(self):
        """Check if appointment is within next 7 days"""
        if self.status != 'SCHEDULED':
            return False
        today = date.today()
        days_until = (self.appointment_date - today).days
        return 0 <= days_until <= 7
    
    @property
    def needs_reminder(self):
        """Check if appointment needs reminder (1 day before)"""
        if self.status != 'SCHEDULED' or self.reminder_sent:
            return False
        today = date.today()
        return (self.appointment_date - today).days == 1
    
    @property
    def is_today(self):
        """Check if appointment is today"""
        return self.appointment_date == date.today()
    
    @property
    def is_overdue(self):
        """Check if appointment is overdue"""
        if self.status != 'SCHEDULED':
            return False
        return self.appointment_date < date.today()
