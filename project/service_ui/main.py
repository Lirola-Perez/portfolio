from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Annotated
import os

storage_path = os.getenv("STORAGE_PATH", "/common_storage/output")
model_path = os.path.join(storage_path,"model.pkl")

app = FastAPI(title="Energy-Performance Building Simulation Machine Learning Engine")
templates = Jinja2Templates(directory="templates")

class PredictionInput(BaseModel):
    weather: str
    target_variable: str
    area: float = Field(..., gt=0, description="Area of the room or zone.")
    volume: float = Field(..., gt=0, description="Volume of the room or zone.")

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
    
    prediction_result = round(form_data.area * 0.45 + form_data.volume * 0.12, 2)

    return templates.TemplateResponse(request=request,name="index.html",context={
        "request": request,
        "prediction": prediction_result,
        # pass form_data back to keep fields filled out
        "area": form_data.area,
        "volume": form_data.volume,
        "weather": form_data.weather,
        "target": form_data.target_variable
    })

