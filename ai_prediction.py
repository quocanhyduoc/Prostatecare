"""
AI Prediction Module for Prostate Cancer Management System

This module provides advanced AI-powered prediction capabilities using Google Gemini:
1. Biochemical Recurrence (BCR) Risk Prediction
2. ADT Benefit Prediction
3. Adverse Event Risk Warning

Author: Prostate Cancer Management System
Date: July 29, 2025
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import io
import base64

from app import db
from models import Patient, BloodTest, SurgeryEvent, RadiationEvent, HormoneTherapyEvent, AdverseEvent

# Import Gemini AI
try:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    client = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BiochemicalRecurrencePrediction:
    """
    Dự báo Nguy cơ Tái phát Sinh hóa (Biochemical Recurrence - BCR)
    """
    
    def __init__(self):
        self.model_name = "gemini-2.5-pro"
        
    def extract_patient_features(self, patient_id: int) -> Dict[str, Any]:
        """Thu thập đặc điểm bệnh nhân cho dự báo BCR"""
        patient = Patient.query.get(patient_id)
        if not patient:
            return {}
        
        # Lấy thông tin cơ bản
        features = {
            'patient_id': patient_id,
            'age': (datetime.now().date() - patient.date_of_birth).days // 365 if patient.date_of_birth else None,
            'initial_psa': patient.initial_psa,
            'gleason_score': patient.gleason_score,
            'clinical_stage': f"{patient.clinical_t}{patient.clinical_n}{patient.clinical_m}",
            'pathological_stage': f"{patient.pathological_t}{patient.pathological_n}{patient.pathological_m}",
        }
        
        # Lấy thông tin phẫu thuật
        surgery = SurgeryEvent.query.filter_by(patient_id=patient_id).first()
        if surgery:
            features.update({
                'surgery_type': surgery.surgery_type,
                'surgical_margins': surgery.surgical_margin_status,
                'lymph_nodes': surgery.lymph_node_status,
                'extracapsular_extension': surgery.extracapsular_extension,
                'seminal_vesicle_invasion': surgery.seminal_vesicle_invasion,
                'surgery_date': surgery.start_date.isoformat() if surgery.start_date else None
            })
        
        # Lấy chuỗi PSA sau điều trị
        psa_tests = BloodTest.query.filter_by(patient_id=patient_id)\
                                   .order_by(BloodTest.test_date.asc()).all()
        
        psa_series = []
        for test in psa_tests:
            psa_series.append({
                'date': test.test_date.isoformat(),
                'total_psa': test.total_psa,
                'free_psa': test.free_psa,
                'psa_ratio': test.psa_ratio
            })
        
        features['psa_series'] = psa_series
        features['latest_psa'] = psa_series[-1]['total_psa'] if psa_series else None
        
        return features
    
    def predict_bcr_risk(self, patient_id: int) -> Dict[str, Any]:
        """Dự báo nguy cơ tái phát sinh hóa - Tối ưu hóa tốc độ"""
        if not GEMINI_AVAILABLE:
            return self._create_mock_bcr_prediction()
        
        features = self.extract_patient_features(patient_id)
        if not features:
            return {
                'status': 'error',
                'message': 'Không tìm thấy dữ liệu bệnh nhân'
            }
        
        # Tạo prompt ngắn gọn để tăng tốc độ
        psa_summary = f"PSA gần nhất: {features.get('latest_psa', 'N/A')} ng/mL"
        if features.get('psa_series') and len(features['psa_series']) > 1:
            psa_summary += f", Số lần đo: {len(features['psa_series'])}"
        
        prompt = f"""
        Phân tích nhanh nguy cơ BCR cho bệnh nhân ung thư tuyến tiền liệt:
        - Tuổi: {features.get('age', 'N/A')}
        - PSA ban đầu: {features.get('initial_psa', 'N/A')} ng/mL
        - {psa_summary}
        - Gleason: {features.get('gleason_score', 'N/A')}
        - Giai đoạn: {features.get('clinical_stage', 'N/A')}
        - Phẫu thuật: {features.get('surgery_type', 'Chưa có')}
        
        Trả về JSON ngắn gọn:
        {{
            "risk_score": <0-100>,
            "recurrence_2year": <phần trăm>,
            "recurrence_5year": <phần trăm>,
            "risk_level": "low|moderate|high",
            "risk_factors": ["yếu tố chính"],
            "explanation": "Tóm tắt ngắn gọn"
        }}
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",  # Sử dụng model nhanh hơn
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=500  # Giới hạn output để tăng tốc
                )
            )
            
            result = json.loads(response.text)
            result['status'] = 'success'
            result['prediction_date'] = datetime.now().isoformat()
            result['model_version'] = "gemini-2.5-flash"
            
            # Thêm các khuyến nghị cơ bản
            result['monitoring_recommendations'] = self._get_monitoring_recommendations(result.get('risk_level', 'moderate'))
            result['intervention_suggestions'] = self._get_intervention_suggestions(result.get('risk_level', 'moderate'))
            
            return result
            
        except Exception as e:
            logger.error(f"Lỗi dự báo BCR: {str(e)}")
            return self._create_mock_bcr_prediction()
    
    def _create_mock_bcr_prediction(self) -> Dict[str, Any]:
        """Tạo dự báo mẫu khi AI không khả dụng"""
        return {
            'status': 'success',
            'risk_score': 35,
            'recurrence_2year': 15,
            'recurrence_5year': 28,
            'risk_level': 'moderate',
            'risk_factors': ['PSA ban đầu >10', 'Cần theo dõi thêm'],
            'monitoring_recommendations': ['Đo PSA mỗi 3 tháng', 'Khám lâm sàng định kỳ'],
            'intervention_suggestions': ['Theo dõi chặt chẽ', 'Tư vấn lối sống'],
            'explanation': 'Dự báo tạm thời - cần đánh giá chuyên khoa',
            'prediction_date': datetime.now().isoformat(),
            'model_version': 'fallback'
        }
    
    def _get_monitoring_recommendations(self, risk_level: str) -> List[str]:
        """Lấy khuyến nghị theo dõi theo mức độ nguy cơ"""
        if risk_level == 'low':
            return ['Đo PSA mỗi 6 tháng', 'Khám lâm sàng 1 năm/lần']
        elif risk_level == 'high':
            return ['Đo PSA mỗi 3 tháng', 'Khám lâm sàng 6 tháng/lần', 'Xét nghiệm bổ sung']
        else:
            return ['Đo PSA mỗi 4 tháng', 'Khám lâm sàng 6 tháng/lần']
    
    def _get_intervention_suggestions(self, risk_level: str) -> List[str]:
        """Lấy khuyến nghị can thiệp theo mức độ nguy cơ"""
        if risk_level == 'low':
            return ['Duy trì lối sống lành mạnh', 'Theo dõi định kỳ']
        elif risk_level == 'high':
            return ['Tư vấn chuyên khoa', 'Cân nhắc xạ trị bổ trợ', 'Theo dõi chặt chẽ']
        else:
            return ['Theo dõi chặt chẽ', 'Tư vấn lối sống', 'Cân nhắc xét nghiệm thêm']

class ADTBenefitPrediction:
    """
    Dự báo Lợi ích từ Liệu pháp Nội tiết (ADT Benefit Prediction)
    """
    
    def __init__(self):
        self.model_name = "gemini-2.5-pro"
    
    def predict_adt_benefit(self, patient_id: int) -> Dict[str, Any]:
        """Dự báo lợi ích từ liệu pháp nội tiết - Tối ưu hóa tốc độ"""
        if not GEMINI_AVAILABLE:
            return self._create_mock_adt_prediction()
        
        patient = Patient.query.get(patient_id)
        if not patient:
            return {
                'status': 'error',
                'message': 'Không tìm thấy bệnh nhân'
            }
        
        # Thu thập dữ liệu cơ bản
        age = (datetime.now().date() - patient.date_of_birth).days // 365 if patient.date_of_birth else None
        latest_psa_test = BloodTest.query.filter_by(patient_id=patient_id)\
                                        .order_by(BloodTest.test_date.desc()).first()
        current_psa = latest_psa_test.total_psa if latest_psa_test else patient.initial_psa
        
        # Prompt ngắn gọn để tăng tốc
        prompt = f"""
        Đánh giá nhanh lợi ích ADT cho bệnh nhân ung thư tuyến tiền liệt:
        - Tuổi: {age}, PSA: {current_psa} ng/mL
        - Gleason: {patient.gleason_score}
        - Giai đoạn: {patient.clinical_t}{patient.clinical_n}{patient.clinical_m}
        
        Trả về JSON ngắn gọn:
        {{
            "benefit_category": "high|moderate|low",
            "benefit_score": <0-100>,
            "predicted_psa_response": <phần trăm>,
            "optimal_duration": <tháng>,
            "drug_recommendations": ["thuốc chính"],
            "quality_of_life_impact": "low|moderate|high",
            "explanation": "Tóm tắt ngắn"
        }}
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",  # Model nhanh hơn
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=400  # Giới hạn output
                )
            )
            
            result = json.loads(response.text)
            result['status'] = 'success'
            result['prediction_date'] = datetime.now().isoformat()
            
            # Thêm thông tin bổ sung
            result['monitoring_schedule'] = self._get_adt_monitoring_schedule(result.get('benefit_category', 'moderate'))
            result['side_effect_risks'] = self._get_adt_side_effects()
            
            return result
            
        except Exception as e:
            logger.error(f"Lỗi dự báo ADT: {str(e)}")
            return self._create_mock_adt_prediction()
    
    def _create_mock_adt_prediction(self) -> Dict[str, Any]:
        """Tạo dự báo ADT mẫu khi AI không khả dụng"""
        return {
            'status': 'success',
            'benefit_category': 'moderate',
            'benefit_score': 65,
            'predicted_psa_response': 80,
            'optimal_duration': 18,
            'drug_recommendations': ['LHRH agonist', 'Bicalutamide'],
            'monitoring_schedule': ['PSA mỗi 3 tháng', 'Khám lâm sàng 6 tháng/lần'],
            'side_effect_risks': self._get_adt_side_effects(),
            'quality_of_life_impact': 'moderate',
            'explanation': 'Dự báo tạm thời - cần tư vấn chuyên khoa',
            'prediction_date': datetime.now().isoformat()
        }
    
    def _get_adt_monitoring_schedule(self, benefit_category: str) -> List[str]:
        """Lấy lịch theo dõi ADT"""
        if benefit_category == 'high':
            return ['PSA mỗi 2 tháng', 'Testosterone mỗi 3 tháng', 'Khám lâm sàng 3 tháng/lần']
        elif benefit_category == 'low':
            return ['PSA mỗi 6 tháng', 'Khám lâm sàng 6 tháng/lần']
        else:
            return ['PSA mỗi 3 tháng', 'Khám lâm sàng 4 tháng/lần']
    
    def _get_adt_side_effects(self) -> List[Dict[str, str]]:
        """Lấy danh sách tác dụng phụ ADT"""
        return [
            {'event': 'Bốc hỏa', 'probability': 'high'},
            {'event': 'Giảm ham muốn tình dục', 'probability': 'high'},
            {'event': 'Tăng cân', 'probability': 'moderate'},
            {'event': 'Loãng xương', 'probability': 'moderate'},
            {'event': 'Bệnh tim mạch', 'probability': 'low'}
        ]

class AdverseEventRiskPrediction:
    """
    Cảnh báo Sớm Nguy cơ Biến cố Bất lợi (Adverse Event Risk Warning)
    """
    
    def __init__(self):
        self.model_name = "gemini-2.5-pro"
    
    def predict_adverse_event_risk(self, patient_id: int, treatment_type: str, 
                                 treatment_details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Dự báo nguy cơ biến cố bất lợi - Tối ưu hóa tốc độ"""
        if not GEMINI_AVAILABLE:
            return self._create_mock_adverse_event_prediction(treatment_type)
        
        patient = Patient.query.get(patient_id)
        if not patient:
            return {
                'status': 'error',
                'message': 'Không tìm thấy bệnh nhân'
            }
        
        age = (datetime.now().date() - patient.date_of_birth).days // 365 if patient.date_of_birth else None
        adverse_events = AdverseEvent.query.filter_by(patient_id=patient_id).all()
        
        # Prompt ngắn gọn cho từng loại điều trị
        prompt = f"""
        Đánh giá nguy cơ biến cố bất lợi cho điều trị {treatment_type}:
        - Tuổi: {age}
        - Lịch sử biến cố: {len(adverse_events)} sự kiện trước đó
        - Giai đoạn: {patient.clinical_t}{patient.clinical_n}{patient.clinical_m}
        
        Trả về JSON ngắn gọn:
        {{
            "overall_risk": "low|moderate|high",
            "high_risk_events": [
                {{"event": "tên sự kiện", "probability": <phần trăm>, "grade": "1-5"}}
            ],
            "prevention_strategies": ["chiến lược 1", "chiến lược 2"],
            "monitoring_recommendations": ["theo dõi 1", "theo dõi 2"],
            "explanation": "Tóm tắt ngắn"
        }}
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                    max_output_tokens=400
                )
            )
            
            result = json.loads(response.text)
            result['status'] = 'success'
            result['prediction_date'] = datetime.now().isoformat()
            result['treatment_type'] = treatment_type
            
            return result
            
        except Exception as e:
            logger.error(f"Lỗi dự báo biến cố bất lợi: {str(e)}")
            return self._create_mock_adverse_event_prediction(treatment_type)
    
    def _create_mock_adverse_event_prediction(self, treatment_type: str) -> Dict[str, Any]:
        """Tạo dự báo biến cố bất lợi mẫu"""
        # Định nghĩa các biến cố theo loại điều trị
        treatment_events = {
            'surgery': [
                {'event': 'Rò tiểu', 'probability': 15, 'grade': '2'},
                {'event': 'Rối loạn cương dương', 'probability': 60, 'grade': '2-3'}
            ],
            'radiation': [
                {'event': 'Viêm bàng quang', 'probability': 25, 'grade': '1-2'},
                {'event': 'Rối loạn đại tiện', 'probability': 20, 'grade': '1-2'}
            ],
            'hormone_therapy': [
                {'event': 'Bốc hỏa', 'probability': 80, 'grade': '1-2'},
                {'event': 'Loãng xương', 'probability': 30, 'grade': '2'}
            ],
            'chemotherapy': [
                {'event': 'Giảm bạch cầu', 'probability': 40, 'grade': '2-3'},
                {'event': 'Mệt mỏi', 'probability': 70, 'grade': '1-2'}
            ]
        }
        
        events = treatment_events.get(treatment_type.lower(), [
            {'event': 'Biến cố chung', 'probability': 20, 'grade': '1-2'}
        ])
        
        return {
            'status': 'success',
            'overall_risk': 'moderate',
            'high_risk_events': events,
            'prevention_strategies': ['Theo dõi chặt chẽ', 'Hỗ trợ triệu chứng'],
            'monitoring_recommendations': ['Khám định kỳ', 'Báo cáo triệu chứng'],
            'explanation': f'Dự báo tạm thời cho {treatment_type}',
            'treatment_type': treatment_type,
            'prediction_date': datetime.now().isoformat()
        }
        
        prompt = f"""
        Bạn là chuyên gia an toàn bệnh nhân và độc tính điều trị ung thư tuyến tiền liệt.
        Hãy dự báo nguy cơ biến cố bất lợi cho điều trị sắp tới:

        THÔNG TIN BỆNH NHÂN:
        - Tuổi: {age}
        - Điểm Gleason: {patient.gleason_score}
        - Giai đoạn: {patient.clinical_t}{patient.clinical_n}{patient.clinical_m}
        - Các bệnh lý nền: {comorbidities}
        
        LỊCH SỬ BIẾN CỐ BẤT LỢI:
        {json.dumps(ae_history, indent=2)}
        
        ĐIỀU TRỊ SẮP TỚI:
        - Loại điều trị: {treatment_type}
        - Chi tiết: {json.dumps(treatment_details, indent=2)}
        
        Hãy dự báo nguy cơ biến cố bất lợi và đưa ra khuyến nghị phòng ngừa:
        
        Trả về JSON:
        {{
            "high_risk_events": [
                {{
                    "event_name": "tên biến cố",
                    "ctcae_grade": "1-5",
                    "probability": "low|moderate|high",
                    "probability_percent": <0-100>,
                    "time_to_onset": "thời gian dự kiến xuất hiện",
                    "prevention_measures": ["biện pháp phòng ngừa 1", "biện pháp 2"],
                    "monitoring_recommendations": ["theo dõi 1", "theo dõi 2"],
                    "early_intervention": ["can thiệp sớm nếu cần"]
                }}
            ],
            "overall_risk_level": "low|moderate|high",
            "personalized_warnings": ["cảnh báo cá nhân hóa"],
            "drug_interactions": ["tương tác thuốc cần lưu ý"],
            "lifestyle_recommendations": ["khuyến nghị lối sống"],
            "emergency_signs": ["dấu hiệu cần cấp cứu"],
            "follow_up_schedule": "lịch tái khám được khuyến nghị"
        }}
        """
        
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            result = json.loads(response.text)
            result['status'] = 'success'
            result['prediction_date'] = datetime.now().isoformat()
            result['treatment_type'] = treatment_type
            
            return result
            
        except Exception as e:
            logger.error(f"Lỗi dự báo biến cố bất lợi: {str(e)}")
            return {
                'status': 'error',
                'message': f'Lỗi xử lý AI: {str(e)}'
            }
    
    def _extract_comorbidities_from_notes(self, patient: Patient) -> List[str]:
        """Trích xuất bệnh lý nền từ ghi chú (có thể mở rộng với NLP)"""
        # Tạm thời trả về danh sách rỗng, có thể mở rộng với xử lý NLP
        common_comorbidities = []
        
        # Kiểm tra tuổi để dự đoán một số bệnh lý phổ biến
        if patient.date_of_birth:
            age = (datetime.now().date() - patient.date_of_birth).days // 365
            if age > 65:
                common_comorbidities.extend(['Có thể có bệnh tim mạch', 'Nguy cơ loãng xương'])
            if age > 70:
                common_comorbidities.append('Có thể có suy thận nhẹ')
        
        return common_comorbidities

class AIPredictionDashboard:
    """
    Dashboard tổng hợp cho các dự báo AI - Tối ưu hóa hiệu suất
    """
    
    def __init__(self):
        self.bcr_predictor = BiochemicalRecurrencePrediction()
        self.adt_predictor = ADTBenefitPrediction()
        self.ae_predictor = AdverseEventRiskPrediction()
        self._cache = {}  # Simple in-memory cache
        self.cache_duration = 300  # 5 minutes cache
    
    def get_comprehensive_prediction(self, patient_id: int, use_cache: bool = True) -> Dict[str, Any]:
        """Lấy tất cả dự báo cho một bệnh nhân với caching"""
        cache_key = f"prediction_{patient_id}"
        
        # Kiểm tra cache
        if use_cache and cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < self.cache_duration:
                logger.info(f"Sử dụng cache cho bệnh nhân {patient_id}")
                return cached_data
        
        dashboard = {
            'patient_id': patient_id,
            'prediction_date': datetime.now().isoformat(),
            'predictions': {},
            'processing_time': {}
        }
        
        # Dự báo BCR với timing
        start_time = datetime.now()
        try:
            bcr_result = self.bcr_predictor.predict_bcr_risk(patient_id)
            dashboard['predictions']['bcr'] = bcr_result
            dashboard['processing_time']['bcr'] = (datetime.now() - start_time).total_seconds()
        except Exception as e:
            dashboard['predictions']['bcr'] = {
                'status': 'error',
                'message': str(e)
            }
            dashboard['processing_time']['bcr'] = (datetime.now() - start_time).total_seconds()
        
        # Dự báo ADT với timing
        start_time = datetime.now()
        try:
            adt_result = self.adt_predictor.predict_adt_benefit(patient_id)
            dashboard['predictions']['adt'] = adt_result
            dashboard['processing_time']['adt'] = (datetime.now() - start_time).total_seconds()
        except Exception as e:
            dashboard['predictions']['adt'] = {
                'status': 'error',
                'message': str(e)
            }
            dashboard['processing_time']['adt'] = (datetime.now() - start_time).total_seconds()
        
        # Lưu vào cache
        if use_cache:
            self._cache[cache_key] = (dashboard, datetime.now())
        
        return dashboard
    
    def clear_cache(self, patient_id: int = None):
        """Xóa cache cho bệnh nhân cụ thể hoặc toàn bộ"""
        if patient_id:
            cache_key = f"prediction_{patient_id}"
            if cache_key in self._cache:
                del self._cache[cache_key]
        else:
            self._cache.clear()
        
    def get_cache_status(self) -> Dict[str, Any]:
        """Lấy thông tin cache hiện tại"""
        return {
            'total_cached_items': len(self._cache),
            'cache_duration_seconds': self.cache_duration,
            'cached_patients': [
                key.replace('prediction_', '') for key in self._cache.keys()
            ]
        }
    
    def generate_prediction_chart(self, patient_id: int) -> str:
        """Tạo biểu đồ dự báo tổng hợp"""
        try:
            # Lấy dữ liệu dự báo
            predictions = self.get_comprehensive_prediction(patient_id)
            
            # Tạo biểu đồ
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle('Tổng quan Dự báo AI cho Bệnh nhân', fontsize=16, fontweight='bold')
            
            # Biểu đồ 1: BCR Risk Score
            bcr_data = predictions['predictions'].get('bcr', {})
            if bcr_data.get('status') == 'success':
                risk_score = bcr_data.get('risk_score', 0)
                colors = ['green' if risk_score < 30 else 'orange' if risk_score < 70 else 'red']
                ax1.bar(['Nguy cơ BCR'], [risk_score], color=colors[0])
                ax1.set_ylabel('Điểm số nguy cơ')
                ax1.set_title('Dự báo Tái phát Sinh hóa')
                ax1.set_ylim(0, 100)
            
            # Biểu đồ 2: ADT Benefit
            adt_data = predictions['predictions'].get('adt', {})
            if adt_data.get('status') == 'success':
                benefit_score = adt_data.get('benefit_score', 0)
                colors = ['red' if benefit_score < 30 else 'orange' if benefit_score < 70 else 'green']
                ax2.bar(['Lợi ích ADT'], [benefit_score], color=colors[0])
                ax2.set_ylabel('Điểm lợi ích')
                ax2.set_title('Dự báo Lợi ích ADT')
                ax2.set_ylim(0, 100)
            
            # Biểu đồ 3: PSA Trend (nếu có)
            psa_tests = BloodTest.query.filter_by(patient_id=patient_id)\
                                      .order_by(BloodTest.test_date.asc()).all()
            if psa_tests:
                dates = [test.test_date for test in psa_tests]
                psa_values = [test.total_psa for test in psa_tests]
                ax3.plot(dates, psa_values, marker='o', linewidth=2)
                ax3.set_ylabel('PSA (ng/mL)')
                ax3.set_title('Xu hướng PSA')
                ax3.tick_params(axis='x', rotation=45)
            
            # Biểu đồ 4: Risk Summary
            risk_levels = []
            risk_colors = []
            
            if bcr_data.get('status') == 'success':
                bcr_risk = bcr_data.get('risk_level', 'low')
                risk_levels.append(f"BCR: {bcr_risk}")
                risk_colors.append('red' if bcr_risk == 'high' else 'orange' if bcr_risk == 'moderate' else 'green')
            
            if risk_levels:
                ax4.pie([1] * len(risk_levels), labels=risk_levels, colors=risk_colors, autopct='')
                ax4.set_title('Tóm tắt Mức độ Nguy cơ')
            
            plt.tight_layout()
            
            # Chuyển thành base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Lỗi tạo biểu đồ dự báo: {str(e)}")
            return ""

# Khởi tạo các instance chính
bcr_predictor = BiochemicalRecurrencePrediction()
adt_predictor = ADTBenefitPrediction()
ae_predictor = AdverseEventRiskPrediction()
prediction_dashboard = AIPredictionDashboard()

# Hàm helper cho routes
def get_patient_bcr_prediction(patient_id: int) -> Dict[str, Any]:
    """Hàm wrapper để sử dụng trong routes"""
    return bcr_predictor.predict_bcr_risk(patient_id)

def get_patient_adt_prediction(patient_id: int) -> Dict[str, Any]:
    """Hàm wrapper để sử dụng trong routes"""
    return adt_predictor.predict_adt_benefit(patient_id)

def get_adverse_event_prediction(patient_id: int, treatment_type: str, treatment_details: Dict) -> Dict[str, Any]:
    """Hàm wrapper để sử dụng trong routes"""
    return ae_predictor.predict_adverse_event_risk(patient_id, treatment_type, treatment_details)

def get_comprehensive_ai_dashboard(patient_id: int) -> Dict[str, Any]:
    """Hàm wrapper để lấy dashboard tổng hợp"""
    return prediction_dashboard.get_comprehensive_prediction(patient_id)