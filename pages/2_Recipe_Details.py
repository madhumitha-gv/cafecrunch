import streamlit as st
import pandas as pd
from db import get_recipe, ingredient_map, agg_calories_topn

st.title("🧾 Recipe Details + Nutrition")

rid = st.text_input("Recipe _id", placeholder="e.g., mocha_medium")
if not rid:
    st.stop()

r = get_recipe(rid.strip())
if not r:
    st.error("Recipe not found.")
    st.stop()

st.subheader(r.get("name", r["_id"]))
m1, m2, m3, m4 = st.columns(4)
m1.metric("Category", r.get("category", "-"))
m2.metric("Temperature", r.get("temperature", "-"))
m3.metric("Size (ml)", r.get("size_ml", "-"))
m4.metric("Approved", "Yes" if r.get("recipe_ok") else "No")

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
