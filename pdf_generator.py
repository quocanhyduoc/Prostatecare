from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import os
from datetime import datetime
import tempfile

def generate_patient_report(patient, blood_tests=None):
    """Generate comprehensive patient report in PDF format"""
    
    # Register Unicode fonts for Vietnamese text support
    try:
        # Try to register DejaVu Sans fonts (supports Vietnamese)
        pdfmetrics.registerFont(TTFont('DejaVu', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVu-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
        vietnamese_font = 'DejaVu'
        vietnamese_font_bold = 'DejaVu-Bold'
    except:
        # Fallback to default fonts if DejaVu is not available
        vietnamese_font = 'Helvetica'
        vietnamese_font_bold = 'Helvetica-Bold'
    
    # Create a temporary file for the PDF
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        temp_file.name,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Container for the 'Flowable' objects
    story = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles with Vietnamese font support
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2c5aa0'),
        fontName=vietnamese_font_bold
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#2c5aa0'),
        fontName=vietnamese_font_bold
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        fontName=vietnamese_font
    )
    
    # Title
    title = Paragraph("BÁO CÁO BỆNH NHÂN UNG THƯ TIỀN LIỆT TUYẾN", title_style)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Patient Information Section
    story.append(Paragraph("THÔNG TIN HÀNH CHÍNH", heading_style))
    
    patient_data = [
        ['Mã bệnh nhân:', patient.patient_code],
        ['Họ và tên:', patient.full_name],
        ['Ngày sinh:', patient.date_of_birth.strftime('%d/%m/%Y')],
        ['Tuổi:', str(patient.age)],
        ['Số điện thoại:', patient.phone or 'Chưa có'],
        ['Địa chỉ:', patient.address or 'Chưa có'],
        ['Số BHYT:', patient.insurance_number or 'Chưa có'],
        ['Ngày tạo hồ sơ:', patient.created_at.strftime('%d/%m/%Y %H:%M')]
    ]
    
    patient_table = Table(patient_data, colWidths=[4*cm, 8*cm])
    patient_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), vietnamese_font_bold),
        ('FONTNAME', (1, 0), (1, -1), vietnamese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    story.append(patient_table)
    story.append(Spacer(1, 20))
    
    # Diagnosis Information Section
    story.append(Paragraph("THÔNG TIN CHẨN ĐOÁN", heading_style))
    
    diagnosis_data = [
        ['Ngày chẩn đoán:', patient.diagnosis_date.strftime('%d/%m/%Y')],
        ['Điểm Gleason:', patient.gleason_score or 'Chưa có'],
        ['Giai đoạn ung thư:', patient.cancer_stage or 'Chưa có'],
        ['PSA ban đầu:', f"{patient.initial_psa} ng/mL" if patient.initial_psa else 'Chưa có'],
        ['Phương pháp lấy mẫu:', get_sampling_method_text(patient.sampling_method)],
        ['Ngày lấy mẫu:', patient.sampling_date.strftime('%d/%m/%Y') if patient.sampling_date else 'Chưa có']
    ]
    
    diagnosis_table = Table(diagnosis_data, colWidths=[4*cm, 8*cm])
    diagnosis_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), vietnamese_font_bold),
        ('FONTNAME', (1, 0), (1, -1), vietnamese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    story.append(diagnosis_table)
    story.append(Spacer(1, 20))
    
    # TNM Staging Section
    if any([patient.clinical_t, patient.clinical_n, patient.clinical_m, 
            patient.pathological_t, patient.pathological_n, patient.pathological_m]):
        story.append(Paragraph("PHÂN GIAI ĐOẠN TNM", heading_style))
        
        tnm_data = [
            ['Giai đoạn', 'T (Khối u)', 'N (Hạch)', 'M (Di căn)'],
            ['Lâm sàng', patient.clinical_t or 'Chưa xác định', 
             patient.clinical_n or 'Chưa xác định', patient.clinical_m or 'Chưa xác định'],
            ['Giải phẫu bệnh', patient.pathological_t or 'Chưa xác định', 
             patient.pathological_n or 'Chưa xác định', patient.pathological_m or 'Chưa xác định']
        ]
        
        tnm_table = Table(tnm_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
        tnm_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), vietnamese_font_bold),
            ('FONTNAME', (0, 1), (0, -1), vietnamese_font_bold),
            ('FONTNAME', (1, 1), (-1, -1), vietnamese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f4f8'))
        ]))
        
        story.append(tnm_table)
        story.append(Spacer(1, 20))
    
    # AI Assessment Section
    if patient.ai_risk_score or patient.ai_staging_result:
        story.append(Paragraph("ĐÁNH GIÁ NGUY CƠ TỰ ĐỘNG BẰNG AI", heading_style))
        
        if patient.ai_risk_score:
            risk_para = Paragraph(f"<b>Mức độ nguy cơ:</b> {patient.ai_risk_score}", normal_style)
            story.append(risk_para)
        
        if patient.ai_assessment_date:
            date_para = Paragraph(f"<b>Ngày đánh giá:</b> {patient.ai_assessment_date.strftime('%d/%m/%Y %H:%M')}", normal_style)
            story.append(date_para)
        
        if patient.ai_staging_result:
            # Split long AI result into paragraphs
            ai_result_lines = patient.ai_staging_result.split('\n')
            for line in ai_result_lines:
                if line.strip():
                    ai_para = Paragraph(line.strip(), normal_style)
                    story.append(ai_para)
        
        story.append(Spacer(1, 20))
    
    # Blood Test Chart Section
    if blood_tests and len(blood_tests) > 1:
        story.append(Paragraph("BIỂU ĐỒ XÉT NGHIỆM MÁU", heading_style))
        
        # Create blood test chart
        try:
            chart_image = create_blood_test_chart(blood_tests)
            if chart_image:
                story.append(chart_image)
                story.append(Spacer(1, 10))
        except Exception as e:
            print(f"Could not create chart: {e}")
            # Add a note that chart couldn't be generated
            no_chart_text = Paragraph("Biểu đồ không thể tạo được do lỗi kỹ thuật.", normal_style)
            story.append(no_chart_text)
            story.append(Spacer(1, 10))
        
        # Blood test summary table
        recent_tests = blood_tests[-5:] if len(blood_tests) >= 5 else blood_tests
        
        test_data = [['Ngày', 'PSA tổng (ng/mL)', 'PSA tự do (ng/mL)', 'Testosterone (ng/dL)']]
        for test in recent_tests:
            test_data.append([
                test.test_date.strftime('%d/%m/%Y'),
                str(test.total_psa) if test.total_psa else '--',
                str(test.free_psa) if test.free_psa else '--',
                str(test.testosterone) if test.testosterone else '--'
            ])
        
        test_table = Table(test_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
        test_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), vietnamese_font_bold),
            ('FONTNAME', (0, 1), (-1, -1), vietnamese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f4f8'))
        ]))
        
        story.append(test_table)
    
    # Footer
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey,
        fontName=vietnamese_font
    )
    
    footer_text = f"Báo cáo được tạo tự động vào {datetime.now().strftime('%d/%m/%Y %H:%M')} - Hệ thống quản lý bệnh nhân ung thư tiền liệt tuyến"
    story.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(story)
    
    return temp_file.name

def create_blood_test_chart(blood_tests):
    """Create blood test trend chart"""
    try:
        # Prepare data
        dates = [test.test_date for test in blood_tests]
        psa_values = [test.total_psa for test in blood_tests if test.total_psa]
        psa_dates = [test.test_date for test in blood_tests if test.total_psa]
        
        if not psa_values:
            return None
        
        # Create figure
        plt.figure(figsize=(10, 6))
        plt.style.use('default')
        
        # Set Vietnamese font for matplotlib
        plt.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']
        
        # Plot PSA trend
        plt.plot(psa_dates, psa_values, marker='o', linewidth=2, markersize=6, color='#2c5aa0')
        plt.title('Biến thiên PSA theo thời gian', fontsize=14, fontweight='bold', pad=20)
        plt.xlabel('Ngày xét nghiệm', fontsize=12)
        plt.ylabel('PSA tổng (ng/mL)', fontsize=12)
        plt.grid(True, alpha=0.3)
        
        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.xticks(rotation=45)
        
        # Add reference line for normal PSA
        plt.axhline(y=4.0, color='red', linestyle='--', alpha=0.7, label='Ngưỡng bình thường (4.0 ng/mL)')
        plt.legend()
        
        plt.tight_layout()
        
        # Save to temporary image
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        # Create reportlab image directly from buffer
        img_buffer.seek(0)
        chart_image = Image(img_buffer, width=12*cm, height=7*cm)
        
        return chart_image
        
    except Exception as e:
        print(f"Error creating chart: {e}")
        return None

def get_sampling_method_text(method):
    """Convert sampling method code to Vietnamese text"""
    method_mapping = {
        'TRUS_BIOPSY': 'Sinh thiết qua trực tràng có siêu âm',
        'TRANSPERINEAL_BIOPSY': 'Sinh thiết qua tầng sinh môn',
        'SURGICAL_BIOPSY': 'Sinh thiết phẫu thuật',
        'NEEDLE_BIOPSY': 'Sinh thiết kim',
        'OTHER': 'Khác'
    }
    return method_mapping.get(method, method or 'Chưa có')