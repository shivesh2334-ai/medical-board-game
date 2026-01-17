"""
Medical Board Game - Complete Single File Solution
"""
import streamlit as st
import pandas as pd
import numpy as np
import random
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Medical Board Game",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== GAME CONFIGURATION ====================

# Game settings
MAX_ROUNDS = 15
DIAGNOSIS_TIME_LIMIT = 30  # seconds
INITIAL_SCORE = 0
MIN_TEAMS = 2
MAX_TEAMS = 6

# Department configuration
DEPARTMENTS = {
    'Emergency': {
        'beds': 4,
        'color': '#FF6B6B',
        'icon': '🚨'
    },
    'Surgery': {
        'beds': 3,
        'color': '#4ECDC4',
        'icon': '🔪'
    },
    'Pediatrics': {
        'beds': 3,
        'color': '#FFD166',
        'icon': '👶'
    },
    'Cardiology': {
        'beds': 2,
        'color': '#EF476F',
        'icon': '❤️'
    },
    'ICU': {
        'beds': 2,
        'color': '#073B4C',
        'icon': '💀'
    },
    'Orthopedics': {
        'beds': 2,
        'color': '#118AB2',
        'icon': '🦴'
    }
}

# Patient complaints and correct departments
PATIENT_CASES = [
    {
        'complaint': 'Severe chest pain radiating to left arm',
        'correct_dept': 'Cardiology',
        'difficulty': 'Medium',
        'points': 4,
        'options': ['Cardiology', 'Emergency', 'Surgery']
    },
    {
        'complaint': 'High fever and rash in child',
        'correct_dept': 'Pediatrics',
        'difficulty': 'Easy',
        'points': 3,
        'options': ['Pediatrics', 'Emergency', 'ICU']
    },
    {
        'complaint': 'Compound fracture of femur',
        'correct_dept': 'Orthopedics',
        'difficulty': 'Medium',
        'points': 4,
        'options': ['Orthopedics', 'Surgery', 'Emergency']
    },
    {
        'complaint': 'Difficulty breathing and low oxygen',
        'correct_dept': 'ICU',
        'difficulty': 'Hard',
        'points': 5,
        'options': ['ICU', 'Emergency', 'Cardiology']
    },
    {
        'complaint': 'Appendicitis symptoms',
        'correct_dept': 'Surgery',
        'difficulty': 'Medium',
        'points': 4,
        'options': ['Surgery', 'Emergency', 'ICU']
    },
    {
        'complaint': 'Multiple trauma from car accident',
        'correct_dept': 'Emergency',
        'difficulty': 'Hard',
        'points': 5,
        'options': ['Emergency', 'Surgery', 'ICU']
    },
    {
        'complaint': 'Burn injuries 30% body surface',
        'correct_dept': 'Surgery',
        'difficulty': 'Hard',
        'points': 5,
        'options': ['Surgery', 'Emergency', 'ICU']
    },
    {
        'complaint': 'Neonatal jaundice',
        'correct_dept': 'Pediatrics',
        'difficulty': 'Easy',
        'points': 3,
        'options': ['Pediatrics', 'Emergency', 'ICU']
    },
    {
        'complaint': 'Heart attack symptoms',
        'correct_dept': 'Cardiology',
        'difficulty': 'Medium',
        'points': 4,
        'options': ['Cardiology', 'Emergency', 'ICU']
    },
    {
        'complaint': 'Dislocated shoulder',
        'correct_dept': 'Orthopedics',
        'difficulty': 'Easy',
        'points': 3,
        'options': ['Orthopedics', 'Emergency', 'Surgery']
    }
]

# ==================== GAME LOGIC CLASSES ====================

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
    
    def admit_patient(self, patient: dict, department: str) -> bool:
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
    
    def refer_patient(self, patient: dict):
        """Refer patient to another hospital"""
        self.referred_count += 1
        self.score -= 1  # Penalty for referral
    
    def misdiagnose(self, patient: dict):
        """Handle misdiagnosis"""
        self.diagnosis_wrong += 1
        self.score -= patient['points'] // 2  # Lose half points
    
    def get_stats(self) -> dict:
        """Get hospital statistics"""
        total_cases = max(1, self.diagnosis_correct + self.diagnosis_wrong)
        total_beds = sum([dept['total_beds'] for dept in self.departments.values()])
        occupied_beds = sum([dept['occupied_beds'] for dept in self.departments.values()])
        
        return {
            'name': self.name,
            'score': self.score,
            'admitted': len(self.admitted_patients),
            'referred': self.referred_count,
            'diagnosis_accuracy': (self.diagnosis_correct / total_cases) * 100 if total_cases > 0 else 0,
            'bed_occupancy_rate': (occupied_beds / total_beds) * 100 if total_beds > 0 else 0
        }

class GameEngine:
    def __init__(self):
        self.hospitals = []
        self.current_round = 0
        self.game_active = False
        self.current_patients = {}
        self.diagnosis_timers = {}
        self.game_log = []
    
    def initialize_game(self, team_names: list):
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
    
    def submit_diagnosis(self, hospital_name: str, chosen_department: str, diagnosis_time: float) -> dict:
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
                if time_bonus:
                    result['message'] += f" (+1 time bonus)"
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
    
    def get_rankings(self) -> list:
        """Get ranked list of hospitals"""
        ranked = sorted(self.hospitals, key=lambda x: x.score, reverse=True)
        return [
            {
                'rank': i + 1,
                'name': hospital.name,
                'score': hospital.score,
                'admitted': len(hospital.admitted_patients),
                'referred': hospital.referred_count,
                'diagnosis_accuracy': hospital.get_stats()['diagnosis_accuracy']
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
    
    def get_game_state(self) -> dict:
        """Get current game state"""
        return {
            'round': self.current_round,
            'active_hospitals': [h.name for h in self.hospitals],
            'game_active': self.game_active,
            'remaining_patients': len(self.current_patients),
            'rankings': self.get_rankings()
        }

# ==================== STREAMLIT APP ====================

# Initialize session state
if 'game' not in st.session_state:
    st.session_state.game = GameEngine()

if 'game_initialized' not in st.session_state:
    st.session_state.game_initialized = False

if 'current_patient_selections' not in st.session_state:
    st.session_state.current_patient_selections = {}

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2C3E50;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    .hospital-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 5px solid #4ECDC4;
    }
    .patient-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 2px dashed #667eea;
    }
    .score-badge {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .department-bed {
        display: inline-block;
        width: 25px;
        height: 25px;
        margin: 2px;
        border-radius: 50%;
        text-align: center;
        line-height: 25px;
        font-size: 12px;
    }
    .bed-available {
        background-color: #4CAF50;
        color: white;
    }
    .bed-occupied {
        background-color: #F44336;
        color: white;
    }
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }
    .success-msg {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-msg {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🏥 Medical Board Game: Hospital Management</h1>', unsafe_allow_html=True)

# Sidebar for game controls
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3050/3050526.png", width=100)
    st.markdown("### Game Controls")
    
    if not st.session_state.game_initialized:
        # Game setup
        st.markdown("### 🎯 Game Setup")
        num_teams = st.number_input(
            "Number of Teams",
            min_value=MIN_TEAMS,
            max_value=MAX_TEAMS,
            value=3,
            step=1
        )
        
        team_names = []
        for i in range(num_teams):
            name = st.text_input(f"Team {i+1} Name", value=f"Hospital {i+1}")
            team_names.append(name)
        
        if st.button("🚀 Start Game", use_container_width=True, type="primary"):
            if len(set(team_names)) != len(team_names):
                st.error("Team names must be unique!")
            else:
                st.session_state.game.initialize_game(team_names)
                st.session_state.game_initialized = True
                st.session_state.game.start_new_round()
                st.rerun()
    
    else:
        # Game controls when game is running
        game = st.session_state.game
        st.markdown(f"### Round {game.current_round}/{MAX_ROUNDS}")
        
        # Game status
        game_state = game.get_game_state()
        remaining = len(game.current_patients)
        total_teams = len(game.hospitals)
        
        st.progress(game.current_round / MAX_ROUNDS)
        st.caption(f"{remaining}/{total_teams} teams pending diagnosis")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 New Round", use_container_width=True):
                if game.current_round < MAX_ROUNDS:
                    game.start_new_round()
                    st.session_state.current_patient_selections = {}
                    st.rerun()
                else:
                    st.warning("Maximum rounds reached!")
        
        with col2:
            if st.button("🔄 Reset Game", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        rankings = game_state['rankings']
        for rank in rankings[:3]:
            st.caption(f"{rank['rank']}. {rank['name']}: {rank['score']} pts")

# Main content area
if not st.session_state.game_initialized:
    # Game instructions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🎯 Objective")
        st.markdown("""
        Be the top-ranked hospital by:
        - Correctly diagnosing patients
        - Managing bed capacity
        - Minimizing referrals
        """)
    
    with col2:
        st.markdown("### 🏥 Departments")
        dept_data = []
        for dept, config in DEPARTMENTS.items():
            dept_data.append({
                "Department": f"{config['icon']} {dept}",
                "Beds": config['beds']
            })
        dept_df = pd.DataFrame(dept_data)
        st.dataframe(dept_df, use_container_width=True, hide_index=True, column_config={
            "Department": st.column_config.TextColumn("Department"),
            "Beds": st.column_config.NumberColumn("Beds")
        })
    
    with col3:
        st.markdown("### 📈 Scoring")
        st.markdown("""
        - **Correct admission**: 3-5 points
        - **Quick diagnosis bonus**: +1 point
        - **Misdiagnosis**: -1 to -2 points
        - **Referral**: -1 point
        """)
    
    st.markdown("---")
    st.markdown("### 🎮 How to Play")
    st.markdown("""
    1. Each round, patients arrive with random complaints
    2. Choose the correct department for each patient
    3. If the department has beds, patient is admitted
    4. If no beds, patient is referred (penalty)
    5. Wrong diagnosis also results in penalty
    6. Game runs for 15 rounds
    7. Highest score wins!
    """)

else:
    # Game is running
    game = st.session_state.game
    
    # Display current round and rankings
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"### 📅 Round {game.current_round}/{MAX_ROUNDS}")
        st.progress(game.current_round / MAX_ROUNDS)
    
    with col2:
        st.markdown("### 🏆 Current Leader")
        rankings = game.get_rankings()
        if rankings:
            leader = rankings[0]
            st.markdown(f"""
            <div class="hospital-card">
                <h3>🥇 {leader['name']}</h3>
                <p>Score: <span class="score-badge">{leader['score']} pts</span></p>
                <p>Accuracy: {leader['diagnosis_accuracy']:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("### ⏱️ Time Remaining")
        if game.current_patients:
            # Calculate time since round started
            min_time = min(game.diagnosis_timers.values())
            elapsed = time.time() - min_time
            remaining_time = max(0, 30 - elapsed)
            color = "green" if remaining_time > 15 else "orange" if remaining_time > 5 else "red"
            st.markdown(f"<h2 style='color: {color};'>{remaining_time:.0f}s</h2>", unsafe_allow_html=True)
            st.caption("Quick diagnosis bonus: +1 point if < 15s")
        else:
            st.markdown("<h2>⏳</h2>", unsafe_allow_html=True)
            st.caption("Waiting for next round...")
    
    # Display patients for each hospital
    st.markdown("---")
    st.markdown("## 🚑 Current Patients")
    
    if not game.current_patients:
        st.success("All diagnoses submitted for this round! Click 'New Round' to continue.")
    else:
        # Create columns for hospitals
        cols = st.columns(min(3, len(game.hospitals)))
        
        for idx, hospital in enumerate(game.hospitals):
            col_idx = idx % len(cols)
            with cols[col_idx]:
                patient = game.current_patients.get(hospital.name)
                
                if patient:
                    # Hospital card
                    st.markdown(f"""
                    <div class="hospital-card">
                        <h3>{hospital.name}</h3>
                        <p>Score: <strong>{hospital.score}</strong> pts</p>
                        <p>Diagnoses: ✅ {hospital.diagnosis_correct} | ❌ {hospital.diagnosis_wrong}</p>
                        <p>Referred: {hospital.referred_count}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Patient card
                    st.markdown(f"""
                    <div class="patient-card">
                        <h4>Patient: {patient['id']}</h4>
                        <p><strong>Complaint:</strong> {patient['complaint']}</p>
                        <p><strong>Difficulty:</strong> {patient['difficulty']}</p>
                        <p><strong>Points:</strong> {patient['points']}</p>
                        <p><em>Diagnose within 15s for bonus point!</em></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Department selection
                    selected = st.radio(
                        "Select Department:",
                        patient['options'],
                        key=f"diagnosis_{hospital.name}"
                    )
                    
                    st.session_state.current_patient_selections[hospital.name] = selected
                    
                    # Submit button
                    if st.button(f"Submit Diagnosis", key=f"submit_{hospital.name}"):
                        result = game.submit_diagnosis(
                            hospital.name,
                            selected,
                            time.time()
                        )
                        
                        if result['success']:
                            if result['correct'] and result['admitted']:
                                st.markdown(f'<div class="success-msg">{result["message"]}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="error-msg">{result["message"]}</div>', unsafe_allow_html=True)
                            
                            time.sleep(1.5)
                            st.rerun()
                
                else:
                    st.info(f"**{hospital.name}** has completed this round")
    
    # Display hospital status and beds
    st.markdown("---")
    st.markdown("## 🏥 Hospital Status")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Rankings", "🛏️ Bed Status", "📜 Game Log"])
    
    with tab1:
        # Rankings table
        rankings_df = pd.DataFrame(game.get_rankings())
        if not rankings_df.empty:
            # Add medal emojis
            def get_medal(rank):
                if rank == 1:
                    return "🥇"
                elif rank == 2:
                    return "🥈"
                elif rank == 3:
                    return "🥉"
                else:
                    return f"{rank}"
            
            rankings_df['Medal'] = rankings_df['rank'].apply(get_medal)
            
            # Display table
            st.dataframe(
                rankings_df[['Medal', 'name', 'score', 'admitted', 'referred', 'diagnosis_accuracy']].rename(
                    columns={
                        'Medal': 'Rank',
                        'name': 'Hospital',
                        'score': 'Score',
                        'admitted': 'Admitted',
                        'referred': 'Referred',
                        'diagnosis_accuracy': 'Accuracy %'
                    }
                ),
                use_container_width=True,
                hide_index=True
            )
            
            # Score chart
            try:
                import plotly.express as px
                fig = px.bar(
                    rankings_df,
                    x='name',
                    y='score',
                    color='score',
                    title="Hospital Scores",
                    labels={'name': 'Hospital', 'score': 'Score'},
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
            except:
                # Fallback if plotly is not available
                st.bar_chart(rankings_df.set_index('name')['score'])
    
    with tab2:
        # Bed status for each hospital
        for hospital in game.hospitals:
            st.markdown(f"### {hospital.name}")
            
            # Create columns for departments
            dept_cols = st.columns(len(DEPARTMENTS))
            
            for idx, (dept_name, dept_config) in enumerate(hospital.departments.items()):
                with dept_cols[idx]:
                    occupied = dept_config['occupied_beds']
                    total = dept_config['total_beds']
                    available = dept_config['available_beds']
                    
                    # Progress bar for bed occupancy
                    occupancy_pct = (occupied / total) * 100 if total > 0 else 0
                    
                    st.markdown(f"**{DEPARTMENTS[dept_name]['icon']} {dept_name}**")
                    st.progress(occupancy_pct / 100)
                    st.caption(f"{occupied}/{total} beds occupied")
                    
                    # Visual bed display
                    bed_html = "<div style='margin-top: 10px;'>"
                    for i in range(total):
                        if i < occupied:
                            bed_html += f"<span class='department-bed bed-occupied'>💤</span>"
                        else:
                            bed_html += f"<span class='department-bed bed-available'>🛏️</span>"
                    bed_html += "</div>"
                    st.markdown(bed_html, unsafe_allow_html=True)
            
            st.markdown("---")
    
    with tab3:
        # Game log
        st.markdown("### 📝 Game Activity Log")
        log_container = st.container(height=300)
        
        with log_container:
            for log_entry in reversed(game.game_log[-20:]):  # Show last 20 entries
                st.text(log_entry)
        
        # Quick stats
        st.markdown("### 📈 Game Statistics")
        total_admitted = sum(len(h.admitted_patients) for h in game.hospitals)
        total_referred = sum(h.referred_count for h in game.hospitals)
        total_diagnoses = sum(h.diagnosis_correct + h.diagnosis_wrong for h in game.hospitals)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Patients Admitted", total_admitted)
        with col2:
            st.metric("Total Patients Referred", total_referred)
        with col3:
            st.metric("Total Diagnoses Made", total_diagnoses)
    
    # Game over check
    if game.current_round >= MAX_ROUNDS and not game.current_patients:
        st.markdown("---")
        st.markdown("## 🎉 Game Over!")
        
        # Final rankings
        rankings = game.get_rankings()
        
        st.balloons()
        
        col1, col2, col3 = st.columns(3)
        
        # Display top 3
        colors = ["#FFD700", "#C0C0C0", "#CD7F32"]  # Gold, Silver, Bronze
        for i in range(min(3, len(rankings))):
            with [col1, col2, col3][i]:
                medal = ["🥇", "🥈", "🥉"][i]
                st.markdown(f"""
                <div style="text-align: center; padding: 2rem; border-radius: 10px; 
                            background: linear-gradient(135deg, {colors[i]}, white);
                            border: 3px solid {colors[i]};">
                    <h1 style="font-size: 3rem;">{medal}</h1>
                    <h3>{rankings[i]['name']}</h3>
                    <h2 style="color: #2C3E50;">{rankings[i]['score']} points</h2>
                    <p>Admitted: {rankings[i]['admitted']}</p>
                    <p>Accuracy: {rankings[i]['diagnosis_accuracy']:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Certificate of achievement
        st.markdown("""
        <div style="text-align: center; padding: 2rem; margin-top: 2rem; 
                    border: 3px solid gold; border-radius: 15px;
                    background: linear-gradient(45deg, #f8f9fa, #e9ecef);">
            <h2 style="color: #2C3E50;">🏆 Medical Excellence Award 🏆</h2>
            <h3>Congratulations to all participating hospitals!</h3>
            <p>Thank you for your dedication to patient care and hospital management.</p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>Medical Board Game v1.0 | Created with Streamlit | For educational purposes</p>
        <p>Game Design: Hospital Management Simulation | Rules based on real hospital admission protocols</p>
    </div>
    """,
    unsafe_allow_html=True
)
