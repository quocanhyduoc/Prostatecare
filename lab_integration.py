"""
Lab Integration Module
Handles integration with external laboratory systems for automated blood test import
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os

# Import at the top to avoid circular imports
try:
    from app import db
    from models import Patient, BloodTest
except ImportError:
    # Handle the case where Flask app context is needed
    db = None
    Patient = None
    BloodTest = None

class LabIntegrationError(Exception):
    """Custom exception for lab integration errors"""
    pass

class BaseLabSystem:
    """Base class for lab system integrations"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def test_connection(self) -> bool:
        """Test connection to lab system"""
        raise NotImplementedError
    
    def get_patient_results(self, patient_identifier: str, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Get blood test results for a patient"""
        raise NotImplementedError
    
    def import_results_for_patient(self, patient_id: int, patient_identifier: str) -> Tuple[int, List[str]]:
        """Import blood test results for a specific patient"""
        raise NotImplementedError

class LabCorpIntegration(BaseLabSystem):
    """Integration with LabCorp system"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.labcorp.com/v1")
        
    def test_connection(self) -> bool:
        """Test LabCorp API connection"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logging.error(f"LabCorp connection test failed: {str(e)}")
            return False
    
    def get_patient_results(self, patient_identifier: str, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Get blood test results from LabCorp"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
            
        params = {
            'patient_id': patient_identifier,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'test_types': 'PSA,Testosterone'
        }
        
        try:
            response = self.session.get(f"{self.base_url}/results", params=params)
            response.raise_for_status()
            return response.json().get('results', [])
        except Exception as e:
            logging.error(f"Failed to get LabCorp results: {str(e)}")
            raise LabIntegrationError(f"LabCorp API error: {str(e)}")
    
    def _map_labcorp_result(self, result: Dict) -> Dict:
        """Map LabCorp result format to our system format"""
        return {
            'test_date': datetime.fromisoformat(result['collection_date']).date(),
            'free_psa': self._extract_value(result, 'FREE_PSA'),
            'total_psa': self._extract_value(result, 'TOTAL_PSA'),
            'testosterone': self._extract_value(result, 'TESTOSTERONE'),
            'notes': f"Imported from LabCorp - Order: {result.get('order_number', 'N/A')}"
        }
    
    def _extract_value(self, result: Dict, test_name: str) -> Optional[float]:
        """Extract numeric value from LabCorp result"""
        tests = result.get('tests', [])
        for test in tests:
            if test.get('test_name') == test_name:
                try:
                    return float(test.get('value', 0))
                except (ValueError, TypeError):
                    pass
        return None
    
    def import_results_for_patient(self, patient_id: int, patient_identifier: str) -> Tuple[int, List[str]]:
        """Import LabCorp results for patient"""
        imported_count = 0
        errors = []
        
        try:
            results = self.get_patient_results(patient_identifier)
            
            for result in results:
                try:
                    mapped_result = self._map_labcorp_result(result)
                    
                    # Check if we already have this result
                    if BloodTest and db:
                        existing = BloodTest.query.filter_by(
                            patient_id=patient_id,
                            test_date=mapped_result['test_date']
                        ).first()
                        
                        if existing:
                            continue  # Skip duplicates
                    
                    # Create new blood test record
                    if BloodTest and db:
                        blood_test = BloodTest(
                            patient_id=patient_id,
                            test_date=mapped_result['test_date'],
                            free_psa=mapped_result['free_psa'],
                            total_psa=mapped_result['total_psa'],
                            testosterone=mapped_result['testosterone'],
                            notes=mapped_result['notes']
                        )
                        
                        # Calculate PSA ratio
                        if hasattr(blood_test, 'calculate_psa_ratio'):
                            blood_test.calculate_psa_ratio()
                        
                        db.session.add(blood_test)
                        imported_count += 1
                    
                except Exception as e:
                    errors.append(f'Error importing result: {str(e)}')
                    logging.error(f'Lab import error: {str(e)}')
            
            # Commit all changes
            if db:
                db.session.commit()
            
        except Exception as e:
            if db:
                db.session.rollback()
            errors.append(f'Failed to import from LabCorp: {str(e)}')
        
        return imported_count, errors
            
            for result in results:
                try:
                    mapped_result = self._map_labcorp_result(result)
                    
                    # Check if result already exists
                    existing = BloodTest.query.filter_by(
                        patient_id=patient_id,
                        test_date=mapped_result['test_date']
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Create new blood test
                    blood_test = BloodTest(
                        patient_id=patient_id,
                        test_date=mapped_result['test_date'],
                        free_psa=mapped_result['free_psa'],
                        total_psa=mapped_result['total_psa'],
                        testosterone=mapped_result['testosterone'],
                        notes=mapped_result['notes']
                    )
                    
                    blood_test.calculate_psa_ratio()
                    db.session.add(blood_test)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Error importing result from {result.get('collection_date', 'unknown date')}: {str(e)}")
            
            if imported_count > 0:
                db.session.commit()
                
        except Exception as e:
            db.session.rollback()
            errors.append(f"Failed to import from LabCorp: {str(e)}")
        
        return imported_count, errors

class QuestDiagnosticsIntegration(BaseLabSystem):
    """Integration with Quest Diagnostics system"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.questdiagnostics.com/v2")
        
    def test_connection(self) -> bool:
        """Test Quest API connection"""
        try:
            response = self.session.get(f"{self.base_url}/ping")
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Quest connection test failed: {str(e)}")
            return False
    
    def get_patient_results(self, patient_identifier: str, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Get blood test results from Quest"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
            
        payload = {
            'patientId': patient_identifier,
            'fromDate': start_date.strftime('%Y-%m-%d'),
            'toDate': end_date.strftime('%Y-%m-%d'),
            'testCodes': ['PSA_FREE', 'PSA_TOTAL', 'TESTOSTERONE']
        }
        
        try:
            response = self.session.post(f"{self.base_url}/lab-results", json=payload)
            response.raise_for_status()
            return response.json().get('labResults', [])
        except Exception as e:
            logging.error(f"Failed to get Quest results: {str(e)}")
            raise LabIntegrationError(f"Quest API error: {str(e)}")
    
    def _map_quest_result(self, result: Dict) -> Dict:
        """Map Quest result format to our system format"""
        return {
            'test_date': datetime.strptime(result['specimenDate'], '%Y-%m-%d').date(),
            'free_psa': self._extract_quest_value(result, 'PSA_FREE'),
            'total_psa': self._extract_quest_value(result, 'PSA_TOTAL'),
            'testosterone': self._extract_quest_value(result, 'TESTOSTERONE'),
            'notes': f"Imported from Quest - Accession: {result.get('accessionNumber', 'N/A')}"
        }
    
    def _extract_quest_value(self, result: Dict, test_code: str) -> Optional[float]:
        """Extract numeric value from Quest result"""
        for test in result.get('tests', []):
            if test.get('testCode') == test_code:
                try:
                    return float(test.get('numericResult', 0))
                except (ValueError, TypeError):
                    pass
        return None
    
    def import_results_for_patient(self, patient_id: int, patient_identifier: str) -> Tuple[int, List[str]]:
        """Import Quest results for patient"""
        imported_count = 0
        errors = []
        
        try:
            results = self.get_patient_results(patient_identifier)
            
            for result in results:
                try:
                    mapped_result = self._map_quest_result(result)
                    
                    # Check if result already exists
                    existing = BloodTest.query.filter_by(
                        patient_id=patient_id,
                        test_date=mapped_result['test_date']
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Create new blood test
                    blood_test = BloodTest(
                        patient_id=patient_id,
                        test_date=mapped_result['test_date'],
                        free_psa=mapped_result['free_psa'],
                        total_psa=mapped_result['total_psa'],
                        testosterone=mapped_result['testosterone'],
                        notes=mapped_result['notes']
                    )
                    
                    blood_test.calculate_psa_ratio()
                    db.session.add(blood_test)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Error importing result from {result.get('specimenDate', 'unknown date')}: {str(e)}")
            
            if imported_count > 0:
                db.session.commit()
                
        except Exception as e:
            db.session.rollback()
            errors.append(f"Failed to import from Quest: {str(e)}")
        
        return imported_count, errors

class LabIntegrationManager:
    """Manages multiple lab system integrations"""
    
    def __init__(self):
        self.integrations = {}
        self._initialize_integrations()
    
    def _initialize_integrations(self):
        """Initialize available lab integrations"""
        # LabCorp integration
        labcorp_key = os.environ.get('LABCORP_API_KEY')
        if labcorp_key:
            self.integrations['labcorp'] = LabCorpIntegration(labcorp_key)
        
        # Quest integration
        quest_key = os.environ.get('QUEST_API_KEY')
        if quest_key:
            self.integrations['quest'] = QuestDiagnosticsIntegration(quest_key)
    
    def get_available_systems(self) -> List[str]:
        """Get list of available lab systems"""
        return list(self.integrations.keys())
    
    def test_all_connections(self) -> Dict[str, bool]:
        """Test connections to all configured lab systems"""
        results = {}
        for system, integration in self.integrations.items():
            results[system] = integration.test_connection()
        return results
    
    def import_for_patient(self, patient_id: int, lab_system: str, patient_identifier: str) -> Tuple[int, List[str]]:
        """Import results from specific lab system for patient"""
        if lab_system not in self.integrations:
            raise LabIntegrationError(f"Lab system '{lab_system}' not configured")
        
        integration = self.integrations[lab_system]
        return integration.import_results_for_patient(patient_id, patient_identifier)
    
    def import_for_all_patients(self, lab_system: str) -> Dict[str, Tuple[int, List[str]]]:
        """Import results from lab system for all patients with external IDs"""
        if lab_system not in self.integrations:
            raise LabIntegrationError(f"Lab system '{lab_system}' not configured")
        
        results = {}
        patients = Patient.query.filter(Patient.external_lab_id.isnot(None)).all()
        
        for patient in patients:
            try:
                imported_count, errors = self.import_for_patient(
                    patient.id, lab_system, patient.external_lab_id
                )
                results[patient.patient_code] = (imported_count, errors)
            except Exception as e:
                results[patient.patient_code] = (0, [str(e)])
        
        return results

# Global instance
lab_manager = LabIntegrationManager()
class QuestIntegration(BaseLabSystem):
    """Integration with Quest Diagnostics system"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "https://api.questdiagnostics.com/v1")
        
    def test_connection(self) -> bool:
        """Test Quest API connection"""
        try:
            response = self.session.get(f"{self.base_url}/status")
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Quest connection test failed: {str(e)}")
            return False
    
    def get_patient_results(self, patient_identifier: str, start_date: datetime = None, end_date: datetime = None) -> List[Dict]:
        """Get blood test results from Quest Diagnostics"""
        # Mock implementation - replace with actual Quest API calls
        # For demonstration purposes, return sample data
        return [
            {
                'date': '2024-01-15T10:00:00',
                'free_psa': 1.2,
                'total_psa': 4.5,
                'testosterone': 350
            }
        ]

class LabManager:
    """Manages multiple lab system integrations"""
    
    def __init__(self):
        self.systems = {}
        self._initialize_systems()
    
    def _initialize_systems(self):
        """Initialize available lab systems based on environment variables"""
        
        # LabCorp
        labcorp_key = os.environ.get('LABCORP_API_KEY')
        if labcorp_key:
            self.systems['labcorp'] = LabCorpIntegration(labcorp_key)
        
        # Quest Diagnostics
        quest_key = os.environ.get('QUEST_API_KEY')
        if quest_key:
            self.systems['quest'] = QuestIntegration(quest_key)
    
    def get_available_systems(self) -> List[str]:
        """Get list of available lab systems"""
        return list(self.systems.keys())
    
    def test_all_connections(self) -> Dict[str, bool]:
        """Test connections to all configured lab systems"""
        results = {}
        for name, system in self.systems.items():
            results[name] = system.test_connection()
        return results
    
    def import_for_patient(self, patient_id: int, lab_system: str, patient_lab_id: str) -> Tuple[int, List[str]]:
        """Import lab results for a specific patient"""
        if lab_system not in self.systems:
            raise LabIntegrationError(f"Lab system '{lab_system}' not configured")
        
        system = self.systems[lab_system]
        return system.import_results_for_patient(patient_id, patient_lab_id)
    
    def import_for_all_patients(self, lab_system: str) -> Dict[int, Tuple[int, List[str]]]:
        """Import lab results for all patients with configured lab IDs"""
        if lab_system not in self.systems:
            raise LabIntegrationError(f"Lab system '{lab_system}' not configured")
        
        results = {}
        
        # Get all patients with external lab IDs for this system
        try:
            from app import app
            with app.app_context():
                patients = Patient.query.filter(
                    Patient.external_lab_id.isnot(None),
                    Patient.lab_system_type == lab_system
                ).all()
                
                for patient in patients:
                    try:
                        imported_count, errors = self.import_for_patient(
                            patient.id, lab_system, patient.external_lab_id
                        )
                        results[patient.id] = (imported_count, errors)
                        
                        # Update last import time
                        patient.last_lab_import = datetime.now()
                        db.session.commit()
                        
                    except Exception as e:
                        results[patient.id] = (0, [str(e)])
                        logging.error(f"Failed to import for patient {patient.id}: {str(e)}")
        except Exception as e:
            raise LabIntegrationError(f"Failed to import for all patients: {str(e)}")
        
        return results

# Create global lab manager instance
lab_manager = LabManager()
