import streamlit as st
import pandas as pd
from utils.database import get_all_datasets, get_dataset, delete_dataset
from utils.data_processor import get_column_types
import time

# Set page configuration
st.set_page_config(
    page_title="Saved Datasets - Data Analytics Platform",
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
    .dataset-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: white;
        box-shadow: 0 0.15rem 0.5rem rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        transition: transform 0.2s;
        border-left: 4px solid #1E88E5;
    }
    .dataset-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 0.3rem 0.7rem rgba(0, 0, 0, 0.1);
    }
    .info-message {
        background-color: #E3F2FD;
        color: #0D47A1;
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
    .button-row {
        display: flex;
        justify-content: space-between;
        margin-top: 1rem;
    }
    .button-container {
        display: flex;
        gap: 0.5rem;
    }
    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        background-color: #F0F2F6;
        border-radius: 0.5rem;
        margin: 2rem 0;
    }
    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        color: #9E9E9E;
    }
</style>
""", unsafe_allow_html=True)

# Page header
st.markdown('<div class="main-header">Saved Datasets</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Access and manage your previously saved datasets</div>', unsafe_allow_html=True)

# Initialize session state variables
if 'selected_dataset_id' not in st.session_state:
    st.session_state.selected_dataset_id = None

# Function to load dataset into main app session
def load_dataset_to_main(dataset):
    st.session_state.data = dataset["dataframe"]
    st.session_state.filename = dataset["filename"]
    st.session_state.column_types = dataset["column_types"]
    st.success(f"Dataset '{dataset['name']}' loaded successfully!")
    time.sleep(1)
    st.switch_page("app.py")

# Main content
datasets = get_all_datasets()

if datasets:
    # Dataset grid
    st.markdown('<div class="sub-header">Your Datasets</div>', unsafe_allow_html=True)
    
    # Display datasets in a grid
    cols = st.columns(2)
    for i, dataset in enumerate(datasets):
        with cols[i % 2]:
            with st.container():
                st.markdown(f"""
                <div class="dataset-card">
                    <h3 style="color: #1E88E5; margin-top: 0;">{dataset['name']}</h3>
                    <p style="color: #616161; margin-bottom: 0.5rem;">{dataset['description'] or 'No description'}</p>
                    <div style="display: flex; justify-content: space-between; font-size: 0.9rem; color: #9E9E9E;">
                        <span>Filename: {dataset['filename']}</span>
                        <span>Created: {dataset['created_at'].strftime('%Y-%m-%d')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔍 View", key=f"view_{dataset['id']}"):
                        st.session_state.selected_dataset_id = dataset['id']
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{dataset['id']}"):
                        if delete_dataset(dataset['id']):
                            st.success(f"Dataset '{dataset['name']}' deleted!")
                            time.sleep(1)
                            st.experimental_rerun()
    
    # Dataset details
    if st.session_state.selected_dataset_id:
        dataset = get_dataset(st.session_state.selected_dataset_id)
        if dataset:
            st.markdown('<div class="sub-header">Dataset Details</div>', unsafe_allow_html=True)
            
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <h2 style="color: #1E88E5; margin-top: 0;">{dataset['name']}</h2>
                    <p style="color: #616161; margin-bottom: 1rem;">{dataset['description'] or 'No description'}</p>
                    <div style="display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1rem;">
                        <div style="background: #E3F2FD; padding: 0.5rem 1rem; border-radius: 1rem;">
                            <span style="font-weight: 600;">Filename:</span> {dataset['filename']}
                        </div>
                        <div style="background: #E3F2FD; padding: 0.5rem 1rem; border-radius: 1rem;">
                            <span style="font-weight: 600;">Rows:</span> {len(dataset['dataframe'])}
                        </div>
                        <div style="background: #E3F2FD; padding: 0.5rem 1rem; border-radius: 1rem;">
                            <span style="font-weight: 600;">Columns:</span> {len(dataset['dataframe'].columns)}
                        </div>
                        <div style="background: #E3F2FD; padding: 0.5rem 1rem; border-radius: 1rem;">
                            <span style="font-weight: 600;">Created:</span> {dataset['created_at'].strftime('%Y-%m-%d %H:%M')}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.subheader("Data Preview")
            st.dataframe(dataset['dataframe'].head(10), use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Load for Analysis", use_container_width=True):
                    load_dataset_to_main(dataset)
            with col2:
                if st.button("Back to Dataset List", use_container_width=True):
                    st.session_state.selected_dataset_id = None
                    st.experimental_rerun()
else:
    # Empty state
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">📁</div>
        <h2>No Saved Datasets Yet</h2>
        <p style="color: #616161; margin-bottom: 2rem;">Save your datasets from the main analysis page to access them here.</p>
        <p>Go to the main page to upload and save your first dataset.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Go to Main Page", use_container_width=False):
        st.switch_page("app.py")