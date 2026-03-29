import pandas as pd
import re

# ================================
# LOAD DATA
# ================================
df = pd.read_csv("data/clean_transactions.csv")


# ================================
# NORMALISE TEXT
# ================================
def normalize(text):
    if pd.isna(text):
        return ""
    
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s\*]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


# ================================
# 🔥 MERCHANT MAP (PATCHED)
# ================================
merchant_map = {
    # Bills
    "ee topup": "Bills",

    # Financial services (🔥 NEW FIX)
    "mycrs": "Financial Services",
    "crs": "Financial Services",

    # Cash / ATM
    "cardtronics": "Cash Withdrawal",
    "cash machine": "Cash Withdrawal",
    "atm withdrawal": "Cash Withdrawal",

    # Groceries / local
    "little south ealin": "Groceries",
    "south ealing local": "Groceries",
    "select express": "Groceries",

    # Nightlife
    "bar": "Nightlife",
    "bubblekarao": "Nightlife",
    "livingroom": "Nightlife",
    "the living room": "Nightlife",
    "rhum": "Nightlife",
    "ls beat": "Nightlife",
    "tstb london": "Nightlife",
    "damu": "Nightlife",

    # Transfers
    "ref personal": "Transfers",

    # Food overrides
    "ref friend costa": "Food",
    "costa": "Food",
}


# ================================
# CATEGORY LOGIC
# ================================
def categorize(desc):
    desc = normalize(desc)

    # 🔥 1. MERCHANT OVERRIDE (TOP PRIORITY)
    for key, value in merchant_map.items():
        if key in desc:
            return value

    # 👤 PERSONAL
    if "ronald" in desc:
        return "Rent and Shared Expenses"
    # 🍔 FOOD
    elif any(k in desc for k in [
        "deliveroo", "mcdonald", "greggs",
        "boost", "juice", "coffee", "sweet spot"
    ]):
        return "Food"

    # 🛒 GROCERIES
    elif any(k in desc for k in [
        "tesco", "lidl", "iceland",
        "coop", "holland barrett", "fruit"
    ]):
        return "Groceries"

    # 🛍️ SHOPPING
    elif any(k in desc for k in [
        "tk maxx", "boots", "superdrug",
        "perfume", "klarna", "reiss",
        "dune", "apple"
    ]):
        return "Shopping"

    # 🎉 NIGHTLIFE
    elif any(k in desc for k in [
        "drumsheds", "purple owl",
        "resident advisor", "cloakroom", "e1"
    ]):
        return "Nightlife"

    # 🚇 TRANSPORT
    elif any(k in desc for k in [
        "tfl", "bolt", "uber"
    ]):
        return "Transport"

    # 💸 TRANSFERS
    elif any(k in desc for k in [
        "transfer", "sent", "received", "aditya"
    ]):
        return "Transfers"

    return "Other"


# ================================
# APPLY
# ================================
df["category"] = df["description"].apply(categorize)


# ================================
# DEBUG
# ================================
print("\n📄 Preview:")
print(df.head())

print("\n📊 Category Breakdown:")
print(df["category"].value_counts())

print("\n⚠️ Uncategorized (Other):")
print(df[df["category"] == "Other"]["description"].value_counts().head(10))


# ================================
# SAVE
# ================================
df.to_csv("data/enriched_transactions.csv", index=False)

print("\n✅ Categorisation fixed & saved")