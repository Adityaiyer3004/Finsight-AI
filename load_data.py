import pandas as pd
from sqlalchemy import create_engine
from app.config import DB_CONFIG

connection_string = (
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

engine = create_engine(connection_string)

# 🔥 Load ENRICHED data (with category)
df = pd.read_csv("data/enriched_transactions.csv")

# 🔥 Push to DB (replace old table)
df.to_sql("transactions", engine, if_exists="replace", index=False)

print("✅ Enriched data inserted into PostgreSQL")