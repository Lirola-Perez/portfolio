import pytest
from service_ui.main import app, data_preparation
from fastapi.testclient import TestClient
import pandas as pd

client = TestClient(app)

def test_read_incdex():
    response = client.get("/")
    assert response.status_code == 200
    assert "Energy Model Prediction" in response.text

def test_data_preparation_logic():
    # Mocking the form data object
    class MockForm:
        Area = 100.0
        Height = 3.0
        Conductivity = 0.04
        Thickness = 0.05
        Weather = "Madrid"
        Target_variable = "Variable_Cooling Zone Temperature [C]"

    dummy_columns = [
        "Area", "Volume", "Thickness", "Conductivity", 
        "Weather_Madrid", "Weather_Chicago", 
        "Variable_Cooling Zone Temperature [C]"
    ]

    form_data = MockForm()
    volume = form_data.Area * form_data.Height

    df = data_preparation(form_data=form_data,volume=volume,columns_order=dummy_columns)

    assert isinstance(df,pd.DataFrame)
    assert df.shape == (1,len(dummy_columns))
    assert df["Area"].iloc[0] == 100.0
    assert df["Volume"].iloc[0] == 300.0
    assert df["Weather_Madrid"].iloc[0] == 1.0
    assert df["Variable_Cooling Zone Temperature [C]"].iloc[0] == 1.0