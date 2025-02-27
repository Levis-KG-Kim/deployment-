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
import tensorflow as tf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

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
@st.cache_data
def load_data():
    df = pd.read_csv("/mnt/data/final_merged.csv")
    gdf = gpd.read_file("/mnt/data/kbd_with_names.shp")
    
    # Ensure geometries are valid
    gdf = gdf[gdf.geometry.notnull()]
    
    return df, gdf

df_reshaped, gdf = load_data()

# Load LSTM Model
@st.cache_resource
def load_lstm_model():
    return load_model("/mnt/data/Modeling1_2.h5")

model = load_lstm_model()

# Sidebar Filters
with st.sidebar:
    st.title('Kenyan Protected Areas')
    year_list = sorted(df_reshaped.Year.unique(), reverse=True)
    selected_year = st.selectbox('Select a Year', year_list)
    df_selected_year = df_reshaped[df_reshaped.Year == selected_year]
    area_list = sorted(df_selected_year["Area_Name"].dropna().astype(str).unique())
    selected_area = st.selectbox('Select an Area', area_list)


# Main UI
st.title("Kenyan Terrestrial Ecosystems Biodiversity Analysis")
st.subheader(f"Map of {selected_area} in {selected_year}")

# Add an image to the Streamlit app
st.image("/mnt/data/kenya_biodiversity.jpg", caption="Kenyan Biodiversity", use_column_width=True)

# Show area data
st.subheader("Shapefile Data")
st.write(gdf[gdf['AreaName'] == selected_area])

# Time-Series Forecasting with LSTM
st.subheader("Time-Series Forecasting for Biodiversity Indicators")

def prepare_forecast_data(area_name, df):
    area_df = df[df["Area_Name"] == area_name][["Year", "mean_ndvi"]].copy()
    area_df.sort_values(by="Year", inplace=True)
    scaler = MinMaxScaler()
    area_df["mean_ndvi"] = scaler.fit_transform(area_df[["mean_ndvi"]])
    return area_df, scaler

area_data, scaler = prepare_forecast_data(selected_area, df_reshaped)

def predict_future(data, model, steps=5):
    last_sequence = np.array(data["mean_ndvi"].values[-10:]).reshape(1, 10, 1)
    predictions = []
    for _ in range(steps):
        pred = model.predict(last_sequence)[0][0]
        predictions.append(pred)
        last_sequence = np.append(last_sequence[:, 1:, :], [[[pred]]], axis=1)
    return scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()

future_predictions = predict_future(area_data, model)
future_years = list(range(area_data["Year"].max() + 1, area_data["Year"].max() + 6))

forecast_df = pd.DataFrame({"Year": future_years, "Predicted_NDVI": future_predictions})
st.line_chart(forecast_df.set_index("Year"))
