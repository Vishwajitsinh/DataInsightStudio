import streamlit as st
import pandas as pd
import io
import base64
from utils.data_processor import load_data, get_column_types
from utils.statistics import generate_descriptive_stats, generate_correlation_matrix, analyze_distributions
from utils.visualization import create_scatter_plot, create_histogram, create_box_plot, create_correlation_heatmap

# Set page configuration
st.set_page_config(
    page_title="Data Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Application title and description
st.title("Data Analytics Platform")
st.markdown("""
    Upload your data files (CSV or Excel) and analyze them with advanced statistical methods and interactive visualizations.
    Get insights about your data through comprehensive statistical analysis and intuitive charts.
""")

# Initialize session state variables
if 'data' not in st.session_state:
    st.session_state.data = None
if 'filename' not in st.session_state:
    st.session_state.filename = None
if 'column_types' not in st.session_state:
    st.session_state.column_types = {}

# Sidebar for data upload and options
with st.sidebar:
    st.header("Data Upload")
    
    uploaded_file = st.file_uploader("Upload your data file", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file is not None:
        # Load data based on file extension
        try:
            data, filename = load_data(uploaded_file)
            st.session_state.data = data
            st.session_state.filename = filename
            
            # Get column types for further analysis
            st.session_state.column_types = get_column_types(data)
            
            st.success(f"Successfully loaded {filename} with {data.shape[0]} rows and {data.shape[1]} columns.")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
    
    # Display options only if data is loaded
    if st.session_state.data is not None:
        st.header("Analysis Options")
        
        st.subheader("Statistical Analysis")
        stats_options = st.multiselect(
            "Select statistical analyses to perform:",
            ["Descriptive Statistics", "Correlation Analysis", "Distribution Analysis"],
            default=["Descriptive Statistics"]
        )
        
        st.subheader("Visualization")
        viz_options = st.multiselect(
            "Select visualizations to create:",
            ["Scatter Plots", "Histograms", "Box Plots", "Correlation Heatmap"],
            default=["Histograms"]
        )

# Main content area
if st.session_state.data is not None:
    # Display dataset preview
    st.header(f"Dataset Preview: {st.session_state.filename}")
    st.dataframe(st.session_state.data.head(10))
    
    # Additional dataset information
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Rows", st.session_state.data.shape[0])
    with col2:
        st.metric("Columns", st.session_state.data.shape[1])
    with col3:
        st.metric("Missing Values", st.session_state.data.isna().sum().sum())
    
    # Statistical Analysis section
    if 'stats_options' in locals():
        st.header("Statistical Analysis")
        
        if "Descriptive Statistics" in stats_options:
            st.subheader("Descriptive Statistics")
            desc_stats = generate_descriptive_stats(st.session_state.data)
            st.dataframe(desc_stats)
        
        if "Correlation Analysis" in stats_options and len(st.session_state.column_types['numeric']) >= 2:
            st.subheader("Correlation Analysis")
            corr_matrix = generate_correlation_matrix(st.session_state.data, st.session_state.column_types['numeric'])
            st.dataframe(corr_matrix)
        
        if "Distribution Analysis" in stats_options and len(st.session_state.column_types['numeric']) > 0:
            st.subheader("Distribution Analysis")
            dist_stats = analyze_distributions(st.session_state.data, st.session_state.column_types['numeric'])
            st.dataframe(dist_stats)
    
    # Visualization section
    if 'viz_options' in locals():
        st.header("Data Visualization")
        
        if "Scatter Plots" in viz_options and len(st.session_state.column_types['numeric']) >= 2:
            st.subheader("Scatter Plot")
            
            col1, col2 = st.columns(2)
            with col1:
                x_col = st.selectbox("Select X-axis variable:", 
                                    st.session_state.column_types['numeric'],
                                    key='scatter_x')
            with col2:
                y_col = st.selectbox("Select Y-axis variable:", 
                                    [col for col in st.session_state.column_types['numeric'] if col != x_col],
                                    key='scatter_y')
            
            color_col = None
            if len(st.session_state.column_types['categorical']) > 0:
                color_col = st.selectbox("Select color variable (optional):", 
                                        [None] + st.session_state.column_types['categorical'],
                                        key='scatter_color')
            
            fig = create_scatter_plot(st.session_state.data, x_col, y_col, color_col)
            st.plotly_chart(fig, use_container_width=True)
        
        if "Histograms" in viz_options and len(st.session_state.column_types['numeric']) > 0:
            st.subheader("Histogram")
            
            hist_col = st.selectbox("Select variable for histogram:", 
                                  st.session_state.column_types['numeric'],
                                  key='hist_col')
            
            bins = st.slider("Number of bins:", min_value=5, max_value=100, value=20, key='hist_bins')
            
            fig = create_histogram(st.session_state.data, hist_col, bins)
            st.plotly_chart(fig, use_container_width=True)
        
        if "Box Plots" in viz_options and len(st.session_state.column_types['numeric']) > 0:
            st.subheader("Box Plot")
            
            box_col = st.selectbox("Select variable for box plot:", 
                                 st.session_state.column_types['numeric'],
                                 key='box_col')
            
            group_col = None
            if len(st.session_state.column_types['categorical']) > 0:
                group_col = st.selectbox("Group by (optional):", 
                                        [None] + st.session_state.column_types['categorical'],
                                        key='box_group')
            
            fig = create_box_plot(st.session_state.data, box_col, group_col)
            st.plotly_chart(fig, use_container_width=True)
        
        if "Correlation Heatmap" in viz_options and len(st.session_state.column_types['numeric']) >= 2:
            st.subheader("Correlation Heatmap")
            
            fig = create_correlation_heatmap(st.session_state.data, st.session_state.column_types['numeric'])
            st.plotly_chart(fig, use_container_width=True)
    
    # Export section
    st.header("Export Results")
    
    export_format = st.selectbox("Export format:", ["CSV", "Excel", "HTML"], key='export_format')
    
    if st.button("Export Data"):
        # Create file buffer
        if export_format == "CSV":
            buffer = io.StringIO()
            st.session_state.data.to_csv(buffer, index=False)
            buffer.seek(0)
            file_bytes = buffer.getvalue().encode()
            filename = f"{st.session_state.filename.split('.')[0]}_export.csv"
            mime = "text/csv"
        elif export_format == "Excel":
            buffer = io.BytesIO()
            st.session_state.data.to_excel(buffer, index=False)
            buffer.seek(0)
            file_bytes = buffer.getvalue()
            filename = f"{st.session_state.filename.split('.')[0]}_export.xlsx"
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:  # HTML
            buffer = io.StringIO()
            st.session_state.data.to_html(buffer, index=False)
            buffer.seek(0)
            file_bytes = buffer.getvalue().encode()
            filename = f"{st.session_state.filename.split('.')[0]}_export.html"
            mime = "text/html"
            
        # Create download button
        b64 = base64.b64encode(file_bytes).decode()
        href = f'<a href="data:{mime};base64,{b64}" download="{filename}">Download {export_format} file</a>'
        st.markdown(href, unsafe_allow_html=True)
else:
    # Display instructions when no data is loaded
    st.info("Please upload a CSV or Excel file using the sidebar to begin analysis.")
    
    # Sample layout to show how the application will work
    st.header("How to use this application")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Upload your data")
        st.markdown("""
            - Use the file uploader in the sidebar
            - Supports CSV, Excel (.xlsx, .xls) formats
            - Your data remains private and is not stored
        """)
        
        st.subheader("3. Visualize your data")
        st.markdown("""
            - Create interactive scatter plots
            - Generate histograms and box plots
            - Visualize correlations with heatmaps
        """)
    
    with col2:
        st.subheader("2. Analyze your data")
        st.markdown("""
            - Get descriptive statistics (mean, median, etc.)
            - Analyze correlations between variables
            - Explore distributions of your data
        """)
        
        st.subheader("4. Export your results")
        st.markdown("""
            - Export processed data to CSV or Excel
            - Save visualizations for reports
            - Share insights with your team
        """)
