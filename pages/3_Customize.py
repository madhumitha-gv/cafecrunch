import streamlit as st
from typing import Any, Dict, List, Optional

from db import get_recipe, list_ingredients, list_recipes

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

</style>
"""
st.markdown(THEME_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <h1 class="cc-title">✨ Nutrition What‑If</h1>
    <p class="cc-subtitle">Adjust syrup pumps and espresso shots to see how nutrition changes. These changes are temporary and are <b>not</b> saved.</p>
    <div class="cc-divider"></div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Load recipes for browsing
# -----------------------------
try:
    recipes = list_recipes(limit=5000, only_ok=False)
except TypeError:
    recipes = list_recipes(limit=5000)

if not recipes:
    st.warning("No recipes found in database.")
    st.stop()

pairs = []
for r0 in recipes:
    rid0 = r0.get("_id")
    if not rid0:
        continue
    nm0 = r0.get("name")
    label0 = f"{rid0} — {nm0}" if nm0 else str(rid0)
    pairs.append((label0, str(rid0)))

pairs = sorted(pairs, key=lambda x: x[0].lower())
labels = [""] + [p[0] for p in pairs]
id_by_label = {p[0]: p[1] for p in pairs}

st.markdown("<div class='cc-card'>", unsafe_allow_html=True)
st.markdown("<h3 class='cc-h3'>1) Pick a recipe</h3>", unsafe_allow_html=True)
sel = st.selectbox("Select a recipe", options=labels, key="whatif_recipe_label")
rid = id_by_label.get(sel)
st.markdown("</div>", unsafe_allow_html=True)
st.write("")

if not rid:
    st.info("Select a recipe from the dropdown to continue.")
    st.stop()

# -----------------------------
# Load recipe + ingredients
# -----------------------------
r = get_recipe(rid.strip())
if not r:
    st.error("Recipe not found.")
    st.stop()

ings = list_ingredients()
ing_map: Dict[str, Dict[str, Any]] = {x["_id"]: x for x in ings if x.get("_id")}

def _units_from_comp(comp_item: Dict[str, Any], ing: Dict[str, Any]) -> float:
    """Convert a composition entry into 'units' for nutrition scaling."""
    if not ing:
        return 0.0

    # For ml-based ingredients, scale by unit_ml
    if "amount_ml" in comp_item and comp_item.get("amount_ml") is not None:
        unit_ml = float(ing.get("unit_ml") or 0.0)
        if unit_ml <= 0:
            return 0.0
        return float(comp_item["amount_ml"]) / unit_ml

    # Pumps and shots are already unit counts
    if "amount_pumps" in comp_item and comp_item.get("amount_pumps") is not None:
        return float(comp_item["amount_pumps"])
    if "amount_shots" in comp_item and comp_item.get("amount_shots") is not None:
        return float(comp_item["amount_shots"])

    return 0.0

def _nutrition_totals(recipe_doc: Dict[str, Any]) -> Dict[str, float]:
    """Compute totals from composition + ingredient nutrition_per_unit."""
    totals = {"calories": 0.0, "sugar_g": 0.0, "caffeine_mg": 0.0}
    for comp in recipe_doc.get("composition", []) or []:
        iid = comp.get("ingredient_id")
        ing = ing_map.get(iid, {})
        nutr = ing.get("nutrition_per_unit", {}) if isinstance(ing.get("nutrition_per_unit"), dict) else {}

        units = _units_from_comp(comp, ing)
        if units <= 0:
            continue

        totals["calories"] += float(nutr.get("calories", 0.0)) * units
        totals["sugar_g"] += float(nutr.get("sugar_g", 0.0)) * units
        totals["caffeine_mg"] += float(nutr.get("caffeine_mg", 0.0)) * units

    return totals

def _find_default_syrup_id(recipe_doc: Dict[str, Any]) -> Optional[str]:
    defaults = recipe_doc.get("defaults", {}) if isinstance(recipe_doc.get("defaults"), dict) else {}
    sid = defaults.get("syrup_id")
    return str(sid) if sid else None

def _apply_whatif(recipe_doc: Dict[str, Any], espresso_shots: int, syrup_pumps: int) -> Dict[str, Any]:
    """Return a new recipe doc with updated espresso/syrup amounts in composition only."""
    new_doc = {**recipe_doc}
    new_comp: List[Dict[str, Any]] = []
    for item in recipe_doc.get("composition", []) or []:
        new_comp.append(dict(item))

    # Update espresso shots in composition (ingredient_id == 'espresso_shot' OR any item with amount_shots)
    updated_espresso = False
    for item in new_comp:
        if item.get("ingredient_id") == "espresso_shot" or ("amount_shots" in item and item.get("ingredient_id")):
            # Only treat espresso_shot explicitly; avoid modifying other shot-based ingredients by mistake
            if item.get("ingredient_id") == "espresso_shot":
                item.pop("amount_ml", None)
                item.pop("amount_pumps", None)
                item["amount_shots"] = int(espresso_shots)
                updated_espresso = True

    if not updated_espresso:
        new_comp.append({"ingredient_id": "espresso_shot", "amount_shots": int(espresso_shots)})

    # Update syrup pumps for default syrup id (if present)
    syrup_id = _find_default_syrup_id(recipe_doc)
    if syrup_id:
        updated_syrup = False
        for item in new_comp:
            if item.get("ingredient_id") == syrup_id:
                item.pop("amount_ml", None)
                item.pop("amount_shots", None)
                item["amount_pumps"] = int(syrup_pumps)
                updated_syrup = True
                break
        if not updated_syrup:
            new_comp.append({"ingredient_id": syrup_id, "amount_pumps": int(syrup_pumps)})

    new_doc["composition"] = new_comp
    return new_doc

# -----------------------------
# Baseline + UI
# -----------------------------
st.markdown("<div class='cc-card'>", unsafe_allow_html=True)
st.markdown(f"<h3 class='cc-h3'>{r.get('name', r.get('_id', rid))}</h3>", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
m1.metric("Category", r.get("category", "-"))
m2.metric("Temperature", r.get("temperature", "-"))
m3.metric("Size (ml)", r.get("size_ml", "-"))
st.markdown("</div>", unsafe_allow_html=True)
st.write("")

defaults = r.get("defaults", {}) if isinstance(r.get("defaults"), dict) else {}
base_shots = int(defaults.get("espresso_shots") or 0)
base_pumps = int(defaults.get("syrup_pumps") or 0)
base_syrup_id = _find_default_syrup_id(r)

if not base_syrup_id:
    st.info("This recipe has no default syrup. You can still adjust espresso shots; syrup pumps will have no effect.")

# Keep per-recipe state
state_key = f"whatif::{r.get('_id', rid)}"
st.session_state.setdefault(state_key, {"espresso_shots": base_shots, "syrup_pumps": base_pumps, "show": False})

st.markdown("<div class='cc-card'>", unsafe_allow_html=True)
with st.form(key="whatif_form", clear_on_submit=False):
    st.markdown("<h3 class='cc-h3'>2) Adjust the recipe</h3>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        espresso_shots = st.number_input(
            "Espresso shots",
            min_value=0,
            max_value=10,
            value=int(st.session_state[state_key]["espresso_shots"]),
            step=1,
        )

    with c2:
        syrup_pumps = st.number_input(
            "Syrup pumps",
            min_value=0,
            max_value=20,
            value=int(st.session_state[state_key]["syrup_pumps"]),
            step=1,
            disabled=(base_syrup_id is None),
        )

    b1, b2 = st.columns([1, 1])
    next_clicked = b1.form_submit_button("Next ➜ See updated nutrition")
    reset_clicked = b2.form_submit_button("Reset to recipe defaults")

st.markdown("</div>", unsafe_allow_html=True)
st.write("")

if reset_clicked:
    st.session_state[state_key] = {"espresso_shots": base_shots, "syrup_pumps": base_pumps, "show": False}
    st.rerun()

if next_clicked:
    st.session_state[state_key]["espresso_shots"] = int(espresso_shots)
    st.session_state[state_key]["syrup_pumps"] = int(syrup_pumps)
    st.session_state[state_key]["show"] = True
    st.rerun()

# -----------------------------
# Show nutrition results
# -----------------------------
if not st.session_state[state_key].get("show"):
    st.stop()

st.markdown("<div class='cc-card'>", unsafe_allow_html=True)
st.markdown("<h3 class='cc-h3'>3) Nutrition results</h3>", unsafe_allow_html=True)

baseline_doc = r
updated_doc = _apply_whatif(
    r,
    espresso_shots=int(st.session_state[state_key]["espresso_shots"]),
    syrup_pumps=int(st.session_state[state_key]["syrup_pumps"]),
)

base_tot = _nutrition_totals(baseline_doc)
new_tot = _nutrition_totals(updated_doc)

def _round(x: float) -> float:
    return float(round(x, 1))

delta = {
    "calories": new_tot["calories"] - base_tot["calories"],
    "sugar_g": new_tot["sugar_g"] - base_tot["sugar_g"],
    "caffeine_mg": new_tot["caffeine_mg"] - base_tot["caffeine_mg"],
}

a, b, c = st.columns(3)
a.metric("Calories (kcal)", _round(new_tot["calories"]), delta=f"{_round(delta['calories']):+}")
b.metric("Sugar (g)", _round(new_tot["sugar_g"]), delta=f"{_round(delta['sugar_g']):+}")
c.metric("Caffeine (mg)", _round(new_tot["caffeine_mg"]), delta=f"{_round(delta['caffeine_mg']):+}")

with st.expander("Show baseline vs updated details"):
    st.markdown("**Baseline (recipe defaults)**")
    st.write({
        "espresso_shots": base_shots,
        "syrup_id": base_syrup_id,
        "syrup_pumps": base_pumps,
        "calories": _round(base_tot["calories"]),
        "sugar_g": _round(base_tot["sugar_g"]),
        "caffeine_mg": _round(base_tot["caffeine_mg"]),
    })

    st.markdown("**Updated (your changes)**")
    st.write({
        "espresso_shots": int(st.session_state[state_key]["espresso_shots"]),
        "syrup_id": base_syrup_id,
        "syrup_pumps": int(st.session_state[state_key]["syrup_pumps"]),
        "calories": _round(new_tot["calories"]),
        "sugar_g": _round(new_tot["sugar_g"]),
        "caffeine_mg": _round(new_tot["caffeine_mg"]),
    })
st.markdown("</div>", unsafe_allow_html=True)
