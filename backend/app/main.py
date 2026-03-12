from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import xero, myob, organisations

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FP&A Dream API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(organisations.router)
app.include_router(xero.router)
app.include_router(myob.router)


@app.get("/health")
def health():
    return {"status": "ok"}
