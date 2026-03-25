from fastapi import APIRouter, Depends

from ..services.providers import ProviderRegistry
from .deps import get_provider_registry

router = APIRouter()


@router.get("/sites")
async def list_sites(registry: ProviderRegistry = Depends(get_provider_registry)):
    return {"sites": registry.list_sites()}
