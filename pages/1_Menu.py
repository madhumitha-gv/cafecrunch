import streamlit as st
import pandas as pd
from db import list_recipes

# ----------------------------
# Page Header
# ----------------------------
st.markdown("""
<div style="background-color:#FFF7ED;padding:1.2rem 1.5rem;border-radius:12px;">
  <h1 style="margin-bottom:0;">📋 Cafe Crunch Menu</h1>
  <p style="color:#6B4F3F;margin-top:0.2rem;">
    Browse available drinks by category, temperature, and size.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr style='border:1px solid #E3C9A8;margin:1.5rem 0;'>", unsafe_allow_html=True)

# ----------------------------
# Sidebar Filters
# ----------------------------
with st.sidebar:
    st.markdown("### 🔎 Filter Menu")
    category = st.selectbox("Category", ["All", "core", "seasonal"])
    temperature = st.selectbox("Temperature", ["All", "hot", "iced"])
    only_ok = st.checkbox("Only approved (recipe_ok)", value=True)
    size_min, size_max = st.slider(
        "Size (ml)",
        200,
        700,
        (300, 600),
        step=10,
    )

# ----------------------------
# Data Fetch
# ----------------------------
rows = list_recipes(
    category if category != "All" else None,
    temperature if temperature != "All" else None,
    (size_min, size_max),
    only_ok=only_ok,
)

df = pd.DataFrame(rows)

# ----------------------------
# Display Results
# ----------------------------
if df.empty:
    st.info("☕ No recipes match your current filters.")
else:
    display_cols = ["_id", "name", "category", "temperature", "size_ml", "recipe_ok"]
    st.dataframe(
        df[display_cols].sort_values(["category", "temperature", "name"]),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "📌 Tip: Copy a recipe **_id** and open **Recipe Details** to view nutrition."
    )
