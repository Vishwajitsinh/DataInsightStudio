import pandas as pd
import numpy as np
from scipy import stats

def generate_descriptive_stats(data):
    """
    Generate descriptive statistics for numeric columns
    
    Parameters:
    -----------
    data : DataFrame
        The pandas DataFrame to analyze
        
    Returns:
    --------
    DataFrame
        DataFrame containing descriptive statistics for each numeric column
    """
    # Get basic statistics
    desc_stats = data.describe(include='all').transpose()
    
    # Add additional statistics for numeric columns
    numeric_cols = data.select_dtypes(include=np.number).columns
    
    if not numeric_cols.empty:
        # Calculate skewness and kurtosis for numeric columns
        skewness = data[numeric_cols].skew()
        kurtosis = data[numeric_cols].kurtosis()
        
        # Add to descriptive statistics for numeric columns
        for col in numeric_cols:
            desc_stats.loc[col, 'skewness'] = skewness[col]
            desc_stats.loc[col, 'kurtosis'] = kurtosis[col]
            desc_stats.loc[col, 'range'] = desc_stats.loc[col, 'max'] - desc_stats.loc[col, 'min']
            desc_stats.loc[col, 'variance'] = data[col].var()
            desc_stats.loc[col, 'missing'] = data[col].isna().sum()
            desc_stats.loc[col, 'missing_pct'] = (data[col].isna().sum() / len(data)) * 100
    
    # Add statistics for categorical columns
    cat_cols = data.select_dtypes(exclude=np.number).columns
    
    if not cat_cols.empty:
        for col in cat_cols:
            desc_stats.loc[col, 'unique_values'] = data[col].nunique()
            desc_stats.loc[col, 'missing'] = data[col].isna().sum()
            desc_stats.loc[col, 'missing_pct'] = (data[col].isna().sum() / len(data)) * 100
            desc_stats.loc[col, 'most_common'] = data[col].value_counts().index[0] if not data[col].value_counts().empty else None
            desc_stats.loc[col, 'most_common_pct'] = (data[col].value_counts().iloc[0] / len(data)) * 100 if not data[col].value_counts().empty else None
    
    return desc_stats

def generate_correlation_matrix(data, numeric_columns):
    """
    Generate correlation matrix for numeric columns
    
    Parameters:
    -----------
    data : DataFrame
        The pandas DataFrame to analyze
    numeric_columns : list
        List of numeric column names
        
    Returns:
    --------
    DataFrame
        Correlation matrix
    """
    if len(numeric_columns) < 2:
        return pd.DataFrame({"message": ["Need at least 2 numeric columns for correlation analysis"]})
    
    # Calculate correlation matrix
    correlation_matrix = data[numeric_columns].corr()
    
    # Round to 3 decimal places for readability
    correlation_matrix = correlation_matrix.round(3)
    
    return correlation_matrix

def analyze_distributions(data, numeric_columns):
    """
    Analyze the distributions of numeric columns
    
    Parameters:
    -----------
    data : DataFrame
        The pandas DataFrame to analyze
    numeric_columns : list
        List of numeric column names
        
    Returns:
    --------
    DataFrame
        DataFrame with distribution analysis results
    """
    distribution_results = pd.DataFrame(index=numeric_columns)
    
    for col in numeric_columns:
        # Skip columns with all NaN values
        if data[col].isna().all():
            continue
            
        # Check for normality using Shapiro-Wilk test
        # Take a sample if there are too many observations (Shapiro-Wilk is reliable for n < 5000)
        sample = data[col].dropna()
        if len(sample) > 5000:
            sample = sample.sample(5000, random_state=42)
        
        # Only run test if we have non-NaN values
        if len(sample) > 3:  # Minimum required for Shapiro-Wilk test
            try:
                shapiro_stat, shapiro_p = stats.shapiro(sample)
                distribution_results.loc[col, 'shapiro_p_value'] = shapiro_p
                distribution_results.loc[col, 'normal_distribution'] = "Yes" if shapiro_p > 0.05 else "No"
            except:
                distribution_results.loc[col, 'shapiro_p_value'] = None
                distribution_results.loc[col, 'normal_distribution'] = "Test failed"
        else:
            distribution_results.loc[col, 'shapiro_p_value'] = None
            distribution_results.loc[col, 'normal_distribution'] = "Insufficient data"
        
        # Calculate basic distribution metrics
        distribution_results.loc[col, 'skewness'] = data[col].skew()
        distribution_results.loc[col, 'kurtosis'] = data[col].kurtosis()
        
        # Interpret skewness
        skewness = data[col].skew()
        if -0.5 < skewness < 0.5:
            skew_interpretation = "Approximately symmetric"
        elif -1 < skewness <= -0.5 or 0.5 <= skewness < 1:
            skew_interpretation = "Moderately skewed"
        else:
            skew_interpretation = "Highly skewed"
        distribution_results.loc[col, 'skewness_interpretation'] = skew_interpretation
        
        # Check for outliers (using IQR method)
        Q1 = data[col].quantile(0.25)
        Q3 = data[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = data[(data[col] < lower_bound) | (data[col] > upper_bound)][col]
        distribution_results.loc[col, 'outliers_count'] = len(outliers)
        distribution_results.loc[col, 'outliers_percentage'] = (len(outliers) / data[col].count()) * 100
    
    return distribution_results

def calculate_statistics_by_group(data, numeric_column, group_column):
    """
    Calculate statistics for a numeric column grouped by a categorical column
    
    Parameters:
    -----------
    data : DataFrame
        The pandas DataFrame to analyze
    numeric_column : str
        The name of the numeric column to analyze
    group_column : str
        The name of the categorical column to group by
        
    Returns:
    --------
    DataFrame
        DataFrame with statistics for each group
    """
    # Group data and calculate statistics
    grouped_stats = data.groupby(group_column)[numeric_column].agg([
        'count', 'mean', 'std', 'min', 
        lambda x: x.quantile(0.25), 'median', 
        lambda x: x.quantile(0.75), 'max'
    ]).reset_index()
    
    # Rename columns for clarity
    grouped_stats.columns = [
        group_column, 'count', 'mean', 'std', 'min', 
        'Q1', 'median', 'Q3', 'max'
    ]
    
    # Calculate coefficient of variation (CV) for each group
    grouped_stats['cv'] = grouped_stats['std'] / grouped_stats['mean'] * 100
    
    # Round numeric columns for readability
    numeric_cols = grouped_stats.columns.difference([group_column])
    grouped_stats[numeric_cols] = grouped_stats[numeric_cols].round(3)
    
    return grouped_stats
