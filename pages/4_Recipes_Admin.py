from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from db import list_recipes, get_recipe, upsert_recipe, delete_recipe, list_ingredients

st.title("📋 Recipes Admin")

# Mirror Ingredients Admin layout
# Tab 1: Browse/Delete
# Tab 2: Add/Update (Upsert)

tab1, tab2 = st.tabs(["Browse/Delete", "Add/Update"])


# ----------------------------
# Helpers
# ----------------------------

def _as_list(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x) for x in val]
    return [str(val)]


def _idx(options: List[str], value: Optional[str], default: int = 0) -> int:
    return options.index(value) if value in options else default


def _init_comp_state(existing: Optional[List[Dict[str, Any]]] = None) -> None:
    if "recipe_comp" not in st.session_state:
        st.session_state["recipe_comp"] = []
    if existing is not None:
        st.session_state["recipe_comp"] = [dict(x) for x in existing]


def _add_comp_row() -> None:
    st.session_state.setdefault("recipe_comp", [])
    st.session_state["recipe_comp"].append({"ingredient_id": "", "amount_type": "ml", "amount": 0.0})


def _remove_comp_row(i: int) -> None:
    st.session_state.setdefault("recipe_comp", [])
    if 0 <= i < len(st.session_state["recipe_comp"]):
        st.session_state["recipe_comp"].pop(i)


# Pull ingredients once for dropdowns
ings = list_ingredients(limit=5000)
ing_ids = sorted([d.get("_id") for d in ings if d.get("_id")])

milk_ids = [i for i in ing_ids if str(i).startswith("milk_")]
syrup_ids = [i for i in ing_ids if str(i).startswith("syrup_")]
sauce_ids = [i for i in ing_ids if str(i).startswith("sauce_")]


# ----------------------------
# Tab 1: Browse / Delete
# ----------------------------

with tab1:
    st.subheader("Browse")

    c1, c2, c3 = st.columns(3)
    with c1:
        category = st.selectbox("Category", ["All", "core", "seasonal"], index=0)
    with c2:
        temperature = st.selectbox("Temperature", ["All", "hot", "iced"], index=0)
    with c3:
        only_ok = st.checkbox("Only approved (recipe_ok)", value=True)

    cat_f = None if category == "All" else category
    temp_f = None if temperature == "All" else temperature

    df = pd.DataFrame(list_recipes(limit=5000, category=cat_f, temperature=temp_f, only_ok=only_ok))

    if df.empty:
        st.info("No recipes found for the current filters.")
    else:
        cols = [c for c in ["_id", "name", "category", "temperature", "size_ml", "recipe_ok"] if c in df.columns]
        st.dataframe(
            df[cols].sort_values(["category", "temperature", "name"], na_position="last"),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")
    st.subheader("Delete")

    del_id = st.text_input("Delete recipe _id", placeholder="e.g., iced_latte_small")
    if st.button("Delete recipe"):
        if del_id.strip():
            ok = delete_recipe(del_id.strip())
            st.success("Deleted ✅" if ok else "Not found.")
        else:
            st.warning("Enter an _id first.")


# ----------------------------
# Tab 2: Add / Update (Upsert)
# ----------------------------

with tab2:
    st.markdown("Upsert = insert new or replace existing.")

    # Persist loaded recipe across reruns
    if "recipe_loaded" not in st.session_state:
        st.session_state["recipe_loaded"] = {}

    # Prefill from existing recipe
    with st.expander("Load existing recipe to edit (recommended)"):
        lookup_id = st.text_input("Load by _id", placeholder="e.g., iced_latte_small", key="recipes_lookup_id")
        load_btn = st.button("Load", key="recipes_load_btn")

    if load_btn and lookup_id.strip():
        rec = get_recipe(lookup_id.strip()) or {}
        if not rec:
            st.warning("Recipe not found.")
        else:
            st.session_state["recipe_loaded"] = rec
            st.success("Loaded ✅ Edit below then click Upsert recipe.")

            # Prefill widget state so values don't reset on rerun
            st.session_state["recipe_id"] = str(rec.get("_id", ""))
            st.session_state["recipe_name"] = str(rec.get("name", ""))
            st.session_state["recipe_category"] = rec.get("category", "core")
            st.session_state["recipe_temperature"] = rec.get("temperature", "hot")
            st.session_state["recipe_ok"] = bool(rec.get("recipe_ok", True))
            st.session_state["recipe_size_ml"] = int(rec.get("size_ml") or 355)
            st.session_state["recipe_season"] = [s for s in _as_list(rec.get("season"))]

            defaults = rec.get("defaults", {}) if isinstance(rec.get("defaults"), dict) else {}
            st.session_state["default_milk"] = defaults.get("milk_id", "")
            st.session_state["default_syrup"] = defaults.get("syrup_id", "")
            st.session_state["default_sauce"] = defaults.get("sauce_id", "")
            st.session_state["espresso_shots"] = int(defaults.get("espresso_shots") or 0)
            st.session_state["syrup_pumps"] = int(defaults.get("syrup_pumps") or 0)
            st.session_state["sauce_pumps"] = int(defaults.get("sauce_pumps") or 0)
            st.session_state["ice_pct"] = float(defaults.get("ice_pct") or 0.0)

            opts = rec.get("options", {}) if isinstance(rec.get("options"), dict) else {}
            st.session_state["opt_milks"] = [m for m in _as_list(opts.get("milks"))]
            st.session_state["opt_syrups"] = [s for s in _as_list(opts.get("syrups"))]
            st.session_state["opt_sauces"] = [s for s in _as_list(opts.get("sauces"))]

            _init_comp_state(existing=rec.get("composition", []))

    loaded: Dict[str, Any] = st.session_state.get("recipe_loaded", {}) or {}

    _init_comp_state(existing=None)

    # Basic fields (use keys so Streamlit preserves values)
    _id = st.text_input("_id", key="recipe_id", placeholder="iced_latte_small")
    name = st.text_input("name", key="recipe_name", placeholder="Iced Latte (Small)")

    c1, c2, c3 = st.columns(3)
    with c1:
        category = st.selectbox(
            "category",
            ["core", "seasonal"],
            key="recipe_category",
            index=_idx(["core", "seasonal"], st.session_state.get("recipe_category", loaded.get("category", "core")), 0),
        )
    with c2:
        temperature = st.selectbox(
            "temperature",
            ["hot", "iced"],
            key="recipe_temperature",
            index=_idx(["hot", "iced"], st.session_state.get("recipe_temperature", loaded.get("temperature", "hot")), 0),
        )
    with c3:
        recipe_ok = st.checkbox("recipe_ok", key="recipe_ok")

    size_ml = st.number_input("size_ml", min_value=1, step=1, key="recipe_size_ml")

    # Season
    season_options = ["fall", "winter", "spring", "summer"]
    selected_seasons = st.multiselect(
        "season (for seasonal recipes)",
        options=season_options,
        key="recipe_season",
    )

    st.markdown("---")
    st.markdown("### Defaults")

    defaults = loaded.get("defaults", {}) if isinstance(loaded.get("defaults"), dict) else {}

    # Ensure default keys exist (first run only)
    st.session_state.setdefault("default_milk", defaults.get("milk_id", ""))
    st.session_state.setdefault("default_syrup", defaults.get("syrup_id", ""))
    st.session_state.setdefault("default_sauce", defaults.get("sauce_id", ""))
    st.session_state.setdefault("espresso_shots", int(defaults.get("espresso_shots") or 0))
    st.session_state.setdefault("syrup_pumps", int(defaults.get("syrup_pumps") or 0))
    st.session_state.setdefault("sauce_pumps", int(defaults.get("sauce_pumps") or 0))
    st.session_state.setdefault("ice_pct", float(defaults.get("ice_pct") or 0.0))

    d1, d2 = st.columns(2)
    with d1:
        default_milk = st.selectbox(
            "default milk",
            options=[""] + milk_ids,
            key="default_milk",
        )
        default_syrup = st.selectbox(
            "default syrup",
            options=[""] + syrup_ids,
            key="default_syrup",
        )
        default_sauce = st.selectbox(
            "default sauce",
            options=[""] + sauce_ids,
            key="default_sauce",
        )

    with d2:
        espresso_shots = st.number_input(
            "espresso_shots",
            min_value=0,
            step=1,
            key="espresso_shots",
        )
        syrup_pumps = st.number_input(
            "syrup_pumps",
            min_value=0,
            step=1,
            key="syrup_pumps",
        )
        sauce_pumps = st.number_input(
            "sauce_pumps",
            min_value=0,
            step=1,
            key="sauce_pumps",
        )

    ice_pct = st.slider(
        "ice_pct (iced only)",
        min_value=0.0,
        max_value=1.0,
        step=0.05,
        key="ice_pct",
    )

    st.markdown("---")
    st.markdown("### Composition")

    if not st.session_state["recipe_comp"]:
        if temperature == "iced":
            st.session_state["recipe_comp"] = [
                {"ingredient_id": "ice", "amount_type": "ml", "amount": 0.0},
                {"ingredient_id": "espresso_shot", "amount_type": "shots", "amount": 0.0},
            ]
        else:
            st.session_state["recipe_comp"] = [
                {"ingredient_id": "espresso_shot", "amount_type": "shots", "amount": 0.0},
            ]

    add_col, _ = st.columns([1, 4])
    with add_col:
        if st.button("+ Add ingredient row"):
            _add_comp_row()

    for i, row in enumerate(list(st.session_state["recipe_comp"])):
        c_ing, c_type, c_amt, c_rm = st.columns([3, 2, 2, 1])

        current_ing = str(row.get("ingredient_id") or "")
        ing_choice = c_ing.selectbox(
            f"ingredient_{i}",
            options=[""] + ing_ids,
            index=_idx([""] + ing_ids, current_ing, default=0),
            label_visibility="collapsed",
        )

        amount_type = str(row.get("amount_type") or "ml")
        type_choice = c_type.selectbox(
            f"type_{i}",
            options=["ml", "pumps", "shots"],
            index=_idx(["ml", "pumps", "shots"], amount_type, default=0),
            label_visibility="collapsed",
        )

        amount_val = float(row.get("amount") or 0.0)
        amount = c_amt.number_input(
            f"amount_{i}",
            min_value=0.0,
            value=float(amount_val),
            step=1.0,
            label_visibility="collapsed",
        )

        if c_rm.button("✕", key=f"rm_{i}"):
            _remove_comp_row(i)
            st.rerun()

        st.session_state["recipe_comp"][i] = {
            "ingredient_id": ing_choice,
            "amount_type": type_choice,
            "amount": float(amount),
        }

    st.markdown("---")
    st.markdown("### Options")

    loaded_options = loaded.get("options", {}) if isinstance(loaded.get("options"), dict) else {}

    st.session_state.setdefault("opt_milks", [m for m in _as_list(loaded_options.get("milks"))])
    st.session_state.setdefault("opt_syrups", [s for s in _as_list(loaded_options.get("syrups"))])
    st.session_state.setdefault("opt_sauces", [s for s in _as_list(loaded_options.get("sauces"))])

    opt_milks = st.multiselect(
        "allowed milks",
        options=milk_ids,
        key="opt_milks",
    )

    opt_syrups = st.multiselect(
        "allowed syrups",
        options=syrup_ids,
        key="opt_syrups",
    )

    opt_sauces = st.multiselect(
        "allowed sauces",
        options=sauce_ids,
        key="opt_sauces",
    )

    st.markdown("---")

    if st.button("Upsert recipe"):
        if not (_id.strip() and name.strip()):
            st.warning("Provide _id and name.")
        else:
            # Build defaults doc
            defaults_doc: Dict[str, Any] = {"espresso_shots": int(espresso_shots)}

            if default_milk:
                defaults_doc["milk_id"] = default_milk

            if default_syrup:
                defaults_doc["syrup_id"] = default_syrup
                defaults_doc["syrup_pumps"] = int(syrup_pumps)
            elif int(syrup_pumps) > 0:
                defaults_doc["syrup_pumps"] = int(syrup_pumps)

            if default_sauce:
                defaults_doc["sauce_id"] = default_sauce
                defaults_doc["sauce_pumps"] = int(sauce_pumps)
            elif int(sauce_pumps) > 0:
                defaults_doc["sauce_pumps"] = int(sauce_pumps)

            if temperature == "iced" and float(ice_pct) > 0:
                defaults_doc["ice_pct"] = float(ice_pct)

            # Build composition in DB format
            comp_out: List[Dict[str, Any]] = []
            for r in st.session_state.get("recipe_comp", []):
                iid = str(r.get("ingredient_id") or "").strip()
                if not iid:
                    continue
                amt = float(r.get("amount") or 0.0)
                if amt <= 0:
                    continue

                amt_type = str(r.get("amount_type") or "ml")
                item: Dict[str, Any] = {"ingredient_id": iid}
                if amt_type == "ml":
                    item["amount_ml"] = int(round(amt))
                elif amt_type == "pumps":
                    item["amount_pumps"] = int(round(amt))
                else:
                    item["amount_shots"] = int(round(amt))

                comp_out.append(item)

            # Build options
            options_doc: Dict[str, Any] = {}
            if opt_milks:
                options_doc["milks"] = opt_milks
            if opt_syrups:
                options_doc["syrups"] = opt_syrups
            if opt_sauces:
                options_doc["sauces"] = opt_sauces

            doc: Dict[str, Any] = {
                "_id": _id.strip(),
                "name": name.strip(),
                "category": category,
                "temperature": temperature,
                "size_ml": int(size_ml),
                "recipe_ok": bool(recipe_ok),
                "defaults": defaults_doc,
                "composition": comp_out,
            }

            if category == "seasonal" and selected_seasons:
                doc["season"] = selected_seasons

            if options_doc:
                doc["options"] = options_doc

            try:
                upsert_recipe(doc)
                st.success("Upserted ✅")
            except Exception as e:
                st.error(f"Upsert failed: {e}")
