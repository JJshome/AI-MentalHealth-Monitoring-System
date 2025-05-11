"""
Mental Health Monitoring System Simulation Web Interface

This module provides a Flask-based web interface for interacting with the 
mental health monitoring system simulation. It allows users to:
1. Generate synthetic sensor data for different mental states
2. Visualize impedance patterns
3. Test the AI diagnosis pipeline
4. Explore personalized treatment generation
"""

from flask import Flask, render_template, request, jsonify, Response
import json
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime
import os

# Import the sensor simulator
from sensor_simulator import EarSensorSimulator

app = Flask(__name__)

# Ensure the templates directory exists
os.makedirs('templates', exist_ok=True)

# Create a template for the web interface
TEMPLATE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Mental Health Monitoring System Simulation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
        }
        .container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        .panel {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            flex: 1 1 300px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        select, input[type="text"], input[type="number"] {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }
        button:hover {
            background-color: #2980b9;
        }
        .results {
            margin-top: 20px;
            border-top: 1px solid #eee;
            padding-top: 20px;
        }
        pre {
            background-color: #f8f8f8;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 12px;
        }
        .plot {
            margin-top: 15px;
            text-align: center;
        }
        .plot img {
            max-width: 100%;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            color: #7f8c8d;
            font-size: 12px;
        }
        .diagnosis {
            margin-top: 15px;
            padding: 15px;
            border-radius: 4px;
        }
        .diagnosis.normal {
            background-color: #e8f8f5;
            border-left: 4px solid #2ecc71;
        }
        .diagnosis.depression {
            background-color: #eaecee;
            border-left: 4px solid #7f8c8d;
        }
        .diagnosis.anxiety {
            background-color: #ebf5fb;
            border-left: 4px solid #3498db;
        }
        .diagnosis.stress {
            background-color: #fef9e7;
            border-left: 4px solid #f1c40f;
        }
        .diagnosis.bipolar_manic {
            background-color: #fdedec;
            border-left: 4px solid #e74c3c;
        }
        .diagnosis.bipolar_depressive {
            background-color: #f4ecf7;
            border-left: 4px solid #8e44ad;
        }
        .confidence-bar {
            height: 20px;
            background-color: #ddd;
            border-radius: 10px;
            margin-top: 5px;
            overflow: hidden;
        }
        .confidence-level {
            height: 100%;
            background-color: #3498db;
            border-radius: 10px;
            text-align: right;
            padding-right: 10px;
            color: white;
            font-weight: bold;
            line-height: 20px;
            font-size: 12px;
        }
        .treatment {
            margin-top: 20px;
            padding: 15px;
            background-color: #ebf5fb;
            border-radius: 4px;
        }
        .treatment h3 {
            margin-top: 0;
            color: #2980b9;
        }
        .treatment-item {
            margin-bottom: 10px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1>AI-based Mental Health Monitoring System Simulation</h1>
    
    <div class="container">
        <div class="panel">
            <h2>Biosensor Data Simulator</h2>
            <form id="sensorForm">
                <div class="form-group">
                    <label for="userId">User ID:</label>
                    <input type="text" id="userId" name="userId" value="test_user_001">
                </div>
                
                <div class="form-group">
                    <label for="mentalState">Mental State to Simulate:</label>
                    <select id="mentalState" name="mentalState">
                        <option value="normal">Normal</option>
                        <option value="depression">Depression</option>
                        <option value="anxiety">Anxiety</option>
                        <option value="stress">Stress</option>
                        <option value="bipolar_manic">Bipolar (Manic)</option>
                        <option value="bipolar_depressive">Bipolar (Depressive)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="duration">Duration (seconds):</label>
                    <input type="number" id="duration" name="duration" value="1" min="1" max="60">
                </div>
                
                <button type="button" onclick="generateData()">Generate Data</button>
            </form>
            
            <div class="results" id="sensorResults">
                <h3>Generated Data Preview</h3>
                <pre id="dataPreview"></pre>
                
                <div class="plot" id="plotContainer">
                    <!-- Impedance plot will appear here -->
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>AI Diagnosis Module</h2>
            <p>The AI analysis system processes the biosensor data to determine the most likely mental health state.</p>
            
            <button type="button" onclick="performDiagnosis()">Run AI Diagnosis</button>
            
            <div id="diagnosisResults" class="results">
                <h3>Diagnosis Results</h3>
                <div id="diagnosisContainer">
                    <!-- Diagnosis results will appear here -->
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>Treatment Program Generator</h2>
            <p>Based on the AI diagnosis, the system generates a personalized treatment program.</p>
            
            <button type="button" onclick="generateTreatment()">Generate Treatment Plan</button>
            
            <div id="treatmentResults" class="results">
                <h3>Personalized Treatment</h3>
                <div id="treatmentContainer">
                    <!-- Treatment program will appear here -->
                </div>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>AI-based Real-time Personalized Mental Health Monitoring System - Patent Pending</p>
    </div>

    <script>
        let currentData = null;
        let simulatedMentalState = null;
        
        async function generateData() {
            const userId = document.getElementById('userId').value;
            const mentalState = document.getElementById('mentalState').value;
            const duration = document.getElementById('duration').value;
            
            simulatedMentalState = mentalState;
            
            const response = await fetch('/generate_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    userId: userId,
                    mentalState: mentalState,
                    duration: duration
                })
            });
            
            const data = await response.json();
            currentData = data;
            
            // Display sample of data
            document.getElementById('dataPreview').textContent = JSON.stringify(data, null, 2).substring(0, 500) + '...';
            
            // Display the impedance plot
            document.getElementById('plotContainer').innerHTML = `
                <h4>Impedance Spectrum</h4>
                <img src="data:image/png;base64,${data.plot}" alt="Impedance Spectrum">
            `;
        }
        
        async function performDiagnosis() {
            if (!currentData) {
                alert('Please generate sensor data first');
                return;
            }
            
            const response = await fetch('/diagnose', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    data: currentData.data,
                    actualState: simulatedMentalState
                })
            });
            
            const diagnosis = await response.json();
            
            let diagnosisHtml = '';
            
            for (const state in diagnosis.probabilities) {
                const probability = diagnosis.probabilities[state];
                const percentage = Math.round(probability * 100);
                const isHighest = state === diagnosis.diagnosis;
                
                diagnosisHtml += `
                    <div class="diagnosis ${state} ${isHighest ? 'primary' : 'secondary'}">
                        <h4>${formatStateName(state)}</h4>
                        <div class="confidence-bar">
                            <div class="confidence-level" style="width: ${percentage}%">${percentage}%</div>
                        </div>
                    </div>
                `;
            }
            
            document.getElementById('diagnosisContainer').innerHTML = diagnosisHtml + `
                <div style="margin-top: 20px; padding: 10px; background-color: ${diagnosis.diagnosis === simulatedMentalState ? '#e8f8f5' : '#fdedec'}; border-radius: 4px;">
                    <strong>Diagnosis Accuracy:</strong> ${diagnosis.diagnosis === simulatedMentalState ? 'Correct' : 'Incorrect'} 
                    (Simulated state was ${formatStateName(simulatedMentalState)})
                </div>
            `;
        }
        
        async function generateTreatment() {
            if (!currentData) {
                alert('Please generate sensor data first');
                return;
            }
            
            const response = await fetch('/generate_treatment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    mentalState: simulatedMentalState,
                    userId: document.getElementById('userId').value
                })
            });
            
            const treatment = await response.json();
            
            let treatmentHtml = `
                <div class="treatment">
                    <h3>Personalized Treatment Plan for ${formatStateName(simulatedMentalState)}</h3>
                    
                    <div class="treatment-item">
                        <h4>Digital Therapeutic Content</h4>
                        <p>${treatment.digital_therapeutic}</p>
                    </div>
                    
                    <div class="treatment-item">
                        <h4>VR/AR Therapy Session</h4>
                        <p>${treatment.vr_therapy}</p>
                    </div>
                    
                    <div class="treatment-item">
                        <h4>AI-Generated Music Therapy</h4>
                        <p>${treatment.music_therapy}</p>
                    </div>
                    
                    <div class="treatment-item">
                        <h4>Recommended Physical Activity</h4>
                        <p>${treatment.physical_activity}</p>
                    </div>
                    
                    <div class="treatment-item">
                        <h4>Monitoring Schedule</h4>
                        <p>${treatment.monitoring}</p>
                    </div>
                </div>
            `;
            
            document.getElementById('treatmentContainer').innerHTML = treatmentHtml;
        }
        
        function formatStateName(state) {
            switch(state) {
                case 'normal': return 'Normal';
                case 'depression': return 'Depression';
                case 'anxiety': return 'Anxiety';
                case 'stress': return 'Stress';
                case 'bipolar_manic': return 'Bipolar (Manic Phase)';
                case 'bipolar_depressive': return 'Bipolar (Depressive Phase)';
                default: return state;
            }
        }
    </script>
</body>
</html>
"""

# Write the template to the templates directory
with open('templates/index.html', 'w') as f:
    f.write(TEMPLATE_HTML)

@app.route('/')
def index():
    """Render the main simulation interface"""
    return render_template('index.html')

@app.route('/generate_data', methods=['POST'])
def generate_data():
    """
    Generate simulated sensor data based on request parameters
    """
    request_data = request.json
    user_id = request_data.get('userId', 'test_user')
    mental_state = request_data.get('mentalState', 'normal')
    duration = float(request_data.get('duration', 1))
    
    # Create the simulator with the specified parameters
    simulator = EarSensorSimulator(user_id=user_id, mental_state=mental_state)
    
    # Generate a data packet
    data_packet = simulator.generate_sensor_data_packet(duration_seconds=duration)
    
    # Generate a plot of the impedance data
    impedance_data = data_packet["impedance_data"]["impedance_measurements"]
    frequencies = [item["frequency_hz"] for item in impedance_data]
    magnitudes = [item["magnitude_ohm"] for item in impedance_data]
    
    # Create the impedance plot
    plt.figure(figsize=(10, 6))
    plt.loglog(frequencies, magnitudes)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Impedance (Ohm)')
    plt.title(f'Impedance Spectrum - {mental_state.capitalize()} State')
    plt.grid(True, which="both", ls="--")
    
    # Save the plot to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Convert the plot to a base64 string
    plot_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    
    return jsonify({
        'data': data_packet,
        'plot': plot_data
    })

@app.route('/diagnose', methods=['POST'])
def diagnose():
    """
    Simulate AI diagnosis of mental health state based on sensor data
    """
    request_data = request.json
    sensor_data = request_data.get('data', {})
    actual_state = request_data.get('actualState', 'normal')
    
    # In a real system, this would use a trained ML model
    # For simulation, we'll use a simple rule-based approach with randomness
    
    # Define baseline probabilities (higher for the actual state)
    states = ['normal', 'depression', 'anxiety', 'stress', 'bipolar_manic', 'bipolar_depressive']
    
    # Simulate model confidence (with some randomness)
    probabilities = {}
    
    # Base probabilities
    for state in states:
        # Higher probability for the actual state, but with some uncertainty
        if state == actual_state:
            # 70-90% probability for the actual state
            probabilities[state] = 0.7 + (0.2 * np.random.random())
        else:
            # 0-15% probability for other states
            probabilities[state] = 0.15 * np.random.random()
    
    # Normalize probabilities to sum to 1
    total = sum(probabilities.values())
    for state in probabilities:
        probabilities[state] /= total
    
    # Determine the diagnosis (highest probability state)
    diagnosis = max(probabilities, key=probabilities.get)
    
    # Add some processing delay to simulate AI computation
    import time
    time.sleep(1)
    
    return jsonify({
        'diagnosis': diagnosis, 
        'probabilities': probabilities,
        'accuracy': diagnosis == actual_state
    })

@app.route('/generate_treatment', methods=['POST'])
def generate_treatment():
    """
    Generate a personalized treatment plan based on the diagnosed mental state
    """
    request_data = request.json
    mental_state = request_data.get('mentalState', 'normal')
    user_id = request_data.get('userId', 'test_user')
    
    # Mock treatments for different mental states
    treatments = {
        'normal': {
            'digital_therapeutic': 'Maintenance mindfulness program: 10-minute daily sessions focused on awareness and gratitude.',
            'vr_therapy': 'Virtual nature walk in serene environments with guided relaxation exercises.',
            'music_therapy': 'Personalized ambient music with alpha wave entrainment to maintain mental balance.',
            'physical_activity': 'Regular moderate exercise routine: 30 minutes of cardio 3-4 times per week.',
            'monitoring': 'Weekly check-ins to maintain optimal mental health patterns.'
        },
        'depression': {
            'digital_therapeutic': 'Cognitive Behavioral Therapy program with focus on challenging negative thought patterns and behavioral activation.',
            'vr_therapy': 'Immersive positive experience simulation with gradual exposure to rewarding social interactions.',
            'music_therapy': 'Dynamic music therapy with gradually increasing tempo and major key compositions to stimulate positive mood states.',
            'physical_activity': 'Morning light exposure combined with gradual introduction to aerobic exercise, starting with 10-minute sessions.',
            'monitoring': 'Daily mood tracking with AI chatbot check-ins and weekly progress assessment.'
        },
        'anxiety': {
            'digital_therapeutic': 'Guided exposure therapy and breathing regulation exercises with real-time biofeedback.',
            'vr_therapy': 'Gradual exposure to anxiety-triggering scenarios with integrated relaxation techniques.',
            'music_therapy': 'Binaural beats with decreasing tempo pattern to reduce physiological arousal.',
            'physical_activity': 'Stress-reducing yoga and tai chi sequences with mindful breathing components.',
            'monitoring': 'Real-time anxiety level monitoring with automated intervention during peak episodes.'
        },
        'stress': {
            'digital_therapeutic': 'Stress management program with progressive muscle relaxation and cognitive reframing techniques.',
            'vr_therapy': 'Peaceful environment simulation with guided meditation and breathing exercises.',
            'music_therapy': 'Theta wave music composition with nature sounds to promote relaxation response.',
            'physical_activity': 'Moderate intensity exercise alternating with stretching routines to reduce cortisol levels.',
            'monitoring': 'Stress trigger identification and hourly micro-interventions during high-stress periods.'
        },
        'bipolar_manic': {
            'digital_therapeutic': 'Cognitive regulation and sleep hygiene program to stabilize mood and energy levels.',
            'vr_therapy': 'Calming environment with reduced stimulation and structured activity simulation.',
            'music_therapy': 'Rhythmic stabilization music with gradual tempo reduction to modulate arousal.',
            'physical_activity': 'Structured, consistent exercise routine with emphasis on predictable, calming activities.',
            'monitoring': 'Continuous mood and sleep monitoring with early intervention for manic episode indicators.'
        },
        'bipolar_depressive': {
            'digital_therapeutic': 'Integrated mood and activity monitoring with behavioral activation components.',
            'vr_therapy': 'Bright light simulation environment with gradually increasing social interaction scenarios.',
            'music_therapy': 'Dynamic music composition transitioning from minor to major keys with increasing tempo.',
            'physical_activity': 'Structured morning exercise with bright light exposure and social components.',
            'monitoring': 'Daily energy and mood tracking with sleep pattern optimization.'
        }
    }
    
    # Add some personalization based on user ID
    # This would use actual user profile data in a real system
    treatment = treatments.get(mental_state, treatments['normal'])
    
    # Add processing delay to simulate AI treatment generation
    import time
    time.sleep(1.5)
    
    return jsonify(treatment)

if __name__ == '__main__':
    # Create the templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Write the template to file
    with open('templates/index.html', 'w') as f:
        f.write(TEMPLATE_HTML)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
