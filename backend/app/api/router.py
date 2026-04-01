from fastapi import APIRouter

from app.api.routes import chemistry, molecular_probe, planet, quantum, simulation, spectrum

api_router = APIRouter()
api_router.include_router(planet.router, tags=["planet"])
api_router.include_router(chemistry.router, tags=["chemistry"])
api_router.include_router(quantum.router, tags=["quantum"])
api_router.include_router(molecular_probe.router, tags=["molecular-probe"])
api_router.include_router(spectrum.router, tags=["spectrum"])
api_router.include_router(simulation.router, tags=["simulation"])
