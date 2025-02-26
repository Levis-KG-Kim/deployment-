
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
    page_title="Terrestrial ecosystem Kenya",
    page_icon="🏂",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

# Load data
df_reshaped = pd.read_csv('final_merged.csv')

# Sidebar
with st.sidebar:
    st.title('Terrestrial ecosystems in Protected Areas')

    year_list = list(df_reshaped.Year.unique())[::-1]

    selected_year = st.selectbox('Select a year', year_list)
    df_selected_year = df_reshaped[df_reshaped.Year == selected_year]
    df_selected_year_sorted = df_selected_year.sort_values(by="Area_Name", ascending=False)

    area_list = list(df_selected_year_sorted.Area_Name.unique())

    selected_area = st.selectbox('Select an area', area_list)
    df_selected_area = df_selected_year_sorted[df_selected_year_sorted.Area_Name == selected_area]


    color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    selected_color_theme = st.selectbox('Select a color theme', color_theme_list)


# Load Model
@st.cache_resource
def load_model():
    model = xgb.Booster()
    model.load_model("xgboost_model.json")  # Adjust file path
    return model

# Main Dashboard UI
# Dashboard Main Panel
col = st.columns((1.5, 4.5, 2), gap='medium')

with col[0]:
# Load the shapefile
    @st.cache_data
    def load_shapefile():
        gdf = gpd.read_file("shapefiles/kbd_with_names.shp")
        return gdf

    gdf = load_shapefile()

# Create a Folium map
    def create_map(gdf):
        m = folium.Map(location=[-1.286389, 36.817223], zoom_start=6)  # Centered on Kenya
        folium.GeoJson(gdf, name="Kenyan Areas").add_to(m)
        return m

# Streamlit UI
    st.title("Kenyan Areas Visualization")
    st.sidebar.header("Shapefile Data")

# Show basic details
    st.sidebar.write("Number of Areas:", len(gdf))

# Map display
    st.subheader("Map of Kenyan Areas")
    folium_static(create_map(gdf))

# Show table of areas
    st.subheader("Area Data")
    st.write(gdf)

with col[2]:
    st.markdown('#### Area Map')

with st.expander('About', expanded=True):
    st.write('''
            Time series analysis and forecasting
            ''')
