import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Define color scheme according to style guide
COLORS = {
    'primary': '#1E88E5',    # data blue
    'secondary': '#7CB342',  # insight green
    'background': '#FAFAFA', # light grey
    'text': '#212121',       # dark grey
    'accent': '#FFA000'      # highlight orange
}

def create_scatter_plot(data, x_col, y_col, color_col=None):
    """
    Create an interactive scatter plot
    
    Parameters:
    -----------
    data : DataFrame
        The pandas DataFrame containing the data
    x_col : str
        Column name for x-axis
    y_col : str
        Column name for y-axis
    color_col : str, optional
        Column name for color differentiation
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive scatter plot
    """
    if color_col:
        fig = px.scatter(
            data, 
            x=x_col, 
            y=y_col, 
            color=color_col,
            color_discrete_sequence=px.colors.qualitative.G10,
            opacity=0.7,
            hover_data=data.columns
        )
    else:
        fig = px.scatter(
            data, 
            x=x_col, 
            y=y_col,
            color_discrete_sequence=[COLORS['primary']],
            opacity=0.7,
            hover_data=data.columns
        )
    
    # Calculate and add trendline
    if color_col is None:
        x_values = data[x_col].dropna()
        y_values = data[y_col].dropna()
        
        # Only proceed if we have enough valid data points
        if len(x_values) > 1 and len(y_values) > 1:
            mask = ~(np.isnan(x_values) | np.isnan(y_values))
            if mask.sum() > 1:  # Need at least 2 points for a line
                x_clean = x_values[mask]
                y_clean = y_values[mask]
                
                # Calculate correlation coefficient
                corr = np.corrcoef(x_clean, y_clean)[0, 1]
                
                # Add trendline using polyfit
                z = np.polyfit(x_clean, y_clean, 1)
                p = np.poly1d(z)
                
                # Add trendline to plot
                x_range = np.linspace(x_clean.min(), x_clean.max(), 100)
                fig.add_trace(
                    go.Scatter(
                        x=x_range,
                        y=p(x_range),
                        mode='lines',
                        line=dict(color=COLORS['secondary'], width=2, dash='dash'),
                        name=f'Trend (r={corr:.3f})'
                    )
                )
    
    # Update layout
    fig.update_layout(
        template="plotly_white",
        title=f'Scatter Plot: {y_col} vs {x_col}',
        xaxis_title=x_col,
        yaxis_title=y_col,
        legend_title=color_col if color_col else None,
        font=dict(family="IBM Plex Sans, Roboto, Arial", size=12, color=COLORS['text']),
        margin=dict(l=40, r=40, t=60, b=40),
        hovermode="closest"
    )
    
    # Add correlation annotation if no color column
    if color_col is None and 'corr' in locals():
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.98, y=0.02,
            text=f"Correlation: {corr:.3f}",
            showarrow=False,
            font=dict(size=14),
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor=COLORS['text'],
            borderwidth=1,
            borderpad=4
        )
    
    return fig

def create_histogram(data, column, bins=20):
    """
    Create an interactive histogram
    
    Parameters:
    -----------
    data : DataFrame
        The pandas DataFrame containing the data
    column : str
        Column name for which to create histogram
    bins : int, optional
        Number of bins for the histogram
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive histogram
    """
    # Create histogram
    fig = px.histogram(
        data, 
        x=column,
        nbins=bins,
        color_discrete_sequence=[COLORS['primary']],
        opacity=0.7,
        marginal="box"  # Add a box plot at the margin
    )
    
    # Calculate descriptive statistics for annotations
    series = data[column].dropna()
    mean_val = series.mean()
    median_val = series.median()
    
    # Add mean and median lines
    fig.add_vline(
        x=mean_val, 
        line_dash="solid", 
        line_color=COLORS['secondary'],
        line_width=2,
        annotation_text=f"Mean: {mean_val:.2f}",
        annotation_position="top right"
    )
    
    fig.add_vline(
        x=median_val, 
        line_dash="dash", 
        line_color=COLORS['accent'],
        line_width=2,
        annotation_text=f"Median: {median_val:.2f}",
        annotation_position="bottom right"
    )
    
    # Update layout
    fig.update_layout(
        template="plotly_white",
        title=f'Distribution of {column}',
        xaxis_title=column,
        yaxis_title="Frequency",
        font=dict(family="IBM Plex Sans, Roboto, Arial", size=12, color=COLORS['text']),
        margin=dict(l=40, r=40, t=60, b=40),
        bargap=0.1
    )
    
    return fig

def create_box_plot(data, column, group_col=None):
    """
    Create an interactive box plot
    
    Parameters:
    -----------
    data : DataFrame
        The pandas DataFrame containing the data
    column : str
        Column name for which to create box plot
    group_col : str, optional
        Column name for grouping
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive box plot
    """
    if group_col:
        # Ensure group_col has a reasonable number of categories
        unique_groups = data[group_col].nunique()
        if unique_groups > 20:  # Limit to top 20 groups if too many
            top_groups = data[group_col].value_counts().nlargest(20).index
            filtered_data = data[data[group_col].isin(top_groups)]
            fig = px.box(
                filtered_data, 
                x=group_col, 
                y=column,
                color=group_col,
                color_discrete_sequence=px.colors.qualitative.G10,
                points="all",  # Show all points
                notched=True  # Add notch to display confidence interval around median
            )
            fig.update_layout(
                title=f'Box Plot of {column} by {group_col} (Top 20 Groups)'
            )
        else:
            fig = px.box(
                data, 
                x=group_col, 
                y=column,
                color=group_col,
                color_discrete_sequence=px.colors.qualitative.G10,
                points="all",  # Show all points
                notched=True  # Add notch to display confidence interval around median
            )
            fig.update_layout(
                title=f'Box Plot of {column} by {group_col}'
            )
    else:
        fig = px.box(
            data, 
            y=column,
            color_discrete_sequence=[COLORS['primary']],
            points="all",  # Show all points
            notched=True  # Add notch to display confidence interval around median
        )
        fig.update_layout(
            title=f'Box Plot of {column}'
        )
    
    # Update layout
    fig.update_layout(
        template="plotly_white",
        xaxis_title=group_col if group_col else "",
        yaxis_title=column,
        font=dict(family="IBM Plex Sans, Roboto, Arial", size=12, color=COLORS['text']),
        margin=dict(l=40, r=40, t=60, b=40),
        showlegend=False if group_col else False  # Hide legend if it's redundant
    )
    
    return fig

def create_correlation_heatmap(data, numeric_columns):
    """
    Create an interactive correlation heatmap
    
    Parameters:
    -----------
    data : DataFrame
        The pandas DataFrame containing the data
    numeric_columns : list
        List of numeric column names
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive correlation heatmap
    """
    # Calculate correlation matrix
    corr_matrix = data[numeric_columns].corr()
    
    # Create heatmap
    fig = px.imshow(
        corr_matrix,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        color_continuous_scale=px.colors.diverging.RdBu_r,  # Red-Blue diverging scale
        zmin=-1,
        zmax=1,
        text_auto=".2f"  # Show correlation values
    )
    
    # Update layout
    fig.update_layout(
        template="plotly_white",
        title='Correlation Heatmap',
        xaxis_title="",
        yaxis_title="",
        font=dict(family="IBM Plex Sans, Roboto, Arial", size=12, color=COLORS['text']),
        margin=dict(l=40, r=40, t=60, b=40),
        height=600
    )
    
    # Improve annotations for better readability
    fig.update_traces(
        texttemplate="%{text}",
        textfont={"size": 10}
    )
    
    return fig
