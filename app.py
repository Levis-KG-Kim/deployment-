import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
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
    return gpd.read_file("shapefiles/kbd_with_names.shp")  # Updated path

gdf = load_shapefile()

# Debug: Print shapefile columns
st.write("Shapefile Columns:", gdf.columns)

# Identify Correct Column Name for Area Filtering
possible_area_columns = [col for col in gdf.columns if "area" in col.lower()]
area_column = possible_area_columns[0] if possible_area_columns else None

if not area_column:
    st.error("No valid area name column found in the shapefile!")
    st.stop()

# Debug: Print available areas
st.write("Matching Areas in Shapefile:", gdf[area_column].unique())

# Sidebar Filters
with st.sidebar:
    st.title('Kenyan Protected Areas')
    year_list = sorted(df_reshaped.Year.unique(), reverse=True)
    selected_year = st.selectbox('📅 Select a Year', year_list)
    df_selected_year = df_reshaped[df_reshaped.Year == selected_year]
    area_list = sorted(df_selected_year["Area_Name"].dropna().astype(str).unique())
    selected_area = st.selectbox('Select an Area', area_list)

# Ensure correct coordinate reference system
if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
    gdf = gdf.to_crs("EPSG:4326")

# Extract centroid coordinates for visualization
gdf["lon"] = gdf.geometry.centroid.x
gdf["lat"] = gdf.geometry.centroid.y
gdf = gdf.dropna(subset=["lon", "lat"])

# Create Interactive Map
fig = px.scatter_mapbox(
    gdf, lat="lat", lon="lon", hover_name=area_column,
    color_discrete_sequence=["red"], zoom=5, height=500
)
fig.update_layout(mapbox_style="open-street-map", margin={"r":0, "t":0, "l":0, "b":0})
st.subheader("\U0001F4CD Interactive Map of Protected Areas")
st.plotly_chart(fig, use_container_width=True)

# Function to Create Map with Area Highlighting
def create_map(selected_area):
    m = folium.Map(location=[-1.286389, 36.817223], zoom_start=6, tiles="CartoDB dark_matter")
    if area_column not in gdf.columns:
        st.error("Error: The selected area column is missing in the shapefile!")
        return m
    
    # Case-insensitive, whitespace-trimmed filtering
gdf_selected = gdf[gdf[area_column].astype(str).str.strip().str.lower() == selected_area.strip().lower()]
    
    if gdf_selected.empty:
        st.warning(f"No matching area found in the shapefile for '{selected_area}'.")
        return m
    
    risk_color_map = {"High": "red", "Medium": "orange", "Low": "green"}
    for _, row in gdf_selected.iterrows():
        area_name = row[area_column]
        risk_level = df_selected_year[df_selected_year["Area_Name"].str.strip().str.lower() == area_name.strip().lower()]["Risk_Factor"].values
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

# Display Map with Highlights
st.title("\U0001F311 Kenyan Ecosystem Dashboard")
df_area = df_reshaped[df_reshaped["Area_Name"] == selected_area]
col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("\U0001F30D Geospatial Overview")
    folium_static(create_map(selected_area))
