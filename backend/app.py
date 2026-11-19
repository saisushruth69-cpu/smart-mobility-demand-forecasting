from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import pandas as pd
import joblib
import os


# --------------------------------
# 1. PROJECT PATH
# --------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)


# --------------------------------
# 2. FASTAPI APPLICATION
# --------------------------------

app = FastAPI(
    title="Smart Mobility Demand Forecasting API",
    description="Bicycle demand prediction and capacity allocation",
    version="1.0"
)


# --------------------------------
# 3. STATIC FILES
# --------------------------------

app.mount(
    "/static",
    StaticFiles(
        directory=os.path.join(BASE_DIR, "static")
    ),
    name="static"
)


# --------------------------------
# 4. LOAD SAVED ML MODELS
# --------------------------------

demand_data = joblib.load(
    os.path.join(BASE_DIR, "bike_demand_model.pkl")
)

cluster_data = joblib.load(
    os.path.join(BASE_DIR, "bike_clustering_model.pkl")
)


demand_model = demand_data["model"]
demand_features = demand_data["features"]

scaler = cluster_data["scaler"]
kmeans = cluster_data["kmeans"]
cluster_features = cluster_data["features"]
cluster_mapping = cluster_data["cluster_mapping"]


# --------------------------------
# 5. LOAD ORIGINAL DATASETS
# --------------------------------

hour_data = pd.read_csv(
    os.path.join(BASE_DIR, "dataset", "hour.csv")
)

day_data = pd.read_csv(
    os.path.join(BASE_DIR, "dataset", "day.csv")
)


# --------------------------------
# 6. INPUT MODEL
# --------------------------------

class PredictionInput(BaseModel):

    year: int
    season: int
    month: int
    hour: int
    holiday: int
    weekday: int
    workingday: int
    weathersit: int

    temp: float
    atemp: float
    hum: float
    windspeed: float


# --------------------------------
# 7. HOME PAGE
# --------------------------------

@app.get("/", response_class=HTMLResponse)
def home():

    html_path = os.path.join(
        BASE_DIR,
        "templates",
        "index.html"
    )

    with open(html_path, "r", encoding="utf-8") as file:
        return file.read()


# --------------------------------
# 8. PREDICTION API
# --------------------------------

@app.post("/predict")
def predict(data: PredictionInput):

    try:

        # --------------------------------
        # Convert year
        # --------------------------------

        if data.year == 2011:
            yr = 0

        elif data.year == 2012:
            yr = 1

        elif data.year in [0, 1]:
            yr = data.year

        else:
            raise ValueError(
                "Year must be 2011 or 2012"
            )


        # --------------------------------
        # Validate input
        # --------------------------------

        if data.season not in [1, 2, 3, 4]:
            raise ValueError(
                "Season must be between 1 and 4"
            )

        if data.month not in range(1, 13):
            raise ValueError(
                "Month must be between 1 and 12"
            )

        if data.hour not in range(0, 24):
            raise ValueError(
                "Hour must be between 0 and 23"
            )

        if data.weekday not in range(0, 7):
            raise ValueError(
                "Weekday must be between 0 and 6"
            )

        if data.weathersit not in range(1, 5):
            raise ValueError(
                "Weather situation must be between 1 and 4"
            )

        if data.holiday not in [0, 1]:
            raise ValueError(
                "Holiday must be 0 or 1"
            )

        if data.workingday not in [0, 1]:
            raise ValueError(
                "Workingday must be 0 or 1"
            )


        # --------------------------------
        # Validate weather values
        # --------------------------------

        for value in [
            data.temp,
            data.atemp,
            data.hum,
            data.windspeed
        ]:

            if not 0 <= value <= 1:

                raise ValueError(
                    "Weather values must be between 0 and 1"
                )


        # --------------------------------
        # Prepare demand model input
        # --------------------------------

        demand_input = pd.DataFrame(
            0,
            index=[0],
            columns=demand_features,
            dtype=float
        )

        demand_input["yr"] = yr
        demand_input["temp"] = data.temp
        demand_input["atemp"] = data.atemp
        demand_input["hum"] = data.hum
        demand_input["windspeed"] = data.windspeed


        # --------------------------------
        # One-hot encoding
        # --------------------------------

        def set_dummy(column, value):

            if column in demand_input.columns:

                demand_input.loc[0, column] = value


        set_dummy(
            "season_" + str(data.season),
            1
        )

        set_dummy(
            "mnth_" + str(data.month),
            1
        )

        set_dummy(
            "hr_" + str(data.hour),
            1
        )

        set_dummy(
            "holiday_" + str(data.holiday),
            1
        )

        set_dummy(
            "weekday_" + str(data.weekday),
            1
        )

        set_dummy(
            "workingday_" + str(data.workingday),
            1
        )

        set_dummy(
            "weathersit_" + str(data.weathersit),
            1
        )


        # --------------------------------
        # Predict bicycle demand
        # --------------------------------

        prediction = demand_model.predict(
            demand_input
        )[0]

        prediction = max(
            0,
            round(float(prediction))
        )


        # --------------------------------
        # Prepare clustering input
        # --------------------------------

        cluster_input = pd.DataFrame(
            [[
                data.season,
                data.hour,
                data.workingday,
                data.weathersit,
                data.temp,
                data.atemp,
                data.hum,
                data.windspeed
            ]],
            columns=cluster_features
        )


        # --------------------------------
        # Scale clustering input
        # --------------------------------

        scaled_input = scaler.transform(
            cluster_input
        )


        # --------------------------------
        # Predict demand cluster
        # --------------------------------

        cluster_number = int(
            kmeans.predict(
                scaled_input
            )[0]
        )

        demand_profile = cluster_mapping[
            cluster_number
        ]


        # --------------------------------
        # Capacity recommendation
        # --------------------------------

        if demand_profile == "High Demand":

            recommendation = (
                "Increase Bicycle Availability"
            )

        elif demand_profile == "Low Demand":

            recommendation = (
                "Reduce Bicycle Availability"
            )

        else:

            recommendation = (
                "Maintain Bicycle Availability"
            )


        # --------------------------------
        # Return result
        # --------------------------------

        return {

            "predicted_demand": prediction,

            "cluster_number": cluster_number,

            "demand_profile": demand_profile,

            "recommendation": recommendation,

            "status": "Success"

        }


    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------
# 9. DEMAND ANALYTICS API
# --------------------------------

@app.get("/api/analytics")
def analytics():

    try:

        # Hourly average demand

        hourly = (
            hour_data
            .groupby("hr")["cnt"]
            .mean()
            .round(2)
            .reset_index()
        )


        # Monthly average demand

        monthly = (
            day_data
            .groupby("mnth")["cnt"]
            .mean()
            .round(2)
            .reset_index()
        )


        # Weekday average demand

        weekday = (
            day_data
            .groupby("weekday")["cnt"]
            .mean()
            .round(2)
            .reset_index()
        )


        # Weather-wise average demand

        weather = (
            day_data
            .groupby("weathersit")["cnt"]
            .mean()
            .round(2)
            .reset_index()
        )


        return {

            "hourly_demand":
                hourly.to_dict(
                    orient="records"
                ),

            "monthly_demand":
                monthly.to_dict(
                    orient="records"
                ),

            "weekday_demand":
                weekday.to_dict(
                    orient="records"
                ),

            "weather_demand":
                weather.to_dict(
                    orient="records"
                )

        }


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )