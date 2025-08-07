"""
Forms for AI Prediction Module

Các form cho module dự báo AI với Vietnamese interface
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, FloatField, 
                     IntegerField, BooleanField, DateField, SubmitField)
from wtforms.validators import DataRequired, Optional, NumberRange, Length
from datetime import datetime, date

class BCRPredictionForm(FlaskForm):
    """Form dự báo nguy cơ tái phát sinh hóa"""
    
    # Tùy chọn phân tích
    include_psa_trend = BooleanField('Bao gồm phân tích xu hướng PSA', default=True)
    include_surgery_details = BooleanField('Bao gồm chi tiết phẫu thuật', default=True)
    include_pathology_details = BooleanField('Bao gồm chi tiết mô bệnh học', default=True)
    
    # Thông số bổ sung (nếu muốn ghi đè)
    additional_psa = FloatField('PSA bổ sung (ng/mL)', validators=[Optional(), NumberRange(min=0)])
    additional_notes = TextAreaField('Ghi chú bổ sung', validators=[Optional(), Length(max=500)])
    
    # Loại phân tích
    analysis_type = SelectField('Loại phân tích', 
                               choices=[
                                   ('standard', 'Phân tích tiêu chuẩn'),
                                   ('detailed', 'Phân tích chi tiết'),
                                   ('comparative', 'So sánh với cohort')
                               ], 
                               default='standard')
    
    prediction_horizon = SelectField('Thời gian dự báo',
                                   choices=[
                                       ('2_years', '2 năm'),
                                       ('5_years', '5 năm'),
                                       ('both', 'Cả 2 năm và 5 năm')
                                   ],
                                   default='both')
    
    submit = SubmitField('Phân tích Nguy cơ BCR')

class ADTPredictionForm(FlaskForm):
    """Form dự báo lợi ích từ liệu pháp nội tiết"""
    
    # Thông tin điều trị dự kiến
    planned_adt_type = SelectField('Loại ADT dự kiến',
                                  choices=[
                                      ('gnrh_agonist', 'GnRH Agonist'),
                                      ('gnrh_antagonist', 'GnRH Antagonist'),
                                      ('antiandrogen', 'Thuốc kháng androgen'),
                                      ('combination', 'Phối hợp')
                                  ],
                                  validators=[DataRequired()])
    
    planned_duration = IntegerField('Thời gian điều trị dự kiến (tháng)', 
                                   validators=[DataRequired(), NumberRange(min=1, max=120)])
    
    # Thông tin bệnh nhân bổ sung
    performance_status = SelectField('Trạng thái toàn thân (ECOG)',
                                   choices=[
                                       ('0', '0 - Hoạt động bình thường'),
                                       ('1', '1 - Hạn chế hoạt động nặng'),
                                       ('2', '2 - Tự chăm sóc được'),
                                       ('3', '3 - Tự chăm sóc hạn chế'),
                                       ('4', '4 - Nằm liệt giường')
                                   ],
                                   default='0')
    
    comorbidities = TextAreaField('Bệnh lý kèm theo', 
                                 validators=[Optional(), Length(max=500)])
    
    current_medications = TextAreaField('Thuốc đang sử dụng',
                                      validators=[Optional(), Length(max=500)])
    
    quality_of_life_priority = SelectField('Mức độ ưu tiên chất lượng cuộc sống',
                                         choices=[
                                             ('high', 'Cao'),
                                             ('moderate', 'Trung bình'),
                                             ('low', 'Thấp')
                                         ],
                                         default='moderate')
    
    submit = SubmitField('Dự báo Lợi ích ADT')

class AdverseEventPredictionForm(FlaskForm):
    """Form dự báo nguy cơ biến cố bất lợi"""
    
    # Loại điều trị sắp tới
    treatment_type = SelectField('Loại điều trị',
                                choices=[
                                    ('surgery', 'Phẫu thuật'),
                                    ('radiation', 'Xạ trị'),
                                    ('hormone_therapy', 'Liệu pháp nội tiết'),
                                    ('chemotherapy', 'Hóa trị'),
                                    ('immunotherapy', 'Miễn dịch trị liệu')
                                ],
                                validators=[DataRequired()])
    
    # Chi tiết điều trị - Surgery
    surgery_type = SelectField('Loại phẫu thuật',
                              choices=[
                                  ('open_rp', 'Cắt tuyến tiền liệt mở'),
                                  ('laparoscopic_rp', 'Cắt tuyến tiền liệt nội soi'),
                                  ('robotic_rp', 'Cắt tuyến tiền liệt robot'),
                                  ('turp', 'Cắt nội soi qua niệu đạo')
                              ],
                              validators=[Optional()])
    
    # Chi tiết điều trị - Radiation
    radiation_type = SelectField('Loại xạ trị',
                                choices=[
                                    ('ebrt', 'Xạ trị ngoài (EBRT)'),
                                    ('imrt', 'IMRT'),
                                    ('igrt', 'IGRT'),
                                    ('sbrt', 'SBRT'),
                                    ('proton', 'Xạ trị proton'),
                                    ('brachytherapy', 'Xạ trị trong')
                                ],
                                validators=[Optional()])
    
    radiation_dose = FloatField('Liều xạ (Gy)', validators=[Optional(), NumberRange(min=0, max=100)])
    
    # Chi tiết điều trị - Hormone therapy
    hormone_drug = SelectField('Thuốc nội tiết',
                              choices=[
                                  ('leuprolide', 'Leuprolide'),
                                  ('goserelin', 'Goserelin'),
                                  ('triptorelin', 'Triptorelin'),
                                  ('degarelix', 'Degarelix'),
                                  ('bicalutamide', 'Bicalutamide'),
                                  ('enzalutamide', 'Enzalutamide'),
                                  ('apalutamide', 'Apalutamide')
                              ],
                              validators=[Optional()])
    
    # Chi tiết điều trị - Chemotherapy
    chemo_regimen = SelectField('Phác đồ hóa trị',
                               choices=[
                                   ('docetaxel', 'Docetaxel'),
                                   ('cabazitaxel', 'Cabazitaxel'),
                                   ('carboplatin_paclitaxel', 'Carboplatin + Paclitaxel')
                               ],
                               validators=[Optional()])
    
    # Thông tin bệnh nhân
    age_group = SelectField('Nhóm tuổi',
                           choices=[
                               ('<60', 'Dưới 60'),
                               ('60-70', '60-70'),
                               ('70-80', '70-80'),
                               ('>80', 'Trên 80')
                           ],
                           validators=[DataRequired()])
    
    # Yếu tố nguy cơ
    cardiovascular_risk = SelectField('Nguy cơ tim mạch',
                                    choices=[
                                        ('low', 'Thấp'),
                                        ('moderate', 'Trung bình'),
                                        ('high', 'Cao')
                                    ],
                                    default='low')
    
    diabetes_status = SelectField('Tình trạng tiểu đường',
                                 choices=[
                                     ('none', 'Không'),
                                     ('type1', 'Type 1'),
                                     ('type2_controlled', 'Type 2 - Kiểm soát tốt'),
                                     ('type2_uncontrolled', 'Type 2 - Kiểm soát kém')
                                 ],
                                 default='none')
    
    bone_health_status = SelectField('Tình trạng xương',
                                   choices=[
                                       ('normal', 'Bình thường'),
                                       ('osteopenia', 'Loãng xương nhẹ'),
                                       ('osteoporosis', 'Loãng xương nặng')
                                   ],
                                   default='normal')
    
    previous_ae_concern = TextAreaField('Biến cố bất lợi quan tâm đặc biệt',
                                      validators=[Optional(), Length(max=300)])
    
    # Tham số dự báo
    prediction_timeframe = SelectField('Khung thời gian dự báo',
                                     choices=[
                                         ('30_days', '30 ngày'),
                                         ('3_months', '3 tháng'),
                                         ('6_months', '6 tháng'),
                                         ('1_year', '1 năm')
                                     ],
                                     default='3_months')
    
    include_prevention = BooleanField('Bao gồm khuyến nghị phòng ngừa', default=True)
    include_monitoring = BooleanField('Bao gồm kế hoạch theo dõi', default=True)
    
    submit = SubmitField('Dự báo Nguy cơ Biến cố')

class ComprehensivePredictionForm(FlaskForm):
    """Form cho phân tích dự báo tổng hợp"""
    
    # Loại phân tích muốn thực hiện
    include_bcr = BooleanField('Dự báo nguy cơ tái phát sinh hóa', default=True)
    include_adt = BooleanField('Dự báo lợi ích ADT', default=True)
    include_adverse_events = BooleanField('Cảnh báo biến cố bất lợi', default=True)
    
    # Thông số chung
    analysis_depth = SelectField('Mức độ phân tích',
                                choices=[
                                    ('quick', 'Nhanh - Kết quả cơ bản'),
                                    ('standard', 'Tiêu chuẩn - Phân tích đầy đủ'),
                                    ('comprehensive', 'Toàn diện - Bao gồm khuyến nghị')
                                ],
                                default='standard')
    
    report_format = SelectField('Định dạng báo cáo',
                               choices=[
                                   ('dashboard', 'Dashboard tương tác'),
                                   ('summary', 'Tóm tắt ngắn gọn'),
                                   ('detailed', 'Báo cáo chi tiết'),
                                   ('pdf', 'Báo cáo PDF')
                               ],
                               default='dashboard')
    
    # Ưu tiên lâm sàng
    clinical_focus = SelectField('Trọng tâm lâm sàng',
                                choices=[
                                    ('survival', 'Sống thêm tổng thể'),
                                    ('quality_of_life', 'Chất lượng cuộc sống'),
                                    ('safety', 'An toàn bệnh nhân'),
                                    ('cost_effectiveness', 'Hiệu quả chi phí')
                                ],
                                default='survival')
    
    special_considerations = TextAreaField('Yếu tố đặc biệt cần xem xét',
                                         validators=[Optional(), Length(max=500)])
    
    submit = SubmitField('Tạo Phân tích Tổng hợp')

class PredictionConfigForm(FlaskForm):
    """Form cấu hình hệ thống dự báo"""
    
    # Cấu hình mô hình AI
    ai_model_preference = SelectField('Mô hình AI ưu tiên',
                                     choices=[
                                         ('gemini-2.5-pro', 'Gemini 2.5 Pro - Chính xác cao'),
                                         ('gemini-2.5-flash', 'Gemini 2.5 Flash - Nhanh hơn')
                                     ],
                                     default='gemini-2.5-pro')
    
    prediction_confidence_threshold = FloatField('Ngưỡng tin cậy tối thiểu (%)',
                                                validators=[DataRequired(), NumberRange(min=50, max=95)],
                                                default=75)
    
    # Cấu hình cảnh báo
    enable_auto_alerts = BooleanField('Bật cảnh báo tự động', default=True)
    alert_severity_threshold = SelectField('Ngưỡng cảnh báo',
                                         choices=[
                                             ('low', 'Thấp - Tất cả nguy cơ'),
                                             ('moderate', 'Trung bình - Nguy cơ từ trung bình'),
                                             ('high', 'Cao - Chỉ nguy cơ cao')
                                         ],
                                         default='moderate')
    
    # Cấu hình báo cáo
    auto_generate_reports = BooleanField('Tự động tạo báo cáo', default=False)
    report_frequency = SelectField('Tần suất báo cáo',
                                  choices=[
                                      ('weekly', 'Hàng tuần'),
                                      ('monthly', 'Hàng tháng'),
                                      ('quarterly', 'Hàng quý')
                                  ],
                                  default='monthly')
    
    submit = SubmitField('Lưu Cấu hình')