"""
Adverse Event Management Module
Quản lý Biến cố Bất lợi

This module provides comprehensive adverse event tracking with CTCAE grading,
treatment correlation, and standardized reporting for prostate cancer treatments.
"""

from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from enum import Enum
import logging

from app import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CTCAEGrade(Enum):
    """CTCAE (Common Terminology Criteria for Adverse Events) Grading"""
    GRADE_1 = "1"  # Mild
    GRADE_2 = "2"  # Moderate
    GRADE_3 = "3"  # Severe
    GRADE_4 = "4"  # Life-threatening
    GRADE_5 = "5"  # Death

class AdverseEventCategory(Enum):
    """Standard adverse event categories for prostate cancer"""
    GENITOURINARY = "genitourinary"
    GASTROINTESTINAL = "gastrointestinal"
    SEXUAL = "sexual"
    NEUROLOGICAL = "neurological"
    HEMATOLOGICAL = "hematological"
    CARDIOVASCULAR = "cardiovascular"
    ENDOCRINE = "endocrine"
    MUSCULOSKELETAL = "musculoskeletal"
    DERMATOLOGICAL = "dermatological"
    GENERAL = "general"

# Predefined adverse events for prostate cancer treatments
PROSTATE_ADVERSE_EVENTS = {
    'surgery': [
        {
            'name': 'Rối loạn cương dương',
            'category': AdverseEventCategory.SEXUAL,
            'ctcae_term': 'Erectile dysfunction',
            'grades': {
                '1': 'Giảm nhẹ chức năng cương',
                '2': 'Giảm vừa chức năng cương, có thể quan hệ',
                '3': 'Mất hoàn toàn chức năng cương',
                '4': 'Không áp dụng',
                '5': 'Không áp dụng'
            }
        },
        {
            'name': 'Tiểu không tự chủ',
            'category': AdverseEventCategory.GENITOURINARY,
            'ctcae_term': 'Urinary incontinence',
            'grades': {
                '1': 'Chảy nước tiểu khi ho, hắt hơi',
                '2': 'Cần dùng miếng lót, ảnh hưởng sinh hoạt',
                '3': 'Cần can thiệp phẫu thuật',
                '4': 'Biến chứng đe dọa tính mạng',
                '5': 'Tử vong'
            }
        },
        {
            'name': 'Hẹp niệu đạo',
            'category': AdverseEventCategory.GENITOURINARY,
            'ctcae_term': 'Urethral stricture',
            'grades': {
                '1': 'Triệu chứng nhẹ, không cần can thiệp',
                '2': 'Can thiệp không xâm lấn',
                '3': 'Can thiệp xâm lấn',
                '4': 'Biến chứng đe dọa tính mạng',
                '5': 'Tử vong'
            }
        }
    ],
    'radiation': [
        {
            'name': 'Viêm bàng quang do xạ',
            'category': AdverseEventCategory.GENITOURINARY,
            'ctcae_term': 'Radiation cystitis',
            'grades': {
                '1': 'Triệu chứng nhẹ, không cần điều trị',
                '2': 'Cần điều trị nội khoa',
                '3': 'Chảy máu, cần can thiệp',
                '4': 'Biến chứng đe dọa tính mạng',
                '5': 'Tử vong'
            }
        },
        {
            'name': 'Viêm trực tràng do xạ',
            'category': AdverseEventCategory.GASTROINTESTINAL,
            'ctcae_term': 'Radiation proctitis',
            'grades': {
                '1': 'Triệu chứng nhẹ',
                '2': 'Chảy máu ít, đau vừa',
                '3': 'Chảy máu nhiều, đau nặng',
                '4': 'Biến chứng đe dọa tính mạng',
                '5': 'Tử vong'
            }
        },
        {
            'name': 'Mệt mỏi do xạ trị',
            'category': AdverseEventCategory.GENERAL,
            'ctcae_term': 'Fatigue',
            'grades': {
                '1': 'Mệt mỏi nhẹ',
                '2': 'Mệt mỏi vừa, hạn chế hoạt động',
                '3': 'Mệt mỏi nặng, cần nghỉ ngơi',
                '4': 'Không áp dụng',
                '5': 'Không áp dụng'
            }
        }
    ],
    'hormone_therapy': [
        {
            'name': 'Bốc hỏa',
            'category': AdverseEventCategory.ENDOCRINE,
            'ctcae_term': 'Hot flashes',
            'grades': {
                '1': 'Nhẹ, không cần điều trị',
                '2': 'Vừa, ảnh hưởng sinh hoạt',
                '3': 'Nặng, cần điều trị',
                '4': 'Không áp dụng',
                '5': 'Không áp dụng'
            }
        },
        {
            'name': 'Loãng xương',
            'category': AdverseEventCategory.MUSCULOSKELETAL,
            'ctcae_term': 'Osteoporosis',
            'grades': {
                '1': 'Giảm mật độ xương, không triệu chứng',
                '2': 'Loãng xương, không gãy',
                '3': 'Gãy xương bệnh lý',
                '4': 'Biến chứng đe dọa tính mạng',
                '5': 'Tử vong'
            }
        },
        {
            'name': 'Tăng cân',
            'category': AdverseEventCategory.ENDOCRINE,
            'ctcae_term': 'Weight gain',
            'grades': {
                '1': 'Tăng cân < 5%',
                '2': 'Tăng cân 5-20%',
                '3': 'Tăng cân > 20%',
                '4': 'Không áp dụng',
                '5': 'Không áp dụng'
            }
        }
    ],
    'chemotherapy': [
        {
            'name': 'Giảm bạch cầu',
            'category': AdverseEventCategory.HEMATOLOGICAL,
            'ctcae_term': 'Leukopenia',
            'grades': {
                '1': 'WBC 3000-4000/mm³',
                '2': 'WBC 2000-3000/mm³',
                '3': 'WBC 1000-2000/mm³',
                '4': 'WBC < 1000/mm³',
                '5': 'Tử vong'
            }
        },
        {
            'name': 'Buồn nôn, nôn',
            'category': AdverseEventCategory.GASTROINTESTINAL,
            'ctcae_term': 'Nausea/Vomiting',
            'grades': {
                '1': 'Buồn nôn nhẹ, ăn được bình thường',
                '2': 'Buồn nôn vừa, giảm khẩu phần',
                '3': 'Buồn nôn nặng, không ăn được',
                '4': 'Biến chứng đe dọa tính mạng',
                '5': 'Tử vong'
            }
        },
        {
            'name': 'Rụng tóc',
            'category': AdverseEventCategory.DERMATOLOGICAL,
            'ctcae_term': 'Alopecia',
            'grades': {
                '1': 'Rụng tóc < 50%',
                '2': 'Rụng tóc > 50%',
                '3': 'Rụng tóc hoàn toàn',
                '4': 'Không áp dụng',
                '5': 'Không áp dụng'
            }
        }
    ],
    'systemic_therapy': [
        {
            'name': 'Phát ban da',
            'category': AdverseEventCategory.DERMATOLOGICAL,
            'ctcae_term': 'Rash',
            'grades': {
                '1': 'Phát ban < 10% diện tích da',
                '2': 'Phát ban 10-30% diện tích da',
                '3': 'Phát ban > 30% diện tích da',
                '4': 'Phát ban có biến chứng nặng',
                '5': 'Tử vong'
            }
        },
        {
            'name': 'Tăng huyết áp',
            'category': AdverseEventCategory.CARDIOVASCULAR,
            'ctcae_term': 'Hypertension',
            'grades': {
                '1': 'Tăng huyết áp nhẹ',
                '2': 'Cần điều trị nội khoa',
                '3': 'Cần nhiều thuốc điều trị',
                '4': 'Biến chứng đe dọa tính mạng',
                '5': 'Tử vong'
            }
        }
    ]
}

# AdverseEvent model is defined in models.py to avoid conflicts
from models import AdverseEvent

class AdverseEventManager:
    """Manager class for adverse event operations"""
    
    @staticmethod
    def get_events_by_treatment_type(treatment_type: str) -> List[Dict]:
        """Get predefined adverse events for a treatment type"""
        return PROSTATE_ADVERSE_EVENTS.get(treatment_type, [])
    
    @staticmethod
    def create_adverse_event(patient_id: int, event_data: Dict) -> AdverseEvent:
        """Create a new adverse event"""
        try:
            adverse_event = AdverseEvent(
                patient_id=patient_id,
                treatment_type=event_data.get('treatment_type'),
                treatment_event_id=event_data.get('treatment_event_id'),
                event_name=event_data.get('event_name'),
                ctcae_term=event_data.get('ctcae_term'),
                category=event_data.get('category'),
                ctcae_grade=event_data.get('ctcae_grade'),
                grade_description=event_data.get('grade_description'),
                onset_date=event_data.get('onset_date'),
                resolution_date=event_data.get('resolution_date'),
                is_ongoing=event_data.get('is_ongoing', True),
                severity_assessment=event_data.get('severity_assessment'),
                causality_assessment=event_data.get('causality_assessment'),
                action_taken=event_data.get('action_taken'),
                outcome=event_data.get('outcome'),
                treatment_modification=event_data.get('treatment_modification'),
                concomitant_medication=event_data.get('concomitant_medication'),
                notes=event_data.get('notes')
            )
            
            db.session.add(adverse_event)
            db.session.commit()
            
            logger.info(f"Created adverse event {adverse_event.id} for patient {patient_id}")
            return adverse_event
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating adverse event: {e}")
            raise
    
    @staticmethod
    def get_patient_adverse_events(patient_id: int, treatment_type: Optional[str] = None) -> List[AdverseEvent]:
        """Get all adverse events for a patient, optionally filtered by treatment type"""
        query = AdverseEvent.query.filter_by(patient_id=patient_id)
        
        if treatment_type:
            query = query.filter_by(treatment_type=treatment_type)
        
        return query.order_by(AdverseEvent.onset_date.desc()).all()
    
    @staticmethod
    def get_treatment_related_events(treatment_type: str, treatment_event_id: int) -> List[AdverseEvent]:
        """Get adverse events related to a specific treatment"""
        return AdverseEvent.query.filter_by(
            treatment_type=treatment_type,
            treatment_event_id=treatment_event_id
        ).all()
    
    @staticmethod
    def update_adverse_event(event_id: int, update_data: Dict) -> AdverseEvent:
        """Update an existing adverse event"""
        try:
            adverse_event = AdverseEvent.query.get(event_id)
            if not adverse_event:
                raise ValueError("Adverse event not found")
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(adverse_event, field):
                    setattr(adverse_event, field, value)
            
            adverse_event.updated_at = datetime.now()
            db.session.commit()
            
            logger.info(f"Updated adverse event {event_id}")
            return adverse_event
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating adverse event: {e}")
            raise
    
    @staticmethod
    def resolve_adverse_event(event_id: int, resolution_date: date, outcome: str) -> AdverseEvent:
        """Mark an adverse event as resolved"""
        return AdverseEventManager.update_adverse_event(event_id, {
            'resolution_date': resolution_date,
            'is_ongoing': False,
            'outcome': outcome
        })
    
    @staticmethod
    def get_events_by_grade(patient_id: int, min_grade: int = 3) -> List[AdverseEvent]:
        """Get high-grade adverse events for a patient"""
        return AdverseEvent.query.filter(
            AdverseEvent.patient_id == patient_id,
            AdverseEvent.ctcae_grade.cast(db.Integer) >= min_grade
        ).order_by(AdverseEvent.onset_date.desc()).all()
    
    @staticmethod
    def get_ongoing_events(patient_id: int) -> List[AdverseEvent]:
        """Get ongoing adverse events for a patient"""
        return AdverseEvent.query.filter_by(
            patient_id=patient_id,
            is_ongoing=True
        ).order_by(AdverseEvent.onset_date.desc()).all()

class AdverseEventAnalyzer:
    """Analyzer for adverse event patterns and correlations"""
    
    @staticmethod
    def analyze_treatment_safety_profile(patient_id: int) -> Dict:
        """Analyze safety profile across all treatments for a patient"""
        try:
            events = AdverseEventManager.get_patient_adverse_events(patient_id)
            
            if not events:
                return {
                    'total_events': 0,
                    'by_treatment': {},
                    'by_grade': {},
                    'ongoing_events': 0,
                    'safety_summary': 'Chưa có biến cố bất lợi được ghi nhận'
                }
            
            # Analysis by treatment type
            by_treatment = {}
            for event in events:
                treatment = event.treatment_type
                if treatment not in by_treatment:
                    by_treatment[treatment] = {
                        'total': 0,
                        'by_grade': {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0},
                        'ongoing': 0
                    }
                
                by_treatment[treatment]['total'] += 1
                by_treatment[treatment]['by_grade'][event.ctcae_grade] += 1
                if event.is_ongoing:
                    by_treatment[treatment]['ongoing'] += 1
            
            # Analysis by grade
            by_grade = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
            for event in events:
                by_grade[event.ctcae_grade] += 1
            
            # Ongoing events
            ongoing_events = len([e for e in events if e.is_ongoing])
            
            # Safety summary
            high_grade_events = by_grade['3'] + by_grade['4'] + by_grade['5']
            if high_grade_events > 0:
                safety_level = 'Cần theo dõi chặt chẽ'
            elif by_grade['2'] > 3:
                safety_level = 'Cần theo dõi'
            else:
                safety_level = 'Ổn định'
            
            return {
                'total_events': len(events),
                'by_treatment': by_treatment,
                'by_grade': by_grade,
                'ongoing_events': ongoing_events,
                'high_grade_events': high_grade_events,
                'safety_level': safety_level,
                'safety_summary': f'{len(events)} biến cố, {high_grade_events} độ nặng, {ongoing_events} đang diễn ra'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing safety profile: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def generate_ctcae_report(patient_id: int, treatment_type: Optional[str] = None) -> Dict:
        """Generate standardized CTCAE report"""
        try:
            events = AdverseEventManager.get_patient_adverse_events(patient_id, treatment_type)
            
            report = {
                'patient_id': patient_id,
                'treatment_type': treatment_type,
                'report_date': datetime.now().date().isoformat(),
                'total_events': len(events),
                'events_by_category': {},
                'grade_distribution': {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0},
                'serious_adverse_events': [],
                'action_taken_summary': {},
                'events_detail': []
            }
            
            for event in events:
                # By category
                category = event.category
                if category not in report['events_by_category']:
                    report['events_by_category'][category] = 0
                report['events_by_category'][category] += 1
                
                # Grade distribution
                report['grade_distribution'][event.ctcae_grade] += 1
                
                # Serious adverse events (Grade 3+)
                if int(event.ctcae_grade) >= 3:
                    report['serious_adverse_events'].append({
                        'event_name': event.event_name,
                        'grade': event.ctcae_grade,
                        'onset_date': event.onset_date.isoformat(),
                        'outcome': event.outcome
                    })
                
                # Action taken summary
                if event.action_taken:
                    action = event.action_taken
                    if action not in report['action_taken_summary']:
                        report['action_taken_summary'][action] = 0
                    report['action_taken_summary'][action] += 1
                
                # Event details
                report['events_detail'].append(event.to_dict())
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating CTCAE report: {e}")
            return {'error': str(e)}

# Utility functions
def link_adverse_event_to_treatment(treatment_type: str, treatment_event_id: int, 
                                   event_name: str, ctcae_grade: str, 
                                   onset_date: date, patient_id: int) -> AdverseEvent:
    """Link an adverse event directly to a specific treatment"""
    
    # Get predefined event details
    predefined_events = PROSTATE_ADVERSE_EVENTS.get(treatment_type, [])
    event_details = None
    
    for event in predefined_events:
        if event['name'] == event_name:
            event_details = event
            break
    
    if not event_details:
        # Create custom event
        event_details = {
            'name': event_name,
            'category': AdverseEventCategory.GENERAL.value,
            'ctcae_term': event_name,
            'grades': {ctcae_grade: f'Độ {ctcae_grade}'}
        }
    
    event_data = {
        'treatment_type': treatment_type,
        'treatment_event_id': treatment_event_id,
        'event_name': event_name,
        'ctcae_term': event_details['ctcae_term'],
        'category': event_details['category'].value if isinstance(event_details['category'], AdverseEventCategory) else event_details['category'],
        'ctcae_grade': ctcae_grade,
        'grade_description': event_details['grades'].get(ctcae_grade, f'Độ {ctcae_grade}'),
        'onset_date': onset_date,
        'causality_assessment': 'probable'  # Default for treatment-linked events
    }
    
    return AdverseEventManager.create_adverse_event(patient_id, event_data)

def get_treatment_adverse_events_summary(patient_id: int) -> Dict:
    """Get summary of adverse events by treatment for a patient"""
    analyzer = AdverseEventAnalyzer()
    return analyzer.analyze_treatment_safety_profile(patient_id)

def generate_patient_safety_report(patient_id: int) -> Dict:
    """Generate comprehensive safety report for a patient"""
    analyzer = AdverseEventAnalyzer()
    return analyzer.generate_ctcae_report(patient_id)