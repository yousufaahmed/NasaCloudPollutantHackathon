from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from contextlib import asynccontextmanager
from pathlib import Path
import pickle
import numpy as np
from typing import List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Global variable for model
model = None
EXPECTED_FEATURES = 11  # Sri might have to confirm but i think this is right



# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load model
    global model
    try:
        with open("airnowModels/aqi_model.pkl", "rb") as f:
            model = pickle.load(f)
        logger.info("Model loaded successfully from pickle file")
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise RuntimeError(f"Could not load model: {str(e)}")
    
    yield
    
    # Shutdown: Clean up resources (if needed)
    logger.info("Shutting down application")



# Initialize FastAPI app with lifespan
app = FastAPI(
    title="AQI Prediction API",
    description="XGBoost model for predicting Air Quality Index",
    version="1.0.0",
    lifespan=lifespan
)



# Define input schemas with validation
class InputData(BaseModel):
    features: List[float] = Field(
        ..., 
        description="List of feature values for prediction",
        example=[1.0, 2020.0, 6.0, 15.0, 10.0, 45.5, 18.2, 0.5, 12.3, 55.6, 28.4]
    )
    
    @field_validator('features')
    @classmethod
    def validate_features(cls, v: List[float]) -> List[float]:
        if len(v) != EXPECTED_FEATURES:
            raise ValueError(f"Expected {EXPECTED_FEATURES} features, got {len(v)}")
        if any(np.isnan(val) or np.isinf(val) for val in v):
            raise ValueError("Features contain NaN or Inf values")
        return v



class BatchInput(BaseModel):
    batch: List[List[float]] = Field(
        ...,
        description="List of feature arrays for batch prediction",
        example=[
            [1.0, 2020.0, 6.0, 15.0, 10.0, 45.5, 18.2, 0.5, 12.3, 55.6, 28.4],
            [2.0, 2020.0, 6.0, 15.0, 11.0, 50.2, 20.1, 0.6, 13.5, 60.2, 30.1]
        ]
    )
    
    @field_validator('batch')
    @classmethod
    def validate_batch(cls, v: List[List[float]]) -> List[List[float]]:
        if len(v) == 0:
            raise ValueError("Batch cannot be empty")
        if len(v) > 1000:
            raise ValueError("Batch size cannot exceed 1000")
        for idx, features in enumerate(v):
            if len(features) != EXPECTED_FEATURES:
                raise ValueError(f"Row {idx}: Expected {EXPECTED_FEATURES} features, got {len(features)}")
            if any(np.isnan(val) or np.isinf(val) for val in features):
                raise ValueError(f"Row {idx}: Features contain NaN or Inf values")
        return v

class PredictionResponse(BaseModel):
    prediction: float
    status: str = "success"

class BatchPredictionResponse(BaseModel):
    predictions: List[float]
    count: int
    status: str = "success"

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API and model are ready"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy", "model_loaded": True}





# Single prediction endpoint
@app.post("/predict", response_model=PredictionResponse)
async def predict(data: InputData):
    """
    Predict AQI for a single input
    
    Features expected (in order):
    - City_encoded, Year, Month, Day, Hour, PM10, NO2, CO, SO2, O3, PM2.5
    """
    try:
        if model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Convert input to numpy array
        input_array = np.array(data.features).reshape(1, -1)
        
        # Get prediction
        prediction = model.predict(input_array)
        predicted_val = float(prediction[0])
        
        # Validate output
        if np.isnan(predicted_val) or np.isinf(predicted_val):
            raise ValueError("Model produced invalid prediction")
        
        # Ensure AQI is non-negative
        predicted_val = max(0.0, predicted_val)
        
        logger.info(f"Prediction successful: {predicted_val}")
        return PredictionResponse(prediction=predicted_val)
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")




# Batch prediction endpoint
@app.post("/predict-batch", response_model=BatchPredictionResponse)
async def predict_batch(data: BatchInput):
    """
    Predict AQI for multiple inputs in batch
    
    Maximum batch size: 1000
    """
    try:
        if model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Convert input to numpy array
        input_array = np.array(data.batch)
        
        # Get predictions
        predictions = model.predict(input_array)
        
        # Convert to list and ensure non-negative
        predictions_list = [max(0.0, float(p)) for p in predictions]
        
        # Validate outputs
        if any(np.isnan(p) or np.isinf(p) for p in predictions_list):
            raise ValueError("Model produced invalid predictions")
        
        logger.info(f"Batch prediction successful: {len(predictions_list)} predictions")
        return BatchPredictionResponse(
            predictions=predictions_list,
            count=len(predictions_list)
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")




# Model info endpoint
@app.get("/model-info")
async def model_info():
    """Get information about the loaded model"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "model_type": "XGBoost Regressor",
        "expected_features": EXPECTED_FEATURES,
        "feature_names": [
            "City_encoded", "Year", "Month", "Day", "Hour", 
            "PM10", "NO2", "CO", "SO2", "O3", "PM2.5"
        ]
    }




# Root endpoint
@app.get("/")
async def root():
    """API root with basic information"""
    return {
        "message": "AQI Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/predict": "Single prediction",
            "/predict-batch": "Batch prediction",
            "/model-info": "Model information",
            "/docs": "Interactive API documentation"
        }
    }