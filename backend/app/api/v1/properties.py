from fastapi import APIRouter, Depends
from typing import Optional

from ...core.auth import authenticate_request
from ...core.secure_client import SecureClient

router = APIRouter()


@router.get("/properties")
async def get_properties(
    current_user=Depends(authenticate_request),
    city: Optional[str] = None,
    status: Optional[str] = None,
):
    """
    Get properties for the current tenant.
    Requires authentication; returns only properties for the authenticated user's tenant.
    Optional query params: city, status.
    """
    filters = {}
    if city is not None:
        filters["city"] = city
    if status is not None:
        filters["status"] = status
    properties = await SecureClient.get_properties(filters or None)
    tenant_id = getattr(current_user, "tenant_id", None)
    # Return both 'data' (for frontend getProperties) and 'properties' (compatibility); include tenant_id for debugging
    return {
        "data": properties,
        "properties": properties,
        "total": len(properties),
        "tenant_id": tenant_id,
    }
