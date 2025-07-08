from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import canonical_player
from routers import ingest
from ml_service import ml_service
from database import SessionLocal

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Statcast AI API is running!"}

# Only include the new canonical player router
app.include_router(canonical_player.router)
app.include_router(ingest.router)

@app.on_event("startup")
def load_ml_weights():
    db = SessionLocal()
    ml_service.load_level_weights(db)
    db.close()
