import json
import logging
import redis.asyncio as redis
from typing import Dict, Any, List
import os

# Initialize Redis client (typically configured centrally).
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
logger = logging.getLogger(__name__)

async def get_revenue_summary(property_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Fetches revenue summary, utilizing caching to improve performance.
    Cache key is tenant-scoped to prevent cross-tenant data leakage.
    """
    cache_key = f"revenue:{tenant_id}:{property_id}"
    
    # Try to get from cache
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Revenue calculation is delegated to the reservation service.
    from app.services.reservations import calculate_total_revenue
    
    # Calculate revenue
    result = await calculate_total_revenue(property_id, tenant_id)
    
    # Cache the result for 5 minutes
    await redis_client.setex(cache_key, 300, json.dumps(result))
    
    return result


async def invalidate_revenue_cache(tenant_id: str, property_id: str) -> bool:
    """
    Invalidate the revenue cache for a given tenant and property.
    Call this when reservations for this property are created, updated, or
    deleted (or when total_amount changes) so the dashboard shows fresh totals.
    """
    try:
        cache_key = f"revenue:{tenant_id}:{property_id}"
        await redis_client.delete(cache_key)
        logger.debug("Invalidated revenue cache for tenant %s property %s", tenant_id, property_id)
        return True
    except Exception as e:
        logger.warning("Failed to invalidate revenue cache: %s", e)
        return False


async def invalidate_revenue_cache_for_properties(tenant_id: str, property_ids: List[str]) -> int:
    """
    Invalidate revenue cache for multiple properties (e.g. after bulk sync).
    Returns the number of keys invalidated.
    """
    count = 0
    for property_id in property_ids:
        if await invalidate_revenue_cache(tenant_id, property_id):
            count += 1
    return count
