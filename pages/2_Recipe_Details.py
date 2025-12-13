import streamlit as st
import pandas as pd
from db import get_recipe, list_recipes, ingredient_map, agg_calories_topn

# -----------------------------
# Theme (match Dashboard)
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

html, body, [class*="css"] {{
  font-family: 'Nunito', sans-serif;
}}

.stApp {{
  background: radial-gradient(1200px 800px at 15% 10%, {COLORS['paper']} 0%, {COLORS['cream']} 60%, #F3E0C9 100%);
}}

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

.cc-divider {{
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, {COLORS['border']} 20%, {COLORS['border']} 80%, transparent 100%);
  margin: 0.75rem 0 1.25rem 0;
}}

.cc-card {{
  background: rgba(255,255,255,0.55);
  border: 1px solid rgba(215,185,138,0.65);
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: 0 8px 24px rgba(27,14,7,0.06);
}}

.cc-h3 {{
  font-family: 'Playfair Display', serif;
  color: {COLORS['espresso']};
  margin: 0 0 0.25rem 0;
}}

[data-testid="stMetric"] {{
  background: rgba(255,255,255,0.40);
  border: 1px solid rgba(215,185,138,0.55);
  border-radius: 14px;
  padding: 14px 14px;
}}

/* Make dataframes feel like cards */
div[data-testid="stDataFrame"] {{
  background: rgba(255,255,255,0.40);
  border: 1px solid rgba(215,185,138,0.55);
  border-radius: 14px;
  padding: 10px;
}}
</style>
"""

st.markdown(THEME_CSS, unsafe_allow_html=True)

# -----------------------------
# Header
# -----------------------------
st.markdown(
    """
    <h1 class="cc-title">🧾 Recipe Details</h1>
    <p class="cc-subtitle">Pick a drink to view its composition and nutrition.</p>
    <div class="cc-divider"></div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Load all recipes for browsing
# -----------------------------
try:
    recipes = list_recipes(limit=5000, only_ok=False)
except TypeError:
    recipes = list_recipes(limit=5000)

if not recipes:
    st.warning("No recipes found in database.")
    st.stop()

# Build dropdown labels
pairs = []
for r0 in recipes:
    rid0 = r0.get("_id")
    name0 = r0.get("name")
    if rid0:
        label0 = f"{rid0} — {name0}" if name0 else str(rid0)
        pairs.append((label0, str(rid0)))

pairs = sorted(pairs, key=lambda x: x[0].lower())
labels = [""] + [p[0] for p in pairs]
id_by_label = {p[0]: p[1] for p in pairs}

# -----------------------------
# Selector UI
# -----------------------------
st.markdown("<div class='cc-card'>", unsafe_allow_html=True)
sel = st.selectbox(
    "Select a recipe",
    options=labels,
    help="Browse all recipes",
)
rid = id_by_label.get(sel)
st.markdown("</div>", unsafe_allow_html=True)

if not rid:
    st.info("Select a recipe from the dropdown to see details.")
    st.stop()

# -----------------------------
# Load recipe
# -----------------------------
r = get_recipe(rid)
if not r:
    st.error("Recipe not found.")
    st.stop()

# -----------------------------
# Recipe summary
# -----------------------------
st.markdown("<div class='cc-card'>", unsafe_allow_html=True)
st.markdown(f"<h3 class='cc-h3'>{r.get('name', r.get('_id', rid))}</h3>", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Category", r.get("category", "-"))
m2.metric("Temperature", r.get("temperature", "-"))
m3.metric("Size (ml)", r.get("size_ml", "-"))
m4.metric("Approved", "Yes" if r.get("recipe_ok") else "No")
st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# -----------------------------
# Composition table
# -----------------------------
imap = ingredient_map()
comp = []
for x in r.get("composition", []) or []:
    iid = x.get("ingredient_id")
    comp.append(
        {
            "ingredient_id": iid,
            "ingredient_name": imap.get(iid, {}).get("name", iid),
            "amount_ml": x.get("amount_ml"),
            "amount_pumps": x.get("amount_pumps"),
            "amount_shots": x.get("amount_shots"),
        }
    )

st.markdown("<div class='cc-card'>", unsafe_allow_html=True)
st.markdown("<h3 class='cc-h3'>Composition</h3>", unsafe_allow_html=True)
st.dataframe(pd.DataFrame(comp), use_container_width=True, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

st.write("")

# -----------------------------
# Nutrition
# -----------------------------
st.markdown("<div class='cc-card'>", unsafe_allow_html=True)
st.markdown("<h3 class='cc-h3'>Nutrition</h3>", unsafe_allow_html=True)
st.caption("Computed from MongoDB aggregation")

calc = agg_calories_topn(500)
row = next((z for z in calc if z.get("name") == r.get("name")), None)

if row:
    a, b, c = st.columns(3)
    a.metric("Calories (kcal)", row.get("calories_kcal"))
    b.metric("Sugar (g)", row.get("sugar_g"))
    c.metric("Caffeine (mg)", row.get("caffeine_mg"))
else:
    st.info("Nutrition row not found (increase top-N).")

st.markdown("</div>", unsafe_allow_html=True)
