from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import joblib
import pandas as pd
from pydantic import BaseModel, Field
from typing import Annotated
import os
import json

storage_path = os.getenv("STORAGE_PATH", "/common_storage/")
output_path = os.getenv("OUTPUT_PATH", "/common_storage/output")
model_path = os.path.join(storage_path,"model.pkl")
columns_path = os.path.join(output_path,"column_list.json")
with open(columns_path,"r") as f:
    training_columns = json.load(f)
scaler_input_path = os.path.join(output_path,"scaler_input.pkl")
scaler_output_path = os.path.join(output_path,"scaler_output.pkl")
#training_columns = joblib.load(columns_path) if os.path.exists(columns_path) else []

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
    
    volume = form_data.area * form_data.height

    print(training_columns)
    data_input = data_preparation(form_data,volume,columns_order=training_columns)

    scaler_input = joblib.load(scaler_input_path) if os.path.exists(scaler_input_path) else None
    scaler_output = joblib.load(scaler_output_path) if os.path.exists(scaler_output_path) else None
    if scaler_input:
        data_input = scaler_input.transform(data_input)
    print(data_input)
    model = use_model()
    if model:
        prediction_result = model.predict(data_input)[0]
        # 2. If it's a 1D array or list, ensure it's 2D for the scaler:
        if scaler_output:
            if len(prediction_result.shape) == 1:
                prediction_result = prediction_result.reshape(1, -1)
            prediction_result = scaler_output.inverse_transform(prediction_result)
    else:
        print(f"FAKE PREDICTION!")
        prediction_result = round(form_data.area * 0.45 + form_data.height * 0.12, 2)

    print(f"{volume}, {prediction_result}") 

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

def data_preparation(form_data:Annotated, volume:float, columns_order=training_columns):

    feature_dict = {col.lower(): 0.0 for col in list(columns_order)}

    if "area" in feature_dict:
        feature_dict["area"] = form_data.area
    if "volume" in feature_dict:
        feature_dict["volume"] = volume
    if "conductivity" in feature_dict:
        feature_dict["conductivity"] = form_data.conductivity
    if "thickness" in feature_dict:
        feature_dict["thickness"] = form_data.thickness
        
    # Handle weather or categorical columns if they exist in your training columns
    weather_col = f"weather_{form_data.weather}"
    if weather_col in feature_dict:
        feature_dict[weather_col] = 1.0
        
    target_col = f"{form_data.target_variable}"
    if target_col in feature_dict:
        feature_dict[target_col] = 1.0
    
    # 2. Convert to a DataFrame (this preserves column names if your model was trained on a DataFrame)
    input_df = pd.DataFrame([feature_dict])
    
    return input_df

