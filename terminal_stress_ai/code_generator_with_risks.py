"""
CoSensei Implementation Generator - Enhanced with Real Code & Security Risks (AI #4)
Generates concrete implementation details with actual code templates showing security vulnerabilities
"""

import sys
import os
from typing import Dict, List, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class CodeGenerator:
    """Generates actual code templates with embedded security risks"""
    
    @staticmethod
    def get_main_py() -> tuple:
        """main.py with security risks highlighted"""
        code = '''"""Main entry point - Flask application"""
from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# [RISK #1] DEBUG MODE ENABLED IN PRODUCTION
app.config['DEBUG'] = True  # DANGER: Never set to True in production!

# [RISK #2] No HTTPS/SSL enforcement
@app.route('/api/data', methods=['GET'])
def get_data():
    return {"data": "unencrypted"}  # Data sent over HTTP!

if __name__ == '__main__':
    # [RISK #3] Hardcoded port, exposed to all interfaces
    app.run(host='0.0.0.0', port=5000)  # Accessible from anywhere!
'''
        
        risks = [
            ("CRITICAL", "Debug mode enabled", "Exposes stack traces, source code, secrets"),
            ("CRITICAL", "No HTTPS", "All data transmitted in plain text"),
            ("HIGH", "Exposed host", "Server accessible from any network interface")
        ]
        
        fixes = [
            "[OK] Set DEBUG = False in production",
            "[OK] Force HTTPS with Talisman: Talisman(app, force_https=True)",
            "[OK] Bind to localhost: host='127.0.0.1' with reverse proxy"
        ]
        
        return code, risks, fixes
    
    @staticmethod
    def get_config_py() -> tuple:
        """config.py with hardcoded credentials"""
        code = '''"""Application Configuration - UNSAFE"""
import os

class Config:
    # [RISK #1] Hardcoded database credentials
    SQLALCHEMY_DATABASE_URI = 'mysql://root:password123@localhost/mydb'
    # DANGER: Everyone can see the password!
    
    # [RISK #2] Weak secret key
    SECRET_KEY = 'super-secret-key-123'  # Predictable!
    
    # [RISK #3] No CORS restrictions
    CORS_ORIGINS = '*'  # Allows attacks from any domain!
    
    # [RISK #4] API keys exposed in source code
    STRIPE_API_KEY = 'sk_live_abc123xyz789'  # Will commit to git!
    AWS_SECRET = 'AKIA2XXXXXXXXXXXXX'  # AWS will revoke!
    TWILIO_TOKEN = 'your-secret-token-here'  # Public!
    
    # [RISK #5] No encryption for sensitive settings
    JWT_SECRET = 'its-a-secret'  # Not truly secret if in code!
'''
        
        risks = [
            ("CRITICAL", "DB password in code", "Anyone with repo access has database access"),
            ("CRITICAL", "API keys exposed", "Third-party services can be abused"),
            ("HIGH", "Weak SECRET_KEY", "Sessions can be forged"),
            ("HIGH", "CORS open to all", "CSRF and XSS attacks possible"),
            ("HIGH", "No encryption", "Sensitive config visible in plaintext")
        ]
        
        fixes = [
            "[OK] Use environment variables: SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')",
            "[OK] Load from .env file: from dotenv import load_dotenv",
            "[OK] Generate strong key: import secrets; SECRET_KEY = secrets.token_hex(32)",
            "[OK] Restrict CORS: CORS_ORIGINS = ['https://yourdomain.com']",
            "[OK] Never commit .env: Add to .gitignore"
        ]
        
        return code, risks, fixes
    
    @staticmethod
    def get_routes_py() -> tuple:
        """routes.py with multiple security vulnerabilities"""
        code = '''"""API Routes - Multiple Security Issues"""
from flask import request, jsonify, render_template_string
from app import app
import mysql.connector

conn = mysql.connector.connect(host='localhost', user='root', password='pass123')

# [RISK #1] No authentication on endpoint
@app.route('/api/users', methods=['GET'])
def get_users():
    # DANGER: Anyone can get ALL user data!
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password, ssn, credit_card FROM users")
    users = cursor.fetchall()
    return jsonify({'users': users})  # PII exposed!

# [RISK #2] SQL Injection vulnerability
@app.route('/api/search', methods=['POST'])
def search_users():
    name = request.json.get('name')
    # DANGER: Direct string concatenation allows SQL injection!
    query = f"SELECT * FROM users WHERE name = '{name}'"
    cursor = conn.cursor()
    cursor.execute(query)
    return jsonify({'result': cursor.fetchall()})

# [RISK #3] No file type validation
@app.route('/api/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    # DANGER: No validation - attacker can upload executable!
    file.save(f'/uploads/{file.filename}')
    return {'success': True}

# [RISK #4] Server-Side Template Injection (SSTI)
@app.route('/api/render', methods=['POST'])
def render_page():
    user_template = request.json.get('template')
    # DANGER: SSTI - Attacker can execute arbitrary Python!
    return render_template_string(user_template)

# [RISK #5] No rate limiting
@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    # DANGER: Brute force attack possible! No rate limit!
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
    user = cursor.fetchone()
    if user and user[2] == password:  # Plain text password comparison!
        return {'success': True}
    return {'error': 'Invalid credentials'}
'''
        
        risks = [
            ("CRITICAL", "No authentication", "Anyone can access all user data including PII"),
            ("CRITICAL", "SQL Injection", "Attacker can extract/modify database"),
            ("CRITICAL", "SSTI vulnerability", "Attacker can execute arbitrary Python code"),
            ("HIGH", "No file validation", "Malware can be uploaded and executed"),
            ("HIGH", "No rate limiting", "Brute force attacks on authentication"),
            ("HIGH", "Exposed credentials", "Database connection string hardcoded")
        ]
        
        fixes = [
            "[OK] Add auth: @app.route('/api/users'); @requires_auth",
            "[OK] Use parameterized queries: execute('SELECT * FROM users WHERE name = %s', (name,))",
            "[OK] Never use render_template_string with user input",
            "[OK] Whitelist file types: if file.mimetype not in ALLOWED_TYPES",
            "[OK] Add rate limiting: from flask_limiter import Limiter",
            "[OK] Move DB connection to environment variables"
        ]
        
        return code, risks, fixes
    
    @staticmethod
    def get_models_py() -> tuple:
        """models.py with unencrypted sensitive data"""
        code = '''"""Database Models - No Encryption for Sensitive Data"""
from flask_sqlalchemy import SQLAlchemy
from app import app

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    
    # [RISK #1] Password stored in PLAIN TEXT!
    password = db.Column(db.String(255))  # NO HASHING! Anyone with DB gets passwords!
    
    # [RISK #2] PII not encrypted (Personally Identifiable Information)
    ssn = db.Column(db.String(11))  # Social Security Number unencrypted!
    credit_card = db.Column(db.String(16))  # VISA number visible in DB!
    bank_account = db.Column(db.String(20))  # Bank account unencrypted!
    phone = db.Column(db.String(20))  # Phone number exposed!
    
    # [RISK #3] No indexes on frequently queried fields
    created_at = db.Column(db.DateTime)  # Missing index = slow queries
    
    # [RISK #4] No soft delete / audit trail
    # If record deleted, no way to recover or audit!

class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # [RISK #5] API keys stored in plaintext
    key = db.Column(db.String(255))  # Anyone with DB gets all API keys!
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Missing fields: expiration, rate_limit, permissions, last_used
'''
        
        risks = [
            ("CRITICAL", "Plaintext passwords", "Database breach = all user passwords compromised"),
            ("CRITICAL", "Unencrypted PII", "SSN, credit cards exposed - identity theft risk"),
            ("CRITICAL", "Plaintext API keys", "API keys can be used by attackers"),
            ("HIGH", "No indexes", "Slow queries, poor performance under load"),
            ("HIGH", "No audit trail", "Cannot track who accessed/modified data")
        ]
        
        fixes = [
            "[OK] Hash passwords: from werkzeug.security import generate_password_hash",
            "[OK] Encrypt PII: from cryptography.fernet import Fernet; encrypted = cipher.encrypt(ssn)",
            "[OK] Hash API keys: return hash(key) to database, never store plain",
            "[OK] Add indexes: db.Index('idx_created_at', User.created_at)",
            "[OK] Add soft delete: deleted_at = db.Column(db.DateTime, nullable=True)",
            "[OK] Add audit logs: Track all access and modifications"
        ]
        
        return code, risks, fixes


class ImplementationGenerator:
    """AI #4: Enhanced implementation guide with real code and security risks"""
    
    def generate_code_with_risks(self, solution: str) -> Dict[str, Any]:
        """Generate actual code files with embedded security risks"""
        
        code_gen = CodeGenerator()
        
        files_with_risks = {
            'main.py': code_gen.get_main_py(),
            'config.py': code_gen.get_config_py(),
            'routes.py': code_gen.get_routes_py(),
            'models.py': code_gen.get_models_py()
        }
        
        return files_with_risks
    
    def format_code_with_risks_display(self, files_with_risks: Dict) -> str:
        """Format code files with highlighted risks for terminal display"""
        
        output = []
        output.append("\n" + "="*70)
        output.append("ACTUAL CODE TEMPLATES - WITH SECURITY RISKS HIGHLIGHTED")
        output.append("="*70 + "\n")
        
        for filename, (code, risks, fixes) in files_with_risks.items():
            output.append(f"\n[FILE] {filename}")
            output.append("-"*70)
            
            # Show code sample (first 15 lines)
            code_lines = code.split('\n')[:15]
            for line in code_lines:
                output.append(line)
            output.append("    ... [code continues] ...\n")
            
            # Show risks
            output.append("[RISKS FOUND]:")
            for severity, title, description in risks:
                marker = "[CRITICAL]" if severity == "CRITICAL" else "[HIGH]" if severity == "HIGH" else "[MEDIUM]"
                output.append(f"  {marker} {title}")
                output.append(f"     -> {description}")
            
            # Show fixes
            output.append("\n[HOW TO FIX]:")
            for i, fix in enumerate(fixes[:3], 1):
                fix = fix.replace("[OK]", "[FIX]")
                output.append(f"  {i}. {fix}")
            if len(fixes) > 3:
                output.append(f"  ... and {len(fixes)-3} more fixes")
            
            output.append("")
        
        output.append("\n" + "="*70)
        output.append("[SECURITY SUMMARY]")
        output.append("="*70)
        
        total_critical = sum(1 for _, (_, risks, _) in files_with_risks.items() 
                            for severity, _, _ in risks if severity == "CRITICAL")
        total_high = sum(1 for _, (_, risks, _) in files_with_risks.items() 
                        for severity, _, _ in risks if severity == "HIGH")
        
        output.append(f"\nTotal Vulnerabilities Found:")
        output.append(f"  [CRITICAL]: {total_critical} (Must fix before deployment)")
        output.append(f"  [HIGH]:     {total_high} (Should fix before deployment)")
        output.append("\nAll vulnerabilities have recommended fixes above!")
        output.append("\nTIP: Use this output to implement secure code from the start!")
        output.append("\n")
        
        return "\n".join(output)


def demo_code_with_risks():
    """Demonstrate code generation with security risks"""
    
    print("\n" + "="*70)
    print("COSENSEI - REAL CODE WITH SECURITY RISKS DEMO")
    print("="*70)
    
    generator = ImplementationGenerator()
    files_with_risks = generator.generate_code_with_risks('simple')
    display = generator.format_code_with_risks_display(files_with_risks)
    print(display)
    
    # Show detailed analysis of one file
    print("\n" + "="*70)
    print("[DETAILED ANALYSIS] config.py")
    print("="*70 + "\n")
    
    code, risks, fixes = files_with_risks['config.py']
    
    print("[CURRENT UNSAFE CODE]:")
    print("-"*70)
    for line in code.split('\n')[:15]:
        print(line)
    print()
    
    print("[DETAILED RISKS]:")
    print("-"*70)
    for severity, title, description in risks:
        marker = "[CRITICAL]" if severity == "CRITICAL" else "[HIGH]"
        print(f"\n{marker}: {title}")
        print(f"   Problem: {description}")
    
    print("\n\n[SECURE VERSION (After Fixes)]:")
    print("-"*70)
    secure_version = '''"""Application Configuration - SECURE"""
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
    
    # [SECURE] API keys from environment (not hardcoded)
    STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')
    AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
    TWILIO_TOKEN = os.getenv('TWILIO_TOKEN')
    
    # [SECURE] JWT secret strong and from environment
    JWT_SECRET = os.getenv('JWT_SECRET')
    
    # [SECURE] Security headers
    SECURE_HSTS_SECONDS = 31536000
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
'''
    
    for line in secure_version.split('\n')[:20]:
        print(line)
    
    print("\n\n[KEY IMPROVEMENTS]:")
    print("-"*70)
    for i, fix in enumerate(fixes, 1):
        print(f"{i}. {fix}")


if __name__ == "__main__":
    demo_code_with_risks()
