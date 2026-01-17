"""
Game logic and helper functions
"""
import random
import time
from typing import Dict, List, Tuple, Optional
from game_config import DEPARTMENTS, PATIENT_CASES

class Hospital:
    def __init__(self, name: str):
        self.name = name
        self.score = 0
        self.departments = {}
        self.admitted_patients = []
        self.referred_count = 0
        self.diagnosis_correct = 0
        self.diagnosis_wrong = 0
        
        # Initialize departments with beds
        for dept_name, config in DEPARTMENTS.items():
            self.departments[dept_name] = {
                'total_beds': config['beds'],
                'occupied_beds': 0,
                'available_beds': config['beds'],
                'patients': [],
                'icon': config['icon'],
                'color': config['color']
            }
    
    def admit_patient(self, patient: Dict, department: str) -> bool:
        """Admit patient to department if bed available"""
        if self.departments[department]['available_beds'] > 0:
            # Admit patient
            self.departments[department]['occupied_beds'] += 1
            self.departments[department]['available_beds'] -= 1
            
            patient_record = {
                'complaint': patient['complaint'],
                'department': department,
                'points': patient['points'],
                'admission_time': time.time(),
                'status': 'Admitted'
            }
            
            self.departments[department]['patients'].append(patient_record)
            self.admitted_patients.append(patient_record)
            self.score += patient['points']
            self.diagnosis_correct += 1
            return True
        return False
    
    def refer_patient(self, patient: Dict):
        """Refer patient to another hospital"""
        self.referred_count += 1
        self.score -= 1  # Penalty for referral
    
    def misdiagnose(self, patient: Dict):
        """Handle misdiagnosis"""
        self.diagnosis_wrong += 1
        self.score -= patient['points'] // 2  # Lose half points
    
    def discharge_patient(self, department: str, patient_index: int):
        """Discharge patient to free up bed"""
        if 0 <= patient_index < len(self.departments[department]['patients']):
            discharged = self.departments[department]['patients'].pop(patient_index)
            self.departments[department]['occupied_beds'] -= 1
            self.departments[department]['available_beds'] += 1
            return discharged
        return None
    
    def get_stats(self) -> Dict:
        """Get hospital statistics"""
        return {
            'name': self.name,
            'score': self.score,
            'admitted': len(self.admitted_patients),
            'referred': self.referred_count,
            'diagnosis_accuracy': self.diagnosis_correct / max(1, (self.diagnosis_correct + self.diagnosis_wrong)) * 100,
            'bed_occupancy_rate': sum([dept['occupied_beds'] for dept in self.departments.values()]) / 
                                 sum([dept['total_beds'] for dept in self.departments.values()]) * 100
        }

class GameEngine:
    def __init__(self):
        self.hospitals = []
        self.current_round = 0
        self.game_active = False
        self.current_patients = {}
        self.diagnosis_timers = {}
        self.game_log = []
    
    def initialize_game(self, team_names: List[str]):
        """Initialize game with teams"""
        self.hospitals = [Hospital(name) for name in team_names]
        self.current_round = 0
        self.game_active = True
        self.current_patients = {}
        self.diagnosis_timers = {}
        self.game_log = []
        
        # Log game start
        self.add_to_log(f"Game started with {len(team_names)} teams: {', '.join(team_names)}")
    
    def start_new_round(self):
        """Start a new round with random patients for each team"""
        self.current_round += 1
        
        for hospital in self.hospitals:
            # Select random patient case
            patient = random.choice(PATIENT_CASES).copy()
            
            # Add unique ID and hospital
            patient['id'] = f"P{self.current_round:03d}_{hospital.name[:3].upper()}"
            patient['hospital'] = hospital.name
            patient['round'] = self.current_round
            
            self.current_patients[hospital.name] = patient
            self.diagnosis_timers[hospital.name] = time.time()
        
        self.add_to_log(f"Round {self.current_round} started - New patients arrived")
    
    def submit_diagnosis(self, hospital_name: str, chosen_department: str, diagnosis_time: float) -> Dict:
        """Submit diagnosis for a patient"""
        hospital = next((h for h in self.hospitals if h.name == hospital_name), None)
        patient = self.current_patients.get(hospital_name)
        
        if not hospital or not patient:
            return {'success': False, 'message': 'Invalid hospital or patient'}
        
        # Check if diagnosis was within time limit
        time_taken = diagnosis_time - self.diagnosis_timers[hospital_name]
        time_bonus = 1 if time_taken < 15 else 0
        
        # Check diagnosis
        if chosen_department == patient['correct_dept']:
            # Correct diagnosis - try to admit
            if hospital.admit_patient(patient, chosen_department):
                hospital.score += time_bonus  # Add time bonus
                result = {
                    'success': True,
                    'correct': True,
                    'admitted': True,
                    'points': patient['points'] + time_bonus,
                    'message': f"✓ Correct diagnosis! Patient admitted to {chosen_department}. +{patient['points']} points"
                }
                self.add_to_log(f"{hospital_name}: Correct diagnosis - {patient['complaint']} → {chosen_department}")
            else:
                # No beds available
                hospital.refer_patient(patient)
                result = {
                    'success': True,
                    'correct': True,
                    'admitted': False,
                    'points': -1,
                    'message': f"✓ Correct diagnosis but no beds in {chosen_department}. Patient referred. -1 point"
                }
                self.add_to_log(f"{hospital_name}: Correct diagnosis but no beds - patient referred")
        else:
            # Wrong diagnosis
            hospital.misdiagnose(patient)
            result = {
                'success': True,
                'correct': False,
                'admitted': False,
                'points': -(patient['points'] // 2),
                'message': f"✗ Wrong diagnosis! Should be {patient['correct_dept']}. -{patient['points'] // 2} points"
            }
            self.add_to_log(f"{hospital_name}: Wrong diagnosis - thought {chosen_department}, actual {patient['correct_dept']}")
        
        # Clear current patient
        self.current_patients.pop(hospital_name, None)
        
        return result
    
    def get_rankings(self) -> List[Dict]:
        """Get ranked list of hospitals"""
        ranked = sorted(self.hospitals, key=lambda x: x.score, reverse=True)
        return [
            {
                'rank': i + 1,
                'name': hospital.name,
                'score': hospital.score,
                'admitted': len(hospital.admitted_patients),
                'referred': hospital.referred_count,
                'diagnosis_accuracy': hospital.diagnosis_correct / max(1, (hospital.diagnosis_correct + hospital.diagnosis_wrong)) * 100
            }
            for i, hospital in enumerate(ranked)
        ]
    
    def add_to_log(self, message: str):
        """Add message to game log"""
        timestamp = time.strftime("%H:%M:%S")
        self.game_log.append(f"[{timestamp}] {message}")
        
        # Keep only last 50 log entries
        if len(self.game_log) > 50:
            self.game_log = self.game_log[-50:]
    
    def get_game_state(self) -> Dict:
        """Get current game state"""
        return {
            'round': self.current_round,
            'active_hospitals': [h.name for h in self.hospitals],
            'game_active': self.game_active,
            'remaining_patients': len(self.current_patients),
            'rankings': self.get_rankings()
      }
