import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# Function to calculate CSAT for each entity type
def calculate_csat_by_entity(data):
    csat_summary = {}
    grouped = data.groupby('Entity')
    
    for entity, group in grouped:
        satisfied_customers = group[(group['Rating'] == 4) | (group['Rating'] == 5)]
        csat_score = (len(satisfied_customers) / len(group)) * 100
        total_submissions = len(group)
        csat_summary[entity] = {
            "CSAT": csat_score,
            "Total Submissions": total_submissions
        }
    
    return csat_summary

# Function to filter data by time range
def filter_data(data, time_range):
    if time_range == 'Past Week':
        return data[data['Submitted At'] >= (datetime.now() - pd.to_timedelta(7, unit='d'))]
    elif time_range == 'Past Month':
        return data[data['Submitted At'] >= (datetime.now() - pd.to_timedelta(30, unit='d'))]
    else:  # All-time
        return data

# Function to filter data by date range
def filter_data_by_date_range(data, start_date, end_date):
    return data[(data['Submitted At'] >= start_date) & (data['Submitted At'] <= end_date)]

# Function to calculate CSAT day-by-day with respondent counts
def calculate_daily_csat(data, entity):
    data = data[data['Entity'] == entity]
    data['Date'] = data['Submitted At'].dt.date
    grouped = data.groupby('Date')
    
    daily_csat = grouped.apply(lambda group: (group[(group['Rating'] == 4) | (group['Rating'] == 5)].shape[0] / group.shape[0]) * 100)
    respondent_counts = grouped.size()
    
    return daily_csat, respondent_counts

# Load CSV file
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file is not None:
    # Read the uploaded CSV file
    data = pd.read_csv(uploaded_file)
    
    # Clean up column names by stripping whitespace
    data.columns = data.columns.str.strip()
    
    # Print column names for debugging
    st.write("Column names in the uploaded CSV file:", data.columns.tolist())
    
    # Convert 'Submitted At' column to datetime
    data['Submitted At'] = pd.to_datetime(data['Submitted At'], format='%Y-%m-%d %H:%M:%S')
    
    # Filter by time range
    time_range = st.selectbox('Filter by', ['All Time', 'Past Week', 'Past Month'])
    filtered_data = filter_data(data, time_range)
    
    # Calculate CSAT by entity
    csat_summary = calculate_csat_by_entity(filtered_data)
    
    # Display CSAT summary
    st.write("CSAT Breakdown by Entity:")
    csat_df = pd.DataFrame([
        {"Entity": entity, "CSAT (%)": f"{info['CSAT']:.2f}%", "Total Submissions": f"{info['Total Submissions']}"}
        for entity, info in csat_summary.items()
    ])
    
    st.table(csat_df)
    
    # Section to select Entity, date range and show CSAT day-by-day
    st.write("### CSAT Day-by-Day Analysis")
    
    entity = st.selectbox("Select Entity", data['Entity'].unique())
    start_date = st.date_input("Start Date", value=data['Submitted At'].min().date())
    end_date = st.date_input("End Date", value=data['Submitted At'].max().date())
    
    if start_date and end_date:
        date_filtered_data = filter_data_by_date_range(data, pd.to_datetime(start_date), pd.to_datetime(end_date))
        daily_csat, respondent_counts = calculate_daily_csat(date_filtered_data, entity)
        
        if not daily_csat.empty:
            st.write(f"CSAT Day-by-Day for Entity: {entity}")
            
            # Plotting with Matplotlib
            fig, ax = plt.subplots()
            ax.plot(daily_csat.index, daily_csat.values, marker='o')
            ax.set_xlabel('Date')
            ax.set_ylabel('CSAT (%)')
            ax.set_title(f'Daily CSAT for {entity}')
            
            # Restrict y-axis to range from 60 to 100
            ax.set_ylim([60, 100])
            
            # Rotate x-axis labels
            plt.xticks(rotation=90)
            
            # Draw a horizontal line at CSAT = 80 in light grey
            ax.axhline(y=80, color='lightgrey', linestyle='--')
            
            # Add respondent counts above each data point
            for i, (date, csat) in enumerate(daily_csat.items()):
                respondent_count = respondent_counts[date]
                ax.text(date, csat + 2, f'{respondent_count}', ha='center', va='bottom', fontsize=8, color='blue')
            
            st.pyplot(fig)
            
            # Display data as table
            st.write("CSAT Day-by-Day Data")
            st.table(daily_csat.reset_index(name="CSAT (%)"))
        else:
            st.write("No data available for the selected date range.")
