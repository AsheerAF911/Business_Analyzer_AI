from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.reports import router as reports_router

from app.database import engine
from app.models import Base


app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(reports_router)


@app.get("/")
def root():
    return {"message": "Business AI API is running"}