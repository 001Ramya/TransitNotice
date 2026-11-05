from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import settings
from app.database import SessionLocal
from app.services.demo_seed import seed_demo_data
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.demo_mode:
        with SessionLocal() as session:
            seed_demo_data(session)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="TransitNotice API",
    version="1.0.0",
    description="Tracks official public transport service advisories with visible freshness and provenance.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router, prefix="/api")
