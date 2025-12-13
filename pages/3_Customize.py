import streamlit as st
from db import get_recipe, list_ingredients, update_recipe_defaults

st.title("🛠️ Customize Defaults")

rid = st.text_input("Recipe _id", placeholder="e.g., iced_flavored_latte_medium")
if not rid:
    st.stop()

r = get_recipe(rid.strip())
if not r:
    st.error("Recipe not found.")
    st.stop()

st.subheader(r["name"])
defaults = r.get("defaults", {})
options = r.get("options", {})

ings = list_ingredients()
id2name = {x["_id"]: x["name"] for x in ings}

milk_choices = options.get("milks") or [x["_id"] for x in ings if "milk_" in x["_id"]]
syrup_choices = options.get("syrups") or [x["_id"] for x in ings if ("syrup_" in x["_id"] or "sauce_" in x["_id"])]

c1, c2 = st.columns(2)
with c1:
    milk_id = st.selectbox(
        "Default milk",
        milk_choices,
        index=milk_choices.index(defaults.get("milk_id")) if defaults.get("milk_id") in milk_choices else 0,
        format_func=lambda x: f"{x} — {id2name.get(x, x)}"
    )
    espresso_shots = st.number_input("Espresso shots", 0, 10, int(defaults.get("espresso_shots", 0)))

with c2:
    syrup_id = st.selectbox(
        "Default syrup/sauce",
        ["(none)"] + syrup_choices,
        index=(["(none)"]+syrup_choices).index(defaults.get("syrup_id")) if defaults.get("syrup_id") in syrup_choices else 0,
        format_func=lambda x: x if x=="(none)" else f"{x} — {id2name.get(x, x)}"
    )
    syrup_pumps = st.number_input("Syrup pumps", 0, 20, int(defaults.get("syrup_pumps", 0)))

patch = {"milk_id": milk_id, "espresso_shots": espresso_shots, "syrup_pumps": syrup_pumps}
if syrup_id != "(none)":
    patch["syrup_id"] = syrup_id

if st.button("Save"):
    changed = update_recipe_defaults(r["_id"], patch)
    st.success("Updated ✅" if changed else "No changes.")
