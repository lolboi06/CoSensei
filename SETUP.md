# CoSensei Web Setup Guide

Complete setup instructions for running the React frontend with the Python backend.

## Quick Start

### Option 1: Run Everything at Once (Windows)

**PowerShell:**
```powershell
& "c:\Users\Sam Roger\OneDrive\Documents\ContextFlow\start-fullstack.ps1"
```

**Command Prompt:**
```cmd
cd c:\Users\Sam Roger\OneDrive\Documents\ContextFlow
start-fullstack.bat
```

This will open two new terminals:
- Terminal 1: Python Flask API on http://localhost:5000
- Terminal 2: React Vite dev server on http://localhost:3000

---

## Manual Setup

### Backend Setup (Python)

1. **Activate virtual environment:**
```powershell
& "c:\Users\Sam Roger\OneDrive\Documents\ContextFlow\.venv\Scripts\Activate.ps1"
```

2. **Navigate to app directory:**
```powershell
cd "c:\Users\Sam Roger\OneDrive\Documents\ContextFlow\terminal_stress_ai"
```

3. **Install required packages (if not already installed):**
```bash
pip install flask flask-cors
```

4. **Start the API server:**
```bash
python app/risk_api_server.py
```

You should see:
```
======================================================================
CoSensei Risk Analysis API Server
======================================================================

APIs Available:
  GET  /api/risks              - Get all security risks
  GET  /api/file/<filename>    - Get specific file analysis
  GET  /health                 - Health check

Server running on http://localhost:5000
```

### Frontend Setup (React)

1. **In a new terminal, navigate to the web directory:**
```powershell
cd "c:\Users\Sam Roger\OneDrive\Documents\ContextFlow\cosensei-web"
```

2. **Install dependencies (first time only):**
```bash
npm install
```

3. **Start the development server:**
```bash
npm run dev
```

You should see:
```
  VITE v5.0.0  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  press h to show help
```

4. **Open your browser to http://localhost:3000**

---

## API Endpoints

### Get All Risks

**GET** `/api/risks`

Returns all security risks across all files.

**Response:**
```json
{
  "summary": {
    "critical": 10,
    "high": 9,
    "medium": 3,
    "total": 22
  },
  "files": {
    "main.py": { ... },
    "config.py": { ... },
    "routes.py": { ... },
    "models.py": { ... }
  }
}
```

### Get Specific File Analysis

**GET** `/api/file/<filename>`

Get analysis for a specific file (main.py, config.py, routes.py, or models.py).

**Response:**
```json
{
  "filename": "config.py",
  "title": "Application Configuration",
  "unsafeCode": "...",
  "secureCode": "...",
  "risks": [ ... ],
  "fixes": [ ... ]
}
```

### Health Check

**GET** `/health`

Check if the API server is running.

---

## Features

### File Analysis Display
The React app displays four key files with security issues:

1. **main.py** - Flask application entry point
   - 3 Critical/High issues
   - Debug mode, HTTPS, host exposure issues

2. **config.py** - Configuration file
   - 5 Critical/High issues
   - Hardcoded credentials, weak secrets, CORS issues

3. **routes.py** - API endpoints
   - 6 Critical/High issues
   - No authentication, SQL injection, SSTI

4. **models.py** - Database models
   - 5 Critical/High issues
   - Plaintext passwords, unencrypted PII

### Risk Visualization

Each risk shows:
- **Severity Badge** - Color-coded (Red=Critical, Orange=High, Yellow=Medium)
- **Title** - Brief issue description
- **Description** - Detailed explanation of the risk
- **Unsafe Code** - The problematic code snippet
- **Secure Code** - Fixed version of the code
- **Fixes List** - Step-by-step remediation

### Live Toggle
Switch between unsafe and secure code versions with a button click.

---

## Troubleshooting

### Port Already in Use

If port 3000 or 5000 is already in use:

**React on different port:**
```bash
npm run dev -- --port 3001
```

**Python on different port:**
Edit `risk_api_server.py` line 127:
```python
app.run(debug=True, port=5001)  # Change to 5001
```

Then update `vite.config.js` proxy target accordingly.

### CORS Errors

If you see CORS errors in the browser console, make sure:
1. The Flask backend is running with `CORS(app)` enabled (it should be by default)
2. The frontend is making requests to the correct backend URL
3. Both servers are using http:// not https:// for local development

### npm Install Issues

If `npm install` fails, try:
```bash
npm install --legacy-peer-deps
npm cache clean --force
npm install
```

### Python Module Not Found

If you get import errors, make sure you're in the virtual environment:
```powershell
& "c:\Users\Sam Roger\OneDrive\Documents\ContextFlow\.venv\Scripts\Activate.ps1"
```

---

## Building for Production

### Create an optimized React build:
```bash
cd cosensei-web
npm run build
```

This creates a `dist/` folder with optimized production files.

### Preview the production build:
```bash
npm run preview
```

---

## Environment Variables

Create a `.env` file in `cosensei-web/` if you need to customize settings:

```env
VITE_API_URL=http://localhost:5000
VITE_API_ENDPOINT=/api/risks
```

---

## File Structure

```
ContextFlow/
├── terminal_stress_ai/
│   ├── app/
│   │   ├── code_generator_with_risks.py  (Security risk templates)
│   │   ├── risk_api_server.py            (Flask API backend)
│   │   ├── contextflow_coordinator.py    (Main system)
│   │   └── ... (other app files)
│   ├── .venv/                            (Python virtual environment)
│   └── ...
├── cosensei-web/                         (React frontend)
│   ├── src/
│   │   ├── components/
│   │   │   ├── RiskCard.jsx
│   │   │   ├── CodeComparison.jsx
│   │   │   └── SecuritySummary.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   └── ...
├── start-fullstack.ps1                   (PowerShell startup script)
├── start-fullstack.bat                   (Batch startup script)
└── ...
```

---

## Next Steps

1. **Customize the demo data**: Edit `App.jsx` to load real data from your own code analysis
2. **Add more files**: Extend the code generator to analyze more Python files
3. **Build reports**: Add export-to-PDF functionality for security audit reports
4. **Team collaboration**: Add GitHub integration to scan actual repositories
5. **Real-time updates**: WebSocket integration for live security monitoring

---

## Support

For issues or questions:
1. Check the CoSensei README in terminal_stress_ai/
2. Review the code_generator_with_risks.py for risk templates
3. Check React console for frontend errors (F12 in browser)
4. Check Python console for backend errors

Happy security auditing! 🔒
