"""
FairSplit — FastAPI backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import ingest, survey, allocate, metrics, dummy

app = FastAPI(title="FairSplit API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router,  prefix="/api")
app.include_router(survey.router,  prefix="/api")
app.include_router(allocate.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(dummy.router,   prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}
