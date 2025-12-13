import streamlit as st
import pandas as pd
from db import get_recipe, list_recipes, ingredient_map, agg_calories_topn

st.title("🧾 Recipe Details + Nutrition")

# -----------------------------
# Load all recipes for browsing
# -----------------------------
recipes = list_recipes(limit=5000, only_ok=False)

if not recipes:
    st.warning("No recipes found in database.")
    st.stop()

# Build dropdown labels
pairs = []
for r in recipes:
    rid = r.get("_id")
    name = r.get("name")
    if rid:
        label = f"{rid} — {name}" if name else rid
        pairs.append((label, rid))

pairs = sorted(pairs, key=lambda x: x[0].lower())
labels = [""] + [p[0] for p in pairs]
id_by_label = {p[0]: p[1] for p in pairs}

# -----------------------------
# Selector UI
# -----------------------------
st.markdown("### Browse or search for a recipe")

col1 = st.container()

with col1:
    sel = st.selectbox(
        "Select a recipe",
        options=labels,
        help="Browse all recipes",
    )
    rid = id_by_label.get(sel)

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
st.subheader(r.get("name", r["_id"]))
m1, m2, m3, m4 = st.columns(4)
m1.metric("Category", r.get("category", "-"))
m2.metric("Temperature", r.get("temperature", "-"))
m3.metric("Size (ml)", r.get("size_ml", "-"))
m4.metric("Approved", "Yes" if r.get("recipe_ok") else "No")

# -----------------------------
# Composition table
# -----------------------------
imap = ingredient_map()
comp = []
for x in r.get("composition", []):
    iid = x.get("ingredient_id")
    comp.append({
        "ingredient_id": iid,
        "ingredient_name": imap.get(iid, {}).get("name", iid),
        "amount_ml": x.get("amount_ml"),
        "amount_pumps": x.get("amount_pumps"),
        "amount_shots": x.get("amount_shots"),
    })

st.markdown("### Composition")
st.dataframe(pd.DataFrame(comp), use_container_width=True, hide_index=True)

# -----------------------------
# Nutrition
# -----------------------------
st.markdown("### Nutrition (computed from MongoDB aggregation)")
calc = agg_calories_topn(500)
row = next((z for z in calc if z["name"] == r.get("name")), None)

if row:
    a, b, c = st.columns(3)
    a.metric("Calories (kcal)", row["calories_kcal"])
    b.metric("Sugar (g)", row["sugar_g"])
    c.metric("Caffeine (mg)", row["caffeine_mg"])
else:
    st.info("Nutrition row not found (increase top-N).")
