import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.generativeai as genai

# โหลด .env (ใน Railway จะใช้ Environment Variables แทนไฟล์ .env ก็ได้)
load_dotenv()

app = FastAPI()

# Template และ Static Files
templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")

# ตั้งค่า Gemini API
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-2.0-flash')
except KeyError:
    model = None
    print("❌ GEMINI_API_KEY not found")
except Exception as e:
    model = None
    print(f"❌ Error configuring Gemini API: {e}")

DATA_FILE = "emotion_history.json"

# โหลดประวัติ
def load_history():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            return json.loads(content) if content else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# บันทึกประวัติ
def save_history(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ประเมินความเสี่ยงซึมเศร้า
def evaluate_depression_risk(avg_score):
    if avg_score < 20:
        return {
            "level": "สูง",
            "message": "คะแนนอารมณ์ต่ำมาก แสดงว่ามีความเสี่ยงสูงที่จะเป็นภาวะซึมเศร้า ควรรีบพบผู้เชี่ยวชาญหรือนักจิตวิทยา"
        }
    elif avg_score < 40:
        return {
            "level": "ปานกลาง",
            "message": "คะแนนอารมณ์อยู่ในระดับปานกลาง อาจมีความเครียดหรือวิตกกังวล ควรดูแลสุขภาพจิตอย่างใกล้ชิด"
        }
    elif avg_score < 60:
        return {
            "level": "เล็กน้อย",
            "message": "คะแนนอารมณ์อยู่ในระดับพึ่งเริ่ม เข้าค่ายที่จะเป็นภาวะซึมเศร้า อาจมีความเครียดหรือวิตกกังวล"
        }
    else:
        return {
            "level": "ปกติ",
            "message": "คะแนนอารมณ์อยู่ในระดับปกติ ไม่มีความเสี่ยงซึมเศร้าในระดับน่ากังวล"
        }

# หน้าแรก
@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# วิเคราะห์อารมณ์
@app.post("/analyze")
async def analyze(data: dict = Body(...)):
    if not model:
        return JSONResponse({"error": "Gemini API is not configured."}, status_code=500)

    message = data.get("message", "").strip()
    emoji = data.get("emoji", "").strip()

    if not message:
        return JSONResponse({"error": "Missing message"}, status_code=400)
    if not emoji:
        return JSONResponse({"error": "Missing emoji"}, status_code=400)

    prompt = f"""
    วิเคราะห์ข้อความและอีโมจิต่อไปนี้ แล้วตอบกลับเป็น JSON object เท่านั้น ห้ามมีข้อความอื่นนอกเหนือจาก JSON
    ข้อความ: "{message}"
    อีโมจิ: {emoji}

    หน้าที่ของคุณ:
    1.  `emotion`: ระบุอารมณ์หลักของข้อความเป็นภาษาไทย (เช่น "มีความสุข", "เศร้า", "โกรธ").
    2.  `summary`: สรุปใจความสำคัญของข้อความสั้นๆ เป็นภาษาไทย.
    3.  `emotionScore`: ให้คะแนนอารมณ์จาก 0 ถึง 100 (0 คือแง่ลบสุดๆ, 100 คือแง่บวกสุดๆ).

    ตัวอย่าง JSON output ที่ต้องการ:
    {{
      "emotion": "มีความสุข",
      "summary": "ผู้เขียนรู้สึกดีใจที่ได้ไปเที่ยวทะเลกับเพื่อนๆ",
      "emotionScore": 95
    }}

    วิเคราะห์ข้อมูลต่อไปนี้และสร้าง JSON object ตามรูปแบบที่กำหนด:
    """

    try:
        response = model.generate_content(prompt)
        cleaned = response.text.strip().replace("```json", "").replace("```", "").strip()
        ai_result = json.loads(cleaned)

        entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "message": message,
            "emoji": emoji,
            "emotion": ai_result.get("emotion", "N/A"),
            "summary": ai_result.get("summary", "N/A"),
            "emotionScore": ai_result.get("emotionScore", 50),
        }
        return JSONResponse(entry)

    except Exception as e:
        return JSONResponse({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "message": message,
            "emoji": emoji,
            "emotion": "ไม่สามารถวิเคราะห์ได้",
            "summary": f"เกิดข้อผิดพลาดในการสื่อสารกับ AI: {e}",
            "emotionScore": 50,
        }, status_code=500)

# บันทึกข้อมูล
@app.post("/save")
async def save_entry(entry: dict = Body(...)):
    if not isinstance(entry, dict) or not entry.get("message") or not entry.get("emoji"):
        return JSONResponse({"error": "Invalid or incomplete entry data"}, status_code=400)

    entry['date'] = datetime.now().strftime("%Y-%m-%d")
    history = load_history()
    if not isinstance(history, list):
        history = []
    history.append(entry)
    save_history(history)
    return JSONResponse({"status": "saved", "entry": entry})

from fastapi import Body
@app.post('/generate')
async def generate_text(data: dict = Body(...)):
    try:
        prompt = data.get('prompt')
        if not prompt:
            return JSONResponse({'error': 'Prompt is missing.'}, status_code=400)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return JSONResponse({'response': response.text})
    except Exception as e:
        print(f"An error occurred: {e}")
        return JSONResponse({'error': 'Failed to generate response from the model.'}, status_code=500)

# ประวัติย้อนหลัง 90 วัน (FastAPI)
from fastapi import Response
@app.get("/history90")
async def history90():
    history = load_history()
    if not isinstance(history, list):
        history = [] # Ensure it's a list if file is corrupted

    today = datetime.now().date()
    ninety_days_ago = today - timedelta(days=89)

    filtered = []
    for entry in history:
        try:
            entry_date = datetime.strptime(entry.get("date", ""), "%Y-%m-%d").date()
            if ninety_days_ago <= entry_date <= today:
                filtered.append(entry)
        except (ValueError, TypeError):
            pass

    if not filtered:
        return JSONResponse({"history90": [], "averageScore": 0, "risk": evaluate_depression_risk(0)})

    total_score = sum(entry.get("emotionScore", 0) for entry in filtered)
    avg_score = total_score / len(filtered) if filtered else 0
    risk = evaluate_depression_risk(avg_score)

    return JSONResponse({
        "history90": filtered,
        "averageScore": avg_score,
        "risk": risk,
    })

# รันแอป (สำหรับ Railway)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)