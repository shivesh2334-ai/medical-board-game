"""
Medical Board Game - Streamlit App
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from datetime import datetime
from utils.game_logic import GameEngine, Hospital
from game_config import DEPARTMENTS, PATIENT_CASES, MAX_ROUNDS, MIN_TEAMS, MAX_TEAMS

# Page configuration
st.set_page_config(
    page_title="Medical Board Game",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        
        if st.button("🚀 Start Game", use_container_width=True):
            if len(set(team_names)) != len(team_names):
                st.error("Team names must be unique!")
            else:
                st.session_state.game.initialize_game(team_names)
                st.session_state.game_initialized = True
                st.session_state.game.start_new_round()
                st.rerun()
    
    else:
        # Game controls when game is running
        st.markdown(f"### Round {st.session_state.game.current_round}/{MAX_ROUNDS}")
        
        # Game status
        game_state = st.session_state.game.get_game_state()
        remaining = len(st.session_state.game.current_patients)
        total_teams = len(st.session_state.game.hospitals)
        
        st.progress(st.session_state.game.current_round / MAX_ROUNDS)
        st.caption(f"{remaining}/{total_teams} teams pending diagnosis")
        
        if st.button("🔄 New Round", use_container_width=True):
            if st.session_state.game.current_round < MAX_ROUNDS:
                st.session_state.game.start_new_round()
                st.session_state.current_patient_selections = {}
                st.rerun()
            else:
                st.warning("Maximum rounds reached!")
        
        if st.button("🔄 Reset Game", use_container_width=True):
            st.session_state.game = GameEngine()
            st.session_state.game_initialized = False
            st.session_state.current_patient_selections = {}
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
        dept_df = pd.DataFrame([
            {"Department": dept, "Beds": config['beds'], "Icon": config['icon']}
            for dept, config in DEPARTMENTS.items()
        ])
        st.dataframe(dept_df, use_container_width=True, hide_index=True)
    
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
            st.markdown(f"<h2 style='color: {'green' if remaining_time > 15 else 'orange' if remaining_time > 5 else 'red'};'>{remaining_time:.0f}s</h2>", unsafe_allow_html=True)
            st.caption("Quick diagnosis bonus: +1 point if < 15s")
    
    # Display patients for each hospital
    st.markdown("---")
    st.markdown("## 🚑 Current Patients")
    
    if not game.current_patients:
        st.success("All diagnoses submitted for this round! Click 'New Round' to continue.")
    else:
        # Create columns for hospitals
        cols = st.columns(len(game.hospitals))
        
        for idx, hospital in enumerate(game.hospitals):
            with cols[idx]:
                patient = game.current_patients.get(hospital.name)
                
                if patient:
                    # Hospital card
                    st.markdown(f"""
                    <div class="hospital-card">
                        <h3>{hospital.name}</h3>
                        <p>Score: <strong>{hospital.score}</strong> pts</p>
                        <p>Diagnoses: ✅ {hospital.diagnosis_correct} | ❌ {hospital.diagnosis_wrong}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Patient card
                    st.markdown(f"""
                    <div class="patient-card">
                        <h4>Patient: {patient['id']}</h4>
                        <p><strong>Complaint:</strong> {patient['complaint']}</p>
                        <p><strong>Difficulty:</strong> {patient['difficulty']}</p>
                        <p><strong>Points:</strong> {patient['points']}</p>
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
                            st.success(result['message'])
                            time.sleep(1)
                            st.rerun()
                
                else:
                    st.info(f"{hospital.name} has completed this round")
    
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
            rankings_df['Rank'] = rankings_df['rank'].apply(
                lambda x: f"🥇" if x == 1 else f"🥈" if x == 2 else f"🥉" if x == 3 else f"{x}"
            )
            
            # Display table
            st.dataframe(
                rankings_df[['Rank', 'name', 'score', 'admitted', 'referred', 'diagnosis_accuracy']].rename(
                    columns={
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
        for i in range(min(3, len(rankings))):
            with [col1, col2, col3][i]:
                medal = ["🥇", "🥈", "🥉"][i]
                st.markdown(f"""
                <div style="text-align: center; padding: 2rem; border-radius: 10px; 
                            background: linear-gradient(135deg, {'#FFD700' if i==0 else '#C0C0C0' if i==1 else '#CD7F32'}, white);">
                    <h1>{medal}</h1>
                    <h3>{rankings[i]['name']}</h3>
                    <h2>{rankings[i]['score']} points</h2>
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
