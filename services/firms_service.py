import csv
import io
import os

import geopandas as gpd
import requests
from dotenv import load_dotenv


load_dotenv()

FIRMS_MAP_KEY = os.getenv("FIRMS_MAP_KEY")

FIRMS_URL = (
    "https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
    f"{FIRMS_MAP_KEY}/MODIS_NRT/68,6,98,36/5"
)

INDIA_BOUNDARY = gpd.read_file(
    "data/boundaries/india.geojson"
).dissolve()


def calculate_risk(frp: float, brightness: float) -> str:
    """
    Temporary heuristic risk score.

    This is NOT an ML classifier.
    It uses FIRMS FRP and brightness only.
    """

    if frp >= 20 or brightness >= 330:
        return "HIGH"

    if frp >= 10 or brightness >= 315:
        return "MEDIUM"

    return "LOW"


def get_firms_anomalies():
    response = requests.get(FIRMS_URL, timeout=10)
    response.raise_for_status()

    reader = csv.DictReader(io.StringIO(response.text))

    raw_anomalies = []

    for index, row in enumerate(reader, start=1):
        frp = float(row["frp"])
        brightness = float(row["brightness"])

        raw_anomalies.append(
            {
                "id": index,
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "confidence": int(row["confidence"]),
                "satellite": row["satellite"],
                "instrument": row["instrument"],
                "date": row["acq_date"],
                "time": row["acq_time"],
                "frp": frp,
                "brightness": brightness,
                "daynight": row["daynight"],
                "type": "Thermal Anomaly",
                "status": "Active",

                # Classifier contract.
                # These remain placeholders until a real
                # classifier/model is implemented.
                "classification": "Under Analysis",
                "classification_confidence": 0.0,
                "land_cover": "Under Analysis",

                # Temporary FRP + brightness heuristic.
                # This is NOT an ML prediction.
                "risk": calculate_risk(frp, brightness),
            }
        )

    points = gpd.GeoDataFrame(
        raw_anomalies,
        geometry=gpd.points_from_xy(
            [item["longitude"] for item in raw_anomalies],
            [item["latitude"] for item in raw_anomalies],
        ),
        crs="EPSG:4326",
    )

    inside_india = points.geometry.within(
        INDIA_BOUNDARY.geometry.iloc[0]
    )

    filtered = points[inside_india].drop(columns="geometry")

    records = filtered.to_dict("records")

    for new_id, record in enumerate(records, start=1):
        record["id"] = new_id

    return records