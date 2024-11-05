import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.express as px
import streamlit as st

# Run in command line to run app
# streamlit run sg_dashboard.py

#####################
# Page configuration
st.set_page_config(page_title = "SG Population Dashboard", layout = "wide")

#####################
# Read in data
sg_geojson = gpd.read_file("data/wk11_MasterPlan2019.geojson")
sg_pop = pd.read_csv("data/wk11_sg_pop.csv")

#####################
# Side bar
with st.sidebar:
    # App title
    st.title(":flag-sg: SG Population Dashboard")
    # Year list
    year_list = list(sg_pop["Time"].unique())
    min_year = sg_pop["Time"].min()
    max_year = sg_pop["Time"].max()
    # Select year (slider)
    selected_year = st.slider("Select a year", min_value = min_year, max_value = max_year, value = max_year, step = 1)
    df_selected_year = sg_pop[sg_pop["Time"]== selected_year].copy()

    # Town list
    town_list = list(sg_pop["PA"].unique())
    # Select town (multiple selector)
    selected_towns = st.multiselect("Select up to 5 towns", town_list, default = town_list[0], max_selections = 5)
    df_selected_towns = sg_pop[sg_pop["PA"].isin(selected_towns)].copy()

    # Instructions
    st.sidebar.header("Instructions")
    st.sidebar.markdown('''
            - Choose a year to view the **geographic distribution**.
            - Choose up to five towns to display the **population trends**.
            - The information on top gains/losses will update based on the selected year.
            ''')
    st.sidebar.subheader("About")
    st.sidebar.markdown('''
            - **Data Source:** [Singapore Department of Statistics](<https://www.singstat.gov.sg/>).
            - The figures have been rounded to the nearest 10. 
            ''')

#####################
# Prepare data
sg_selected_year = sg_pop[sg_pop["Time"]== selected_year].copy()

max_row = sg_selected_year.nlargest(1, "change").iloc[0]
min_row = sg_selected_year.nsmallest(1, "change").iloc[0]

total_pop = sg_selected_year["total"].sum()
net_change = sg_selected_year["change"].sum()

#####################
# Prepare plots
# 1. Cholorpleth map
fig = px.choropleth_mapbox(
    sg_pop, geojson = sg_geojson,
    locations = "PA", featureidkey = "properties.town",
    color = "total", color_continuous_scale = "Blues",
    mapbox_style = "carto-positron",
    center = {"lat": 1.35, "lon": 103.82}, zoom = 9.5)
fig.update_layout(coloraxis_showscale = False)

# 2. Line chart with selected towns
fig2 = px.line(
    df_selected_towns, x = "Time", y = "total", color = "PA")
fig2.update_traces(line = dict(width = 5)) 

#####################
# App layout
st.markdown(f"#### Geographic distribution in {selected_year}")
st.plotly_chart(fig)

col1, col2 = st.columns([0.4, 0.6])
# Column 1
with col1:
    # Top changes in selected year
    st.markdown(f"#### Top Gains/Losses in {selected_year}")     
    max_PA = max_row["PA"]
    max_value = max_row["total"]
    max_change = max_row["change"]
    st.metric(label = max_PA, value = max_value, delta = max_change)
    
    min_PA = min_row["PA"]
    min_value = min_row["total"]
    min_change = min_row["change"]
    st.metric(label = min_PA, value = min_value, delta = min_change)
    
    # Total inbound/outbound
    st.metric(label = "TOTAL", value = total_pop, delta = net_change)
    st.write("**Gains/Losses:** Regions with high inbound/ outbound residents for the selected year.") 

# Column 2
with col2:
    st.markdown("#### Population trend in selected towns")
    st.plotly_chart(fig2)      