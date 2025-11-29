import pandas as pd
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestClassifier

BASE = Path(__file__).resolve().parent
DATA = BASE.parent / "dataset" / "sample_transactions.csv"
OUT = BASE / "expense_model.pkl"

df = pd.read_csv(DATA)
df["text"] = (
    df["description"].fillna("") + " " + df["merchant"].fillna("")
).str.lower()

X = df["text"] + " amt_" + df["amount"].astype(str)
y = df["category"]

model = make_pipeline(
    TfidfVectorizer(max_features=1000),
    RandomForestClassifier(n_estimators=100, random_state=42)
)

model.fit(X, y)
joblib.dump(model, OUT)

print("Model trained & saved at:", OUT)
