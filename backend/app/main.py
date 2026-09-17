from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.reports import router as reports_router
from app.database import engine
from app.models import Base
import os
from app.routes.ask import router as ask_router
from app.routes.business_data import (
    router as business_data_router,
)

app = FastAPI()

Base.metadata.create_all(bind=engine)

frontend_origin = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5173",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(reports_router)

app.include_router(ask_router)

app.include_router(
    business_data_router
)


@app.get("/")
def root():
    return {"message": "Business AI API is running"}