import pandas as pd
from fastapi.testclient import TestClient
from main import app, data_preparation  # type: ignore
from supabase import Client, create_client
import os

client = TestClient(app)

SUPABASE_URL = os.getenv("SUPABASE_URL", "Missing_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "Missing_SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_read_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "Energy Model Prediction" in response.text

def test_data_preparation_logic():
    # Mocking the form data object
    class MockForm:
        # Area = 100.0
        Height = 3.0
        Conductivity = 0.04
        Thickness = 0.05
        Weather = "Madrid"
        Target_variable = "Variable_Cooling Zone Temperature [C]"

    dummy_columns = [
        # "Area", 
        # "Volume", 
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

    form_data = MockForm()
    Area = 100
    volume = Area * form_data.Height

    df,_ = data_preparation(form_data=form_data,volume=volume,columns_order=dummy_columns)

    assert isinstance(df,pd.DataFrame)
    assert df.shape == (1,len(dummy_columns))
    # assert df["Area"].iloc[0] == 100.0
    # assert df["Volume"].iloc[0] == 300.0
    assert df["Weather_Madrid"].iloc[0] == 1.0
    assert df["Variable_Cooling Zone Temperature [C]"].iloc[0] == 1.0