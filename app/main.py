from fastapi import FastAPI
from generate_report import generate_ai_report

app = FastAPI(
    title="FinSight AI API",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "FinSight API running 🚀"}

@app.post("/generate-report")
def generate_report():
    try:
        report = generate_ai_report()
        return {
            "status": "success",
            "data": report
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }