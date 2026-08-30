from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.firms_service import get_firms_anomalies
from services.classifier_service import classify_anomaly


class Anomaly(BaseModel):
    id: int
    latitude: float
    longitude: float
    confidence: int = Field(ge=0, le=100)
    satellite: str
    instrument: str
    date: str
    time: str
    frp: float
    brightness: float
    daynight: str
    type: str
    status: str
    classification: str
    classification_confidence: float
    land_cover: str
    risk: str


app = FastAPI(title="IgnisVision Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
       "https://ignisvision-frontend-lkgs52ino-tech-titans-5cec.vercel.app",
        
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "IgnisVision backend is running"}


@app.get("/api/anomalies", response_model=list[Anomaly])
def get_anomalies():
    return get_firms_anomalies()


@app.get("/api/anomalies/{anomaly_id}", response_model=Anomaly)
def get_anomaly(anomaly_id: int):
    anomalies = get_firms_anomalies()

    for anomaly in anomalies:
        if anomaly["id"] == anomaly_id:
            classifier_result = classify_anomaly(anomaly)
            anomaly.update(classifier_result)
            return anomaly

    raise HTTPException(
        status_code=404,
        detail="Anomaly not found",
    )


@app.get("/api/anomalies/count")
def get_anomaly_count():
    return {"count": len(get_anomalies())}


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}