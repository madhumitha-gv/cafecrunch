import streamlit as st
import pandas as pd
from db import list_ingredients, upsert_ingredient, delete_ingredient

st.title("🧪 Ingredients Admin")

tab1, tab2 = st.tabs(["Browse/Delete", "Add/Update"])

with tab1:
    df = pd.DataFrame(list_ingredients())
    st.dataframe(df[["_id","name","unit","unit_ml"]], use_container_width=True, hide_index=True)
    del_id = st.text_input("Delete ingredient _id", placeholder="e.g., syrup_vanilla")
    if st.button("Delete"):
        if del_id.strip():
            ok = delete_ingredient(del_id.strip())
            st.success("Deleted ✅" if ok else "Not found.")
        else:
            st.warning("Enter an _id first.")

with tab2:
    st.markdown("Upsert = insert new or replace existing.")
    _id = st.text_input("_id", placeholder="syrup_strawberry")
    name = st.text_input("name", placeholder="Strawberry syrup")
    unit = st.text_input("unit", placeholder="pump")
    unit_ml = st.number_input("unit_ml", min_value=0.000001, value=10.0)

    st.markdown("#### nutrition_per_unit")
    calories = st.number_input("calories", min_value=0.0, value=0.0)
    protein_g = st.number_input("protein_g", min_value=0.0, value=0.0)
    fat_g = st.number_input("fat_g", min_value=0.0, value=0.0)
    carbs_g = st.number_input("carbs_g", min_value=0.0, value=0.0)
    sugar_g = st.number_input("sugar_g", min_value=0.0, value=0.0)
    sodium_mg = st.number_input("sodium_mg", min_value=0.0, value=0.0)
    caffeine_mg = st.number_input("caffeine_mg", min_value=0.0, value=0.0)
    tags = st.text_input("tags (comma)", placeholder="vegan, sweetener")

    if st.button("Upsert"):
        if not (_id.strip() and name.strip() and unit.strip()):
            st.warning("Provide _id, name, unit.")
        else:
            doc = {
                "_id": _id.strip(),
                "name": name.strip(),
                "unit": unit.strip(),
                "unit_ml": float(unit_ml),
                "nutrition_per_unit": {
                    "calories": float(calories),
                    "protein_g": float(protein_g),
                    "fat_g": float(fat_g),
                    "carbs_g": float(carbs_g),
                    "sugar_g": float(sugar_g),
                    "sodium_mg": float(sodium_mg),
                    "caffeine_mg": float(caffeine_mg),
                },
                "tags": [t.strip() for t in tags.split(",") if t.strip()]
            }
            upsert_ingredient(doc)
            st.success("Upserted ✅")
