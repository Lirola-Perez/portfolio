from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import joblib
import pandas as pd
from pydantic import BaseModel, Field
from typing import Annotated
import os

storage_path = os.getenv("STORAGE_PATH", "/common_storage/")
model_path = os.path.join(storage_path,"model.pkl")

app = FastAPI(title="Energy-Performance Building Simulation Machine Learning Engine")
templates = Jinja2Templates(directory="templates")

class PredictionInput(BaseModel):
    weather: str
    target_variable: str
    area: float = Field(..., gt=0, description="Area of the room or zone.")
    height: float = Field(..., gt=0, description="Height of the room or zone.")
    conductivity: float
    thickness: float
    
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request=request,name="index.html",context={"request":request, "prediction":None})

@app.post("/", response_class=HTMLResponse)
async def calculate_prediction(
    request: Request,
    # 2. FastAPI automatically maps the HTML form data into your Pydantic model!
    form_data: Annotated[PredictionInput, Form()]
):
    # Pydantic has already validated that area and volume are valid floats > 0
    # You can access them cleanly using dot notation: form_data.area
    
    prediction_result = round(form_data.area * 0.45 + form_data.height * 0.12, 2)
    volume = form_data.area * form_data.height
    print(f"{volume}, {prediction_result}") 

    model = use_model()

    return templates.TemplateResponse(request=request,name="index.html",context={
        "request": request,
        "prediction": prediction_result,
        # pass form_data back to keep fields filled out
        "area": form_data.area,
        "height": form_data.height,
        "volume": volume,
        "weather": form_data.weather,
        "target": form_data.target_variable,
        "thickness": form_data.thickness,
        "conductivity": form_data.conductivity
    })

def use_model():

    if not os.path.exists(model_path):
        print(f"No model found at {model_path}. Please train or upload one first.")
        return None
    
    try:
        # Pass the path string directly to joblib.load
        model = joblib.load(model_path)
        print(f"Model successfully loaded from {model_path}.")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def data_preparation(model, form_data, volume, conductivity, thickness):
    # 1. Create a base dictionary representing ALL features your model expects (defaulting others to 0)
    features = {
        "area": form_data.area,
        "volume": volume,
        "conductivity": conductivity,
        "thickness": thickness,
        # Add your other columns set to 0 or their default training baselines
        "extra_feature_1": 0.0,
        "extra_feature_2": 0.0,
        
        # Handle categorical encoding if your model expects dummy columns:
        "weather_chicago": 1 if form_data.weather == "chicago" else 0,
        "weather_madrid": 1 if form_data.weather == "madrid" else 0,
        
        "target_temperature": 1 if form_data.target_variable == "Zone Air Temperature" else 0,
        "target_heating": 1 if form_data.target_variable == "Zone Air System Sensible Heating Energy" else 0,
        "target_cooling": 1 if form_data.target_variable == "Zone Air System Sensible Cooling Energy" else 0,
    }
    
    # 2. Convert to a DataFrame (this preserves column names if your model was trained on a DataFrame)
    input_df = pd.DataFrame([features])
    
    return input_df

