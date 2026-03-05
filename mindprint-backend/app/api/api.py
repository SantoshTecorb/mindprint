from fastapi import APIRouter
from .endpoints import memory, rentals, telemetry, consult, discovery, integrations, whatsapp

api_router = APIRouter()
api_router.include_router(memory.router)
api_router.include_router(rentals.router)
api_router.include_router(telemetry.router)
api_router.include_router(consult.router)
api_router.include_router(discovery.router)
api_router.include_router(integrations.router)
api_router.include_router(whatsapp.router)
