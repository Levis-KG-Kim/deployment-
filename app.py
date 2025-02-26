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

# Function to Create Map with Area Highlighting
def create_map(selected_area):
    m = folium.Map(location=[-1.286389, 36.817223], zoom_start=6)  # Centered on Kenya

    # Filter shapefile for selected area
    gdf_selected = gdf[gdf[area_column].str.contains(selected_area, na=False, case=False)]

    if gdf_selected.empty:
        st.warning(f"No matching area found in the shapefile for '{selected_area}'.")
        return m

    # Assign Risk Colors
    risk_color_map = {"High": "red", "Medium": "orange", "Low": "green"}
    
    for _, row in gdf_selected.iterrows():
        area_name = row[area_column]
        
        # Retrieve risk level (If available in CSV)
        risk_level = df_selected_year[df_selected_year["Area_Name"] == area_name]["Risk_Factor"].values
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

# Main UI
st.title("Kenyan Areas Visualization")

# Map display
st.subheader(f"Map of {selected_area} in {selected_year}")
folium_static(create_map(selected_area))

# Show area data
st.subheader("Shapefile Data")
st.write(gdf[gdf[area_column] == selected_area])  # Show selected area details

# ======================== Area Risk Trend Visualization ========================

# Filter Data for Selected Area
df_area = df_reshaped[df_reshaped["Area_Name"] == selected_area]

st.subheader(f"Risk Trend for {selected_area}")

# Line Chart for Risk Trends
risk_chart = alt.Chart(df_area).mark_line().encode(
    x="Year:O",
    y="Risk_Factor:Q",
    color=alt.value("red")
).interactive()

st.altair_chart(risk_chart, use_container_width=True)

# ======================== Time-Series Biodiversity Indicators ========================

st.subheader(f"Biodiversity Indicators Trends for {selected_area}")
line_chart = alt.Chart(df_area).transform_fold(
    ["mean_ndvi", "mean_ndwi", "mean_bsi", "Mean_Rainfall_mm"], as_=["Index", "Value"]
).mark_line().encode(
    x="Year:O",
    y="Value:Q",
    color="Index:N"
).interactive()

st.altair_chart(line_chart, use_container_width=True)

# ======================== Data Distribution & Correlations ========================

st.subheader("Distribution of NDVI, NDWI, and BSI")
fig, ax = plt.subplots(1, 3, figsize=(15, 5))

sns.histplot(df_area["mean_ndvi"], bins=20, kde=True, ax=ax[0], color="green")
ax[0].set_title("NDVI Distribution")

sns.histplot(df_area["mean_ndwi"], bins=20, kde=True, ax=ax[1], color="blue")
ax[1].set_title("NDWI Distribution")

sns.histplot(df_area["mean_bsi"], bins=20, kde=True, ax=ax[2], color="red")
ax[2].set_title("BSI Distribution")

st.pyplot(fig)

# Correlation Heatmap
st.subheader("Correlation Heatmap of Biodiversity Indicators")
corr_matrix = df_area[["mean_ndvi", "mean_ndwi", "mean_bsi"]].corr()
fig, ax = plt.subplots(figsize=(6, 4))
sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5, ax=ax)
st.pyplot(fig)

# Boxplot for Variability Analysis
st.subheader("Variability of Biodiversity Indicators")
fig, ax = plt.subplots(figsize=(10, 5))
sns.boxplot(data=df_area[["mean_ndvi", "mean_ndwi", "mean_bsi"]], palette="Set2")
st.pyplot(fig)
