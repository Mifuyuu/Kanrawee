# Copilot Instructions for Kanrawee Project

## Project Overview
- This is a Flask web application for analyzing user emotions using the Gemini AI API (Google Generative AI).
- The app provides a web UI for users to submit a message and emoji, analyzes the input with Gemini, and stores the result in `emotion_history.json`.
- The app also computes a 7-day rolling risk assessment for depression based on emotion scores.

## Key Files & Structure
- `app.py`: Main Flask app. All routes, AI integration, and data logic are here.
- `templates/index.html`: Main UI. Handles emoji selection, text input, and displays results/history. Uses vanilla JS for API calls.
- `emotion_history.json`: Stores all user entries and analysis results.
- `requirements.txt`: Python dependencies (Flask, python-dotenv, google-generativeai, uvicorn).
- `Procfile`: For deployment (e.g., Heroku). Runs with `uvicorn app:app`.
- `.env` (not committed): Must provide `GEMINI_API_KEY` for Gemini API access.

## Developer Workflows
- **Run locally:**
  1. Install dependencies: `pip install -r requirements.txt`
  2. Set up `.env` with `GEMINI_API_KEY`.
  3. Start server: `python app.py` (for Flask debug) or `uvicorn app:app --host 0.0.0.0 --port 5000` (for production-like run).
- **Deploy:** Use `Procfile` with a platform like Heroku. Ensure `GEMINI_API_KEY` is set in environment variables.
- **Data reset:** Delete or edit `emotion_history.json` to clear user data/history.

## Patterns & Conventions
- All API endpoints are defined in `app.py`.
- JSON responses are used for all API endpoints.
- AI prompt and response format is strictly enforced (see `analyze` route in `app.py`).
- Error handling: If Gemini API fails, a fallback response is returned with a default score and error message.
- UI and backend are tightly coupled: Frontend JS expects specific JSON fields from backend.
- All user data is stored in a single JSON file (`emotion_history.json`). No database is used.

## Integration Points
- **Gemini API:** Requires valid API key in `.env` as `GEMINI_API_KEY`.
- **Frontend-backend:** All communication via fetch/XHR to Flask endpoints (`/analyze`, `/save`, `/history7`).

## Examples
- To add a new emotion analysis metric, update both the AI prompt in `app.py` and the frontend display logic in `index.html`.
- To change risk assessment logic, edit `evaluate_depression_risk` in `app.py`.

## Cautions
- Do not commit `.env` or sensitive keys.
- `run.bat` references `index.py` (should be `app.py` if used for this project).
- `emotion_history.json` may become large; consider archiving or rotating if needed.

---
For questions or unclear conventions, review `app.py` and `index.html` for the latest patterns.
