from flask import Flask, render_template, jsonify, request
from analysis.flask_ai_distress_integration import FlaskAIDistressIntegration

app = Flask(__name__)
distress_integration = FlaskAIDistressIntegration()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/analyze-distress', methods=['POST'])
def analyze_property_distress():
    data = request.json
    result = distress_integration.calculate_distress_score(data)
    return jsonify(result)

@app.route('/api/detailed-analysis', methods=['POST'])
def get_detailed_analysis():
    data = request.json
    result = distress_integration.get_detailed_analysis(data)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000) 