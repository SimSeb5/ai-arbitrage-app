# 🌍 AI Global Arbitrage Finder — MVP (Streamlit)

Public demo that surfaces **price/yield gaps across countries** for products, services, and real estate.

### Deploy to Streamlit Cloud
1) Create a new GitHub repo and upload these files.  
2) Go to https://share.streamlit.io → **New app**  
3) Repo = this repo, Branch = `main`, **Main file = `app.py`**  
4) Deploy → get your public URL.

### Run locally
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### Structure
```
app.py
arbitrage_core.py
requirements.txt
README.md
data/
```

> Data are sample values for demo. Replace CSVs in `data/` with real exports using the same columns.
