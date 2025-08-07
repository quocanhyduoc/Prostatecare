"""
Follow-up and Adverse Event Management Forms
Forms để quản lý theo dõi và biến cố bất lợi
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, BooleanField, IntegerField, FloatField, HiddenField
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from datetime import date, datetime

class FollowUpScheduleForm(FlaskForm):
    """Form for scheduling follow-up appointments"""
    
    # Basic information
    followup_type = SelectField('Loại tái khám',
                               choices=[('routine', 'Định kỳ'),
                                       ('urgent', 'Khẩn cấp'),
                                       ('post_treatment', 'Sau điều trị'),
                                       ('psa_monitoring', 'Theo dõi PSA'),
                                       ('symptom_check', 'Kiểm tra triệu chứng')],
                               validators=[DataRequired()])
    
    scheduled_date = DateField('Ngày hẹn', validators=[DataRequired()])
    
    # Clinical reasoning
    reason = TextAreaField('Lý do tái khám', 
                          validators=[DataRequired(), Length(10, 500)],
                          render_kw={"rows": 3, "placeholder": "Mô tả lý do cần tái khám..."})
    
    priority = SelectField('Mức độ ưu tiên',
                          choices=[('low', 'Thấp'),
                                  ('moderate', 'Vừa'),
                                  ('high', 'Cao'),
                                  ('urgent', 'Khẩn cấp')],
                          validators=[DataRequired()])
    
    # Recommended tests/procedures
    recommended_tests = TextAreaField('Xét nghiệm/thủ thuật khuyến nghị',
                                     validators=[Optional()],
                                     render_kw={"rows": 2, "placeholder": "PSA, testosterone, imaging..."})
    
    # Notification preferences
    send_sms_reminder = BooleanField('Gửi SMS nhắc nhở', default=True)
    send_email_reminder = BooleanField('Gửi email nhắc nhở', default=True)
    reminder_days_before = IntegerField('Nhắc nhở trước (ngày)', 
                                       validators=[Optional(), NumberRange(min=1, max=30)], 
                                       default=1)
    
    # Notes
    notes = TextAreaField('Ghi chú thêm', 
                         validators=[Optional()],
                         render_kw={"rows": 2})

class PSAAnalysisForm(FlaskForm):
    """Form for PSA analysis and monitoring"""
    
    # Analysis parameters
    analysis_type = SelectField('Loại phân tích',
                               choices=[('trend', 'Xu hướng PSA'),
                                       ('doubling_time', 'Thời gian nhân đôi'),
                                       ('velocity', 'Vận tốc PSA'),
                                       ('comprehensive', 'Phân tích toàn diện')],
                               validators=[DataRequired()])
    
    # Alert settings
    enable_alerts = BooleanField('Bật cảnh báo tự động', default=True)
    psa_threshold = FloatField('Ngưỡng cảnh báo PSA (ng/mL)',
                              validators=[Optional(), NumberRange(min=0.1, max=100)],
                              default=4.0)
    
    doubling_time_threshold = IntegerField('Ngưỡng cảnh báo thời gian nhân đôi (tháng)',
                                          validators=[Optional(), NumberRange(min=1, max=60)],
                                          default=12)
    
    velocity_threshold = FloatField('Ngưỡng cảnh báo vận tốc (ng/mL/năm)',
                                   validators=[Optional(), NumberRange(min=0.1, max=10)],
                                   default=2.0)
    
    # Clinical context
    current_treatment = SelectField('Điều trị hiện tại',
                                   choices=[('', 'Không điều trị'),
                                           ('surveillance', 'Theo dõi tích cực'),
                                           ('hormone_therapy', 'Liệu pháp nội tiết'),
                                           ('chemotherapy', 'Hóa trị'),
                                           ('radiation', 'Xạ trị'),
                                           ('surgery_followup', 'Sau phẫu thuật')],
                                   validators=[Optional()])
    
    # AI analysis options
    request_ai_analysis = BooleanField('Yêu cầu phân tích AI', default=True)
    include_treatment_correlation = BooleanField('Bao gồm tương quan điều trị', default=True)

class AdverseEventForm(FlaskForm):
    """Form for reporting adverse events with CTCAE grading"""
    
    # Treatment correlation
    treatment_type = SelectField('Loại điều trị liên quan',
                                choices=[('surgery', 'Phẫu thuật'),
                                        ('radiation', 'Xạ trị'),
                                        ('hormone_therapy', 'Liệu pháp nội tiết'),
                                        ('chemotherapy', 'Hóa trị'),
                                        ('systemic_therapy', 'Liệu pháp toàn thân'),
                                        ('other', 'Khác')],
                                validators=[DataRequired()])
    
    treatment_event_id = HiddenField('ID sự kiện điều trị')
    
    # Event details
    event_name = SelectField('Tên biến cố',
                            choices=[],  # Will be populated dynamically based on treatment_type
                            validators=[DataRequired()])
    
    custom_event_name = StringField('Tên biến cố khác',
                                   validators=[Optional(), Length(1, 200)],
                                   render_kw={"placeholder": "Nếu chọn 'Khác' ở trên"})
    
    category = SelectField('Phân loại',
                          choices=[('genitourinary', 'Tiết niệu sinh dục'),
                                  ('gastrointestinal', 'Tiêu hóa'),
                                  ('sexual', 'Chức năng tình dục'),
                                  ('neurological', 'Thần kinh'),
                                  ('hematological', 'Huyết học'),
                                  ('cardiovascular', 'Tim mạch'),
                                  ('endocrine', 'Nội tiết'),
                                  ('musculoskeletal', 'Cơ xương khớp'),
                                  ('dermatological', 'Da liễu'),
                                  ('general', 'Toàn thân')],
                          validators=[DataRequired()])
    
    # CTCAE Grading
    ctcae_grade = SelectField('Độ nặng CTCAE',
                             choices=[('1', 'Độ 1 - Nhẹ'),
                                     ('2', 'Độ 2 - Trung bình'),
                                     ('3', 'Độ 3 - Nặng'),
                                     ('4', 'Độ 4 - Đe dọa tính mạng'),
                                     ('5', 'Độ 5 - Tử vong')],
                             validators=[DataRequired()])
    
    grade_description = TextAreaField('Mô tả độ nặng',
                                     validators=[Optional()],
                                     render_kw={"rows": 2, "placeholder": "Mô tả chi tiết triệu chứng theo độ nặng CTCAE"})
    
    # Timeline
    onset_date = DateField('Ngày khởi phát', validators=[DataRequired()])
    resolution_date = DateField('Ngày hết triệu chứng', validators=[Optional()])
    is_ongoing = BooleanField('Còn diễn ra', default=True)
    
    # Clinical assessment
    severity_assessment = SelectField('Đánh giá mức độ nghiêm trọng',
                                     choices=[('mild', 'Nhẹ'),
                                             ('moderate', 'Vừa'),
                                             ('severe', 'Nặng')],
                                     validators=[Optional()])
    
    causality_assessment = SelectField('Đánh giá mối liên quan với điều trị',
                                      choices=[('definite', 'Chắc chắn'),
                                              ('probable', 'Có thể'),
                                              ('possible', 'Khả năng'),
                                              ('unlikely', 'Không chắc'),
                                              ('unrelated', 'Không liên quan')],
                                      validators=[Optional()])
    
    # Management
    action_taken = SelectField('Biện pháp xử trí',
                              choices=[('', 'Chưa có'),
                                      ('observation', 'Theo dõi'),
                                      ('symptomatic_treatment', 'Điều trị triệu chứng'),
                                      ('dose_reduction', 'Giảm liều'),
                                      ('treatment_delay', 'Trì hoãn điều trị'),
                                      ('discontinuation', 'Ngừng điều trị'),
                                      ('hospitalization', 'Nhập viện')],
                              validators=[Optional()])
    
    treatment_modification = TextAreaField('Điều chỉnh điều trị',
                                          validators=[Optional()],
                                          render_kw={"rows": 2, "placeholder": "Mô tả cách điều chỉnh điều trị..."})
    
    concomitant_medication = TextAreaField('Thuốc đồng thời',
                                          validators=[Optional()],
                                          render_kw={"rows": 2, "placeholder": "Thuốc dùng để điều trị biến cố..."})
    
    outcome = SelectField('Kết quả',
                         choices=[('', 'Chưa xác định'),
                                 ('resolved', 'Khỏi hoàn toàn'),
                                 ('improved', 'Cải thiện'),
                                 ('stable', 'Ổn định'),
                                 ('worsened', 'Xấu đi'),
                                 ('ongoing', 'Còn tiếp diễn')],
                         validators=[Optional()])
    
    # Additional information
    notes = TextAreaField('Ghi chú thêm',
                         validators=[Optional()],
                         render_kw={"rows": 3, "placeholder": "Thông tin bổ sung về biến cố..."})

class NotificationSettingsForm(FlaskForm):
    """Form for configuring notification preferences"""
    
    # SMS Settings
    enable_sms = BooleanField('Bật thông báo SMS', default=True)
    sms_phone_number = StringField('Số điện thoại SMS',
                                  validators=[Optional(), Length(10, 15)],
                                  render_kw={"placeholder": "0901234567"})
    
    # Email Settings
    enable_email = BooleanField('Bật thông báo Email', default=True)
    email_address = StringField('Địa chỉ Email',
                               validators=[Optional(), Length(5, 120)],
                               render_kw={"placeholder": "patient@email.com"})
    
    # Notification Types
    followup_reminders = BooleanField('Nhắc nhở tái khám', default=True)
    psa_alerts = BooleanField('Cảnh báo PSA', default=True)
    adverse_event_notifications = BooleanField('Thông báo biến cố bất lợi', default=True)
    
    # Timing
    reminder_advance_days = IntegerField('Nhắc nhở trước (ngày)',
                                        validators=[Optional(), NumberRange(min=1, max=30)],
                                        default=1)
    
    psa_monitoring_frequency = SelectField('Tần suất theo dõi PSA',
                                          choices=[('monthly', 'Hàng tháng'),
                                                  ('quarterly', 'Mỗi quý'),
                                                  ('biannually', 'Mỗi nửa năm'),
                                                  ('annually', 'Hàng năm')],
                                          default='quarterly')

class FollowUpReportForm(FlaskForm):
    """Form for generating follow-up reports"""
    
    # Report type
    report_type = SelectField('Loại báo cáo',
                             choices=[('individual', 'Báo cáo cá nhân'),
                                     ('cohort', 'Báo cáo nhóm bệnh nhân'),
                                     ('safety', 'Báo cáo an toàn'),
                                     ('psa_trends', 'Báo cáo xu hướng PSA'),
                                     ('adverse_events', 'Báo cáo biến cố bất lợi')],
                             validators=[DataRequired()])
    
    # Date range
    start_date = DateField('Từ ngày', validators=[DataRequired()])
    end_date = DateField('Đến ngày', validators=[DataRequired()])
    
    # Filters
    treatment_type_filter = SelectField('Lọc theo điều trị',
                                       choices=[('', 'Tất cả'),
                                               ('surgery', 'Phẫu thuật'),
                                               ('radiation', 'Xạ trị'),
                                               ('hormone_therapy', 'Nội tiết'),
                                               ('chemotherapy', 'Hóa trị'),
                                               ('systemic_therapy', 'Liệu pháp toàn thân')],
                                       validators=[Optional()])
    
    risk_level_filter = SelectField('Lọc theo mức độ nguy cơ',
                                   choices=[('', 'Tất cả'),
                                           ('low', 'Thấp'),
                                           ('moderate', 'Vừa'),
                                           ('high', 'Cao'),
                                           ('urgent', 'Khẩn cấp')],
                                   validators=[Optional()])
    
    # Report options
    include_charts = BooleanField('Bao gồm biểu đồ', default=True)
    include_ai_analysis = BooleanField('Bao gồm phân tích AI', default=True)
    export_format = SelectField('Định dạng xuất',
                               choices=[('pdf', 'PDF'),
                                       ('excel', 'Excel'),
                                       ('html', 'HTML')],
                               default='pdf')

# Predefined adverse events for dynamic form population
ADVERSE_EVENTS_BY_TREATMENT = {
    'surgery': [
        ('erectile_dysfunction', 'Rối loạn cương dương'),
        ('urinary_incontinence', 'Tiểu không tự chủ'),
        ('urethral_stricture', 'Hẹp niệu đạo'),
        ('bleeding', 'Chảy máu'),
        ('infection', 'Nhiễm trùng'),
        ('other', 'Khác')
    ],
    'radiation': [
        ('radiation_cystitis', 'Viêm bàng quang do xạ'),
        ('radiation_proctitis', 'Viêm trực tràng do xạ'),
        ('fatigue', 'Mệt mỏi'),
        ('skin_reaction', 'Phản ứng da'),
        ('bowel_problems', 'Rối loạn ruột'),
        ('urinary_problems', 'Rối loạn tiểu tiện'),
        ('other', 'Khác')
    ],
    'hormone_therapy': [
        ('hot_flashes', 'Bốc hỏa'),
        ('osteoporosis', 'Loãng xương'),
        ('weight_gain', 'Tăng cân'),
        ('mood_changes', 'Thay đổi tâm trạng'),
        ('decreased_libido', 'Giảm ham muốn tình dục'),
        ('gynecomastia', 'To tuyến vú'),
        ('other', 'Khác')
    ],
    'chemotherapy': [
        ('nausea_vomiting', 'Buồn nôn, nôn'),
        ('leukopenia', 'Giảm bạch cầu'),
        ('anemia', 'Thiếu máu'),
        ('thrombocytopenia', 'Giảm tiểu cầu'),
        ('alopecia', 'Rụng tóc'),
        ('neuropathy', 'Tổn thương thần kinh'),
        ('other', 'Khác')
    ],
    'systemic_therapy': [
        ('skin_rash', 'Phát ban da'),
        ('hypertension', 'Tăng huyết áp'),
        ('diarrhea', 'Tiêu chảy'),
        ('fatigue', 'Mệt mỏi'),
        ('joint_pain', 'Đau khớp'),
        ('liver_toxicity', 'Độc tính gan'),
        ('other', 'Khác')
    ]
}

def get_adverse_events_for_treatment(treatment_type):
    """Get adverse events choices for a specific treatment type"""
    return ADVERSE_EVENTS_BY_TREATMENT.get(treatment_type, [('other', 'Khác')])