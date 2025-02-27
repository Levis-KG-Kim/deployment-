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
fig, axes = plt.subplots(1, 3, figsize=(10, 3), constrained_layout=True)

sns.histplot(df_area["mean_ndvi"], bins=20, kde=True, ax=axes[0], color="green")
axes[0].set_title("NDVI Distribution")

sns.histplot(df_area["mean_ndwi"], bins=20, kde=True, ax=axes[1], color="blue")
axes[1].set_title("NDWI Distribution")

sns.histplot(df_area["mean_bsi"], bins=20, kde=True, ax=axes[2], color="red")
axes[2].set_title("BSI Distribution")

st.pyplot(fig)

# Heatmap of Correlations and Boxplot
fig, axes = plt.subplots(1, 2, figsize=(10, 3), constrained_layout=True)

sns.heatmap(df_area[["mean_ndvi", "mean_ndwi", "mean_bsi"]].corr(), annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5, ax=axes[0])
axes[0].set_title("Correlation Heatmap")

sns.boxplot(data=df_area[["mean_ndvi", "mean_ndwi", "mean_bsi"]], palette="Set2", ax=axes[1])
axes[1].set_title("Variability of Biodiversity Indicators")

st.pyplot(fig)

# Classification Visualization for Area Risk Trend and Final Label
st.subheader("Classification of Area Risk Trend and Final Label")
fig, axes = plt.subplots(1, 2, figsize=(10, 3), constrained_layout=True)

sns.histplot(df_area, x="Area_Risk_Trend", bins=10, kde=True, ax=axes[0], color="purple")
axes[0].set_title("Distribution of Area Risk Trend")

sns.histplot(df_area, x="Final_Label", bins=10, kde=True, ax=axes[1], color="orange")

st.pyplot(fig)

with st.expander('About', expanded=True):
        st.write('''
            This project was prepared as a final project by a group of students from Moringa.
            Biodiversity is key to our livelihood and a primary concern to most if not all. There's still more to be done.
            ''')
axes[1].set_title("Distribution of Final Label")


