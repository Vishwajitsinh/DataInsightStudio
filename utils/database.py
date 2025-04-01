import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from datetime import datetime
import io
import base64
import json

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define models
class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    filename = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data = Column(Text)  # JSON string of the data
    column_types = Column(Text)  # JSON string of column types

# Create all tables
Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_dataset(name, description, filename, dataframe, column_types):
    """
    Save a dataset to the database
    """
    try:
        # Convert DataFrame to JSON
        data_json = dataframe.to_json(orient="records", date_format="iso")
        
        # Convert column_types dict to JSON
        column_types_json = json.dumps(column_types)
        
        # Create a database session
        db = SessionLocal()
        
        # Create a new dataset
        new_dataset = Dataset(
            name=name,
            description=description,
            filename=filename,
            data=data_json,
            column_types=column_types_json
        )
        
        # Add to session and commit
        db.add(new_dataset)
        db.commit()
        db.refresh(new_dataset)
        
        db.close()
        
        return new_dataset.id
    except Exception as e:
        st.error(f"Error saving dataset: {str(e)}")
        return None

def get_all_datasets():
    """
    Get all datasets from the database
    """
    try:
        db = SessionLocal()
        datasets = db.query(Dataset).all()
        db.close()
        
        # Convert to a list of dictionaries for easier handling
        result = []
        for dataset in datasets:
            result.append({
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "filename": dataset.filename,
                "created_at": dataset.created_at,
                "updated_at": dataset.updated_at
            })
        
        return result
    except Exception as e:
        st.error(f"Error getting datasets: {str(e)}")
        return []

def get_dataset(dataset_id):
    """
    Get a specific dataset by ID
    """
    try:
        db = SessionLocal()
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        
        if dataset is None:
            db.close()
            return None
        
        # Convert JSON data back to DataFrame
        df = pd.read_json(dataset.data, orient="records")
        
        # Convert JSON column_types back to dict
        column_types = json.loads(dataset.column_types)
        
        db.close()
        
        return {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "filename": dataset.filename,
            "created_at": dataset.created_at,
            "updated_at": dataset.updated_at,
            "dataframe": df,
            "column_types": column_types
        }
    except Exception as e:
        st.error(f"Error getting dataset: {str(e)}")
        return None

def delete_dataset(dataset_id):
    """
    Delete a dataset by ID
    """
    try:
        db = SessionLocal()
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        
        if dataset is None:
            db.close()
            return False
        
        db.delete(dataset)
        db.commit()
        db.close()
        
        return True
    except Exception as e:
        st.error(f"Error deleting dataset: {str(e)}")
        return False

def update_dataset(dataset_id, name=None, description=None):
    """
    Update dataset metadata
    """
    try:
        db = SessionLocal()
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        
        if dataset is None:
            db.close()
            return False
        
        if name:
            dataset.name = name
        if description:
            dataset.description = description
            
        dataset.updated_at = datetime.utcnow()
        
        db.commit()
        db.close()
        
        return True
    except Exception as e:
        st.error(f"Error updating dataset: {str(e)}")
        return False