import json
import logging
import os
from datetime import datetime
from google import genai
from google.genai import types

# Initialize Gemini client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def evaluate_prostate_cancer_risk(patient_data):
    """
    Đánh giá nguy cơ ung thư tuyến tiền liệt bằng AI Gemini
    Evaluate prostate cancer risk using AI Gemini
    """
    try:
        # Prepare patient data for AI analysis
        clinical_data = {
            'age': patient_data.get('age'),
            'psa_level': patient_data.get('initial_psa'),
            'gleason_score': patient_data.get('gleason_score'),
            'clinical_t': patient_data.get('clinical_t'),
            'clinical_n': patient_data.get('clinical_n'),
            'clinical_m': patient_data.get('clinical_m'),
            'pathological_t': patient_data.get('pathological_t'),
            'pathological_n': patient_data.get('pathological_n'),
            'pathological_m': patient_data.get('pathological_m'),
            'sampling_method': patient_data.get('sampling_method')
        }

        # Create comprehensive prompt for AI analysis
        prompt = f"""
        Bạn là một chuyên gia ung thư học chuyên về ung thư tuyến tiền liệt. Hãy phân tích dữ liệu bệnh nhân và đưa ra đánh giá nguy cơ chi tiết.

        THÔNG TIN BỆNH NHÂN:
        - Tuổi: {clinical_data['age']} tuổi
        - PSA ban đầu: {clinical_data['psa_level']} ng/mL
        - Điểm Gleason: {clinical_data['gleason_score']}
        - Giai đoạn T lâm sàng: {clinical_data['clinical_t']}
        - Giai đoạn N lâm sàng: {clinical_data['clinical_n']}
        - Giai đoạn M lâm sàng: {clinical_data['clinical_m']}
        - Giai đoạn T giải phẫu bệnh: {clinical_data['pathological_t']}
        - Giai đoạn N giải phẫu bệnh: {clinical_data['pathological_n']}
        - Giai đoạn M giải phẫu bệnh: {clinical_data['pathological_m']}
        - Phương pháp lấy mẫu: {clinical_data['sampling_method']}

        YÊU CẦU PHÂN TÍCH:
        1. Phân tầng nguy cơ theo thang điểm D'Amico (LOW, INTERMEDIATE, HIGH)
        2. Đánh giá tiên lượng sống sót 5 năm và 10 năm
        3. Khuyến nghị phương pháp điều trị phù hợp
        4. Đề xuất lịch theo dõi và xét nghiệm
        5. Các yếu tố nguy cơ cần lưu ý

        Hãy trả lời bằng tiếng Việt, ngắn gọn và dễ hiểu cho nhân viên y tế.
        Định dạng kết quả theo JSON với các trường: risk_level, survival_5yr, survival_10yr, treatment_recommendation, follow_up_plan, risk_factors.
        """

        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        if response.text:
            result = json.loads(response.text)
            
            # Map risk level to standard categories
            risk_mapping = {
                'LOW': 'THẤP',
                'INTERMEDIATE': 'TRUNG BÌNH', 
                'HIGH': 'CAO',
                'VERY_HIGH': 'RẤT CAO'
            }
            
            # Process and validate the result
            processed_result = {
                'risk_score': result.get('risk_level', 'TRUNG BÌNH'),
                'assessment_summary': f"""
🎯 PHÂN TẦNG NGUY CƠ: {risk_mapping.get(result.get('risk_level', 'INTERMEDIATE'), 'TRUNG BÌNH')}

📊 TIÊN LƯỢNG SỐNG SÓT:
• 5 năm: {result.get('survival_5yr', 'Chưa xác định')}
• 10 năm: {result.get('survival_10yr', 'Chưa xác định')}

💊 KHUYẾN NGHỊ ĐIỀU TRỊ:
{result.get('treatment_recommendation', 'Cần tham khảo thêm ý kiến chuyên gia')}

📅 KẾ HOẠCH THEO DÕI:
{result.get('follow_up_plan', 'Theo dõi định kỳ 3-6 tháng')}

⚠️ YẾU TỐ NGUY CƠ:
{result.get('risk_factors', 'Cần theo dõi chặt chẽ các chỉ số PSA và triệu chứng lâm sàng')}
                """.strip(),
                'assessment_date': datetime.utcnow()
            }
            
            return processed_result
            
        else:
            raise ValueError("Không nhận được phản hồi từ AI")
            
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in AI assessment: {e}")
        return {
            'risk_score': 'TRUNG BÌNH',
            'assessment_summary': 'Lỗi phân tích dữ liệu. Vui lòng tham khảo ý kiến bác sĩ chuyên khoa.',
            'assessment_date': datetime.utcnow()
        }
    except Exception as e:
        logging.error(f"Error in AI risk assessment: {e}")
        return {
            'risk_score': 'TRUNG BÌNH', 
            'assessment_summary': 'Không thể thực hiện đánh giá tự động. Vui lòng tham khảo ý kiến bác sĩ chuyên khoa.',
            'assessment_date': datetime.utcnow()
        }

def analyze_pathology_image(image_path):
    """
    Phân tích hình ảnh giải phẫu bệnh bằng AI Gemini
    Analyze pathology image using AI Gemini
    """
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            
        prompt = """
        Bạn là một chuyên gia giải phẫu bệnh chuyên về ung thư tuyến tiền liệt. 
        Hãy phân tích hình ảnh giải phẫu bệnh này và mô tả:
        
        1. Đặc điểm mô học quan sát được
        2. Mức độ biệt hóa tế bào
        3. Dấu hiệu xâm lấn mạch máu hoặc thần kinh
        4. Đề xuất điểm Gleason (nếu có thể)
        5. Các phát hiện bất thường khác
        
        Trả lời bằng tiếng Việt, chuyên nghiệp và chi tiết.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg",
                ),
                prompt
            ],
        )
        
        return response.text if response.text else "Không thể phân tích hình ảnh."
        
    except Exception as e:
        logging.error(f"Error analyzing pathology image: {e}")
        return "Lỗi phân tích hình ảnh. Vui lòng kiểm tra lại file hình ảnh."