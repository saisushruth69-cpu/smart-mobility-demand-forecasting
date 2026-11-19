
from flask import Flask, request, jsonify, render_template
import pandas as pd
import joblib
import os


# --------------------------------
# 1. PROJECT PATH
# --------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)


# --------------------------------
# 2. LOAD SAVED ML MODELS
# --------------------------------

demand_data = joblib.load(
    os.path.join(BASE_DIR, "bike_demand_model.pkl")
)

cluster_data = joblib.load(
    os.path.join(BASE_DIR, "bike_clustering_model.pkl")
)

# Extract trained models and features

demand_model = demand_data["model"]
demand_features = demand_data["features"]

scaler = cluster_data["scaler"]
kmeans = cluster_data["kmeans"]
cluster_features = cluster_data["features"]
cluster_mapping = cluster_data["cluster_mapping"]


# --------------------------------
# 3. LOAD ORIGINAL DATASETS
# --------------------------------

hour_data = pd.read_csv(
    os.path.join(BASE_DIR, "dataset", "hour.csv")
)

day_data = pd.read_csv(
    os.path.join(BASE_DIR, "dataset", "day.csv")
)


# --------------------------------
# 4. HOME PAGE
# --------------------------------

@app.route("/")
def home():

    return render_template("index.html")


# --------------------------------
# 5. PREDICTION API
# --------------------------------

@app.route("/predict", methods=["POST"])
def predict():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "No input data received"
            }), 400

        # Get user input

        year = int(data["year"])
        season = int(data["season"])
        month = int(data["month"])
        hour = int(data["hour"])
        holiday = int(data["holiday"])
        weekday = int(data["weekday"])
        workingday = int(data["workingday"])
        weathersit = int(data["weathersit"])

        temp = float(data["temp"])
        atemp = float(data["atemp"])
        hum = float(data["hum"])
        windspeed = float(data["windspeed"])

        # Convert year into dataset encoding

        if year == 2011:
            yr = 0

        elif year == 2012:
            yr = 1

        elif year in [0, 1]:
            yr = year

        else:
            return jsonify({
                "error": "Year must be 2011 or 2012"
            }), 400

        # Validate input

        if season not in [1, 2, 3, 4]:
            raise ValueError("Season must be between 1 and 4")

        if month not in range(1, 13):
            raise ValueError("Month must be between 1 and 12")

        if hour not in range(0, 24):
            raise ValueError("Hour must be between 0 and 23")

        if weekday not in range(0, 7):
            raise ValueError("Weekday must be between 0 and 6")

        if weathersit not in range(1, 5):
            raise ValueError("Weather situation must be between 1 and 4")

        if holiday not in [0, 1] or workingday not in [0, 1]:
            raise ValueError("Holiday and workingday must be 0 or 1")

        for value in [temp, atemp, hum, windspeed]:

            if not 0 <= value <= 1:
                raise ValueError(
                    "Weather values must be between 0 and 1"
                )

        # Prepare demand model input

        demand_input = pd.DataFrame(
            0,
            index=[0],
            columns=demand_features,
            dtype=float
        )

        demand_input["yr"] = yr
        demand_input["temp"] = temp
        demand_input["atemp"] = atemp
        demand_input["hum"] = hum
        demand_input["windspeed"] = windspeed

        # One-hot encoding

        def set_dummy(column, value):

            if column in demand_input.columns:
                demand_input.loc[0, column] = value

        set_dummy("season_" + str(season), 1)
        set_dummy("mnth_" + str(month), 1)
        set_dummy("hr_" + str(hour), 1)
        set_dummy("holiday_" + str(holiday), 1)
        set_dummy("weekday_" + str(weekday), 1)
        set_dummy("workingday_" + str(workingday), 1)
        set_dummy("weathersit_" + str(weathersit), 1)

        # Predict bicycle demand

        prediction = demand_model.predict(demand_input)[0]

        prediction = max(0, round(float(prediction)))

        # Prepare clustering input

        cluster_input = pd.DataFrame(
            [[
                season,
                hour,
                workingday,
                weathersit,
                temp,
                atemp,
                hum,
                windspeed
            ]],
            columns=cluster_features
        )

        # Scale clustering input

        scaled_input = scaler.transform(cluster_input)

        # Predict demand cluster

        cluster_number = int(
            kmeans.predict(scaled_input)[0]
        )

        demand_profile = cluster_mapping[cluster_number]

        # Capacity recommendation

        if demand_profile == "High Demand":

            recommendation = "Increase Bicycle Availability"

        elif demand_profile == "Low Demand":

            recommendation = "Reduce Bicycle Availability"

        else:

            recommendation = "Maintain Bicycle Availability"

        # Return prediction results

        return jsonify({

            "predicted_demand": prediction,

            "cluster_number": cluster_number,

            "demand_profile": demand_profile,

            "recommendation": recommendation,

            "status": "Success"

        })

    except KeyError as e:

        return jsonify({
            "error": "Missing input: " + str(e)
        }), 400

    except ValueError as e:

        return jsonify({
            "error": str(e)
        }), 400

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# --------------------------------
# 6. DEMAND ANALYTICS API
# --------------------------------

@app.route("/api/analytics")
def analytics():

    try:

        # 1. Hourly average demand

        hourly = (
            hour_data.groupby("hr")["cnt"]
            .mean()
            .round(2)
            .reset_index()
        )

        # 2. Monthly average demand

        monthly = (
            day_data.groupby("mnth")["cnt"]
            .mean()
            .round(2)
            .reset_index()
        )

        # 3. Weekday average demand

        weekday = (
            day_data.groupby("weekday")["cnt"]
            .mean()
            .round(2)
            .reset_index()
        )

        # 4. Weather-wise average demand

        weather = (
            day_data.groupby("weathersit")["cnt"]
            .mean()
            .round(2)
            .reset_index()
        )

        # Send analytics data

        return jsonify({

            "hourly_demand":
                hourly.to_dict(orient="records"),

            "monthly_demand":
                monthly.to_dict(orient="records"),

            "weekday_demand":
                weekday.to_dict(orient="records"),

            "weather_demand":
                weather.to_dict(orient="records")

        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# --------------------------------
# 7. RUN FLASK APPLICATION
# --------------------------------

if __name__ == "__main__":

    app.run(debug=True)
