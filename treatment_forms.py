"""
Treatment Event Forms - Form xử lý các sự kiện điều trị chuyên biệt
Specialized forms for different treatment modalities in prostate cancer management
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, DateField, SelectField, TextAreaField, 
                     IntegerField, FloatField, BooleanField, SubmitField)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from datetime import date

class BaseTreatmentEventForm(FlaskForm):
    """Base form for treatment events"""
    treatment_name = StringField('Tên điều trị', validators=[DataRequired(), Length(1, 200)])
    start_date = DateField('Ngày bắt đầu', validators=[DataRequired()], default=date.today)
    end_date = DateField('Ngày kết thúc', validators=[Optional()])
    status = SelectField('Trạng thái', 
                        choices=[('PLANNED', 'Dự kiến'),
                                ('ACTIVE', 'Đang thực hiện'),
                                ('COMPLETED', 'Hoàn thành'),
                                ('CANCELLED', 'Hủy bỏ')], 
                        default='PLANNED')
    notes = TextAreaField('Ghi chú', validators=[Optional()])
    submit = SubmitField('Lưu')

class SurgeryEventForm(BaseTreatmentEventForm):
    """Form for surgery events"""
    
    # Thông tin phẫu thuật cơ bản - Basic surgery information
    surgery_method = SelectField('Phương pháp phẫu thuật', 
                              choices=[('', 'Chọn phương pháp'),
                                      ('OPEN', 'Mổ mở'),
                                      ('LAPAROSCOPIC', 'Nội soi'),
                                      ('ROBOTIC', 'Robot')], 
                              validators=[DataRequired()])
    procedure_name = StringField('Tên thủ thuật', validators=[DataRequired(), Length(1, 200)])
    surgeon_name = StringField('Phẫu thuật viên', validators=[Optional(), Length(0, 100)])
    
    # Kết quả giải phẫu bệnh - Pathology results
    pathology_date = DateField('Ngày có kết quả GPB', validators=[Optional()])
    pathology_t_stage = SelectField('Giai đoạn pT',
                                   choices=[('', 'Chọn giai đoạn'),
                                           ('pT2a', 'pT2a'),
                                           ('pT2b', 'pT2b'),
                                           ('pT2c', 'pT2c'),
                                           ('pT3a', 'pT3a'),
                                           ('pT3b', 'pT3b'),
                                           ('pT4', 'pT4')],
                                   validators=[Optional()])
    pathology_n_stage = SelectField('Giai đoạn pN',
                                   choices=[('', 'Chọn giai đoạn'),
                                           ('pN0', 'pN0'),
                                           ('pN1', 'pN1')],
                                   validators=[Optional()])
    pathology_m_stage = SelectField('Giai đoạn pM',
                                   choices=[('', 'Chọn giai đoạn'),
                                           ('pM0', 'pM0'),
                                           ('pM1', 'pM1'),
                                           ('pM1a', 'pM1a'),
                                           ('pM1b', 'pM1b'),
                                           ('pM1c', 'pM1c')],
                                   validators=[Optional()])
    pathology_gleason = StringField('Điểm Gleason sau mổ', 
                                   validators=[Optional(), Length(0, 20)],
                                   render_kw={"placeholder": "VD: 4+3=7"})
    gleason_score = StringField('Điểm Gleason', 
                               validators=[Optional(), Length(0, 20)],
                               render_kw={"placeholder": "VD: 4+3=7"})
    surgical_margin_status = SelectField('Tình trạng bờ phẫu thuật',
                                        choices=[('', 'Chưa có kết quả'),
                                                ('NEGATIVE', 'Âm tính (R0)'),
                                                ('POSITIVE', 'Dương tính (R1)'),
                                                ('CLOSE', 'Gần (< 1mm)')],
                                        validators=[Optional()])
    surgical_margin = SelectField('Bờ phẫu thuật',
                                 choices=[('', 'Chưa có kết quả'),
                                         ('NEGATIVE', 'Âm tính'),
                                         ('POSITIVE', 'Dương tính'),
                                         ('CLOSE', 'Gần')],
                                 validators=[Optional()])
    lymph_node_status = StringField('Tình trạng hạch', 
                                   validators=[Optional(), Length(0, 50)],
                                   render_kw={"placeholder": "VD: 0/12 hạch dương tính"})
    lymph_nodes_examined = IntegerField('Số hạch xét nghiệm', 
                                       validators=[Optional(), NumberRange(min=0, max=50)])
    lymph_nodes_positive = IntegerField('Số hạch dương tính', 
                                       validators=[Optional(), NumberRange(min=0, max=50)])
    extracapsular_extension = BooleanField('Vượt vỏ tuyến')
    seminal_vesicle_invasion = BooleanField('Xâm lấn túi tinh')
    prostate_weight = FloatField('Khối lượng tuyến tiền liệt (g)', 
                                validators=[Optional(), NumberRange(min=0, max=500)])
    
    # Thông tin bổ sung - Additional information
    operative_time = IntegerField('Thời gian mổ (phút)', 
                                 validators=[Optional(), NumberRange(min=0, max=720)])
    blood_loss = IntegerField('Mất máu (mL)', 
                             validators=[Optional(), NumberRange(min=0, max=5000)])
    complications = TextAreaField('Biến chứng', validators=[Optional()])

class RadiationEventForm(BaseTreatmentEventForm):
    """Form for radiation therapy events"""
    
    # Thông tin xạ trị cơ bản - Basic radiation information
    radiation_type = SelectField('Loại xạ trị',
                                choices=[('', 'Chọn loại xạ trị'),
                                        ('EXTERNAL', 'Xạ ngoài (EBRT)'),
                                        ('BRACHYTHERAPY', 'Áp sát (Brachytherapy)'),
                                        ('SBRT', 'Xạ trị định hướng (SBRT)')],
                                validators=[DataRequired()])
    technique = SelectField('Kỹ thuật',
                           choices=[('', 'Chọn kỹ thuật'),
                                   ('IMRT', 'IMRT'),
                                   ('VMAT', 'VMAT'),
                                   ('3D-CRT', '3D-CRT'),
                                   ('HDR', 'HDR Brachytherapy'),
                                   ('LDR', 'LDR Brachytherapy')],
                           validators=[Optional()])
    
    # Liều lượng - Dosage information
    total_dose = FloatField('Tổng liều (Gy)', 
                           validators=[Optional(), NumberRange(min=0, max=200)])
    dose_per_fraction = FloatField('Liều/phân đoạn (Gy)', 
                                  validators=[Optional(), NumberRange(min=0, max=30)])
    fractions = IntegerField('Số phân đoạn', 
                            validators=[Optional(), NumberRange(min=1, max=50)])
    
    # Vùng điều trị - Treatment areas
    treatment_areas = TextAreaField('Vùng chiếu xạ', 
                                   validators=[Optional()],
                                   render_kw={"placeholder": "VD: Tuyến tiền liệt, túi tinh, hạch chậu"})
    planning_target_volume = FloatField('Thể tích đích (cc)', 
                                       validators=[Optional(), NumberRange(min=0, max=1000)])
    
    # Thiết bị - Equipment
    machine_type = StringField('Loại máy', validators=[Optional(), Length(0, 50)])
    planning_system = StringField('Hệ thống lập kế hoạch', validators=[Optional(), Length(0, 50)])
    image_guidance = StringField('Hướng dẫn hình ảnh', validators=[Optional(), Length(0, 50)])
    
    # Tác dụng phụ - Side effects
    acute_toxicity = TextAreaField('Độc tính cấp', validators=[Optional()])
    late_toxicity = TextAreaField('Độc tính muộn', validators=[Optional()])

class HormoneTherapyEventForm(BaseTreatmentEventForm):
    """Form for hormone therapy (ADT) events"""
    
    # Thông tin ADT cơ bản - Basic ADT information
    therapy_type = SelectField('Loại liệu pháp',
                              choices=[('', 'Chọn loại'),
                                      ('CONTINUOUS', 'Liên tục'),
                                      ('INTERMITTENT', 'Ngắt quãng')],
                              validators=[DataRequired()])
    adt_type = SelectField('Loại ADT',
                          choices=[('', 'Chọn loại ADT'),
                                  ('LHRH_AGONIST', 'LHRH Agonist'),
                                  ('LHRH_ANTAGONIST', 'LHRH Antagonist'),
                                  ('ANTIANDROGEN', 'Antiandrogen'),
                                  ('COMBINED', 'Phối hợp')],
                          validators=[Optional()])
    
    # Thông tin thuốc - Drug information
    drug_name = StringField('Tên thuốc', validators=[DataRequired(), Length(1, 100)])
    dosage = StringField('Liều lượng', validators=[Optional(), Length(0, 50)])
    administration_route = SelectField('Đường dùng',
                                     choices=[('', 'Chọn đường dùng'),
                                             ('IM', 'Tiêm bắp'),
                                             ('SC', 'Tiêm dưới da'),
                                             ('ORAL', 'Uống')],
                                     validators=[Optional()])
    injection_frequency = SelectField('Tần suất tiêm',
                                    choices=[('', 'Chọn tần suất'),
                                            ('MONTHLY', 'Hàng tháng'),
                                            ('3_MONTHS', '3 tháng/lần'),
                                            ('6_MONTHS', '6 tháng/lần'),
                                            ('DAILY', 'Hàng ngày')],
                                    validators=[Optional()])
    
    # Liệu pháp gián đoạn - Intermittent therapy
    is_intermittent = BooleanField('Liệu pháp gián đoạn')
    cycle_duration_months = IntegerField('Thời gian điều trị (tháng)', 
                                       validators=[Optional(), NumberRange(min=1, max=36)])
    break_duration_months = IntegerField('Thời gian nghỉ (tháng)', 
                                       validators=[Optional(), NumberRange(min=1, max=24)])
    
    # Theo dõi PSA - PSA monitoring
    baseline_psa = FloatField('PSA ban đầu (ng/mL)', 
                             validators=[Optional(), NumberRange(min=0, max=10000)])
    nadir_psa = FloatField('PSA thấp nhất (ng/mL)', 
                          validators=[Optional(), NumberRange(min=0, max=10000)])
    psa_nadir = FloatField('PSA nadir (ng/mL)', 
                          validators=[Optional(), NumberRange(min=0, max=10000)])
    psa_response_time = IntegerField('Thời gian đáp ứng PSA (tuần)', 
                                   validators=[Optional(), NumberRange(min=1, max=52)])
    
    # Theo dõi testosterone - Testosterone monitoring
    baseline_testosterone = FloatField('Testosterone ban đầu (ng/dL)', 
                                      validators=[Optional(), NumberRange(min=0, max=2000)])
    testosterone_suppression = SelectField('Ức chế testosterone',
                                         choices=[('', 'Chưa đánh giá'),
                                                 ('ACHIEVED', 'Đạt được (<50 ng/dL)'),
                                                 ('PARTIAL', 'Một phần (50-100 ng/dL)'),
                                                 ('INADEQUATE', 'Không đạt (>100 ng/dL)')],
                                         validators=[Optional()])
    castration_achieved = BooleanField('Đạt mức thiến')
    castration_date = DateField('Ngày đạt thiến', validators=[Optional()])
    
    # Thời gian điều trị - Treatment duration
    duration_months = IntegerField('Thời gian điều trị (tháng)', 
                                  validators=[Optional(), NumberRange(min=1, max=120)])
    cycle_length = IntegerField('Độ dài chu kỳ (tháng)', 
                               validators=[Optional(), NumberRange(min=1, max=48)])
    off_treatment_period = IntegerField('Thời gian nghỉ (tháng)', 
                                       validators=[Optional(), NumberRange(min=0, max=24)])
    
    # Tác dụng phụ - Side effects
    side_effects = TextAreaField('Tác dụng phụ', validators=[Optional()])
    quality_of_life_impact = SelectField('Ảnh hưởng chất lượng cuộc sống',
                                        choices=[('', 'Chưa đánh giá'),
                                                ('MINIMAL', 'Tối thiểu'),
                                                ('MODERATE', 'Vừa phải'),
                                                ('SEVERE', 'Nghiêm trọng')],
                                        validators=[Optional()])

class ChemotherapyEventForm(BaseTreatmentEventForm):
    """Form for chemotherapy events"""
    
    # Thông tin hóa trị cơ bản - Basic chemotherapy information
    protocol_name = StringField('Phác đồ hóa trị', 
                               validators=[DataRequired(), Length(1, 100)],
                               render_kw={"placeholder": "VD: Docetaxel + Prednisone"})
    indication = SelectField('Chỉ định',
                            choices=[('', 'Chọn chỉ định'),
                                    ('mCRPC', 'mCRPC'),
                                    ('mCSPC', 'mCSPC'),
                                    ('ADJUVANT', 'Phụ trợ'),
                                    ('NEOADJUVANT', 'Tiền phẫu')],
                            validators=[Optional()])
    drug_regimen = TextAreaField('Chi tiết thuốc và liều dùng',
                                validators=[Optional()],
                                render_kw={"placeholder": "Mô tả chi tiết các thuốc và liều dùng"})
    
    # Chu kỳ điều trị - Treatment cycles
    planned_cycles = IntegerField('Số chu kỳ dự kiến', 
                                 validators=[Optional(), NumberRange(min=1, max=20)])
    completed_cycles = IntegerField('Số chu kỳ đã hoàn thành', 
                                   validators=[Optional(), NumberRange(min=0, max=20)],
                                   default=0)
    cycle_length_days = IntegerField('Độ dài chu kỳ (ngày)', 
                                    validators=[Optional(), NumberRange(min=7, max=42)])
    
    # Thông tin thuốc chính - Primary drug information
    primary_drug = StringField('Thuốc chính', validators=[Optional(), Length(0, 100)])
    dose_per_cycle = StringField('Liều/chu kỳ', validators=[Optional(), Length(0, 100)])
    dose_modifications = TextAreaField('Điều chỉnh liều', validators=[Optional()])
    
    # Đáp ứng điều trị - Treatment response
    response_assessment = SelectField('Đánh giá đáp ứng',
                                     choices=[('', 'Chưa đánh giá'),
                                             ('CR', 'Đáp ứng hoàn toàn'),
                                             ('PR', 'Đáp ứng một phần'),
                                             ('SD', 'Bệnh ổn định'),
                                             ('PD', 'Bệnh tiến triển')],
                                     validators=[Optional()])
    best_response = SelectField('Đáp ứng tốt nhất',
                               choices=[('', 'Chưa có'),
                                       ('CR', 'Đáp ứng hoàn toàn'),
                                       ('PR', 'Đáp ứng một phần'),
                                       ('SD', 'Bệnh ổn định'),
                                       ('PD', 'Bệnh tiến triển')],
                               validators=[Optional()])
    psa_response = FloatField('Đáp ứng PSA (%)', 
                             validators=[Optional(), NumberRange(min=-100, max=100)])
    radiographic_response = SelectField('Đáp ứng phim X-quang',
                                       choices=[('', 'Chưa có'),
                                               ('CR', 'Đáp ứng hoàn toàn'),
                                               ('PR', 'Đáp ứng một phần'),
                                               ('SD', 'Bệnh ổn định'),
                                               ('PD', 'Bệnh tiến triển')],
                                       validators=[Optional()])
    response_date = DateField('Ngày đánh giá', validators=[Optional()])
    
    # Độc tính - Toxicity
    hematologic_toxicity = SelectField('Độc tính huyết học',
                                      choices=[('', 'Không có'),
                                              ('GRADE_1', 'Độ 1 (nhẹ)'),
                                              ('GRADE_2', 'Độ 2 (vừa)'),
                                              ('GRADE_3', 'Độ 3 (nặng)'),
                                              ('GRADE_4', 'Độ 4 (đe dọa tính mạng)')],
                                      validators=[Optional()])
    non_hematologic_toxicity = SelectField('Độc tính phi huyết học',
                                          choices=[('', 'Không có'),
                                                  ('GRADE_1', 'Độ 1 (nhẹ)'),
                                                  ('GRADE_2', 'Độ 2 (vừa)'),
                                                  ('GRADE_3', 'Độ 3 (nặng)'),
                                                  ('GRADE_4', 'Độ 4 (đe dọa tính mạng)')],
                                          validators=[Optional()])
    adverse_events = TextAreaField('Tác dụng bất lợi', validators=[Optional()])
    grade_3_4_toxicity = TextAreaField('Độc tính độ 3-4', validators=[Optional()])
    dose_delays = IntegerField('Số lần trễ liều', 
                              validators=[Optional(), NumberRange(min=0, max=10)],
                              default=0)
    dose_reductions = IntegerField('Số lần giảm liều', 
                                  validators=[Optional(), NumberRange(min=0, max=10)],
                                  default=0)
    dose_reduction_required = BooleanField('Cần giảm liều')
    
    # Nguyên nhân dừng - Discontinuation
    discontinuation_reason = SelectField('Lý do dừng điều trị',
                                        choices=[('', 'Chưa dừng'),
                                                ('COMPLETED', 'Hoàn thành điều trị'),
                                                ('TOXICITY', 'Độc tính'),
                                                ('PROGRESSION', 'Bệnh tiến triển'),
                                                ('PATIENT_CHOICE', 'Bệnh nhân từ chối'),
                                                ('OTHER', 'Khác')],
                                        validators=[Optional()])

class SystemicTherapyEventForm(BaseTreatmentEventForm):
    """Form for other systemic therapy events"""
    
    # Thông tin liệu pháp cơ bản - Basic therapy information
    therapy_class = SelectField('Nhóm liệu pháp',
                               choices=[('', 'Chọn nhóm'),
                                       ('IMMUNOTHERAPY', 'Miễn dịch trị liệu'),
                                       ('TARGETED', 'Liệu pháp đích'),
                                       ('BONE_TARGETED', 'Thuốc bảo vệ xương')],
                               validators=[DataRequired()])
    agent_name = StringField('Tên thuốc', validators=[DataRequired(), Length(1, 100)])
    mechanism_of_action = StringField('Cơ chế tác dụng', 
                                     validators=[Optional(), Length(0, 200)])
    dosing_schedule = StringField('Lịch dùng thuốc', validators=[Optional(), Length(0, 100)])
    
    # Thông tin điều trị - Treatment details
    treatment_cycles = IntegerField('Số chu kỳ điều trị', 
                                   validators=[Optional(), NumberRange(min=1, max=50)])
    duration_months = IntegerField('Thời gian điều trị (tháng)', 
                                  validators=[Optional(), NumberRange(min=1, max=60)])
    administration_route = SelectField('Đường dùng',
                                     choices=[('', 'Chọn đường dùng'),
                                             ('IV', 'Tiêm tĩnh mạch'),
                                             ('SC', 'Tiêm dưới da'),
                                             ('ORAL', 'Uống')],
                                     validators=[Optional()])
    
    # Đáp ứng và hiệu quả - Response and efficacy
    clinical_response = SelectField('Đáp ứng lâm sàng',
                                   choices=[('', 'Chưa đánh giá'),
                                           ('CR', 'Đáp ứng hoàn toàn'),
                                           ('PR', 'Đáp ứng một phần'),
                                           ('SD', 'Bệnh ổn định'),
                                           ('PD', 'Bệnh tiến triển')],
                                   validators=[Optional()])
    biomarker_response = SelectField('Đáp ứng sinh học',
                                    choices=[('', 'Chưa có'),
                                            ('POSITIVE', 'Dương tính'),
                                            ('NEGATIVE', 'Âm tính'),
                                            ('PARTIAL', 'Một phần')],
                                    validators=[Optional()])
    psa_response = SelectField('Đáp ứng PSA',
                              choices=[('', 'Chưa có'),
                                      ('≥50%', 'Giảm ≥50%'),
                                      ('30-50%', 'Giảm 30-50%'),
                                      ('<30%', 'Giảm <30%'),
                                      ('INCREASE', 'Tăng')],
                              validators=[Optional()])
    
    # Đáp ứng bổ sung - Additional response metrics
    imaging_response = SelectField('Đáp ứng hình ảnh',
                                  choices=[('', 'Chưa có'),
                                          ('CR', 'Đáp ứng hoàn toàn'),
                                          ('PR', 'Đáp ứng một phần'),
                                          ('SD', 'Bệnh ổn định'),
                                          ('PD', 'Bệnh tiến triển')],
                                  validators=[Optional()])
    psa_decline_50 = BooleanField('PSA giảm ≥50%')
    progression_free_survival = FloatField('Sống thêm không tiến triển (tháng)', 
                                          validators=[Optional(), NumberRange(min=0, max=120)])
    time_to_progression = FloatField('Thời gian tới tiến triển (tháng)', 
                                    validators=[Optional(), NumberRange(min=0, max=120)])
    
    # Tác dụng phụ và quản lý - Side effects and management
    adverse_events = TextAreaField('Tác dụng bất lợi', validators=[Optional()])
    dose_modifications_required = BooleanField('Cần điều chỉnh liều')
    tolerability_assessment = SelectField('Đánh giá dung nạp',
                                         choices=[('', 'Chưa đánh giá'),
                                                 ('EXCELLENT', 'Rất tốt'),
                                                 ('GOOD', 'Tốt'),
                                                 ('FAIR', 'Trung bình'),
                                                 ('POOR', 'Kém')],
                                         validators=[Optional()])
    quality_of_life_impact = SelectField('Ảnh hưởng chất lượng cuộc sống',
                                        choices=[('', 'Chưa đánh giá'),
                                                ('MINIMAL', 'Tối thiểu'),
                                                ('MODERATE', 'Vừa phải'),
                                                ('SEVERE', 'Nghiêm trọng')],
                                        validators=[Optional()])
    
    # Sinh chỉ và theo dõi - Biomarkers and monitoring
    biomarker_testing = StringField('Xét nghiệm sinh chỉ', validators=[Optional(), Length(0, 200)])
    companion_diagnostics = StringField('Chẩn đoán đồng hành', validators=[Optional(), Length(0, 200)])
    monitoring_parameters = TextAreaField('Thông số theo dõi', 
                                        validators=[Optional()],
                                        render_kw={"placeholder": "Các thông số cần theo dõi định kỳ"})