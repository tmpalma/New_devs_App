"""
Local Postgres data layer for when Supabase is not configured.
Used by SecureClient for properties and reservations so local Docker has real data.
"""
import logging
from typing import Any, Dict, List, Optional

import asyncpg

from ..config import settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        dsn = settings.database_url
        _pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5, command_timeout=10)
        logger.info("Local Postgres pool created (Challenge mode with real data)")
    return _pool


def _row_to_dict(row: asyncpg.Record) -> Dict[str, Any]:
    return {k: v for k, v in row.items()}


async def get_properties(tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Fetch properties for a tenant from local Postgres. Returns list of dicts like Supabase."""
    try:
        pool = await _get_pool()
        conditions = ["tenant_id = $1"]
        params: List[Any] = [tenant_id]
        idx = 2
        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                if key == "city":
                    if isinstance(value, list):
                        conditions.append(f"city = ANY(${idx}::text[])")
                        params.append(value)
                    else:
                        conditions.append(f"city = ${idx}")
                        params.append(value)
                    idx += 1
                elif key in ("is_active", "is_grouped", "status"):
                    conditions.append(f'"{key}" = ${idx}')
                    params.append(value)
                    idx += 1
        where = " AND ".join(conditions)
        async with pool.acquire() as conn:
            rows = await conn.fetch(f'SELECT * FROM properties WHERE {where}', *params)
        data = [_row_to_dict(r) for r in rows]
        logger.info(f"Local Postgres: found {len(data)} properties for tenant {tenant_id}")
        return data
    except Exception as e:
        logger.error(f"Local Postgres get_properties failed: {e}")
        return []


async def get_reservations(tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Fetch reservations for a tenant from local Postgres. Returns list of dicts like Supabase."""
    try:
        pool = await _get_pool()
        conditions = ["tenant_id = $1"]
        params: List[Any] = [tenant_id]
        idx = 2
        if filters:
            for key, value in filters.items():
                if value is None:
                    continue
                if key == "property_id":
                    conditions.append(f"property_id = ${idx}")
                    params.append(value)
                    idx += 1
                elif key == "status":
                    conditions.append(f"status = ${idx}")
                    params.append(value)
                    idx += 1
                elif key == "check_in_date":
                    conditions.append(f"check_in_date >= ${idx}")
                    params.append(value)
                    idx += 1
                elif key == "check_out_date":
                    conditions.append(f"check_out_date <= ${idx}")
                    params.append(value)
                    idx += 1
                else:
                    conditions.append(f'"{key}" = ${idx}')
                    params.append(value)
                    idx += 1
        where = " AND ".join(conditions)
        async with pool.acquire() as conn:
            rows = await conn.fetch(f'SELECT * FROM reservations WHERE {where}', *params)
        data = [_row_to_dict(r) for r in rows]
        logger.info(f"Local Postgres: found {len(data)} reservations for tenant {tenant_id}")
        return data
    except Exception as e:
        logger.error(f"Local Postgres get_reservations failed: {e}")
        return []
