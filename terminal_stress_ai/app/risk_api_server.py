"""
Flask API Server for CoSensei Risk Analysis & Dual-AI Chat
Serves both security risk data and CoSensei AI chat through REST
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code_generator_with_risks import CodeGenerator
from cosensei_api_service import cosensei_service

app = Flask(__name__)
CORS(app)

# Initialize code generator
code_generator = CodeGenerator()

@app.route('/api/risks', methods=['GET'])
def get_risks():
    """Generate and return all security risks in REST format"""
    
    try:
        # Generate all code and risks
        gen = CodeGenerator()
        
        risk_data = {
            "summary": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "total": 0
            },
            "files": {}
        }
        
        # Process each file template
        files_to_process = [
            ("main.py", gen.get_main_py),
            ("config.py", gen.get_config_py),
            ("routes.py", gen.get_routes_py),
            ("models.py", gen.get_models_py)
        ]
        
        for filename, method in files_to_process:
            code, risks, fixes = method()
            
            # Format risks data
            formatted_risks = []
            risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}
            
            for severity, title, description in risks:
                formatted_risks.append({
                    "severity": severity,
                    "title": title,
                    "description": description
                })
                
                # Count each severity level
                if severity in risk_counts:
                    risk_counts[severity] += 1
            
            # Update global counts
            risk_data["summary"]["critical"] += risk_counts["CRITICAL"]
            risk_data["summary"]["high"] += risk_counts["HIGH"]
            risk_data["summary"]["medium"] += risk_counts["MEDIUM"]
            
            # Store file data
            risk_data["files"][filename] = {
                "title": f"{filename} - {_get_file_title(filename)}",
                "description": _get_file_description(filename),
                "risks": formatted_risks,
                "unsafeCode": code,
                "secureCode": _get_secure_code(filename),
                "fixes": fixes
            }
        
        risk_data["summary"]["total"] = (
            risk_data["summary"]["critical"] + 
            risk_data["summary"]["high"] + 
            risk_data["summary"]["medium"]
        )
        
        return jsonify(risk_data), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/file/<filename>', methods=['GET'])
def get_file_analysis(filename):
    """Get analysis for a specific file"""
    
    gen = CodeGenerator()
    
    try:
        if filename == "main.py":
            code, risks, fixes = gen.get_main_py()
            title = "Flask Application Entry Point"
        elif filename == "config.py":
            code, risks, fixes = gen.get_config_py()
            title = "Application Configuration"
        elif filename == "routes.py":
            code, risks, fixes = gen.get_routes_py()
            title = "API Routes and Endpoints"
        elif filename == "models.py":
            code, risks, fixes = gen.get_models_py()
            title = "Database Models"
        else:
            return jsonify({"error": "File not found"}), 404
        
        formatted_risks = [
            {
                "severity": severity,
                "title": title,
                "description": description
            }
            for severity, title, description in risks
        ]
        
        return jsonify({
            "filename": filename,
            "title": title,
            "unsafeCode": code,
            "secureCode": _get_secure_code(filename),
            "risks": formatted_risks,
            "fixes": fixes
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


def _get_file_title(filename: str) -> str:
    """Get human-readable title for file"""
    titles = {
        "main.py": "Flask Application Entry Point",
        "config.py": "Application Configuration",
        "routes.py": "API Routes and Endpoints",
        "models.py": "Database Models"
    }
    return titles.get(filename, filename)


def _get_file_description(filename: str) -> str:
    """Get description for file"""
    descriptions = {
        "main.py": "Main Flask application with DEBUG mode and HTTPS issues",
        "config.py": "Configuration with hardcoded credentials and weak secrets",
        "routes.py": "API endpoints with no authentication and SQL injection vulnerabilities",
        "models.py": "Database models with plaintext passwords and unencrypted PII"
    }
    return descriptions.get(filename, filename)


def _get_secure_code(filename: str) -> str:
    """Get the secure version of code for each file"""
    secure_versions = {
        "main.py": '''"""main.py - Flask application (SECURE)"""
from flask import Flask
from flask_talisman import Talisman
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# [SECURE] Force HTTPS and set security headers
Talisman(app, force_https=True)

@app.route('/api/data', methods=['GET'])
def get_data():
    return {"data": "encrypted over HTTPS"}

if __name__ == '__main__':
    # [SECURE] Bind to localhost only
    app.run(host='127.0.0.1', port=5000, debug=False)''',
        
        "config.py": '''"""config.py - Application Configuration (SECURE)"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # [SECURE] Database URL from environment
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # [SECURE] Strong secret key from environment
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # [SECURE] CORS restricted to known domains
    CORS_ORIGINS = ['https://yourdomain.com', 'https://app.yourdomain.com']
    
    # [SECURE] API keys from environment (never hardcoded)
    STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')
    AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
    TWILIO_TOKEN = os.getenv('TWILIO_TOKEN')
    
    # [SECURE] Security headers
    SECURE_HSTS_SECONDS = 31536000
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True''',
        
        "routes.py": '''"""routes.py - API Routes (SECURE)"""
from flask import request, jsonify
from flask_limiter import Limiter
from functools import wraps
from werkzeug.security import check_password_hash
import jwt

limiter = Limiter(app)

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not verify_token(token):
            return {'error': 'Unauthorized'}, 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/users', methods=['GET'])
@requires_auth
@limiter.limit("10 per minute")
def get_users():
    cursor = conn.cursor()
    # [SECURE] Parameterized queries prevent SQL injection
    cursor.execute("SELECT * FROM users WHERE name = %s", (request.args.get('name'),))
    users = cursor.fetchall()
    return jsonify({'users': users})

def verify_token(token):
    try:
        if not token:
            return False
        jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
        return True
    except:
        return False''',
        
        "models.py": '''"""models.py - Database Models (SECURE)"""
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from cryptography.fernet import Fernet
import os

db = SQLAlchemy()
cipher = Fernet(os.getenv('ENCRYPTION_KEY').encode())

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, index=True)
    email = db.Column(db.String(255), unique=True, index=True)
    
    # [SECURE] Password hashed with bcrypt
    password_hash = db.Column(db.String(255))
    
    # [SECURE] PII encrypted at rest
    ssn = db.Column(db.String(255))
    credit_card = db.Column(db.String(255))
    
    # [SECURE] API keys hashed before storage
    api_key_hash = db.Column(db.String(255))
    
    # [SECURE] Audit logging
    created_at = db.Column(db.DateTime, index=True)
    updated_at = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def encrypt_ssn(self, ssn):
        self.ssn = cipher.encrypt(ssn.encode()).decode()'''
    }
    return secure_versions.get(filename, "")


# ============================================================================
# CoSensei Dual-AI Chat Endpoints
# ============================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process user message through dual-AI pipeline"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        chat_id = data.get('chat_id')
        user_id = data.get('user_id', 'default_user')
        
        if not message:
            return jsonify({"error": "Message required"}), 400
        
        # Generate chat_id if not provided
        if not chat_id:
            chat_id = f"chat_{user_id}_{uuid.uuid4().hex[:8]}"
        
        # Process through CoSensei dual-AI
        response = cosensei_service.process_message(message, chat_id, user_id)
        
        return jsonify(response), 200
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({"error": str(e), "message": "Error processing request"}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get chat history for user"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        history = cosensei_service.get_history(user_id)
        return jsonify(history), 200
    except Exception as e:
        print(f"History error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/history/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get messages for specific chat"""
    try:
        messages = cosensei_service.get_chat_messages(chat_id)
        return jsonify({"messages": messages}), 200
    except Exception as e:
        print(f"Get chat error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*70)
    print("CoSensei API Server  v2 (full-AI, no templates)")
    print("="*70)

    # Test Grok API connectivity on startup
    print("\n[AI] Testing Grok API connection...")
    try:
        import requests as _req, json as _json
        _cfg_path = os.path.join(os.path.dirname(__file__), '..', '.terminal_stress_ai_config.json')
        with open(_cfg_path) as _f:
            _cfg = _json.load(_f)
        _key = _cfg.get('generator_ai', {}).get('api_key') or _cfg.get('grok_api_key', '')
        _model = _cfg.get('generator_ai', {}).get('model', 'grok-3-mini')
        if _key:
            _r = _req.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {_key}", "Content-Type": "application/json"},
                json={"model": _model, "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5},
                timeout=10,
            )
            if _r.status_code == 200:
                print(f"  [OK] Grok API connected  (model: {_model})")
            else:
                print(f"  [WARN] Grok API returned HTTP {_r.status_code} — AI responses will use fallbacks")
        else:
            print("  [WARN] No API key found in config — AI responses will use fallbacks")
    except Exception as _e:
        print(f"  [WARN] Grok API unreachable: {_e} — AI responses will use fallbacks")

    print("\n[ROUTES]")
    print("  POST /api/chat               - CoSensei AI chat")
    print("  GET  /api/history            - Chat history")
    print("  GET  /health                 - Health check")
    print("\n[OK] Server starting on http://localhost:5000")
    print("="*70 + "\n")

    app.run(debug=False, port=5000)
