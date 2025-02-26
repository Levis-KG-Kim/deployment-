
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
    gdf_selected = gdf[gdf['AreaName'] == selected_area]  # Adjust 'NAME' based on actual column name
    
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

