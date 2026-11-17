import json
import os
from pathlib import Path
from typing import Annotated
import pandas as pd
import tensorflow as tf
import pickle
import asyncio
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from backend_linker import SupabaseStorage

# Get the directory where main.py is currently located
BASE_DIR = Path(__file__).resolve().parent

# 1. Force Pandas to show all columns instead of hiding them with "..."
pd.set_option('display.max_columns', None)

# 2. Force Pandas to show wide lines so it doesn't wrap awkwardly
pd.set_option('display.width', 1000)

# 3. (Optional) Show all rows if it's cutting off vertically too
pd.set_option('display.max_rows', None)

STORAGE_PATH = os.getenv("STORAGE_PATH", "/app/storage")
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "/app/storage/output")

model_path = os.path.join(STORAGE_PATH,"model.keras")
scaler_input_path = os.path.join(STORAGE_PATH,"scaler_x.pkl")
scaler_output_path = os.path.join(STORAGE_PATH,"scaler_y.pkl")
columns_path = os.path.join(OUTPUT_PATH,"column_list.json")
scaler_x_file_name = "scaler_x.pkl"
scaler_y_file_name = "scaler_y.pkl"
model_file_name = "model.keras"
column_file = "column_list.json"

# 1. Initialize Supabase using your environment variables
#supabase: Client = create_client(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)
supabase = SupabaseStorage()

app = FastAPI(title="Energy-Performance Building Simulation Machine Learning Engine")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Needed form for calculations
class PredictionInput(BaseModel):
    Weather: str
    Target_variable: str
    #Area: float = Field(..., gt=0, description="Area of the room or zone.")
    Height: float = Field(..., gt=0, description="Height of the room or zone.")
    Conductivity: float
    Thickness: float
    
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    print("ROUTE HIT: GET /")
    html = templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request":request, "Prediction":None})
    return html

@app.post("/", response_class=HTMLResponse)
async def calculate_prediction(
    request: Request,
    # FastAPI automatically maps the HTML form data into the pydantic model.
    form_data: Annotated[PredictionInput, Form()]
):
    print("ROUTE HIT: POST /", form_data.Target_variable)
    # Pydantic validates Area and volume are valid floats > 0
    # volume = form_data.Area * form_data.Height
    Area = 100
    volume = Area * form_data.Height
    training_columns = ["no values"]

    # --- DOWNLOADING COLUMN LIST -----
    print(f"PHASE 1: DOWNLOADING column list")
    training_columns = await asyncio.to_thread(
        _file_downloader_from_out_folder,
        "output",
        column_file)
    # -------
    
    print(f"PHASE 2: PREPARING the data")
    data_input = data_preparation(form_data,volume,columns_order=training_columns)
    #print(data_input)
    print(f"CHECK -> Training columns: {training_columns}")

    # -- DOWNLOADING THE SCALERS ---
    print(f"PHASE 3: Prepared data. DOWNLOADING the scalers")
    # retrieving from supabase, temporal folder+file, async-function and loading
    scaler_input = await asyncio.to_thread(
            _file_downloader_from_out_folder,
            "model",
            scaler_x_file_name)

    # retrieving from supabase, temporal folder+file, async-function and loading
    scaler_output = await asyncio.to_thread(
        _file_downloader_from_out_folder,
        "model",
        scaler_y_file_name)

    # CHECK POINT
    print(f"CHECK -> SCALER FILE TYPE: \n {type(scaler_input)}")
    print("scaler_input features:", getattr(scaler_input, "n_features_in_", "NOT FITTED"))
    print("scaler_output features:", getattr(scaler_output, "n_features_in_", "NOT FITTED"))
    print(scaler_input)
    # -------------------------------

    if data_input is not None:
        raw_x = data_input.to_numpy() if hasattr(data_input, "to_numpy") else data_input
        if scaler_input is not None and hasattr(scaler_input, "transform"):
            raw_x = scaler_input.transform(raw_x)

        # loading the model with async function:
        print(f"PHASE 4: DOWNLOADING the model")
        model = await asyncio.to_thread(use_model)
        if model is not None:
            # CHECK POINT
            print("model input/output shapes:", model.input_shape, model.output_shape)
            # ---- PREDICTION ----------------------
            print(f"PHASE 5: PREDICTION")
            prediction_result = model.predict(raw_x, verbose=0)[0]
            # 2. If it's a 1D array or list, ensure it's 2D for the scaler:
            if scaler_output is not None and hasattr(scaler_input, "transform"):
                if len(prediction_result.shape) == 1:
                    prediction_result = prediction_result.reshape(1, -1)
                prediction_result = scaler_output.inverse_transform(prediction_result)
        else:
            print("FAKE PREDICTION!")
            prediction_result = round(Area * 0.45 + form_data.Height * 0.12, 2)
    else:
        prediction_result = "Fail to predict"

    print(f"{prediction_result}")

    # Returning the prediction from the model:
    return templates.TemplateResponse(request=request,name="index.html",context={
        "Request": request,
        "Prediction": prediction_result,
        # pass form_data back to keep fields filled out
        #"Area": form_data.Area,
        "Height": form_data.Height,
        #"Volume": volume,
        "Weather": form_data.Weather,
        "Target": form_data.Target_variable,
        "Thickness": form_data.Thickness,
        "Conductivity": form_data.Conductivity
    })

def use_model():
    """This function gathers the trained model ready to use for predictions."""
    model_path = f"output/model/{model_file_name}"

    # Model .keras does not use pickle load:
    model_file = supabase.retrieve("output",f"model/{model_file_name}")
    model_file_final = _temp_container("model","model.keras")
    # writing directly in the created "empty" model.keras
    model_file_final.write_bytes(model_file)

    if not model_file_final:
        print(f"No model found at supabase folder {model_path}. Please train or upload one first.")
        return None
    
    try:
        model = tf.keras.models.load_model(model_file_final)
        print(f"Model successfully loaded from {model_path}.")
        return model
    
    except (FileNotFoundError, OSError) as e:
        print(f"Critical: Model file missing or unreadable at {model_path} in supabase: {e}")
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

def data_preparation(form_data:Annotated, volume:float, columns_order=None):
    """This function maps and prepares the input data for the model.
        The data should be a vector with same dimension as the training
        set of the model."""
    if columns_order is not None:
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
    else:
        return None

def _file_downloader_from_out_folder(folder_name,file_name):
    # retrieving from supabase, temporal folder+file, async-function and loading
    binary_file_downloaded = supabase.retrieve(main_folder="output", 
                                            file_name=f"{folder_name}/{file_name}")
    temp_file = _temp_container(folder_name,file_name)
    file = _file_loader(binary_file_downloaded, temp_file)
    return file

def _temp_container(folder_name:str,file_name= None):
        # Temporary folder in container:
        temp_dir = Path(f"/tmp/{folder_name}")
        temp_dir.mkdir(parents=True,exist_ok=True)
        if not file_name:
            return temp_dir
        return Path(temp_dir/file_name)

def _file_loader(data,temp_path):
    # takes the binary retrieved from supabase, writes it in file and loads the file as return
    if isinstance(data, (bytes,bytearray)):
        suffix = Path(temp_path).suffix
        if suffix == ".pkl":
            return pickle.loads(data)
        elif suffix == ".json":
            return json.loads(data.decode("utf-8"))
    else:
        return data

