import json
import os
from pathlib import Path
from typing import Annotated
from supabase import Client, create_client

import joblib
import pandas as pd
import tensorflow as tf
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Get the directory where main.py is currently located
BASE_DIR = Path(__file__).resolve().parent

# 1. Force Pandas to show all columns instead of hiding them with "..."
pd.set_option('display.max_columns', None)

# 2. Force Pandas to show wide lines so it doesn't wrap awkwardly
pd.set_option('display.width', 1000)

# 3. (Optional) Show all rows if it's cutting off vertically too
pd.set_option('display.max_rows', None)

STORAGE_PATH = os.getenv("STORAGE_PATH", "/common_storage/")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "/common_storage/output")
SUPABASE_URL = os.getenv("SUPABASE_URL", "Missing_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "Missing_SUPABASE_KEY")

model_path = os.path.join(STORAGE_PATH,"model.keras")
scaler_input_path = os.path.join(STORAGE_PATH,"scaler_x.pkl")
scaler_output_path = os.path.join(STORAGE_PATH,"scaler_y.pkl")
columns_path = os.path.join(OUTPUT_PATH,"column_list.json")


# 1. Initialize Supabase using your environment variables
supabase: Client = create_client(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

# CONDITIONAL: used for handle CI Pipeline tests 
if os.path.exists(columns_path):
    with open(columns_path, "r") as f:
        training_columns = json.load(f)
else:
    # Safe mock fallback for CI / testing when upstream artifacts aren't generated yet
    training_columns = [
        "Area", 
        "Volume", 
        "Thickness", 
        "Conductivity", 
        "Weather_Madrid", 
        "Weather_Potsdam", 
        "Variable_Cooling Zone Relative Humidity [%]", 
        "Variable_Cooling Zone Temperature [C]", 
        "Variable_Des Cool Mass Flow [kg/s]", 
        "Variable_Des Heat Load [W]", 
        "Variable_Des Heat Mass Flow [kg/s]", 
        "Variable_Des Sens Cool Load [W]", 
        "Variable_Heating Zone Relative Humidity [%]", 
        "Variable_Heating Zone Temperature [C]"
    ]

app = FastAPI(title="Energy-Performance Building Simulation Machine Learning Engine")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Needed form for calculations
class PredictionInput(BaseModel):
    Weather: str
    Target_variable: str
    Area: float = Field(..., gt=0, description="Area of the room or zone.")
    Height: float = Field(..., gt=0, description="Height of the room or zone.")
    Conductivity: float
    Thickness: float
    
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    html = templates.TemplateResponse(request=request,name="index.html",context={"request":request, "prediction":None})
    return html

@app.post("/", response_class=HTMLResponse)
async def calculate_prediction(
    request: Request,
    # FastAPI automatically maps the HTML form data into the pydantic model.
    form_data: Annotated[PredictionInput, Form()]
):
    # Pydantic validates Area and volume are valid floats > 0
    volume = form_data.Area * form_data.Height

    # Taking the selected input vector for the prediction
    data_input = data_preparation(form_data,volume,columns_order=training_columns)
    #print(data_input)
    #print(training_columns)

    # Applying the trained scalers:
    scaler_input = joblib.load(scaler_input_path) if os.path.exists(scaler_input_path) else None
    scaler_output = joblib.load(scaler_output_path) if os.path.exists(scaler_output_path) else None
    if scaler_input:
        data_input = scaler_input.transform(data_input)

    # Applying the trained model:
    model = use_model()
    if model:
        prediction_result = model.predict(data_input)[0]
        # 2. If it's a 1D array or list, ensure it's 2D for the scaler:
        if scaler_output:
            if len(prediction_result.shape) == 1:
                prediction_result = prediction_result.reshape(1, -1)
            prediction_result = scaler_output.inverse_transform(prediction_result)
    else:
        print("FAKE PREDICTION!")
        prediction_result = round(form_data.Area * 0.45 + form_data.Height * 0.12, 2)

    print(f"{prediction_result}")

    # Returning the prediction from the model:
    return templates.TemplateResponse(request=request,name="index.html",context={
        "Request": request,
        "Prediction": prediction_result,
        # pass form_data back to keep fields filled out
        "Area": form_data.Area,
        "Height": form_data.Height,
        "Volume": volume,
        "Weather": form_data.Weather,
        "Target": form_data.Target_variable,
        "Thickness": form_data.Thickness,
        "Conductivity": form_data.Conductivity
    })

def use_model():
    """This function gathers the trained model ready to use for predictions."""
    if not os.path.exists(model_path):
        print(f"No model found at {model_path}. Please train or upload one first.")
        return None
    
    try:
        model = tf.keras.models.load_model(os.path.join(STORAGE_PATH, 'model.keras'))
        print(f"Model successfully loaded from {model_path}.")
        return model
    
    except (FileNotFoundError, OSError) as e:
        print(f"Critical: Model file missing or unreadable at {model_path}: {e}")
        return None

    except (ValueError, KeyError) as e:
        print(f"Critical: Model file is corrupted or structurally incompatible: {e}")
        return None

    except Exception as e:  # noqa: BLE001
        # If TensorFlow throws an unexpected internal C++ runtime exception 
        # that doesn't inherit from standard Python file/value errors, 
        # use
        print(f"Unexpected TensorFlow internal error loading model: {e}")
        return None

def data_preparation(form_data:Annotated, volume:float, columns_order=training_columns):
    """This function maps and prepares the input data for the model.
        The data should be a vector with same dimension as the training
        set of the model."""
    feature_dict = {col: 0.0 for col in list(columns_order)}

    if "Area" in feature_dict:
        feature_dict["Area"] = form_data.Area
    if "Volume" in feature_dict:
        feature_dict["Volume"] = volume
    if "Conductivity" in feature_dict:
        feature_dict["Conductivity"] = form_data.Conductivity
    if "Thickness" in feature_dict:
        feature_dict["Thickness"] = form_data.Thickness
        
    # Handle Weather or categorical columns if they exist in your training columns
    weather_col = f"Weather_{form_data.Weather}"
    if weather_col in feature_dict:
        feature_dict[weather_col] = 1.0
        
    target_col = f"{form_data.Target_variable}"
    if target_col in feature_dict:
        feature_dict[target_col] = 1.0
        print(f"Successfully activated target flag: {target_col} = 1.0")
    
    # 2. Convert to a DataFrame (this preserves column names if your model was trained on a DataFrame)
    input_df = pd.DataFrame([feature_dict])
    
    return input_df

