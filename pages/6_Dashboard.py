import streamlit as st
import pandas as pd
import plotly.express as px

from db import (
    agg_counts_category_temp,
    agg_milk_popularity,
    agg_ingredient_usage_topn,
    agg_calories_topn
)

st.title("📊 Cafe Crunch Dashboard")
st.caption("Visual analytics powered by MongoDB aggregation pipelines.")

# ===============================
# Row 1: Recipe & Milk Analytics
# ===============================
col1, col2 = st.columns(2)

with col1:
    st.subheader("Recipes by Category × Temperature")
    rows = agg_counts_category_temp()

    if rows:
        df = pd.DataFrame([
            {
                "Category": r["_id"]["category"],
                "Temperature": r["_id"]["temperature"],
                "Count": r["count"]
            }
            for r in rows
        ])
        fig = px.bar(
            df,
            x="Category",
            y="Count",
            color="Temperature",
            barmode="group"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No recipe data available.")

with col2:
    st.subheader("Milk Option Popularity")
    rows = agg_milk_popularity()

    if rows:
        df = pd.DataFrame([
            {"Milk ID": r["_id"], "Count": r["count"]}
            for r in rows
        ])
        fig = px.bar(df, x="Milk ID", y="Count")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No milk options found.")

st.divider()

# ===============================
# Row 2: Ingredient & Calories
# ===============================
col3, col4 = st.columns(2)

with col3:
    st.subheader("Top Ingredients Used")
    rows = agg_ingredient_usage_topn(10)

    if rows:
        df = pd.DataFrame([
            {"Ingredient ID": r["_id"], "Usage Count": r["count"]}
            for r in rows
        ])
        fig = px.bar(df, x="Ingredient ID", y="Usage Count")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No ingredient usage data available.")

with col4:
    st.subheader("Top 10 Highest-Calorie Recipes")
    rows = agg_calories_topn(10)

    if rows:
        df = pd.DataFrame(rows)
        fig = px.bar(
            df,
            x="name",
            y="calories_kcal",
            labels={"name": "Recipe", "calories_kcal": "Calories (kcal)"}
        )
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No calorie data available.")
