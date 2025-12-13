import streamlit as st
import pandas as pd
from db import list_recipes

st.title("📋 Menu")

with st.sidebar:
    category = st.selectbox("Category", ["All", "core", "seasonal"])
    temperature = st.selectbox("Temperature", ["All", "hot", "iced"])
    only_ok = st.checkbox("Only approved (recipe_ok)", value=True)
    size_min, size_max = st.slider("Size (ml)", 200, 700, (300, 600), step=10)

rows = list_recipes(category, temperature, (size_min, size_max), only_ok=only_ok)
df = pd.DataFrame(rows)

if df.empty:
    st.info("No recipes match your filters.")
else:
    st.dataframe(df[["_id","name","category","temperature","size_ml","recipe_ok"]], use_container_width=True, hide_index=True)
    st.caption("Copy a recipe _id and open **Recipe Details**.")
