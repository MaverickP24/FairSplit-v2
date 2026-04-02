import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import ingest, survey, allocate, metrics, dummy

app = FastAPI(title="FairSplit API", version="1.0.0")

# In production, set ALLOWED_ORIGINS to your Vercel frontend URL
# e.g. "https://fairsplit.vercel.app,http://localhost:5173"
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in [ingest, survey, allocate, metrics, dummy]:
    app.include_router(r.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "cors_origins": allowed_origins}
