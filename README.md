# Medical Board Game: Hospital Management

A competitive board game simulation where teams manage hospital admissions, diagnose patients, and compete for the highest score.

## 🎯 Game Objective
Be the top-ranked hospital by successfully admitting patients, making correct diagnoses, and managing limited bed capacity.

## 🎮 How to Play
1. Each team represents a hospital with departments having limited beds
2. Patients arrive with random medical complaints
3. Teams must diagnose the correct department for each patient
4. If the correct department has available beds, admit the patient for points
5. If beds are full, refer the patient (lose points)
6. Game runs for a set number of rounds or until a score target is reached

## 🏥 Departments & Beds
Each hospital starts with:
- Emergency: 4 beds
- Surgery: 3 beds
- Pediatrics: 3 beds
- Cardiology: 2 beds
- ICU: 2 beds
- Orthopedics: 2 beds

## 🏆 Scoring
- Correct diagnosis + admission: Patient's point value (3-5 points)
- Misdiagnosis: -1 point
- Referral (no beds): -1 point
- Quick diagnosis bonus: +1 point (if < 15 seconds)

## 🚀 Running the Game
```bash
pip install -r requirements.txt
streamlit run app.py
