from doctest import debug

from fastapi import FastAPI

app = FastAPI(title="Energy-Performance Building Simulation Machine Learning Engine")
# Define the path where the model is saved

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/prueba")
async def otra():
    return {"Mensaje de prueba"}

