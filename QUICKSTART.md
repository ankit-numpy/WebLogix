# Quick Start Guide

## For Developers

### Setup (First Time)

```bash
# 1. Clone the repo
git clone https://github.com/ankit-numpy/WebLogix.git
cd WebLogix

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file
cp .env.example .env

# 6. Run application
python app.py
```

Visit: `http://localhost:5000`

### Making Changes

```bash
# 1. Make your changes
# Edit files...

# 2. Test locally
python app.py

# 3. Commit changes
git add .
git commit -m "Description of changes"

# 4. Push to GitHub
git push origin main
```

**Render will auto-deploy after push!**

---

## For Admins

**Passkey:** `weblogix2014`

Path: `/tcs/admin`

---

## Common Tasks

### View Logs
```bash
# If deployed on Render, check logs in Render dashboard
# For local development:
python app.py
# Watch terminal output
```

### Reset Database
```bash
# Delete the database file
rm weblogix.db

# Or run init script
python init_db.py
```

### Update Dependencies
```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

---

## File Summary

| File | Purpose |
|------|---------|
| `app.py` | Main Flask application |
| `requirements.txt` | Python dependencies |
| `render.yaml` | Render deployment config |
| `Procfile` | WSGI process definition |
| `runtime.txt` | Python version |
| `.env.example` | Environment variables template |
| `README.md` | Project documentation |
| `DEPLOYMENT.md` | Deployment instructions |

---

## Need Help?

1. **Local Issues:** Run `python app.py` and check terminal output
2. **Deployment Issues:** Check Render dashboard logs
3. **GitHub Issues:** See GitHub repository issues page
