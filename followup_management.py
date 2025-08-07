"""
Follow-up and Adverse Event Management Module
Quản lý Theo dõi và Biến cố Bất lợi

This module provides comprehensive follow-up scheduling, PSA monitoring with AI analysis,
and adverse event tracking with CTCAE grading system integration.
"""

import os
import smtplib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import numpy as np
from scipy import stats
import logging

try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
except ImportError:
    # Fallback for systems without email support
    class MimeText:
        def __init__(self, text, type='plain', charset='utf-8'):
            self.text = text
        def as_string(self):
            return self.text
    
    class MimeMultipart:
        def __init__(self):
            self.parts = []
        def attach(self, part):
            self.parts.append(part)
        def as_string(self):
            return '\n'.join([part.text for part in self.parts if hasattr(part, 'text')])
        def __setitem__(self, key, value):
            pass

from app import db
from models import Patient, BloodTest, SurgeryEvent, RadiationEvent, HormoneTherapyEvent, ChemotherapyEvent, SystemicTherapyEvent
try:
    from gemini_ai import analyze_psa_trend, generate_clinical_recommendations
except ImportError:
    def analyze_psa_trend(data):
        return "AI analysis không khả dụng"
    def generate_clinical_recommendations(data):
        return []

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PSAAnalyzer:
    """PSA Dynamic Monitoring with AI Analysis"""
    
    @staticmethod
    def calculate_psa_doubling_time(psa_values: List[float], dates: List[datetime]) -> Optional[float]:
        """
        Calculate PSA doubling time using log-linear regression
        Returns doubling time in months, None if insufficient data
        """
        if len(psa_values) < 3 or len(dates) < 3:
            return None
            
        # Filter out zero or negative PSA values
        valid_data = [(date, psa) for date, psa in zip(dates, psa_values) if psa > 0]
        if len(valid_data) < 3:
            return None
            
        dates_valid, psa_valid = zip(*valid_data)
        
        # Convert dates to days from first measurement
        days = [(date - dates_valid[0]).days for date in dates_valid]
        log_psa = [np.log(psa) for psa in psa_valid]
        
        try:
            # Linear regression on log(PSA) vs time
            slope, intercept, r_value, p_value, std_err = stats.linregress(days, log_psa)
            
            # PSA doubling time = ln(2) / slope (convert days to months)
            if slope > 0:
                doubling_time_days = np.log(2) / slope
                doubling_time_months = doubling_time_days / 30.44  # Average days per month
                return round(doubling_time_months, 1)
            else:
                return None  # PSA is decreasing
                
        except Exception as e:
            logger.error(f"Error calculating PSA doubling time: {e}")
            return None
    
    @staticmethod
    def calculate_psa_velocity(psa_values: List[float], dates: List[datetime]) -> Optional[float]:
        """
        Calculate PSA velocity (ng/mL/year)
        Returns PSA velocity, None if insufficient data
        """
        if len(psa_values) < 2 or len(dates) < 2:
            return None
            
        try:
            # Use linear regression for more robust calculation
            days = [(date - dates[0]).days for date in dates]
            slope, intercept, r_value, p_value, std_err = stats.linregress(days, psa_values)
            
            # Convert slope from ng/mL/day to ng/mL/year
            psa_velocity = slope * 365.25
            return round(psa_velocity, 2)
            
        except Exception as e:
            logger.error(f"Error calculating PSA velocity: {e}")
            return None
    
    @staticmethod
    def analyze_psa_trend(patient_id: int) -> Dict:
        """Comprehensive PSA trend analysis with AI integration"""
        try:
            # Get all PSA values for the patient
            blood_tests = BloodTest.query.filter_by(patient_id=patient_id)\
                                        .filter(BloodTest.psa_level.isnot(None))\
                                        .order_by(BloodTest.test_date.asc()).all()
            
            if len(blood_tests) < 2:
                return {
                    'status': 'insufficient_data',
                    'message': 'Cần ít nhất 2 kết quả PSA để phân tích',
                    'recommendation': 'Tiếp tục theo dõi PSA định kỳ'
                }
            
            psa_values = [test.psa_level for test in blood_tests]
            dates = [test.test_date for test in blood_tests]
            
            # Calculate PSA metrics
            doubling_time = PSAAnalyzer.calculate_psa_doubling_time(psa_values, dates)
            velocity = PSAAnalyzer.calculate_psa_velocity(psa_values, dates)
            
            # Current vs previous PSA
            current_psa = psa_values[-1]
            previous_psa = psa_values[-2] if len(psa_values) > 1 else None
            
            # Determine trend
            trend = 'stable'
            if previous_psa:
                change_percent = ((current_psa - previous_psa) / previous_psa) * 100
                if change_percent > 25:
                    trend = 'rising_significant'
                elif change_percent > 10:
                    trend = 'rising_moderate'
                elif change_percent < -25:
                    trend = 'declining_significant'
                elif change_percent < -10:
                    trend = 'declining_moderate'
            
            # Risk assessment
            risk_level = 'low'
            alerts = []
            
            if doubling_time and doubling_time < 6:
                risk_level = 'high'
                alerts.append('PSA doubling time < 6 tháng - nguy cơ tái phát cao')
            elif doubling_time and doubling_time < 12:
                risk_level = 'moderate'
                alerts.append('PSA doubling time < 12 tháng - cần theo dõi chặt chẽ')
                
            if velocity and velocity > 2.0:
                if risk_level == 'low':
                    risk_level = 'moderate'
                alerts.append('PSA velocity > 2.0 ng/mL/năm - cần đánh giá thêm')
                
            if current_psa > 10.0:
                risk_level = 'high'
                alerts.append('PSA hiện tại > 10.0 ng/mL - cần can thiệp')
            
            # Get AI analysis
            ai_analysis = None
            try:
                psa_data_text = f"Dữ liệu PSA: {', '.join([f'{psa:.1f}' for psa in psa_values[-5:]])}"  # Last 5 values
                ai_analysis = analyze_psa_trend(psa_data_text)
            except Exception as e:
                logger.error(f"AI analysis failed: {e}")
            
            return {
                'status': 'success',
                'current_psa': current_psa,
                'previous_psa': previous_psa,
                'doubling_time': doubling_time,
                'velocity': velocity,
                'trend': trend,
                'risk_level': risk_level,
                'alerts': alerts,
                'total_tests': len(blood_tests),
                'latest_test_date': dates[-1],
                'ai_analysis': ai_analysis,
                'recommendations': PSAAnalyzer.generate_recommendations(risk_level, doubling_time, velocity)
            }
            
        except Exception as e:
            logger.error(f"Error in PSA trend analysis: {e}")
            return {
                'status': 'error',
                'message': f'Lỗi phân tích PSA: {str(e)}'
            }
    
    @staticmethod
    def generate_recommendations(risk_level: str, doubling_time: Optional[float], velocity: Optional[float]) -> List[str]:
        """Generate clinical recommendations based on PSA analysis"""
        recommendations = []
        
        if risk_level == 'high':
            recommendations.extend([
                'Cần tái khám gấp trong vòng 2-4 tuần',
                'Xem xét chụp PET-PSMA hoặc MRI',
                'Tham khảo ý kiến chuyên gia ung thư học',
                'Cân nhắc điều trị can thiệp'
            ])
        elif risk_level == 'moderate':
            recommendations.extend([
                'Tái khám trong vòng 4-6 tuần',
                'Xét nghiệm PSA lại sau 1 tháng',
                'Cân nhắc chụp hình ảnh học',
                'Theo dõi chặt chẽ'
            ])
        else:
            recommendations.extend([
                'Tiếp tục theo dõi PSA định kỳ',
                'Tái khám theo lịch hẹn',
                'Duy trì lối sống lành mạnh'
            ])
            
        if doubling_time and doubling_time < 3:
            recommendations.append('PSA tăng rất nhanh - cần can thiệp khẩn cấp')
        
        return recommendations

class FollowUpScheduler:
    """Automatic Follow-up Scheduling and Reminders"""
    
    # Standard follow-up intervals (in months)
    FOLLOWUP_SCHEDULES = {
        'post_surgery': [1, 3, 6, 12, 18, 24],
        'post_radiation': [1, 3, 6, 9, 12, 18, 24],
        'hormone_therapy': [3, 6, 9, 12, 15, 18, 21, 24],
        'chemotherapy': [1, 2, 3, 6, 9, 12],
        'surveillance': [6, 12, 18, 24, 30, 36]
    }
    
    @staticmethod
    def calculate_next_followup(patient_id: int) -> Dict:
        """Calculate next follow-up based on treatment history and guidelines"""
        try:
            patient = Patient.query.get(patient_id)
            if not patient:
                return {'error': 'Patient not found'}
            
            # Get latest treatment
            latest_treatment = FollowUpScheduler.get_latest_treatment(patient_id)
            
            if not latest_treatment:
                # No treatment history - use surveillance schedule
                last_visit = FollowUpScheduler.get_last_visit_date(patient_id)
                next_date = last_visit + timedelta(days=180)  # 6 months
                return {
                    'next_date': next_date,
                    'reason': 'Theo dõi định kỳ',
                    'interval': '6 tháng',
                    'priority': 'routine'
                }
            
            treatment_type = latest_treatment['type']
            treatment_date = latest_treatment['date']
            
            # Calculate appropriate follow-up schedule
            schedule = FollowUpScheduler.FOLLOWUP_SCHEDULES.get(treatment_type, 
                                                              FollowUpScheduler.FOLLOWUP_SCHEDULES['surveillance'])
            
            # Find next appropriate interval
            months_since_treatment = (datetime.now().date() - treatment_date).days // 30
            
            next_interval = None
            for interval in schedule:
                if interval > months_since_treatment:
                    next_interval = interval
                    break
            
            if not next_interval:
                next_interval = 12  # Default to yearly follow-up
            
            next_date = treatment_date + timedelta(days=next_interval * 30)
            
            # Determine priority based on risk factors
            priority = FollowUpScheduler.assess_followup_priority(patient_id, latest_treatment)
            
            return {
                'next_date': next_date,
                'reason': f'Theo dõi sau {latest_treatment["name"]}',
                'interval': f'{next_interval} tháng',
                'priority': priority,
                'treatment_type': treatment_type
            }
            
        except Exception as e:
            logger.error(f"Error calculating follow-up: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def get_latest_treatment(patient_id: int) -> Optional[Dict]:
        """Get the most recent treatment for a patient"""
        treatments = []
        
        # Check all treatment types
        surgery = SurgeryEvent.query.filter_by(patient_id=patient_id)\
                                  .order_by(SurgeryEvent.treatment_date.desc()).first()
        if surgery:
            treatments.append({
                'type': 'post_surgery',
                'name': 'phẫu thuật',
                'date': surgery.treatment_date,
                'timestamp': surgery.treatment_date
            })
        
        radiation = RadiationEvent.query.filter_by(patient_id=patient_id)\
                                      .order_by(RadiationEvent.treatment_date.desc()).first()
        if radiation:
            treatments.append({
                'type': 'post_radiation',
                'name': 'xạ trị',
                'date': radiation.treatment_date,
                'timestamp': radiation.treatment_date
            })
        
        hormone = HormoneTherapyEvent.query.filter_by(patient_id=patient_id)\
                                  .order_by(HormoneTherapyEvent.treatment_date.desc()).first()
        if hormone:
            treatments.append({
                'type': 'hormone_therapy',
                'name': 'liệu pháp nội tiết',
                'date': hormone.treatment_date,
                'timestamp': hormone.treatment_date
            })
        
        chemo = ChemotherapyEvent.query.filter_by(patient_id=patient_id)\
                                     .order_by(ChemotherapyEvent.treatment_date.desc()).first()
        if chemo:
            treatments.append({
                'type': 'chemotherapy',
                'name': 'hóa trị',
                'date': chemo.treatment_date,
                'timestamp': chemo.treatment_date
            })
        
        systemic = SystemicTherapyEvent.query.filter_by(patient_id=patient_id)\
                                           .order_by(SystemicTherapyEvent.treatment_date.desc()).first()
        if systemic:
            treatments.append({
                'type': 'chemotherapy',  # Use chemo schedule for systemic therapy
                'name': 'liệu pháp toàn thân',
                'date': systemic.treatment_date,
                'timestamp': systemic.treatment_date
            })
        
        if not treatments:
            return None
        
        # Return the most recent treatment
        return max(treatments, key=lambda x: x['timestamp'])
    
    @staticmethod
    def get_last_visit_date(patient_id: int) -> datetime.date:
        """Get the last visit date for a patient"""
        # Check blood tests
        last_blood_test = BloodTest.query.filter_by(patient_id=patient_id)\
                                        .order_by(BloodTest.test_date.desc()).first()
        
        if last_blood_test:
            return last_blood_test.test_date
        
        # If no blood tests, use patient creation date
        patient = Patient.query.get(patient_id)
        return patient.created_at.date() if patient else datetime.now().date()
    
    @staticmethod
    def assess_followup_priority(patient_id: int, latest_treatment: Dict) -> str:
        """Assess follow-up priority based on risk factors"""
        # Get latest PSA
        latest_blood_test = BloodTest.query.filter_by(patient_id=patient_id)\
                                          .order_by(BloodTest.test_date.desc()).first()
        
        if latest_blood_test and latest_blood_test.psa_level:
            if latest_blood_test.psa_level > 10.0:
                return 'high'
            elif latest_blood_test.psa_level > 4.0:
                return 'moderate'
        
        # Check treatment type
        if latest_treatment['type'] in ['post_surgery', 'chemotherapy']:
            return 'moderate'
        
        return 'routine'

class NotificationService:
    """SMS and Email Notification Service"""
    
    def __init__(self):
        self.twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER')
        
        # Email configuration
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.email_user = os.environ.get('EMAIL_USER')
        self.email_password = os.environ.get('EMAIL_PASSWORD')
    
    def send_followup_reminder_sms(self, patient: Patient, followup_info: Dict) -> bool:
        """Send SMS reminder for follow-up appointment"""
        if not all([self.twilio_sid, self.twilio_token, self.twilio_phone]):
            logger.warning("Twilio credentials not configured")
            return False
        
        if not patient.phone_number:
            logger.warning(f"No phone number for patient {patient.id}")
            return False
        
        try:
            from twilio.rest import Client
            client = Client(self.twilio_sid, self.twilio_token)
            
            message_body = f"""
Nhắc nhở tái khám - Bệnh viện Ung bướu

Kính gửi {patient.full_name},
Bạn có lịch tái khám ngày {followup_info['next_date'].strftime('%d/%m/%Y')}.
Lý do: {followup_info['reason']}
Vui lòng liên hệ để xác nhận lịch hẹn.
            """.strip()
            
            message = client.messages.create(
                body=message_body,
                from_=self.twilio_phone,
                to=patient.phone_number
            )
            
            logger.info(f"SMS sent to {patient.phone_number}: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    def send_followup_reminder_email(self, patient: Patient, followup_info: Dict) -> bool:
        """Send email reminder for follow-up appointment"""
        if not all([self.email_user, self.email_password]):
            logger.warning("Email credentials not configured")
            return False
        
        if not patient.email:
            logger.warning(f"No email for patient {patient.id}")
            return False
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.email_user
            msg['To'] = patient.email
            msg['Subject'] = "Nhắc nhở tái khám - Bệnh viện Ung bướu"
            
            body = f"""
Kính gửi {patient.full_name},

Đây là thông báo nhắc nhở về lịch tái khám của quý bệnh nhân:

📅 Ngày tái khám: {followup_info['next_date'].strftime('%d/%m/%Y')}
📋 Lý do: {followup_info['reason']}
🔄 Chu kỳ theo dõi: {followup_info['interval']}
⚠️ Mức độ ưu tiên: {followup_info['priority']}

Để đảm bảo việc điều trị và theo dõi hiệu quả, vui lòng:
• Liên hệ với bệnh viện để xác nhận lịch hẹn
• Chuẩn bị các xét nghiệm cần thiết
• Mang theo hồ sơ bệnh án và thuốc đang sử dụng

Mọi thắc mắc xin liên hệ: [Số điện thoại bệnh viện]

Trân trọng,
Bệnh viện Ung bướu
            """
            
            msg.attach(MimeText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_user, patient.email, text)
            server.quit()
            
            logger.info(f"Email sent to {patient.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_psa_alert(self, patient: Patient, psa_analysis: Dict) -> bool:
        """Send alert for concerning PSA trends"""
        if psa_analysis['risk_level'] not in ['moderate', 'high']:
            return False
        
        # Send to both patient and healthcare team
        success = True
        
        # Patient notification
        if patient.phone_number:
            success &= self.send_psa_alert_sms(patient, psa_analysis)
        
        if patient.email:
            success &= self.send_psa_alert_email(patient, psa_analysis)
        
        return success
    
    def send_psa_alert_sms(self, patient: Patient, psa_analysis: Dict) -> bool:
        """Send SMS alert for PSA changes"""
        try:
            from twilio.rest import Client
            client = Client(self.twilio_sid, self.twilio_token)
            
            risk_text = {
                'moderate': 'Cần theo dõi',
                'high': 'CẦN KHẨN CẤP'
            }[psa_analysis['risk_level']]
            
            message_body = f"""
Cảnh báo PSA - {risk_text}

{patient.full_name},
Kết quả PSA: {psa_analysis['current_psa']:.1f} ng/mL
Mức độ: {risk_text}

Vui lòng liên hệ bác sĩ ngay.
            """.strip()
            
            message = client.messages.create(
                body=message_body,
                from_=self.twilio_phone,
                to=patient.phone_number
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send PSA alert SMS: {e}")
            return False
    
    def send_psa_alert_email(self, patient: Patient, psa_analysis: Dict) -> bool:
        """Send email alert for PSA changes"""
        try:
            msg = MimeMultipart()
            msg['From'] = self.email_user
            msg['To'] = patient.email
            msg['Subject'] = f"Cảnh báo PSA - {patient.full_name}"
            
            alerts_text = '\n'.join([f"• {alert}" for alert in psa_analysis['alerts']])
            recommendations_text = '\n'.join([f"• {rec}" for rec in psa_analysis['recommendations']])
            
            body = f"""
CẢNH BÁO PSA - MỨC ĐỘ {psa_analysis['risk_level'].upper()}

Kính gửi {patient.full_name},

Kết quả phân tích PSA mới nhất cho thấy:

📊 PSA hiện tại: {psa_analysis['current_psa']:.1f} ng/mL
📈 Xu hướng: {psa_analysis['trend']}
⏱️ Thời gian nhân đôi PSA: {psa_analysis['doubling_time']} tháng (nếu có)
🚀 Vận tốc PSA: {psa_analysis['velocity']} ng/mL/năm (nếu có)

⚠️ CẢNH BÁO:
{alerts_text}

💡 KHUYẾN NGHỊ:
{recommendations_text}

Vui lòng liên hệ với bác sĩ điều trị ngay để được tư vấn chi tiết.

Trân trọng,
Hệ thống theo dõi bệnh nhân
            """
            
            msg.attach(MimeText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_user, patient.email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send PSA alert email: {e}")
            return False

# Utility functions for easy integration
def get_patient_psa_analysis(patient_id: int) -> Dict:
    """Get comprehensive PSA analysis for a patient"""
    return PSAAnalyzer.analyze_psa_trend(patient_id)

def get_patient_followup_schedule(patient_id: int) -> Dict:
    """Get next follow-up schedule for a patient"""
    return FollowUpScheduler.calculate_next_followup(patient_id)

def send_followup_reminders(patient_id: int) -> Dict:
    """Send follow-up reminders to a patient"""
    try:
        patient = Patient.query.get(patient_id)
        if not patient:
            return {'success': False, 'error': 'Patient not found'}
        
        followup_info = get_patient_followup_schedule(patient_id)
        if 'error' in followup_info:
            return {'success': False, 'error': followup_info['error']}
        
        notification_service = NotificationService()
        sms_sent = notification_service.send_followup_reminder_sms(patient, followup_info)
        email_sent = notification_service.send_followup_reminder_email(patient, followup_info)
        
        return {
            'success': True,
            'sms_sent': sms_sent,
            'email_sent': email_sent,
            'followup_date': followup_info['next_date']
        }
        
    except Exception as e:
        logger.error(f"Error sending follow-up reminders: {e}")
        return {'success': False, 'error': str(e)}

def check_and_alert_psa_changes(patient_id: int) -> Dict:
    """Check PSA trends and send alerts if needed"""
    try:
        psa_analysis = get_patient_psa_analysis(patient_id)
        
        if psa_analysis['status'] != 'success':
            return {'success': False, 'error': psa_analysis.get('message', 'Analysis failed')}
        
        if psa_analysis['risk_level'] in ['moderate', 'high']:
            patient = Patient.query.get(patient_id)
            notification_service = NotificationService()
            alert_sent = notification_service.send_psa_alert(patient, psa_analysis)
            
            return {
                'success': True,
                'alert_sent': alert_sent,
                'risk_level': psa_analysis['risk_level'],
                'alerts': psa_analysis['alerts']
            }
        
        return {
            'success': True,
            'alert_sent': False,
            'risk_level': psa_analysis['risk_level'],
            'message': 'PSA trong giới hạn bình thường'
        }
        
    except Exception as e:
        logger.error(f"Error checking PSA changes: {e}")
        return {'success': False, 'error': str(e)}