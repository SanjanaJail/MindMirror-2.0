from flask import Flask, send_from_directory, render_template
from flask_cors import CORS
import os

# Create a separate Flask app just for the landing page
landing_app = Flask(__name__)
CORS(landing_app)

# Simple route for landing page
@landing_app.route('/')
def landing():
    """Serve the landing page"""
    print("🎯 Serving landing page")
    return render_template('landing.html')

# Serve static files (CSS, JS) - SIMPLIFIED
@landing_app.route('/auth.css')
def serve_css():
    return send_from_directory('.', 'auth.css')

@landing_app.route('/auth.js')
def serve_js():
    return send_from_directory('.', 'auth.js')

if __name__ == "__main__":
    print("✅ Starting LANDING PAGE server on port 5000...")
    print("📁 Current directory:", os.getcwd())
    print("📁 Files available:", os.listdir('.'))
    landing_app.run(host="0.0.0.0", port=5500, debug=True)