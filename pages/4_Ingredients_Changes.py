import streamlit as st
import pandas as pd
from db import list_ingredients, upsert_ingredient, delete_ingredient

st.title("🧪 Ingredients Changes")

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

    # --- Load existing ingredient (dropdown) ---
    df_all = pd.DataFrame(list_ingredients())
    ing_ids = []
    if not df_all.empty and "_id" in df_all.columns:
        ing_ids = sorted(df_all["_id"].dropna().astype(str).tolist())

    if "ing_loaded" not in st.session_state:
        st.session_state["ing_loaded"] = {}

    with st.expander("Load existing ingredient to edit (recommended)"):
        sel_id = st.selectbox("Choose ingredient _id", options=[""] + ing_ids, key="ing_select_id")
        if st.button("Load ingredient"):
            if sel_id:
                rec = next((x for x in list_ingredients() if x.get("_id") == sel_id), None) or {}
                st.session_state["ing_loaded"] = rec

                # Prefill widget state
                st.session_state["ing_id"] = str(rec.get("_id", ""))
                st.session_state["ing_name"] = str(rec.get("name", ""))
                st.session_state["ing_unit"] = str(rec.get("unit", ""))
                st.session_state["ing_unit_ml"] = float(rec.get("unit_ml") or 10.0)

                nutr = rec.get("nutrition_per_unit", {}) if isinstance(rec.get("nutrition_per_unit"), dict) else {}
                st.session_state["ing_calories"] = float(nutr.get("calories") or 0.0)
                st.session_state["ing_protein_g"] = float(nutr.get("protein_g") or 0.0)
                st.session_state["ing_fat_g"] = float(nutr.get("fat_g") or 0.0)
                st.session_state["ing_carbs_g"] = float(nutr.get("carbs_g") or 0.0)
                st.session_state["ing_sugar_g"] = float(nutr.get("sugar_g") or 0.0)
                st.session_state["ing_sodium_mg"] = float(nutr.get("sodium_mg") or 0.0)
                st.session_state["ing_caffeine_mg"] = float(nutr.get("caffeine_mg") or 0.0)

                st.session_state["ing_tags"] = ", ".join([t for t in rec.get("tags", []) if isinstance(t, str)])

                st.success("Loaded ✅ Edit below then click Upsert.")
            else:
                st.warning("Pick an ingredient _id first.")

    loaded = st.session_state.get("ing_loaded", {}) or {}

    # Ensure defaults exist (first run only)
    st.session_state.setdefault("ing_id", str(loaded.get("_id", "")))
    st.session_state.setdefault("ing_name", str(loaded.get("name", "")))
    st.session_state.setdefault("ing_unit", str(loaded.get("unit", "")))
    st.session_state.setdefault("ing_unit_ml", float(loaded.get("unit_ml") or 10.0))

    nutr0 = loaded.get("nutrition_per_unit", {}) if isinstance(loaded.get("nutrition_per_unit"), dict) else {}
    st.session_state.setdefault("ing_calories", float(nutr0.get("calories") or 0.0))
    st.session_state.setdefault("ing_protein_g", float(nutr0.get("protein_g") or 0.0))
    st.session_state.setdefault("ing_fat_g", float(nutr0.get("fat_g") or 0.0))
    st.session_state.setdefault("ing_carbs_g", float(nutr0.get("carbs_g") or 0.0))
    st.session_state.setdefault("ing_sugar_g", float(nutr0.get("sugar_g") or 0.0))
    st.session_state.setdefault("ing_sodium_mg", float(nutr0.get("sodium_mg") or 0.0))
    st.session_state.setdefault("ing_caffeine_mg", float(nutr0.get("caffeine_mg") or 0.0))
    st.session_state.setdefault("ing_tags", ", ".join([t for t in loaded.get("tags", []) if isinstance(t, str)]))

    # --- Form fields (staff friendly) ---
    _id = st.text_input("_id", placeholder="syrup_strawberry", key="ing_id")
    name = st.text_input("name", placeholder="Strawberry syrup", key="ing_name")
    unit = st.text_input("unit", placeholder="pump", key="ing_unit")
    unit_ml = st.number_input("unit_ml", min_value=0.000001, key="ing_unit_ml")

    st.markdown("#### nutrition_per_unit")
    calories = st.number_input("calories", min_value=0.0, key="ing_calories")
    protein_g = st.number_input("protein_g", min_value=0.0, key="ing_protein_g")
    fat_g = st.number_input("fat_g", min_value=0.0, key="ing_fat_g")
    carbs_g = st.number_input("carbs_g", min_value=0.0, key="ing_carbs_g")
    sugar_g = st.number_input("sugar_g", min_value=0.0, key="ing_sugar_g")
    sodium_mg = st.number_input("sodium_mg", min_value=0.0, key="ing_sodium_mg")
    caffeine_mg = st.number_input("caffeine_mg", min_value=0.0, key="ing_caffeine_mg")
    tags = st.text_input("tags (comma)", placeholder="vegan, sweetener", key="ing_tags")

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
                "tags": [t.strip() for t in tags.split(",") if t.strip()],
            }
            upsert_ingredient(doc)
            st.session_state["ing_loaded"] = doc
            st.success("Upserted ✅")
