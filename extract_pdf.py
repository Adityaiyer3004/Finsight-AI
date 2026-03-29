import pdfplumber
import pandas as pd
import os
import re
from datetime import datetime

# ================================
# CONFIG
# ================================
data_folder = "data"
all_files = [f for f in os.listdir(data_folder) if f.endswith(".pdf")]

rows = []

# 🔥 MERCHANT NORMALIZATION MAP
merchant_map = {
    "tfl": "TFL Travel",
    "ee topup": "EE Topup",
    "deliveroo": "Deliveroo",
    "cardtronics": "ATM Withdrawal",
    "tesco": "Tesco",
    "coop": "CoOp",
    "holland barrett": "Holland Barrett"
}

# ================================
# PROCESS FILES
# ================================
for file in all_files:
    path = os.path.join(data_folder, file)
    print(f"📂 Processing {file}")

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if not text:
                continue

            lines = text.split("\n")

            # ================================
            # STEP 1: RECONSTRUCT LINES
            # ================================
            clean_lines = []
            buffer = ""

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                buffer += " " + line

                if re.search(r"[\d,]+\.\d{2}$", line):
                    clean_lines.append(buffer.strip())
                    buffer = ""

            # ================================
            # STEP 2: PROCESS LINES
            # ================================
            for line in clean_lines:

                # ❌ SKIP NON-TRANSACTIONS
                if any(skip in line.lower() for skip in [
                    "start balance", "end balance",
                    "money in", "money out",
                    "statement", "account", "sort code"
                ]):
                    continue

                # 🔥 EXTRACT AMOUNT
                amounts = re.findall(r"[\d,]+\.\d{2}", line)
                if not amounts:
                    continue

                amount = float(amounts[0].replace(",", ""))

                # 🔥 EXTRACT DATE
                date_match = re.search(r"\b(\d{1,2}\s\w{3})\b", line)
                if not date_match:
                    continue

                date = date_match.group(1)

                # 🔥 CLEAN DESCRIPTION
                description = line.replace(date, "").replace(amounts[0], "")

                # TRANSACTION TYPE
                if any(k in description for k in ["Received", "Giro", "Refund"]):
                    txn_type = "credit"
                else:
                    txn_type = "debit"
                    amount = -amount

                # ================================
                # CLEANING PIPELINE
                # ================================

                # Remove keywords
                description = re.sub(r"Card Purchase|Card Payment|Bill Payment|to", "", description)

                # Remove "On"
                description = re.sub(r"\bOn\b", "", description)

                # Remove dates
                description = re.sub(r"\b\d{1,2}\s\w{3}\b", "", description)

                # ✅ KEEP NUMBERS (FIXES E1)
                description = re.sub(r"[^a-zA-Z0-9\s\*]", "", description)

                # Normalize spaces
                description = re.sub(r"\s+", " ", description).strip()

                # Remove filler words
                words = description.split()
                while words and words[0].lower() in ["to", "from", "the"]:
                    words.pop(0)

                # ✅ KEEP MORE CONTEXT
                description = " ".join(words[:5])

                # ================================
                # MERCHANT NORMALIZATION (FIXED)
                # ================================
                desc_lower = description.lower()

                for key in merchant_map:
                    if key in desc_lower:
                        description = merchant_map[key]
                        break

                # ================================
                # DATE PARSE
                # ================================
                try:
                    full_date = datetime.strptime(date + " 2026", "%d %b %Y")
                except:
                    continue

                # ================================
                # APPEND ROW
                # ================================
                rows.append({
                    "transaction_type": txn_type,
                    "description": description,
                    "transaction_date": full_date,
                    "amount": amount,
                    "source_file": file
                })


# ================================
# FINAL PROCESSING
# ================================
if not rows:
    print("❌ No transactions found")
    exit()

df = pd.DataFrame(rows)

print("\n📄 Preview:")
print(df.head())

print("\n📊 Total transactions:", len(df))

# 🔍 DUPLICATES
dupes = df[df.duplicated(subset=["description", "transaction_date", "amount"], keep=False)]
print("\n⚠️ Potential duplicates:")
print(dupes)

# REMOVE DUPLICATES
df = df.drop_duplicates(subset=[
    "transaction_type",
    "description",
    "transaction_date",
    "amount"
])

# SAVE
df.to_csv("data/clean_transactions.csv", index=False)

print("\n✅ Clean data saved")