from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field, field_validator
from contextlib import asynccontextmanager
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
from typing import List, Optional
import logging
import sys


# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fetch_airnow_bbox import fetch_and_save
    AIRNOW_AVAILABLE = True
except ImportError as e:
    logging.warning(f"AirNow fetching not available: {e}")
    AIRNOW_AVAILABLE = False


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Global variable for model
model = None
EXPECTED_FEATURES = 52  # Sri might have to confirm but i think this is right



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

class LocationInput(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    miles_radius: Optional[float] = Field(10.0, ge=1, le=50, description="Search radius in miles")


class PredictionResponse(BaseModel):
    prediction: float
    status: str = "success"


class BatchPredictionResponse(BaseModel):
    predictions: List[float]
    count: int
    status: str = "success"


class AirNowDataResponse(BaseModel):
    status: str
    file_path: str
    data_points: int
    message: str


# Health Check
@app.get("/health")
async def health_check():
    """Check if the API and model are ready"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {
        "status": "healthy", 
        "model_loaded": True,
        "airnow_available": AIRNOW_AVAILABLE
    }



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


# Fetch AirNow data endpoint
@app.post("/fetch-airnow", response_model=AirNowDataResponse)
async def fetch_airnow_data(location: LocationInput):
    """
    Fetch current AirNow data for a given location
    
    Returns pollutant data (NO2, OZONE, CO, SO2, PM2.5, PM10) and saves to Excel file
    """
    if not AIRNOW_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="AirNow fetching not available. Check that fetch_airnow_bbox.py and bbox_utils.py are present."
        )
    
    try:
        # Fetch data
        file_path = fetch_and_save(
            lat=location.latitude,
            lon=location.longitude,
            miles_to_edge=location.miles_radius
        )
        
        # Read the saved file to get row count
        df = pd.read_excel(file_path)
        
        logger.info(f"AirNow data fetched successfully: {len(df)} data points")
        
        return AirNowDataResponse(
            status="success",
            file_path=str(file_path),
            data_points=len(df),
            message=f"Successfully fetched {len(df)} data points for location ({location.latitude}, {location.longitude})"
        )
        
    except Exception as e:
        logger.error(f"Error fetching AirNow data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch AirNow data: {str(e)}")


#Fetch coords from frontend
@app.post("/fetch-coords")
async def fetch_coords(location: LocationInput):
    """
    Receive coordinates from frontend and return confirmation
    
    This endpoint accepts latitude/longitude from the frontend
    and can be used to validate coordinates before fetching data
    """
    try:
        logger.info(f"Received coordinates: lat={location.latitude}, lon={location.longitude}")
        
        return {
            "status": "success",
            "received_coordinates": {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "miles_radius": location.miles_radius
            },
            "message": f"Coordinates received successfully"
        }
        
    except Exception as e:
        logger.error(f"Error processing coordinates: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid coordinates: {str(e)}")




# Download AirNow data file
@app.get("/download-airnow/{filename}")
async def download_airnow_file(filename: str):
    """
    Download a previously generated AirNow data file
    """
    user_output_dir = Path(__file__).resolve().parent / "user_output"
    file_path = user_output_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.suffix == ".xlsx":
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

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

# Combined endpoint: Fetch AirNow data and predict
@app.post("/fetch-and-predict")
async def fetch_and_predict(location: LocationInput):
    """
    Fetch AirNow data for a location and make AQI predictions
    
    This combines data fetching and prediction in one call
    """
    if not AIRNOW_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="AirNow fetching not available"
        )
    
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Fetch AirNow data
        file_path = fetch_and_save(
            lat=location.latitude,
            lon=location.longitude,
            miles_to_edge=location.miles_radius
        )
        
        # Read the data
        df = pd.read_excel(file_path)
        
        if len(df) == 0:
            raise HTTPException(
                status_code=404,
                detail="No data found for this location. Try increasing the search radius."
            )
        
        # Extract features for prediction (you'll need to adjust this based on your actual data format)
        # Example: assume we need City_encoded, Year, Month, Day, Hour, PM10, NO2, CO, SO2, O3, PM2.5
        
        logger.info(f"Fetched {len(df)} data points, file saved to {file_path}")
        
        return {
            "status": "success",
            "location": {
                "latitude": location.latitude,
                "longitude": location.longitude
            },
            "data_file": str(file_path),
            "data_points": len(df),
            "message": "Data fetched successfully. Use the data to make predictions via /predict endpoint"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in fetch-and-predict: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


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
            "/fetch-airnow": "Fetch current AirNow sensor data",
            "/download-airnow/{filename}": "Download AirNow data file",
            "/model-info": "Model information",
            "/docs": "Interactive API documentation"
        },
        "airnow_available": AIRNOW_AVAILABLE
    }