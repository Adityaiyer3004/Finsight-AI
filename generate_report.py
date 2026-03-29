from dotenv import load_dotenv
load_dotenv()

import os
import json
import pandas as pd
from sqlalchemy import create_engine
from openai import OpenAI
from app.config import DB_CONFIG

# ================================
# INIT
# ================================
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found.")

client = OpenAI(api_key=api_key)

engine = create_engine(
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# ================================
# SAFE PARSER
# ================================
def safe_json_parse(content):
    if not content:
        raise ValueError("❌ Empty response")

    try:
        return json.loads(content)
    except Exception:
        print("\n⚠️ RAW OUTPUT:\n", content)
        raise

# ================================
# VALIDATION
# ================================
def validate_output(report_json):
    if not report_json:
        return False

    summary = report_json.get("summary", "").lower()

    banned = [
        "diverse spending pattern",
        "could be improved",
        "consider budgeting",
        "suggests a need"
    ]

    categories = [c["category"] for c in report_json.get("category_analysis", [])]

    if len(categories) < 5:
        return False

    return not any(p in summary for p in banned)

# ================================
# MAIN FUNCTION
# ================================
def generate_ai_report():

    # ================================
    # FETCH DATA (FROM VIEW)
    # ================================
    df = pd.read_sql("SELECT * FROM category_summary", engine)

    if df.empty:
        raise ValueError("❌ No data found.")

    df = df.sort_values(by="total", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    summary = "\n".join([
        f"- Rank {row['rank']}: {row['category']} — £{row['total']:.2f} ({row['percentage']:.1f}%)"
        for _, row in df.iterrows()
    ])

    # ================================
    # PASS 1 — ANALYSIS
    # ================================
    analysis_prompt = f"""
You are a financial computation engine.

INPUT:
{summary}

STRICT:
- DO NOT rename categories
- USE exact names
- ALL outputs must include numbers (£ or %)

OUTPUT JSON:
{{
  "top_3": ["...", "...", "..."],
  "top_3_pct": "...",
  "food_vs_groceries": {{
    "food": "...",
    "groceries": "...",
    "ratio": "..."
  }},
  "cash_ratio": {{
    "cash": "...",
    "percentage": "..."
  }},
  "discretionary_pct": "...",
  "inefficiencies": ["...", "..."],
  "patterns": ["...", "..."],
  "hidden_risk": "...",
  "categories": [
    {{
      "name": "...",
      "type": "...",
      "comment": "..."
    }}
  ]
}}
"""

    analysis = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": analysis_prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    analysis_data = safe_json_parse(analysis.choices[0].message.content)

    # ================================
    # PASS 2 — REPORT GENERATION
    # ================================
    def generate_report(strict_level=1):

        extra_strict = ""
        if strict_level > 1:
            extra_strict = """
- If output sounds generic → rewrite sharper
- MUST include total spend (£)
- MUST include top 3 combined %
"""

        prompt = f"""
You are a top 1% fintech analyst reviewing a colleague’s work.

DATA:
{summary}

STRUCTURED ANALYSIS:
{json.dumps(analysis_data, indent=2)}

CORE RULES:
- DO NOT rename categories
- MUST include ALL categories
- EVERY sentence MUST include £ or %
- MUST compare categories
- MUST highlight inefficiencies
- MUST include 1 hidden risk
- NO generic phrasing

TONE:
- Be decisive and opinionated

CRITICAL THINKING:
- Include cross-category insight
- Include behavioural conclusion

{extra_strict}

OUTPUT JSON:
{{
  "summary": "...",
  "key_insights": ["...", "...", "..."],
  "category_analysis": [
    {{
      "category": "...",
      "type": "...",
      "insight": "..."
    }}
  ],
  "spending_split": "...",
  "risk_flags": ["...", "..."],
  "recommendations": ["...", "..."],
  "final_verdict": "..."
}}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.15,
            response_format={"type": "json_object"}
        )

        return safe_json_parse(response.choices[0].message.content)

    # ================================
    # RETRY LOOP
    # ================================
    report_json = None

    for attempt in range(3):
        try:
            report_json = generate_report(strict_level=attempt + 1)

            if validate_output(report_json):
                break

        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} failed:", e)

    if not report_json:
        raise ValueError("❌ Failed after retries")

    return report_json
