import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import shap
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from joblib import load
import altair as alt
import geopandas as gpd
import folium
from streamlit_folium import folium_static 

# Page configuration
st.set_page_config(
    page_title="Terrestrial Ecosystem Kenya",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for greenish background
st.markdown(
    """
    <style>
        body {
            background-color: #e6f4ea;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Load Data
df_reshaped = pd.read_csv('final_merged.csv')

@st.cache_data
def load_shapefile():
    return gpd.read_file("shapefiles/kbd_with_names.shp")

gdf = load_shapefile()

# Sidebar Filters
with st.sidebar:
    st.title('Kenyan Protected Areas')
    year_list = sorted(df_reshaped.Year.unique(), reverse=True)
    selected_year = st.selectbox('Select a Year', year_list)
    df_selected_year = df_reshaped[df_reshaped.Year == selected_year]
    area_list = sorted(df_selected_year["Area_Name"].dropna().astype(str).unique())
    selected_area = st.selectbox('Select an Area', area_list)

# Function to Create Map
def create_map(selected_area):
    m = folium.Map(location=[-1.286389, 36.817223], zoom_start=6)
    if gdf.crs and gdf.crs != "EPSG:4326":
        gdf.to_crs("EPSG:4326", inplace=True)
    gdf_selected = gdf[gdf['AreaName'] == selected_area] 
    if not gdf_selected.empty:
        folium.GeoJson(
            gdf_selected,
            name="Selected Area",
            style_function=lambda feature: {
                "fillColor": "green",
                "color": "black",
                "weight": 2,
                "fillOpacity": 0.6,
            }
        ).add_to(m)
    return m

# Main UI
st.title("Kenyan Terrestrial Ecosystems Biodiversity Analysis")
st.subheader(f"Map of {selected_area} in {selected_year}")
folium_static(create_map(selected_area))

# Show area data
st.subheader("Shapefile Data")
st.write(gdf[gdf['AreaName'] == selected_area])

# ======================== Adjusted Visualizations ========================

df_area = df_reshaped[df_reshaped["Area_Name"] == selected_area]

# Time-Series Line Chart
st.subheader(f"Time-Series Trends for {selected_area}")
line_chart = alt.Chart(df_area).transform_fold(
    ["mean_dvi", "mean_ndwi", "mean_bsi", "Mean_Rainfall_mm"], as_=["Index", "Value"]
).mark_line().encode(
    x="Year:O",
    y="Value:Q",
    color="Index:N"
).properties(width=600, height=300)

st.altair_chart(line_chart)

# Histogram of Biodiversity Indicators
st.subheader("Distribution of NDVI, NDWI, and BSI")
fig, axes = plt.subplots(1, 3, figsize=(12, 3), constrained_layout=True)

sns.histplot(df_area["mean_ndvi"], bins=20, kde=True, ax=axes[0], color="green")
axes[0].set_title("NDVI Distribution")

sns.histplot(df_area["mean_ndwi"], bins=20, kde=True, ax=axes[1], color="blue")
axes[1].set_title("NDWI Distribution")

sns.histplot(df_area["mean_bsi"], bins=20, kde=True, ax=axes[2], color="red")
axes[2].set_title("BSI Distribution")

st.pyplot(fig)

# Heatmap of Correlations
st.subheader("Correlation Heatmap of Biodiversity Indicators")
fig, ax = plt.subplots(figsize=(4, 2.5))
sns.heatmap(df_area[["mean_ndvi", "mean_ndwi", "mean_bsi"]].corr(), annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5, ax=ax)
st.pyplot(fig)

# Boxplot for Variability Analysis
st.subheader("Variability of Biodiversity Indicators")
fig, ax = plt.subplots(figsize=(6, 3))
sns.boxplot(data=df_area[["mean_ndvi", "mean_ndwi", "mean_bsi"]], palette="Set2", ax=ax)
st.pyplot(fig)

# Classification Visualization for Area Trend and Risk Trend
st.subheader("Classification of Area Trend and Area Risk Trend")
fig, ax = plt.subplots(figsize=(7, 4))
sns.countplot(data=df_area, x="Area_Trend", hue="Area_Risk_Trend", palette="muted", ax=ax)
ax.set_xlabel("Area Trend")
ax.set_ylabel("Count")
ax.set_title("Classification of Areas by Trend and Risk Trend")
st.pyplot(fig)
