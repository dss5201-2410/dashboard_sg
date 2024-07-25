import pandas as pd
import numpy as np
import geopandas as gpd
from plotnine import *
import streamlit as st

# Run in command line to run app
# streamlit run wk12_dashboard_sg.py

#####################
# Page configuration
st.set_page_config(page_title = "SG Population Dashboard", layout = "wide")

#####################
# Read in data
sg_pop = pd.read_csv("wk10_sg_pop_01_23.csv")
sg_map = gpd.read_file("wk10_MasterPlan2019.geojson")
df = sg_map.merge(sg_pop, how = "left", left_on = "town", right_on = "PA")

#####################
# Side bar
with st.sidebar:
    # App title
    st.title(":flag-sg: SG Population Dashboard")
    # Year list
    year_list = list(sg_pop["Time"].unique())
    
    # Select year 
    # Slider
    selected_year = st.slider("Select a year", min_value = min(year_list), max_value = max(year_list), value = max(year_list), step = 1)
    df_selected_year = sg_pop[sg_pop["Time"]== selected_year].copy()
    # Dropdown list
    #selected_year = st.selectbox("Select a year", year_list, index = len(year_list)-1)
    
    # Town list
    town_list = list(sg_pop["PA"].unique())
    # Select town
    selected_towns = st.multiselect("Select up to 3 towns", town_list, default = town_list[0], max_selections = 3)
    df_selected_towns = sg_pop[sg_pop["PA"].isin(selected_towns)].copy()

    # Instructions
    st.sidebar.header("Instructions")
    st.sidebar.markdown('''
            - Choose a year to view the **geographic distribution**.
            - Choose up to three towns to display the **population trends**.
            - The information on top gains/losses, most populous, and highest inbound/outbound regions will update based on the selected year.
            ''')
    st.sidebar.subheader("About")
    st.sidebar.markdown('''
            - **Data Source:** [Singapore Department of Statistics](<https://www.singstat.gov.sg/>).
            - The figures have been rounded to the nearest 10. 
            ''')

#####################
# Prepare data
sg_pop_selected = sg_pop[sg_pop["Time"]== selected_year].copy()
df_selected = df[df["Time"]== selected_year].copy()
df_selected_towns["PA"] = pd.Categorical(df_selected_towns["PA"], 
                                         categories = sorted(df_selected_towns["PA"].unique(), reverse = True), ordered = True)

df_total_pop = df.groupby("Time")["total"].sum().reset_index()
df_total_pop.columns = ["Time", "total_population"]
df_total_pop["change"] = df_total_pop["total_population"].diff()
df_total_pop["change"].fillna(0, inplace = True)
    
#####################
# Plots
# 1. Cholorpleth map
p_map = (ggplot(df_selected) +
     geom_map(aes(fill = "total"), color = "white", show_legend = False) +
     scale_fill_gradient(low = "lightblue", high = "steelblue", na_value = "white") +
     labs(title = "", x = "", y = "", fill = "Population") +
     theme_void() +
     theme(plot_title = element_text(ha = "left"))) 

# 2. Heatmap for selected towns
# Remove if total = 0
sg_pop_text = df_selected_towns[df_selected_towns["Time"] == 2010].copy()
p_tile = (ggplot(df_selected_towns, aes(x = "Time", y = "PA")) +
     geom_tile(aes(fill = "total"), show_legend = False) +
     geom_text(sg_pop_text, aes(label = "PA"), show_legend = False) +
     scale_fill_gradient(low = "azure", high = "steelblue", na_value = "white") +
     labs(x = "", y = "", fill = "Population") +
     theme_void())

# 3. Line chart with selected towns highlighted
sg_text_selected = df_selected_towns[df_selected_towns["Time"] == 2023].copy()
#sg_text = df[df["Time"] == 2023].copy()
p_line = (ggplot(df_selected_towns, aes(x = "Time", y = "total")) +
          geom_line(df, aes(group = "PA"), size = 2, color = "lightgray") +
          geom_line(aes(color = "PA"), size = 2, show_legend = False) +
          geom_label(sg_text_selected, aes(x = "Time+1", color = "PA", label = "PA"), ha = "left", show_legend = False) +
          labs(x = "", y = "", color = "",
               title = "Trend in selected towns") +
          scale_x_continuous(breaks = range(min(year_list), 2035, 5))  +
          theme_light() +
          scale_color_brewer(type = "qual", palette = "Set1") +
          xlim(2001, 2030) +
          theme(legend_position = "top",
                plot_title = element_text(ha = "left")))

#####################
# App layout
col = st.columns((2.5, 7, 4.5), gap = "small", vertical_alignment = "top")

# Column 1
with col[0]:
    # Top changes in selected year
    st.markdown("#### Top Gains/Losses")    
    max_row = sg_pop_selected.loc[sg_pop_selected["change"].idxmax()]
    min_row = sg_pop_selected.loc[sg_pop_selected["change"].idxmin()]
    
    max_PA = max_row["PA"]
    min_PA = min_row["PA"]
    max_value = int(max_row["total"])
    min_value = int(min_row["total"])
    max_change = int(max_row["change"])
    min_change = int(min_row["change"])
    
    st.metric(label = max_PA, value = max_value, delta = max_change)
    st.metric(label = min_PA, value = min_value, delta = min_change)
    
    # Total inbound/outbound
    df_total_pop_selected = df_total_pop[df_total_pop["Time"]== selected_year].copy()
    net_change = int(df_total_pop_selected["change"])
    
    total_pop = sg_pop_selected["total"].sum().astype(int)
    
    st.metric(label = "TOTAL", value = total_pop, delta = net_change)
    
    with st.expander("Definition", expanded = False):
        st.write('''
            **Gains/Losses:** Regions with high inbound/ outbound residents for the selected year.
            ''')
           
# Column 2
with col[1]:
    st.markdown(f"#### Geographic distribution in {selected_year}")
    st.pyplot(p_map.draw()) 
       
# Column 3
with col[2]:
    st.markdown("#### Most Populus Regions")  
    top_five_PA = sg_pop_selected.nlargest(3, "total").sort_values(by = "total", ascending = False)
    st.dataframe(top_five_PA,
                 column_order=("PA", "total"),
                 hide_index = True, width = None,
                 column_config = {
                    "PA": st.column_config.TextColumn("Planning Region",),
                    "total": st.column_config.ProgressColumn("Population", format = "%f", min_value = 0, max_value = 110000)})
    
    st.markdown("#### Highest inbounds")  
    top_five_PA = sg_pop_selected.nlargest(3, "change").sort_values(by = "change", ascending = False)
    st.dataframe(top_five_PA,
                 column_order=("PA", "change"),
                 hide_index = True, width = None,
                 column_config = {
                    "PA": st.column_config.TextColumn("Planning Region",),
                    "change": st.column_config.ProgressColumn("Changes", format = "%f", min_value = -3000, max_value = 8000)})
    
    st.markdown("#### Highest outbounds")  
    top_five_PA = sg_pop_selected.nsmallest(3, "change").sort_values(by = "change", ascending = True)
    st.dataframe(top_five_PA,
                 column_order=("PA", "change"),
                 hide_index = True, width = None,
                 column_config = {
                    "PA": st.column_config.TextColumn("Planning Region",),
                    "change": st.column_config.ProgressColumn("Changes", format = "%f", min_value = -3000, max_value = 8000)}) 
    
with st.container():
    st.markdown("#### Trend in selected towns")
    col = st.columns((5, 5), gap = "small", vertical_alignment = "top")
    
    with col[0]:
        st.pyplot(p_tile.draw())
    
    with col[1]:
        st.pyplot(p_line.draw())