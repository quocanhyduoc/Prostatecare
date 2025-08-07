from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DateField, DateTimeField, FloatField, SelectField, BooleanField, IntegerField, TimeField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, Email, EqualTo
from wtforms.widgets import TextInput
from datetime import datetime

class LoginForm(FlaskForm):
    """Form đăng nhập - Login form"""
    username = StringField('Tên đăng nhập', validators=[DataRequired(), Length(1, 80)])
    password = PasswordField('Mật khẩu', validators=[DataRequired()])
    remember_me = BooleanField('Ghi nhớ đăng nhập')

class UserForm(FlaskForm):
    """Form tạo/sửa người dùng - User creation/edit form"""
    
    # Thông tin đăng nhập - Login information
    username = StringField('Tên đăng nhập', validators=[DataRequired(), Length(1, 80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 120)])
    password = PasswordField('Mật khẩu', validators=[DataRequired(), Length(8, 256)])
    password_confirm = PasswordField('Xác nhận mật khẩu', 
                                   validators=[DataRequired(), EqualTo('password', message='Mật khẩu không khớp')])
    
    # Thông tin cá nhân - Personal information
    full_name = StringField('Họ và tên', validators=[DataRequired(), Length(1, 100)])
    phone = StringField('Số điện thoại', validators=[Optional(), Length(0, 15)])
    role = SelectField('Vai trò', 
                      choices=[('nurse', 'Y tá'),
                              ('doctor', 'Bác sĩ'),
                              ('admin', 'Quản trị viên')],
                      validators=[DataRequired()])
    department = StringField('Khoa', validators=[Optional(), Length(0, 50)])
    employee_id = StringField('Mã nhân viên', validators=[Optional(), Length(0, 20)])
    
    # Trạng thái tài khoản - Account status
    active = BooleanField('Tài khoản hoạt động', default=True)

class UserEditForm(FlaskForm):
    """Form sửa người dùng - User edit form (without password)"""
    
    # Thông tin đăng nhập - Login information
    username = StringField('Tên đăng nhập', validators=[DataRequired(), Length(1, 80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(1, 120)])
    
    # Thông tin cá nhân - Personal information
    full_name = StringField('Họ và tên', validators=[DataRequired(), Length(1, 100)])
    phone = StringField('Số điện thoại', validators=[Optional(), Length(0, 15)])
    role = SelectField('Vai trò', 
                      choices=[('nurse', 'Y tá'),
                              ('doctor', 'Bác sĩ'),
                              ('admin', 'Quản trị viên')],
                      validators=[DataRequired()])
    department = StringField('Khoa', validators=[Optional(), Length(0, 50)])
    employee_id = StringField('Mã nhân viên', validators=[Optional(), Length(0, 20)])
    
    # Trạng thái tài khoản - Account status
    active = BooleanField('Tài khoản hoạt động', default=True)

class ChangePasswordForm(FlaskForm):
    """Form đổi mật khẩu - Change password form"""
    current_password = PasswordField('Mật khẩu hiện tại', validators=[DataRequired()])
    new_password = PasswordField('Mật khẩu mới', validators=[DataRequired(), Length(8, 256)])
    confirm_password = PasswordField('Xác nhận mật khẩu mới', 
                                   validators=[DataRequired(), EqualTo('new_password', message='Mật khẩu không khớp')])

class PatientForm(FlaskForm):
    """Form tạo/sửa bệnh nhân - Patient creation/edit form"""
    
    # Thông tin hành chính - Administrative information
    patient_code = StringField('Mã bệnh nhân', validators=[DataRequired(), Length(1, 20)])
    full_name = StringField('Họ và tên', validators=[DataRequired(), Length(1, 100)])
    date_of_birth = DateField('Ngày sinh', validators=[DataRequired()])
    phone = StringField('Số điện thoại', validators=[Optional(), Length(0, 15)])
    address = TextAreaField('Địa chỉ', validators=[Optional()])
    insurance_number = StringField('Số BHYT', validators=[Optional(), Length(0, 20)])
    
    # Thông tin chẩn đoán ban đầu - Initial diagnosis information
    diagnosis_date = DateField('Ngày chẩn đoán', validators=[DataRequired()])
    gleason_score = StringField('Điểm Gleason', validators=[Optional(), Length(0, 10)])
    cancer_stage = StringField('Giai đoạn ung thư', validators=[Optional(), Length(0, 10)])
    initial_psa = FloatField('PSA ban đầu (ng/mL)', validators=[Optional(), NumberRange(min=0)])
    
    # Phương pháp lấy mẫu - Sampling method
    sampling_method = SelectField('Phương pháp lấy mẫu', 
                                 choices=[('', 'Chọn phương pháp'),
                                         ('TURP', 'TURP'),
                                         ('TRUS_BIOPSY', 'TRUS BIOPSY')],
                                 validators=[Optional()])
    sampling_date = DateField('Ngày lấy mẫu', validators=[Optional()])
    
    # TNM Clinical Staging - Phân giai đoạn TNM lâm sàng
    clinical_t = SelectField('T (Khối u) - Lâm sàng', 
                            choices=[('', 'Chọn giai đoạn T'),
                                   ('T1a', 'T1a'), ('T1b', 'T1b'), ('T1c', 'T1c'),
                                   ('T2a', 'T2a'), ('T2b', 'T2b'), ('T2c', 'T2c'),
                                   ('T3a', 'T3a'), ('T3b', 'T3b'),
                                   ('T4', 'T4')],
                            validators=[Optional()])
    clinical_n = SelectField('N (Hạch) - Lâm sàng', 
                            choices=[('', 'Chọn giai đoạn N'),
                                   ('N0', 'N0 - Không có hạch'),
                                   ('N1', 'N1 - Có hạch vùng')],
                            validators=[Optional()])
    clinical_m = SelectField('M (Di căn) - Lâm sàng', 
                            choices=[('', 'Chọn giai đoạn M'),
                                   ('M0', 'M0 - Không di căn'),
                                   ('M1a', 'M1a - Di căn hạch xa'),
                                   ('M1b', 'M1b - Di căn xương'),
                                   ('M1c', 'M1c - Di căn cơ quan khác')],
                            validators=[Optional()])
    
    # TNM Pathological Staging - Phân giai đoạn TNM giải phẫu bệnh
    pathological_t = SelectField('T (Khối u) - Giải phẫu bệnh', 
                                choices=[('', 'Chọn giai đoạn pT'),
                                       ('pT2a', 'pT2a'), ('pT2b', 'pT2b'), ('pT2c', 'pT2c'),
                                       ('pT3a', 'pT3a'), ('pT3b', 'pT3b'),
                                       ('pT4', 'pT4')],
                                validators=[Optional()])
    pathological_n = SelectField('N (Hạch) - Giải phẫu bệnh', 
                                choices=[('', 'Chọn giai đoạn pN'),
                                       ('pN0', 'pN0 - Không có hạch'),
                                       ('pN1', 'pN1 - Có hạch vùng')],
                                validators=[Optional()])
    pathological_m = SelectField('M (Di căn) - Giải phẫu bệnh', 
                                choices=[('', 'Chọn giai đoạn pM'),
                                       ('pM0', 'pM0 - Không di căn'),
                                       ('pM1', 'pM1 - Có di căn')],
                                validators=[Optional()])
    
    # Pathology Image Upload - Upload hình ảnh giải phẫu bệnh
    pathology_image = FileField('Hình ảnh giải phẫu bệnh',
                               validators=[Optional(), 
                                         FileAllowed(['jpg', 'jpeg', 'png'], 
                                                   'Chỉ cho phép file JPG, JPEG, PNG')])

class TreatmentForm(FlaskForm):
    """Form tạo/sửa điều trị - Treatment creation/edit form"""
    
    treatment_name = StringField('Tên phác đồ điều trị', validators=[DataRequired(), Length(1, 100)])
    start_date = DateField('Ngày bắt đầu', validators=[DataRequired()])
    end_date = DateField('Ngày kết thúc', validators=[Optional()])
    is_active = BooleanField('Đang điều trị', default=True)
    notes = TextAreaField('Ghi chú', validators=[Optional()])

class MedicationForm(FlaskForm):
    """Form tạo/sửa thuốc - Medication creation/edit form"""
    
    drug_name = StringField('Tên thuốc', validators=[DataRequired(), Length(1, 100)])
    dosage = StringField('Liều lượng', validators=[Optional(), Length(0, 50)])
    frequency = StringField('Tần suất', validators=[Optional(), Length(0, 50)])
    route = SelectField('Đường dùng', 
                       choices=[('', 'Chọn đường dùng'),
                               ('Uống', 'Uống'),
                               ('Tiêm', 'Tiêm'),
                               ('Bôi', 'Bôi'),
                               ('Nhỏ', 'Nhỏ')],
                       validators=[Optional()])
    start_date = DateField('Ngày bắt đầu', validators=[DataRequired()])
    end_date = DateField('Ngày kết thúc', validators=[Optional()])
    is_active = BooleanField('Đang sử dụng', default=True)
    notes = TextAreaField('Ghi chú', validators=[Optional()])

class BloodTestForm(FlaskForm):
    """Form tạo/sửa xét nghiệm máu - Blood test creation/edit form"""
    
    test_date = DateField('Ngày xét nghiệm', validators=[DataRequired()])
    free_psa = FloatField('FREE PSA (ng/mL)', validators=[Optional(), NumberRange(min=0)])
    total_psa = FloatField('TOTAL PSA (ng/mL)', validators=[Optional(), NumberRange(min=0)])
    testosterone = FloatField('Nồng độ Testosterone (ng/dL)', validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField('Ghi chú', validators=[Optional()])

class ImagingForm(FlaskForm):
    """Form tạo/sửa chẩn đoán hình ảnh - Imaging record creation/edit form"""
    
    imaging_type = SelectField('Loại chẩn đoán', 
                              choices=[('', 'Chọn loại chẩn đoán'),
                                      ('CT', 'CT Scan'),
                                      ('MRI', 'MRI'),
                                      ('BONE_SCAN', 'Bone Scan'),
                                      ('ULTRASOUND', 'Siêu âm'),
                                      ('X_RAY', 'X-quang')],
                              validators=[DataRequired()])
    imaging_date = DateField('Ngày chẩn đoán', validators=[DataRequired()])
    findings = TextAreaField('Kết quả', validators=[Optional()])
    impression = TextAreaField('Kết luận', validators=[Optional()])
    contrast_used = BooleanField('Sử dụng thuốc cản quang')
    radiologist = StringField('Bác sĩ đọc phim', validators=[Optional(), Length(0, 100)])

class EventForm(FlaskForm):
    """Form tạo/sửa sự kiện - Event creation/edit form"""
    
    event_date = DateField('Ngày sự kiện', validators=[DataRequired()])
    event_type = SelectField('Loại sự kiện',
                            choices=[('', 'Chọn loại sự kiện'),
                                    ('CHECKUP', 'Khám định kỳ'),
                                    ('COMPLICATION', 'Biến chứng'),
                                    ('TREATMENT_CHANGE', 'Thay đổi điều trị'),
                                    ('HOSPITALIZATION', 'Nhập viện'),
                                    ('SURGERY', 'Phẫu thuật'),
                                    ('OTHER', 'Khác')],
                            validators=[DataRequired()])
    title = StringField('Tiêu đề', validators=[DataRequired(), Length(1, 200)])
    description = TextAreaField('Mô tả chi tiết', validators=[Optional()])
    priority = SelectField('Mức độ quan trọng',
                          choices=[('LOW', 'Thấp'),
                                  ('NORMAL', 'Bình thường'),
                                  ('HIGH', 'Cao'),
                                  ('URGENT', 'Khẩn cấp')],
                          default='NORMAL',
                          validators=[DataRequired()])
    status = SelectField('Trạng thái',
                        choices=[('OPEN', 'Mở'),
                                ('IN_PROGRESS', 'Đang xử lý'),
                                ('RESOLVED', 'Đã giải quyết')],
                        default='OPEN',
                        validators=[DataRequired()])

class MedicationScheduleForm(FlaskForm):
    """Form tạo/sửa lịch trình thuốc - Medication schedule creation/edit form"""
    
    scheduled_date = DateField('Ngày dự kiến sử dụng', validators=[DataRequired()])
    administered_date = DateField('Ngày thực tế sử dụng', validators=[Optional()])
    status = SelectField('Trạng thái',
                        choices=[('PENDING', 'Chờ xử lý'),
                                ('COMPLETED', 'Đã xử lý'),
                                ('POSTPONED', 'Hoãn')],
                        default='PENDING',  
                        validators=[DataRequired()])
    postpone_reason = TextAreaField('Lý do hoãn', validators=[Optional()])
    dosage_given = StringField('Liều lượng thực tế', validators=[Optional(), Length(0, 50)])
    administration_notes = TextAreaField('Ghi chú sử dụng thuốc', validators=[Optional()])

class AppointmentForm(FlaskForm):
    """Form tạo/sửa lịch hẹn tái khám - Appointment creation/edit form"""
    
    appointment_date = DateField('Ngày hẹn', validators=[DataRequired()])
    appointment_time = TimeField('Giờ hẹn', validators=[Optional()])
    appointment_type = SelectField('Loại lịch hẹn',
                                  choices=[('FOLLOW_UP', 'Tái khám'),
                                          ('MEDICATION', 'Sử dụng thuốc'),
                                          ('CONSULTATION', 'Tư vấn')],
                                  default='FOLLOW_UP',
                                  validators=[DataRequired()])
    purpose = StringField('Mục đích', validators=[Optional(), Length(0, 200)])
    notes = TextAreaField('Ghi chú', validators=[Optional()])
    status = SelectField('Trạng thái',
                        choices=[('SCHEDULED', 'Đã lên lịch'),
                                ('COMPLETED', 'Đã hoàn thành'),
                                ('CANCELLED', 'Đã hủy'),
                                ('RESCHEDULED', 'Đã dời lịch')],
                        default='SCHEDULED',
                        validators=[DataRequired()])

class ExcelImportForm(FlaskForm):
    excel_file = FileField('Tệp Excel (.xlsx)', 
                          validators=[DataRequired(message='Vui lòng chọn tệp Excel'),
                                    FileAllowed(['xlsx'], 'Chỉ chấp nhận tệp .xlsx')])
    submit = SubmitField('Nhập dữ liệu')

class LabIntegrationForm(FlaskForm):
    """Form cấu hình tích hợp lab - Lab integration configuration form"""
    external_lab_id = StringField('Mã bệnh nhân ngoài (Lab ID)', validators=[Optional(), Length(0, 50)])
    lab_system_type = SelectField('Hệ thống xét nghiệm', 
                                choices=[('', 'Chọn hệ thống...'),
                                        ('labcorp', 'LabCorp'),
                                        ('quest', 'Quest Diagnostics'),
                                        ('custom', 'Khác')],
                                validators=[Optional()])
    submit = SubmitField('Cập nhật')

class LabImportForm(FlaskForm):
    """Form nhập xét nghiệm từ lab - Lab import form"""
    lab_system = SelectField('Hệ thống lab', 
                            choices=[('labcorp', 'LabCorp'),
                                   ('quest', 'Quest Diagnostics')],
                            validators=[DataRequired()])
    patient_lab_id = StringField('Mã bệnh nhân trong hệ thống lab', 
                               validators=[DataRequired(), Length(1, 50)])
    import_days = SelectField('Nhập dữ liệu trong', 
                            choices=[('7', '7 ngày qua'),
                                   ('30', '30 ngày qua'),
                                   ('90', '90 ngày qua'),
                                   ('180', '6 tháng qua')],
                            default='30',
                            validators=[DataRequired()])
    submit = SubmitField('Nhập từ Lab')

class AppointmentForm(FlaskForm):
    """Form tạo lịch hẹn - Appointment creation form"""
    appointment_date = DateField('Ngày hẹn', 
                               validators=[DataRequired(message='Vui lòng chọn ngày hẹn')])
    appointment_time = TimeField('Giờ hẹn',
                               validators=[DataRequired(message='Vui lòng chọn giờ hẹn')])
    appointment_type = SelectField('Loại lịch hẹn',
                                 choices=[
                                     ('Tái khám', 'Tái khám'),
                                     ('Xét nghiệm', 'Xét nghiệm'),
                                     ('Tư vấn', 'Tư vấn'),
                                     ('Theo dõi điều trị nội tiết', 'Theo dõi ADT'),
                                     ('Tái khám theo dõi BCR', 'Theo dõi BCR'),
                                     ('Xét nghiệm máu', 'Xét nghiệm máu'),
                                     ('Tái khám tổng quát', 'Tái khám tổng quát')
                                 ],
                                 validators=[DataRequired(message='Vui lòng chọn loại lịch hẹn')])
    status = SelectField('Trạng thái',
                        choices=[
                            ('scheduled', 'Đã lên lịch'),
                            ('confirmed', 'Đã xác nhận'),
                            ('completed', 'Đã hoàn thành'),
                            ('cancelled', 'Đã hủy')
                        ],
                        default='scheduled',
                        validators=[DataRequired()])
    purpose = StringField('Mục đích khám',
                         validators=[Optional(), Length(0, 200)])
    description = TextAreaField('Mô tả', 
                              validators=[Optional(), Length(0, 500)],
                              render_kw={'rows': 3})
    notes = TextAreaField('Ghi chú',
                         validators=[Optional()],  
                         render_kw={'rows': 4})
    submit = SubmitField('Tạo lịch hẹn')
