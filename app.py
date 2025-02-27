import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import altair as alt
import geopandas as gpd
import plotly.express as px

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

# Identify Correct Column Name for Area Filtering
possible_area_columns = [col for col in gdf.columns if "area" in col.lower()]
area_column = possible_area_columns[0] if possible_area_columns else None

if not area_column:
    st.error("No valid area name column found in the shapefile!")
    st.stop()

# Sidebar Filters
with st.sidebar:
    st.title('Kenyan Protected Areas')

    # **Year Selection**
    year_list = sorted(df_reshaped.Year.unique(), reverse=True)
    selected_year = st.selectbox('📅 Select a Year', year_list)

    # **Filter data for selected year**
    df_selected_year = df_reshaped[df_reshaped.Year == selected_year]

    # **Area Selection**
    area_list = sorted(df_selected_year["Area_Name"].dropna().astype(str).unique())
    selected_area = st.selectbox('📍 Select an Area', area_list)

# Check if CRS (Coordinate Reference System) is defined and convert if needed
if gdf.crs is not None and gdf.crs.to_string() != "EPSG:4326":
    gdf = gdf.to_crs("EPSG:4326")

# Extract centroid coordinates for each area
gdf["lon"] = gdf.geometry.centroid.x
gdf["lat"] = gdf.geometry.centroid.y

# Drop rows with missing coordinates (NaN values)
gdf = gdf.dropna(subset=["lon", "lat"])

# Debugging: Display sample data
st.write("Sample Data for Map:", gdf[[area_column, "lon", "lat"]].head())

# Create an Interactive Scatter Map
fig = px.scatter_mapbox(
    gdf, 
    lat="lat", 
    lon="lon", 
    hover_name=area_column,
    color_discrete_sequence=["red"], 
    zoom=5, 
    height=500
)

# Use OpenStreetMap (No API Key Required)
fig.update_layout(
    mapbox_style="open-street-map",
    margin={"r":0, "t":0, "l":0, "b":0}  # Removes extra white space
)

# ======================== New Dashboard Layout ========================
st.title("🌑 Kenyan Ecosystem Dashboard")

# **Display the Interactive Map**
st.subheader("🌍 Interactive Map of Protected Areas")
st.plotly_chart(fig, use_container_width=True)

# **Filter Data for Selected Area**
df_area = df_reshaped[df_reshaped["Area_Name"] == selected_area]

# **Area Risk Trend**
st.subheader("⚠️ Area Risk Trend")
if "Risk_Factor" in df_area.columns:
    risk_chart = alt.Chart(df_area).mark_line(color="red").encode(
        x="Year:O",
        y="Risk_Factor:Q"
    ).interactive()
    st.altair_chart(risk_chart, use_container_width=True)
else:
    st.warning("Risk data unavailable.")

# ---------------------- Biodiversity Trends ----------------------
st.subheader("📈 Biodiversity Trends")
trend_chart = alt.Chart(df_area).transform_fold(
    ["mean_ndvi", "mean_ndwi", "mean_bsi", "Mean_Rainfall_mm"], as_=["Index", "Value"]
).mark_line().encode(
    x="Year:O",
    y="Value:Q",
    color="Index:N"
).interactive()
st.altair_chart(trend_chart, use_container_width=True)

# ---------------------- Distribution Charts ----------------------
col3, col4 = st.columns(2)

with col3:
    st.subheader("📊 Indicator Distributions")
    fig, ax = plt.subplots(1, 3, figsize=(15, 5))

    sns.histplot(df_area["mean_ndvi"], bins=20, kde=True, ax=ax[0], color="green")
    ax[0].set_title("NDVI Distribution")

    sns.histplot(df_area["mean_ndwi"], bins=20, kde=True, ax=ax[1], color="blue")
    ax[1].set_title("NDWI Distribution")

    sns.histplot(df_area["mean_bsi"], bins=20, kde=True, ax=ax[2], color="red")
    ax[2].set_title("BSI Distribution")

    st.pyplot(fig)

with col4:
    st.subheader("🔗 Correlation Heatmap")
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(df_area[["mean_ndvi", "mean_ndwi", "mean_bsi"]].corr(), annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5, ax=ax)
    st.pyplot(fig)

# ---------------------- Variability Boxplot ----------------------
st.subheader("📌 Variability Analysis")
fig, ax = plt.subplots(figsize=(10, 5))
sns.boxplot(data=df_area[["mean_ndvi", "mean_ndwi", "mean_bsi"]], palette="coolwarm")
st.pyplot(fig)
