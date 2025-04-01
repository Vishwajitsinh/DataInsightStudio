import streamlit as st
import pandas as pd
import io
import base64
import time
import os
from utils.data_processor import load_data, get_column_types
from utils.statistics import generate_descriptive_stats, generate_correlation_matrix, analyze_distributions
from utils.visualization import create_scatter_plot, create_histogram, create_box_plot, create_correlation_heatmap
from utils.auth import auth_sidebar, init_auth_state
from utils.database import save_dataset, get_dataset, get_all_datasets, delete_dataset

# Set page configuration
st.set_page_config(
    page_title="Data Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.8rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #212121;
        margin-top: 2rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #F0F2F6;
    }
    .description {
        font-size: 1.1rem;
        color: #424242;
        margin-bottom: 2rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #F9F9F9;
        box-shadow: 0 0.15rem 0.5rem rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }
    .metric-container {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 0.15rem 0.5rem rgba(0, 0, 0, 0.05);
        text-align: center;
        transition: transform 0.3s;
    }
    .metric-container:hover {
        transform: translateY(-5px);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E88E5;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #616161;
        text-transform: uppercase;
        letter-spacing: 0.05rem;
    }
    .upload-container {
        border: 2px dashed #1E88E5;
        border-radius: 0.5rem;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .success-message {
        background-color: #E8F5E9;
        color: #1B5E20;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin-top: 1rem;
    }
    .info-message {
        background-color: #E3F2FD;
        color: #0D47A1;
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #E3F2FD;
        border-bottom: 2px solid #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# Application title and description
st.markdown('<div class="main-header">Intelligent Data Analytics Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Transform your data into actionable insights with advanced statistical analysis and stunning interactive visualizations.</div>', unsafe_allow_html=True)

# Initialize session state variables
if 'data' not in st.session_state:
    st.session_state.data = None
if 'filename' not in st.session_state:
    st.session_state.filename = None
if 'column_types' not in st.session_state:
    st.session_state.column_types = {}

# Initialize analysis options in session state if not present
if 'stats_options' not in st.session_state:
    st.session_state.stats_options = ["Descriptive Statistics"]
if 'viz_options' not in st.session_state:
    st.session_state.viz_options = ["Histograms"]
    
# Save dataset dialog state
if 'show_save_dialog' not in st.session_state:
    st.session_state.show_save_dialog = False

# Initialize authentication state
init_auth_state()

# Sidebar for authentication, data upload and options
with st.sidebar:
    # Add authentication section
    auth_sidebar()
    
    st.markdown('<div class="sub-header">Data Management</div>', unsafe_allow_html=True)
    
    # Dataset tabs for upload or loading
    dataset_action = st.radio("Dataset Source:", ["Upload New", "Load Saved"], horizontal=True)
    
    if dataset_action == "Upload New":
        st.markdown('<div class="upload-container">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Drop your CSV or Excel file here", type=['csv', 'xlsx', 'xls'])
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_file is not None:
            # Show loading spinner
            with st.spinner("Processing your data..."):
                try:
                    # Load data based on file extension
                    data, filename = load_data(uploaded_file)
                    st.session_state.data = data
                    st.session_state.filename = filename
                    
                    # Get column types for further analysis
                    st.session_state.column_types = get_column_types(data)
                    
                    # Success message with custom styling
                    st.markdown(f"""
                    <div class="success-message">
                        <strong>✅ Success!</strong> Loaded {filename}<br>
                        📊 {data.shape[0]} rows × {data.shape[1]} columns
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Save dataset to database if user is authenticated
                    if st.session_state.is_authenticated and st.button("💾 Save Dataset to Database"):
                        description = st.text_area("Dataset Description (optional):", key="dataset_description")
                        file_type = filename.split('.')[-1]
                        is_public = st.checkbox("Make Dataset Public", value=False, key="is_public")
                        
                        try:
                            dataset_name = filename.split('.')[0]  # Remove extension
                            dataset_id = save_dataset(
                                dataset_name,
                                description,
                                filename,
                                st.session_state.data,
                                st.session_state.column_types
                            )
                            if dataset_id:
                                st.success(f"Dataset '{dataset_name}' saved successfully!")
                                st.session_state.show_save_dialog = False
                            else:
                                st.error("Failed to save dataset. Please try again.")
                        except Exception as e:
                            st.error(f"Error saving dataset: {str(e)}")
                    
                except Exception as e:
                    st.error(f"Error loading data: {str(e)}")
    else:  # Load Saved
        st.info("Navigate to the 'Saved Datasets' page to view and load your saved datasets.")
        if st.button("Go to Saved Datasets"):
            st.switch_page("pages/saved_datasets.py")
            
    # Display options only if data is loaded
    if st.session_state.data is not None:
        st.markdown('<div class="sub-header">Analysis Options</div>', unsafe_allow_html=True)
        
        st.markdown("### 📈 Statistical Analysis")
        st.session_state.stats_options = st.multiselect(
            "Select analyses to perform:",
            ["Descriptive Statistics", "Correlation Analysis", "Distribution Analysis"],
            default=st.session_state.stats_options
        )
        
        st.markdown("### 🎨 Visualization")
        st.session_state.viz_options = st.multiselect(
            "Select visualizations to create:",
            ["Scatter Plots", "Histograms", "Box Plots", "Correlation Heatmap"],
            default=st.session_state.viz_options
        )
        
        # Add a "Save Dataset" button if data exists and not already saved
        if st.session_state.data is not None and st.session_state.is_authenticated:
            if st.button("💾 Save Current Dataset"):
                dataset_name = st.text_input("Dataset Name:", value=st.session_state.filename.split('.')[0] if st.session_state.filename else "My Dataset")
                description = st.text_area("Description (optional):")
                
                if st.button("Confirm Save"):
                    try:
                        dataset_id = save_dataset(
                            dataset_name,
                            description,
                            st.session_state.filename,
                            st.session_state.data,
                            st.session_state.column_types
                        )
                        if dataset_id:
                            st.success(f"Dataset '{dataset_name}' saved successfully!")
                        else:
                            st.error("Failed to save dataset. Please try again.")
                    except Exception as e:
                        st.error(f"Error saving dataset: {str(e)}")
        
        # Add a divider
        st.markdown("---")
        
        # Add a quick tips section
        st.markdown("### 💡 Quick Tips")
        tips = [
            "Use histograms to understand data distribution",
            "Correlation heatmaps help identify relationships",
            "Box plots are perfect for detecting outliers",
            "Hover over charts for interactive details",
            "Save your datasets to access them later",
            "Log in to save your analyses and visualizations"
        ]
        tip_idx = int(time.time()) % len(tips)  # Cycle through tips
        st.info(tips[tip_idx])

# Main content area
if st.session_state.data is not None:
    # Create tabs for better organization
    tabs = st.tabs(["📊 Dataset Overview", "📈 Statistics", "🎨 Visualizations", "💾 Export"])
    
    with tabs[0]:
        # Dataset overview tab
        st.markdown(f'<div class="sub-header">Dataset: {st.session_state.filename}</div>', unsafe_allow_html=True)
        
        # Display dataset preview with styling
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.dataframe(st.session_state.data.head(10), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Dataset metrics in a nicer format with custom CSS
        st.markdown('<div style="display: flex; justify-content: space-between; margin: 1rem 0;">', unsafe_allow_html=True)
        
        # Create metrics with nicer styling
        metrics = [
            {"label": "Rows", "value": f"{st.session_state.data.shape[0]:,}"},
            {"label": "Columns", "value": st.session_state.data.shape[1]},
            {"label": "Missing Values", "value": f"{st.session_state.data.isna().sum().sum():,}"},
            {"label": "Data Types", "value": len(set(st.session_state.data.dtypes))},
        ]
        
        cols = st.columns(len(metrics))
        for i, metric in enumerate(metrics):
            with cols[i]:
                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{metric['value']}</div>
                    <div class="metric-label">{metric['label']}</div>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Data types summary
        st.markdown('<div class="sub-header">Data Types Summary</div>', unsafe_allow_html=True)
        
        data_types = pd.DataFrame({
            'Column': st.session_state.data.columns,
            'Type': st.session_state.data.dtypes.values,
            'Non-Null Count': st.session_state.data.count().values,
            'Null Count': st.session_state.data.isna().sum().values,
            'Unique Values': [st.session_state.data[col].nunique() for col in st.session_state.data.columns]
        })
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.dataframe(data_types, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tabs[1]:
        # Statistics tab
        st.markdown('<div class="sub-header">Statistical Analysis</div>', unsafe_allow_html=True)
        
        # Use expanders for each type of statistics to save space
        if "Descriptive Statistics" in st.session_state.stats_options:
            with st.expander("Descriptive Statistics", expanded=True):
                desc_stats = generate_descriptive_stats(st.session_state.data)
                st.dataframe(desc_stats, use_container_width=True)
        
        if "Correlation Analysis" in st.session_state.stats_options and len(st.session_state.column_types['numeric']) >= 2:
            with st.expander("Correlation Analysis", expanded=True):
                corr_matrix = generate_correlation_matrix(st.session_state.data, st.session_state.column_types['numeric'])
                st.dataframe(corr_matrix, use_container_width=True)
        
        if "Distribution Analysis" in st.session_state.stats_options and len(st.session_state.column_types['numeric']) > 0:
            with st.expander("Distribution Analysis", expanded=True):
                dist_stats = analyze_distributions(st.session_state.data, st.session_state.column_types['numeric'])
                st.dataframe(dist_stats, use_container_width=True)
        
        if not st.session_state.stats_options:
            st.warning("Please select statistical analyses from the sidebar.")
    
    with tabs[2]:
        # Visualizations tab
        st.markdown('<div class="sub-header">Interactive Data Visualizations</div>', unsafe_allow_html=True)
        
        # Create subtabs for different visualization types
        if any(viz in st.session_state.viz_options for viz in ["Scatter Plots", "Histograms", "Box Plots", "Correlation Heatmap"]):
            viz_subtabs = []
            
            if "Scatter Plots" in st.session_state.viz_options and len(st.session_state.column_types['numeric']) >= 2:
                viz_subtabs.append("Scatter Plot")
            
            if "Histograms" in st.session_state.viz_options and len(st.session_state.column_types['numeric']) > 0:
                viz_subtabs.append("Histogram")
            
            if "Box Plots" in st.session_state.viz_options and len(st.session_state.column_types['numeric']) > 0:
                viz_subtabs.append("Box Plot")
            
            if "Correlation Heatmap" in st.session_state.viz_options and len(st.session_state.column_types['numeric']) >= 2:
                viz_subtabs.append("Correlation Heatmap")
            
            if viz_subtabs:  # Only create tabs if there are visualization options
                viz_tabs = st.tabs(viz_subtabs)
                
                tab_index = 0
                
                # Scatter Plot
                if "Scatter Plots" in st.session_state.viz_options and len(st.session_state.column_types['numeric']) >= 2:
                    with viz_tabs[tab_index]:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            x_col = st.selectbox("X-axis:", 
                                            st.session_state.column_types['numeric'],
                                            key='scatter_x')
                        with col2:
                            y_col = st.selectbox("Y-axis:", 
                                            [col for col in st.session_state.column_types['numeric'] if col != x_col],
                                            key='scatter_y')
                        
                        color_col = None
                        if len(st.session_state.column_types['categorical']) > 0:
                            color_col = st.selectbox("Color by (optional):", 
                                                [None] + st.session_state.column_types['categorical'],
                                                key='scatter_color')
                        
                        fig = create_scatter_plot(st.session_state.data, x_col, y_col, color_col)
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    tab_index += 1
                
                # Histogram
                if "Histograms" in st.session_state.viz_options and len(st.session_state.column_types['numeric']) > 0:
                    with viz_tabs[tab_index]:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            hist_col = st.selectbox("Variable:", 
                                            st.session_state.column_types['numeric'],
                                            key='hist_col')
                        with col2:
                            bins = st.slider("Bins:", min_value=5, max_value=100, value=20, key='hist_bins')
                        
                        fig = create_histogram(st.session_state.data, hist_col, bins)
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    tab_index += 1
                
                # Box Plot
                if "Box Plots" in st.session_state.viz_options and len(st.session_state.column_types['numeric']) > 0:
                    with viz_tabs[tab_index]:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            box_col = st.selectbox("Variable:", 
                                            st.session_state.column_types['numeric'],
                                            key='box_col')
                        
                        with col2:
                            group_col = None
                            if len(st.session_state.column_types['categorical']) > 0:
                                group_col = st.selectbox("Group by (optional):", 
                                                    [None] + st.session_state.column_types['categorical'],
                                                    key='box_group')
                        
                        fig = create_box_plot(st.session_state.data, box_col, group_col)
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    tab_index += 1
                
                # Correlation Heatmap
                if "Correlation Heatmap" in st.session_state.viz_options and len(st.session_state.column_types['numeric']) >= 2:
                    with viz_tabs[tab_index]:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        
                        st.markdown("""
                        <div style="text-align: center; margin-bottom: 1rem;">
                            <p style="color: #616161;">Explore relationships between numeric variables</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        fig = create_correlation_heatmap(st.session_state.data, st.session_state.column_types['numeric'])
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    tab_index += 1
            else:
                st.info("No visualizations available for this dataset type. Please select different visualization options.")
        else:
            st.info("Please select visualization types from the sidebar to begin.")
    
    with tabs[3]:
        # Export tab
        st.markdown('<div class="sub-header">Export Your Analysis</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="margin-bottom: 1.5rem;">
            <p>Download your data in your preferred format for further analysis or reporting.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            export_format = st.selectbox("Select Format:", ["CSV", "Excel", "HTML"], key='export_format')
            
            format_descriptions = {
                "CSV": "Comma-separated values format, compatible with most data analysis tools.",
                "Excel": "Microsoft Excel spreadsheet format with formatting preserved.",
                "HTML": "Web page format, useful for sharing results online."
            }
            
            st.markdown(f"<p style='color: #616161;'>{format_descriptions[export_format]}</p>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacer
            export_button = st.button("📥 Export Data", use_container_width=True)
        
        if export_button:
            with st.spinner(f"Preparing {export_format} export..."):
                # Create file buffer
                if export_format == "CSV":
                    buffer = io.StringIO()
                    st.session_state.data.to_csv(buffer, index=False)
                    buffer.seek(0)
                    file_bytes = buffer.getvalue().encode()
                    
                    # Safely handle the filename with or without extension
                    base_filename = "data_export"
                    if st.session_state.filename:
                        base_filename = st.session_state.filename.rsplit('.', 1)[0] if '.' in st.session_state.filename else st.session_state.filename
                    
                    filename = f"{base_filename}_export.csv"
                    mime = "text/csv"
                elif export_format == "Excel":
                    buffer = io.BytesIO()
                    st.session_state.data.to_excel(buffer, index=False, engine="openpyxl")
                    buffer.seek(0)
                    file_bytes = buffer.getvalue()
                    
                    # Safely handle the filename with or without extension
                    base_filename = "data_export"
                    if st.session_state.filename:
                        base_filename = st.session_state.filename.rsplit('.', 1)[0] if '.' in st.session_state.filename else st.session_state.filename
                    
                    filename = f"{base_filename}_export.xlsx"
                    mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                else:  # HTML
                    buffer = io.StringIO()
                    html_table = st.session_state.data.to_html(index=False, classes=["table", "table-striped"])
                    
                    # Create a full HTML document with some basic styling
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Data Export - {st.session_state.filename}</title>
                        <style>
                            body {{ font-family: 'IBM Plex Sans', Arial, sans-serif; margin: 2rem; }}
                            .table {{ border-collapse: collapse; width: 100%; }}
                            .table-striped tbody tr:nth-of-type(odd) {{ background-color: rgba(0,0,0,.05); }}
                            .table th, .table td {{ padding: 0.75rem; border-top: 1px solid #dee2e6; text-align: left; }}
                            .table thead th {{ vertical-align: bottom; border-bottom: 2px solid #dee2e6; }}
                            h1 {{ color: #1E88E5; }}
                        </style>
                    </head>
                    <body>
                        <h1>Data Export - {st.session_state.filename}</h1>
                        <p>Exported on {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                        {html_table}
                    </body>
                    </html>
                    """
                    
                    buffer.write(html_content)
                    buffer.seek(0)
                    file_bytes = buffer.getvalue().encode()
                    
                    # Safely handle the filename with or without extension
                    base_filename = "data_export"
                    if st.session_state.filename:
                        base_filename = st.session_state.filename.rsplit('.', 1)[0] if '.' in st.session_state.filename else st.session_state.filename
                    
                    filename = f"{base_filename}_export.html"
                    mime = "text/html"
                
                # Create download button with nice styling
                b64 = base64.b64encode(file_bytes).decode()
                download_link = f'<a href="data:{mime};base64,{b64}" download="{filename}" class="download-button" style="display: inline-block; background-color: #1E88E5; color: white; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 0.25rem; font-weight: 600; text-align: center; margin-top: 1rem;"><span style="margin-right: 0.5rem;">📥</span> Download {export_format} file</a>'
                st.markdown(download_link, unsafe_allow_html=True)
                
                # Show success message
                st.success(f"Your data is ready to download in {export_format} format.")
else:
    # Display welcome screen with modern design
    st.markdown('<div class="info-message">Please upload a CSV or Excel file in the sidebar to begin your data analysis journey.</div>', unsafe_allow_html=True)
    
    # Feature cards in a modern layout
    st.markdown('<div class="sub-header">Unlock the Power of Your Data</div>', unsafe_allow_html=True)
    
    # Intro text
    st.markdown("""
    <div style="margin-bottom: 2rem; color: #424242; font-size: 1.1rem; line-height: 1.6;">
        Transform raw data into actionable insights with our advanced analytics platform. Upload your dataset to discover patterns, 
        correlations, and trends that will help you make data-driven decisions with confidence.
    </div>
    """, unsafe_allow_html=True)
    
    # Feature cards
    features = [
        {
            "icon": "📊",
            "title": "Data Exploration",
            "description": "Get a comprehensive overview of your dataset with detailed statistics and summaries."
        },
        {
            "icon": "📈",
            "title": "Statistical Analysis",
            "description": "Generate descriptive statistics, correlation matrices, and distribution analysis automatically."
        },
        {
            "icon": "🎨",
            "title": "Interactive Visualizations",
            "description": "Create beautiful, interactive charts to visualize patterns and relationships in your data."
        },
        {
            "icon": "💾",
            "title": "Export Capabilities",
            "description": "Download your analysis results in multiple formats for reports and presentations."
        }
    ]
    
    # Create two rows of feature cards
    for i in range(0, len(features), 2):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 0.15rem 0.5rem rgba(0, 0, 0, 0.05); height: 100%; margin-bottom: 1rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{features[i]['icon']}</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: #1E88E5; margin-bottom: 0.5rem;">{features[i]['title']}</div>
                <div style="color: #616161;">{features[i]['description']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        if i+1 < len(features):
            with col2:
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 0.5rem; box-shadow: 0 0.15rem 0.5rem rgba(0, 0, 0, 0.05); height: 100%; margin-bottom: 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">{features[i+1]['icon']}</div>
                    <div style="font-size: 1.2rem; font-weight: 600; color: #1E88E5; margin-bottom: 0.5rem;">{features[i+1]['title']}</div>
                    <div style="color: #616161;">{features[i+1]['description']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Quick start guide
    st.markdown('<div class="sub-header">Quick Start Guide</div>', unsafe_allow_html=True)
    
    steps = [
        {
            "number": "1",
            "title": "Upload Your Data",
            "description": "Use the file uploader in the sidebar to upload your CSV or Excel file."
        },
        {
            "number": "2",
            "title": "Select Analysis Options",
            "description": "Choose the statistical analyses and visualizations you want to generate."
        },
        {
            "number": "3",
            "title": "Explore Insights",
            "description": "Navigate through the tabs to view statistics and interactive visualizations."
        },
        {
            "number": "4",
            "title": "Export Your Results",
            "description": "Download your data and analysis results in your preferred format."
        }
    ]
    
    # Display steps in a horizontal timeline
    st.markdown('<div style="display: flex; justify-content: space-between; margin-top: 1rem;">', unsafe_allow_html=True)
    
    for step in steps:
        st.markdown(f"""
        <div style="flex: 1; padding: 0 0.5rem; text-align: center;">
            <div style="background-color: #1E88E5; color: white; width: 2rem; height: 2rem; border-radius: 50%; display: inline-flex; justify-content: center; align-items: center; font-weight: bold; margin-bottom: 0.5rem;">{step['number']}</div>
            <div style="font-weight: 600; margin-bottom: 0.5rem;">{step['title']}</div>
            <div style="font-size: 0.9rem; color: #616161;">{step['description']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sample data note
    st.markdown("""
    <div style="margin-top: 2rem; text-align: center; padding: 1rem; background-color: #F0F2F6; border-radius: 0.5rem;">
        <p style="color: #424242;">Don't have a dataset ready? No problem! You can use sample datasets from sources like 
        <a href="https://www.kaggle.com/datasets" target="_blank">Kaggle</a> or 
        <a href="https://data.gov/" target="_blank">Data.gov</a> to test the platform.</p>
    </div>
    """, unsafe_allow_html=True)
