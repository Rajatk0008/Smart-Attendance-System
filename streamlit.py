import streamlit as st
import pandas as pd
import xlrd
import os

# Function to read the attendance Excel file and return a list of DataFrames for each sheet
def read_attendance_file(file_path):
    workbook = xlrd.open_workbook(file_path, formatting_info=True)
    sheet_names = workbook.sheet_names()
    
    attendance_data = []
    for sheet in sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet)
        attendance_data.append((sheet, df))
    
    return attendance_data

# Streamlit app
st.title("Attendance Records")

# Set the current folder and file path
current_folder = os.getcwd()
attendance_file = os.path.join(current_folder, 'attendence_excel.xls')

# Check if the attendance file exists
if os.path.exists(attendance_file):
    attendance_data = read_attendance_file(attendance_file)
    
    st.sidebar.title("Subjects")
    selected_subject = st.sidebar.selectbox("Select a subject", [sheet for sheet, _ in attendance_data])
    
    for sheet, df in attendance_data:           
        if sheet == selected_subject:
            st.subheader(f"Attendance for {sheet}")
            st.dataframe(df)
else:
    st.error("Attendance file not found!")
