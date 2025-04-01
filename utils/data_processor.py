import pandas as pd
import numpy as np

def load_data(uploaded_file):
    """
    Load data from uploaded file (CSV or Excel)
    
    Parameters:
    -----------
    uploaded_file : UploadedFile
        The file uploaded through Streamlit's file uploader
        
    Returns:
    --------
    tuple: (DataFrame, str)
        The loaded DataFrame and the filename
    """
    filename = uploaded_file.name
    
    if filename.endswith('.csv'):
        # Try to intelligently detect the separator
        try:
            data = pd.read_csv(uploaded_file, sep=None, engine='python')
        except:
            # Fallback to comma
            data = pd.read_csv(uploaded_file)
    elif filename.endswith(('.xlsx', '.xls')):
        # Load Excel file
        data = pd.read_excel(uploaded_file)
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")
    
    # Perform basic cleaning
    # Remove completely empty columns
    data = data.dropna(axis=1, how='all')
    
    # Try to convert numeric columns to numeric type
    for col in data.columns:
        try:
            # Only convert if column appears to be numeric but was read as object/string
            if data[col].dtype == 'object':
                data[col] = pd.to_numeric(data[col], errors='coerce')
        except:
            # Keep as is if conversion fails
            pass
    
    return data, filename

def get_column_types(data):
    """
    Categorize columns by data type
    
    Parameters:
    -----------
    data : DataFrame
        The pandas DataFrame to analyze
        
    Returns:
    --------
    dict
        Dictionary with keys 'numeric', 'categorical', 'datetime', 'text'
        containing lists of column names
    """
    column_types = {
        'numeric': [],
        'categorical': [],
        'datetime': [],
        'text': []
    }
    
    for col in data.columns:
        # Check if column is numeric
        if pd.api.types.is_numeric_dtype(data[col]):
            column_types['numeric'].append(col)
        
        # Check if column is datetime
        elif pd.api.types.is_datetime64_dtype(data[col]):
            column_types['datetime'].append(col)
        
        # Check if column is categorical or text
        else:
            # If less than 10 unique values or ratio of unique values to total values < 0.05, 
            # consider it categorical, otherwise consider it text
            unique_count = data[col].nunique()
            if unique_count < 10 or (unique_count / len(data) < 0.05):
                column_types['categorical'].append(col)
            else:
                column_types['text'].append(col)
    
    return column_types

def filter_data(data, filters):
    """
    Filter data based on specified conditions
    
    Parameters:
    -----------
    data : DataFrame
        The pandas DataFrame to filter
    filters : list of dict
        List of filter conditions, each with 'column', 'operator', and 'value'
        
    Returns:
    --------
    DataFrame
        Filtered DataFrame
    """
    filtered_data = data.copy()
    
    for filter_condition in filters:
        column = filter_condition['column']
        operator = filter_condition['operator']
        value = filter_condition['value']
        
        if operator == "equals":
            filtered_data = filtered_data[filtered_data[column] == value]
        elif operator == "not_equals":
            filtered_data = filtered_data[filtered_data[column] != value]
        elif operator == "greater_than":
            filtered_data = filtered_data[filtered_data[column] > value]
        elif operator == "less_than":
            filtered_data = filtered_data[filtered_data[column] < value]
        elif operator == "contains":
            filtered_data = filtered_data[filtered_data[column].astype(str).str.contains(value, na=False)]
            
    return filtered_data
