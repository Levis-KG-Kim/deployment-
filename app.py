
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

# Load Data
df_reshaped = pd.read_csv('final_merged.csv')

@st.cache_data
def load_shapefile():
    return gpd.read_file("shapefiles/kbd_with_names.shp")

gdf = load_shapefile()

# Sidebar Filters
with st.sidebar:
    st.title('Kenyan Protected Areas')

    # Year Selection
    year_list = sorted(df_reshaped.Year.unique(), reverse=True)
    selected_year = st.selectbox('Select a Year', year_list)

    # Filter data for selected year
    df_selected_year = df_reshaped[df_reshaped.Year == selected_year]
    
    # Area Selection
    area_list = sorted(df_selected_year["Area_Name"].dropna().astype(str).unique())
    selected_area = st.selectbox('Select an Area', area_list)

    # Color Theme Selection
    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('Select a Color Theme', color_theme_list)

# Function to Create Map
def create_map(selected_area, selected_color_theme):
    m = folium.Map(location=[-1.286389, 36.817223], zoom_start=6)  # Centered on Kenya

    # Filter shapefile for selected area
    gdf_selected = gdf[gdf['AreaName'] == selected_area]  # Adjust column name
    
    # If the area exists, highlight it
    if not gdf_selected.empty:
        folium.GeoJson(
            gdf_selected,
            name="Selected Area",
            style_function=lambda feature: {
                "fillColor": "blue" if selected_color_theme == "blues" else "green",
                "color": "black",
                "weight": 2,
                "fillOpacity": 0.6,
            }
        ).add_to(m)

    return m

# Main UI
st.title("Kenyan Areas Visualization")

# Map display
st.subheader(f"Map of {selected_area} in {selected_year}")
folium_static(create_map(selected_area, selected_color_theme))

# Show area data
st.subheader("Shapefile Data")
st.write(gdf[gdf['AreaName'] == selected_area])  # Show selected area details

# ======================== New Visualizations ========================

# Filter Data for Selected Area
df_area = df_reshaped[df_reshaped["Area_Name"] == selected_area]

# Time-Series Line Chart
st.subheader(f"Time-Series Trends for {selected_area}")
line_chart = alt.Chart(df_area).transform_fold(
    ["mean_dvi", "mean_ndwi", "mean_bsi","Mean_Rainfall_mm"], as_=["Index", "Value"]
).mark_line().encode(
    x="Year:O",
    y="Value:Q",
    color="Index:N"
).interactive()

st.altair_chart(line_chart, use_container_width=True)

# Histogram of Biodiversity Indicators
st.subheader("Distribution of NDVI, NDWI, and BSI")
fig, ax = plt.subplots(1, 3, figsize=(15, 5))

sns.histplot(df_area["mean_ndvi"], bins=20, kde=True, ax=ax[0], color="green")
ax[0].set_title("NDVI Distribution")

sns.histplot(df_area["mean_ndwi"], bins=20, kde=True, ax=ax[1], color="blue")
ax[1].set_title("NDWI Distribution")

sns.histplot(df_area["mean_bsi"], bins=20, kde=True, ax=ax[2], color="red")
ax[2].set_title("BSI Distribution")

st.pyplot(fig)

# Heatmap of Correlations
st.subheader("Correlation Heatmap of Biodiversity Indicators")
corr_matrix = df_area[["mean_ndvi", "mean_ndwi", "mean_bsi"]].corr()
fig, ax = plt.subplots(figsize=(6, 4))
sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5, ax=ax)
st.pyplot(fig)

# Boxplot for Variability Analysis
st.subheader("Variability of Biodiversity Indicators")
fig, ax = plt.subplots(figsize=(10, 5))
sns.boxplot(data=df_area[["NDVI", "NDWI", "BSI"]], palette="Set2")
st.pyplot(fig)
