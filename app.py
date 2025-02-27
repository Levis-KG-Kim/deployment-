import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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

# Ensure CRS is correct
if gdf.crs and gdf.crs != "EPSG:4326":
    gdf.to_crs("EPSG:4326", inplace=True)

# Identify Correct Column Name for Area Filtering
possible_area_columns = [col for col in gdf.columns if "area" in col.lower()]
area_column = possible_area_columns[0] if possible_area_columns else None

if not area_column:
    st.error("No valid area name column found in the shapefile!")
    st.stop()

# Sidebar Filters
with st.sidebar:
    st.title('Kenyan Protected Areas')
    
    # Area Selection
    area_list = sorted(df_selected_year["Area_Name"].dropna().astype(str).unique())
    selected_area = st.selectbox('Select an Area', area_list)

# Function to Create Map with Area Highlighting
def create_map(selected_area, selected_color_theme):
    m = folium.Map(location=[-1.286389, 36.817223], zoom_start=6)  # Centered on Kenya

    # Filter shapefile for selected area
    gdf_selected = gdf[gdf[area_column].str.contains(selected_area, na=False, case=False)]

    if gdf_selected.empty:
        st.warning(f"No matching area found in the shapefile for '{selected_area}'.")
        return m

    # Assign Risk Colors
    risk_color_map = {"Overall Gain": "red", "Overall Stable": "orange", "Overall Loss": "green"}
    
    for _, row in gdf_selected.iterrows():
        area_name = row[area_column]
        
        # Retrieve risk level (If available in CSV)
        risk_level = df_selected_year[df_selected_year["Area_Name"] == area_name]["Area_Trend"].values
        risk_level = risk_level[0] if len(risk_level) > 0 else "Low"
        
        folium.GeoJson(
            row["geometry"],
            name=area_name,
            style_function=lambda feature, risk=risk_level: {
                "fillColor": risk_color_map.get(risk, "blue"),
                "color": "black",
                "weight": 2,
                "fillOpacity": 0.6,
            },
            tooltip=folium.Tooltip(f"{area_name} - Risk: {risk_level}")
        ).add_to(m)

    return m

# ======================== New Dashboard Layout ========================
st.title("🌑 Kenyan Ecosystem Dashboard")

# **Filter Data for Selected Area**
df_area = df_reshaped[df_reshaped["Area_Name"] == selected_area]

# **Grid Layout for Aesthetics**
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("🌍 Geospatial Overview")
    folium_static(create_map(selected_area))

# **Area Risk Trend Now Moved Below the Map**
st.subheader("⚠️ Area Risk Trend")
if "Risk_Factor" in df_area.columns:
    risk_chart = alt.Chart(df_area).mark_line(color="red").encode(
        x="Year:O",
        y="Risk_Factor:Q"
    ).interactive()
    st.altair_chart(risk_chart, use_container_width=True)
else:
    st.warning("Risk data unavailable.")

# **Biodiversity Trends**
st.subheader("📈 Biodiversity Trends")
alt.themes.enable("dark")

trend_chart = alt.Chart(df_area).transform_fold(
    ["mean_ndvi", "mean_ndwi", "mean_bsi", "Mean_Rainfall_mm"], as_=["Index", "Value"]
).mark_line().encode(
    x="Year:O",
    y="Value:Q",
    color="Index:N"
).interactive()

st.altair_chart(trend_chart, use_container_width=True)

# **Distributions & Heatmap**
col3, col4 = st.columns(2)

with col3:
    st.subheader("📊 Indicator Distributions")
    fig, ax = plt.subplots(1, 3, figsize=(15, 5), facecolor="#0e1117")

    sns.histplot(df_area["mean_ndvi"], bins=20, kde=True, ax=ax[0], color="lime")
    ax[0].set_title("NDVI", color="white")
    ax[0].set_facecolor("#0e1117")

    sns.histplot(df_area["mean_ndwi"], bins=20, kde=True, ax=ax[1], color="cyan")
    ax[1].set_title("NDWI", color="white")
    ax[1].set_facecolor("#0e1117")

    sns.histplot(df_area["mean_bsi"], bins=20, kde=True, ax=ax[2], color="red")
    ax[2].set_title("BSI", color="white")
    ax[2].set_facecolor("#0e1117")

    plt.setp(ax, xticks=[], yticks=[])
    st.pyplot(fig)

with col4:
    st.subheader("🔗 Correlation Heatmap")
    fig, ax = plt.subplots(figsize=(6, 4), facecolor="#0e1117")
    sns.heatmap(df_area[["mean_ndvi", "mean_ndwi", "mean_bsi"]].corr(), annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5, ax=ax)
    ax.set_facecolor("#0e1117")
    st.pyplot(fig)

# **Variability Boxplot**
st.subheader("📌 Variability Analysis")
fig, ax = plt.subplots(figsize=(10, 5), facecolor="#0e1117")
sns.boxplot(data=df_area[["mean_ndvi", "mean_ndwi", "mean_bsi"]], palette="coolwarm")
ax.set_facecolor("#0e1117")
st.pyplot(fig)
