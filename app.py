import streamlit as st
from db import list_recipes, list_ingredients

# -----------------------------
# Theme (shared look & feel)
# -----------------------------
COLORS = {
    "espresso": "#1B0E07",
    "dark_roast": "#3C2415",
    "mocha": "#5D4037",
    "caramel": "#C4873A",
    "latte": "#D4A574",
    "cream": "#F5E6D3",
    "paper": "#FBF6EE",
    "border": "#D7B98A",
    "sage": "#81C784",
    "berry": "#E57373",
    "gold": "#FFB300",
    "white": "#FFFFFF",
}

THEME_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Nunito:wght@400;600;700&display=swap');

html, body, [class*="css"]  {{
  font-family: 'Nunito', sans-serif;
}}

/* Page background */
.stApp {{
  background: radial-gradient(1200px 800px at 15% 10%, {COLORS['paper']} 0%, {COLORS['cream']} 60%, #F3E0C9 100%);
}}

/* Headings */
.cc-title {{
  font-family: 'Playfair Display', serif;
  color: {COLORS['espresso']};
  letter-spacing: 0.2px;
  margin: 0;
}}
.cc-subtitle {{
  color: {COLORS['mocha']};
  margin-top: 0.35rem;
}}

/* Divider line */
.cc-divider {{
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, {COLORS['border']} 20%, {COLORS['border']} 80%, transparent 100%);
  margin: 0.75rem 0 1.25rem 0;
}}

/* Cards */
.cc-card {{
  background: rgba(255,255,255,0.55);
  border: 1px solid rgba(215,185,138,0.65);
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: 0 8px 24px rgba(27,14,7,0.06);
}}

.cc-kpi-label {{
  color: {COLORS['mocha']};
  font-size: 0.9rem;
  margin-bottom: 6px;
}}
.cc-kpi-value {{
  color: {COLORS['espresso']};
  font-family: 'Playfair Display', serif;
  font-size: 2.0rem;
  margin: 0;
}}

.cc-pill-ok {{
  display: inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(129,199,132,0.18);
  border: 1px solid rgba(129,199,132,0.55);
  color: {COLORS['espresso']};
  font-weight: 700;
}}

.cc-pill-bad {{
  display: inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(229,115,115,0.16);
  border: 1px solid rgba(229,115,115,0.55);
  color: {COLORS['espresso']};
  font-weight: 700;
}}

/* Make Streamlit default metric boxes blend in */
[data-testid="stMetric"] {{
  background: rgba(255,255,255,0.40);
  border: 1px solid rgba(215,185,138,0.55);
  border-radius: 14px;
  padding: 14px 14px;
}}

</style>
"""

st.markdown(THEME_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <h1 class="cc-title">☕ Cafe Crunch</h1>
    <p class="cc-subtitle">Menu • nutrition • customization • dashboards powered by MongoDB Atlas</p>
    <div class="cc-divider"></div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)
st.markdown("<div class='cc-card'>Welcome! Use the sidebar to navigate the app pages below.</div>", unsafe_allow_html=True)
st.write("")
try:
    recipes = list_recipes(limit=5000, only_ok=False)
    ings = list_ingredients(limit=5000)
    core = sum(1 for r in recipes if r.get("category") == "core")
    seasonal = sum(1 for r in recipes if r.get("category") == "seasonal")
    c1.metric("Recipes", len(recipes))
    c2.metric("Ingredients", len(ings))
    c3.metric("Core / Seasonal", f"{core} / {seasonal}")
    st.success("Connected to MongoDB Atlas ✅")
except Exception as e:
    st.error("MongoDB connection failed. Check secrets.toml + Atlas IP allowlist.")
    st.exception(e)

st.markdown("<h3 class='cc-title' style='font-size: 1.5rem;'>🧭 Navigation</h3>", unsafe_allow_html=True)

cols = st.columns(3)
items = [
    ("📋 Menu", "Browse recipes with filters"),
    ("🧾 Recipe Details", "View composition + computed nutrition"),
    ("🛠️ Customize", "Try adjustments and see nutrition impact"),
    ("🧪 Ingredients Admin", "Create / update / delete ingredients"),
    ("🧩 Recipes Admin", "Create / update / delete recipes"),
    ("📊 Dashboard", "Analytics charts from MongoDB aggregations"),
]

for i, (title, desc) in enumerate(items):
    with cols[i % 3]:
        st.markdown(
            f"""
            <div class="cc-card">
              <div class="cc-kpi-label">{title}</div>
              <div style="color:{COLORS['espresso']}; font-weight:600;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
