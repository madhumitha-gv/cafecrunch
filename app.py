import streamlit as st
from db import list_recipes, list_ingredients

st.set_page_config(page_title="Cafe Crunch", page_icon="☕", layout="wide")

st.title("☕ Cafe Crunch")
st.caption("Menu + nutrition + customization + dashboards powered by MongoDB Atlas.")

c1, c2, c3 = st.columns(3)
try:
    recipes = list_recipes(limit=5000, only_ok=False)
    ings = list_ingredients(limit=5000)
    core = sum(1 for r in recipes if r.get("category") == "core")
    seasonal = sum(1 for r in recipes if r.get("category") == "seasonal")
    c1.metric("Recipes", len(recipes))
    c2.metric("Ingredients", len(ings))
    c3.metric("Core / Seasonal", f"{core} / {seasonal}")
    st.success("Connected to MongoDB Atlas ✅")
except Exception as e:
    st.error("MongoDB connection failed. Check secrets.toml + Atlas IP allowlist.")
    st.exception(e)

st.markdown("""
### Pages
- **Menu**: browse recipes with filters  
- **Recipe Details**: composition + computed nutrition  
- **Customize**: update recipe defaults  
- **Ingredients Admin**: CRUD  
- **Dashboard**: charts from MongoDB aggregations
""")

