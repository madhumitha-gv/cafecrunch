import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from db import (
    agg_counts_category_temp,
    agg_milk_popularity,
    agg_ingredient_usage_topn,
    agg_calories_topn,
    list_recipes,
    list_ingredients,
    ingredient_map,
)

# =============================================================================
# COFFEE COLOR PALETTE
# =============================================================================
COLORS = {
    "espresso": "#1B0E07",
    "dark_roast": "#3C2415",
    "mocha": "#5D4037",
    "caramel": "#C4873A",
    "latte": "#D4A574",
    "cream": "#F5E6D3",
    "mint": "#4DB6AC",
    "berry": "#E57373",
    "gold": "#FFB300",
    "sage": "#81C784",
    "white": "#FFFFFF",
}

# =============================================================================
# CUSTOM CSS
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Nunito:wght@400;600;700&display=swap');
    
    .stApp { background: linear-gradient(180deg, #FDF8F3 0%, #F5E6D3 100%); }
    
    h1 {
        font-family: 'Playfair Display', serif !important;
        color: #1B0E07 !important;
        text-align: center;
        border-bottom: 3px solid #C4873A;
        padding-bottom: 0.5rem;
    }
    
    h2, h3, h4 {
        font-family: 'Nunito', sans-serif !important;
        color: #3C2415 !important;
    }
    
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #FFFFFF 0%, #F5E6D3 100%);
        border: 2px solid #D4A574;
        border-radius: 12px;
        padding: 0.75rem;
        box-shadow: 0 4px 12px rgba(60, 36, 21, 0.12);
    }
    
    div[data-testid="metric-container"] label {
        font-family: 'Nunito', sans-serif !important;
        color: #5D4037 !important;
        font-size: 0.85rem !important;
    }
    
    hr { border-color: #D4A574 !important; }
    
    .insight-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #FFF8E1 100%);
        border: 2px solid #FFB300;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .healthy-card {
        background: linear-gradient(135deg, #E8F5E9, #C8E6C9);
        border: 1px solid #A5D6A7;
        border-radius: 12px;
        padding: 1rem;
    }
    
    .indulgent-card {
        background: linear-gradient(135deg, #FBE9E7, #FFCCBC);
        border: 1px solid #FFAB91;
        border-radius: 12px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# LOAD ALL DATA
# =============================================================================
@st.cache_data(ttl=300)
def load_all_data():
    recipes = list_recipes(limit=5000, only_ok=False)
    ingredients = list_ingredients(limit=5000)
    nutrition = agg_calories_topn(100)
    return recipes, ingredients, nutrition

try:
    all_recipes, all_ingredients, nutrition_data = load_all_data()
    ing_map = ingredient_map()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# =============================================================================
# HEADER
# =============================================================================
st.title("☕ Cafe Crunch Analytics")

# =============================================================================
# KPIs (calculated, but not displayed)
# =============================================================================
total_recipes = len(all_recipes)
total_ingredients = len(all_ingredients)
core_count = sum(1 for r in all_recipes if r.get("category") == "core")
seasonal_count = sum(1 for r in all_recipes if r.get("category") == "seasonal")
hot_count = sum(1 for r in all_recipes if r.get("temperature") == "hot")
iced_count = sum(1 for r in all_recipes if r.get("temperature") == "iced")
approved_count = sum(1 for r in all_recipes if r.get("recipe_ok"))



# =============================================================================
# NUTRITION SUMMARY KPIs
# =============================================================================
if nutrition_data:
    nutr_df = pd.DataFrame(nutrition_data)
    
    avg_cal = nutr_df["calories_kcal"].mean()
    max_cal = nutr_df["calories_kcal"].max()
    min_cal = nutr_df["calories_kcal"].min()
    avg_sugar = nutr_df["sugar_g"].mean()
    avg_caffeine = nutr_df["caffeine_mg"].mean()
    max_caffeine = nutr_df["caffeine_mg"].max()
    
    # Find specific drinks
    healthiest = nutr_df.loc[nutr_df["calories_kcal"].idxmin()]
    most_indulgent = nutr_df.loc[nutr_df["calories_kcal"].idxmax()]
    most_caffeinated = nutr_df.loc[nutr_df["caffeine_mg"].idxmax()]
    
    st.subheader(" Nutrition Overview")
    
    n1, n2, n3, n4, n5, n6 = st.columns(6)
    n1.metric("Avg Calories", f"{avg_cal:.0f} kcal")
    n2.metric("Calorie Range", f"{min_cal:.0f} - {max_cal:.0f}")
    n3.metric("Avg Sugar", f"{avg_sugar:.1f} g")
    n4.metric("Avg Caffeine", f"{avg_caffeine:.0f} mg")
    n5.metric("Max Caffeine", f"{max_caffeine:.0f} mg")
    n6.metric("Approval Rate", f"{(approved_count/total_recipes)*100:.0f}%")
    
    st.divider()



# =============================================================================
# ROW 2: SEASONAL ANALYSIS
# =============================================================================
st.subheader("🍂 Seasonal Menu Analysis")

# Extract season data
season_counts = {"Winter": 0, "Spring": 0, "Summer": 0, "Fall": 0}
for r in all_recipes:
    seasons = r.get("season", [])
    if seasons:
        for s in seasons:
            season_key = str(s).title()
            if season_key in season_counts:
                season_counts[season_key] += 1

col_s1, col_s2 = st.columns([2, 1])

with col_s1:
    # Seasonal drinks bar chart
    season_df = pd.DataFrame({
        "Season": list(season_counts.keys()),
        "Drinks": list(season_counts.values())
    })
    
    season_colors = {
        "Winter": "#5C6BC0",
        "Spring": "#81C784", 
        "Summer": "#FFB74D",
        "Fall": "#A1887F"
    }
    
    fig = px.bar(
        season_df, x="Season", y="Drinks",
        color="Season",
        color_discrete_map=season_colors,
        text="Drinks"
    )
    fig.update_layout(
        title=dict(text="Seasonal Drink Availability", font=dict(size=16, family="Nunito")),
        height=350,
        margin=dict(t=50, l=20, r=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Nunito"),
        showlegend=False,
        xaxis=dict(title=""),
        yaxis=dict(title="Number of Drinks", showgrid=True, gridcolor="#E0E0E0"),
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

with col_s2:
    # Seasonal insights
    st.markdown("#### Seasonal Insights")
    
    total_seasonal = sum(season_counts.values())
    if total_seasonal > 0:
        peak_season = max(season_counts, key=season_counts.get)
        st.metric("Peak Season", peak_season, f"{season_counts[peak_season]} drinks")
        
        st.markdown(f"""
        <div class="insight-card">
            <p style="margin:0; font-weight:600; color:#F57C00;">💡 Menu Strategy</p>
            <p style="margin:0.5rem 0 0 0; color:#5D4037; font-size:0.9rem;">
                <b>{seasonal_count}</b> seasonal items rotate through the year.<br>
                <b>{core_count}</b> core items available year-round.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No seasonal data available")

st.divider()

# =============================================================================
# ROW 3: INGREDIENT ANALYSIS
# =============================================================================
st.subheader(" Ingredient Analysis")

col_i1, col_i2 = st.columns(2)

with col_i1:
    # Top 10 Ingredients
    rows = agg_ingredient_usage_topn(10)
    if rows:
        df = pd.DataFrame([
            {"Ingredient": str(r["_id"]).replace("_", " ").title(), "Usage": r["count"]}
            for r in rows
        ]).sort_values("Usage", ascending=True)
        
        fig = go.Figure(data=[go.Bar(
            x=df["Usage"], y=df["Ingredient"],
            orientation="h",
            marker=dict(
                color=df["Usage"],
                colorscale=[[0, COLORS["latte"]], [0.5, COLORS["caramel"]], [1, COLORS["dark_roast"]]],
                line=dict(color=COLORS["espresso"], width=1)
            ),
            text=df["Usage"],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Used in %{x} recipes<extra></extra>"
        )])
        
        fig.update_layout(
            title=dict(text="Top 10 Most Used Ingredients", font=dict(size=16, family="Nunito")),
            height=400,
            margin=dict(t=50, l=20, r=60, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Nunito"),
            xaxis=dict(title="Usage Count", showgrid=True, gridcolor="#E0E0E0"),
            yaxis=dict(title=""),
        )
        st.plotly_chart(fig, use_container_width=True)

with col_i2:
    # Milk Popularity
    rows = agg_milk_popularity()
    if rows:
        df = pd.DataFrame([
            {"Milk": str(r["_id"]).replace("milk_", "").replace("_", " ").title(), "Count": r["count"]}
            for r in rows
        ]).sort_values("Count", ascending=True)
        
        fig = go.Figure(data=[go.Bar(
            x=df["Count"], y=df["Milk"],
            orientation="h",
            marker=dict(
                color=df["Count"],
                colorscale=[[0, COLORS["cream"]], [0.5, COLORS["latte"]], [1, COLORS["mocha"]]],
                line=dict(color=COLORS["dark_roast"], width=1)
            ),
            text=df["Count"],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Available in %{x} recipes<extra></extra>"
        )])
        
        fig.update_layout(
            title=dict(text="Milk Options by Availability", font=dict(size=16, family="Nunito")),
            height=400,
            margin=dict(t=50, l=20, r=60, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Nunito"),
            xaxis=dict(title="Available in # Recipes", showgrid=True, gridcolor="#E0E0E0"),
            yaxis=dict(title=""),
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# =============================================================================
# ROW 4: NUTRITION DEEP DIVE
# =============================================================================
st.subheader(" Nutrition Deep Dive")

if nutrition_data:
    nutr_df = pd.DataFrame(nutrition_data)
    
    col_n1, col_n2 = st.columns(2)
    
    with col_n1:
        # Calorie Distribution Histogram
        fig = px.histogram(
            nutr_df, x="calories_kcal",
            nbins=15,
            color_discrete_sequence=[COLORS["caramel"]]
        )
        fig.update_layout(
            title=dict(text="Calorie Distribution Across Menu", font=dict(size=16, family="Nunito")),
            height=350,
            margin=dict(t=50, l=20, r=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Nunito"),
            xaxis=dict(title="Calories (kcal)", showgrid=True, gridcolor="#E0E0E0"),
            yaxis=dict(title="Number of Drinks", showgrid=True, gridcolor="#E0E0E0"),
            bargap=0.1
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_n2:
        # Calories vs Caffeine Scatter
        fig = px.scatter(
            nutr_df, x="caffeine_mg", y="calories_kcal",
            size="sugar_g", color="sugar_g",
            color_continuous_scale=[[0, COLORS["sage"]], [0.5, COLORS["gold"]], [1, COLORS["berry"]]],
            hover_name="name",
            labels={"caffeine_mg": "Caffeine (mg)", "calories_kcal": "Calories (kcal)", "sugar_g": "Sugar (g)"}
        )
        fig.update_layout(
            title=dict(text="Calories vs Caffeine (size = sugar)", font=dict(size=16, family="Nunito")),
            height=350,
            margin=dict(t=50, l=20, r=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Nunito"),
            coloraxis_colorbar=dict(title="Sugar (g)")
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Top 10 Calorie Chart with all metrics
    st.markdown("#### Top 10 Highest Calorie Drinks")
    
    top10 = nutr_df.nlargest(10, "calories_kcal")
    
    col_t1, col_t2 = st.columns([3, 1])
    
    with col_t1:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name="Calories (kcal)", x=top10["name"], y=top10["calories_kcal"],
            marker_color=COLORS["caramel"],
            text=top10["calories_kcal"].round(0).astype(int),
            textposition="outside", textfont=dict(size=9),
        ))
        fig.add_trace(go.Bar(
            name="Sugar (g)", x=top10["name"], y=top10["sugar_g"],
            marker_color=COLORS["latte"],
            text=top10["sugar_g"].round(0).astype(int),
            textposition="outside", textfont=dict(size=9),
        ))
        fig.add_trace(go.Bar(
            name="Caffeine (mg)", x=top10["name"], y=top10["caffeine_mg"],
            marker_color=COLORS["mocha"],
            text=top10["caffeine_mg"].round(0).astype(int),
            textposition="outside", textfont=dict(size=9),
        ))
        
        fig.update_layout(
            barmode="group",
            height=400,
            margin=dict(t=30, l=20, r=20, b=120),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Nunito"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            xaxis=dict(title="", tickangle=-40, showgrid=False),
            yaxis=dict(title="", showgrid=True, gridcolor="#E0E0E0"),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_t2:
        # Healthiest vs Most Indulgent
        st.markdown(f"""
        <div class="healthy-card">
            <p style="margin:0; font-weight:700; color:#2E7D32;">💚 Lightest Choice</p>
            <p style="margin:0.25rem 0 0 0; color:#1B5E20; font-size:0.9rem;">
                {healthiest['name']}<br>
                <b>{healthiest['calories_kcal']:.0f} kcal</b> • {healthiest['sugar_g']:.0f}g sugar
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="indulgent-card" style="margin-top: 1rem;">
            <p style="margin:0; font-weight:700; color:#D84315;">🍫 Most Indulgent</p>
            <p style="margin:0.25rem 0 0 0; color:#BF360C; font-size:0.9rem;">
                {most_indulgent['name']}<br>
                <b>{most_indulgent['calories_kcal']:.0f} kcal</b> • {most_indulgent['sugar_g']:.0f}g sugar
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="insight-card" style="margin-top: 1rem;">
            <p style="margin:0; font-weight:700; color:#F57C00;">⚡ Most Caffeinated</p>
            <p style="margin:0.25rem 0 0 0; color:#E65100; font-size:0.9rem;">
                {most_caffeinated['name']}<br>
                <b>{most_caffeinated['caffeine_mg']:.0f} mg</b> caffeine
            </p>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# =============================================================================
# ROW 5: CATEGORY × TEMPERATURE MATRIX
# =============================================================================
st.subheader("📋 Menu Matrix: Category × Temperature")

rows = agg_counts_category_temp()
if rows:
    matrix_data = {}
    for r in rows:
        cat = str(r["_id"]["category"]).title()
        temp = str(r["_id"]["temperature"]).title()
        matrix_data[(cat, temp)] = r["count"]
    
    # Create heatmap data
    categories = ["Core", "Seasonal"]
    temperatures = ["Hot", "Iced"]
    z_data = [[matrix_data.get((cat, temp), 0) for temp in temperatures] for cat in categories]
    
    col_m1, col_m2 = st.columns([2, 1])
    
    with col_m1:
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=temperatures,
            y=categories,
            colorscale=[[0, COLORS["cream"]], [0.5, COLORS["caramel"]], [1, COLORS["dark_roast"]]],
            text=[[str(v) for v in row] for row in z_data],
            texttemplate="%{text}",
            textfont=dict(size=24, family="Nunito", color="white"),
            hovertemplate="<b>%{y} - %{x}</b><br>Count: %{z}<extra></extra>"
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(t=30, l=20, r=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Nunito", size=14),
            xaxis=dict(title="Temperature", side="bottom"),
            yaxis=dict(title="Category"),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_m2:
        st.markdown("#### 📊 Matrix Insights")
        
        # Find dominant combination
        max_combo = max(matrix_data, key=matrix_data.get)
        max_count = matrix_data[max_combo]
        
        st.metric("Dominant Combo", f"{max_combo[0]} + {max_combo[1]}", f"{max_count} drinks")
        
        # Balance ratio
        hot_total = sum(v for (c, t), v in matrix_data.items() if t == "Hot")
        iced_total = sum(v for (c, t), v in matrix_data.items() if t == "Iced")
        ratio = hot_total / max(iced_total, 1)
        
        st.metric("Hot:Iced Ratio", f"{ratio:.2f}:1")

st.divider()

# =============================================================================
# FOOTER
# =============================================================================
st.markdown(
    f"""
    <div style="text-align:center; padding: 1.5rem; color: #8D6E63; background: rgba(255,255,255,0.5); border-radius: 12px;">
        <p style="margin:0; font-family: Nunito; font-size: 1.1rem;">
            ☕ <b>Cafe Crunch Analytics Dashboard</b>
        </p>
        <p style="margin:0.5rem 0 0 0; font-size: 0.9rem; font-family: Nunito;">
            📋 {total_recipes} Recipes • 🧪 {total_ingredients} Ingredients • 
            🔥 {hot_count} Hot • 🧊 {iced_count} Iced
        </p>
        <p style="margin:0.25rem 0 0 0; font-size: 0.8rem; font-family: Nunito; color: #A1887F;">
            Powered by MongoDB Atlas & Streamlit
        </p>
    </div>
    """,
    unsafe_allow_html=True
)