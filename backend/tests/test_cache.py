"""Tests for revenue cache (tenant-scoped keys and invalidation)."""

import json
import pytest
from unittest.mock import AsyncMock, patch

from app.services.cache import (
    get_revenue_summary,
    invalidate_revenue_cache,
    invalidate_revenue_cache_for_properties,
)


@pytest.mark.asyncio
async def test_invalidate_revenue_cache_success():
    """invalidate_revenue_cache calls redis delete with correct key and returns True."""
    mock_delete = AsyncMock(return_value=1)
    with patch("app.services.cache.redis_client", delete=mock_delete):
        result = await invalidate_revenue_cache("t1", "p1")
    assert result is True
    mock_delete.assert_called_once_with("revenue:t1:p1")


@pytest.mark.asyncio
async def test_invalidate_revenue_cache_failure():
    """invalidate_revenue_cache returns False when Redis delete raises."""
    mock_delete = AsyncMock(side_effect=Exception("redis error"))
    with patch("app.services.cache.redis_client", delete=mock_delete):
        result = await invalidate_revenue_cache("t1", "p1")
    assert result is False
    mock_delete.assert_called_once_with("revenue:t1:p1")


@pytest.mark.asyncio
async def test_invalidate_revenue_cache_for_properties():
    """invalidate_revenue_cache_for_properties calls delete for each property and returns count."""
    mock_delete = AsyncMock(return_value=1)
    with patch("app.services.cache.redis_client", delete=mock_delete):
        result = await invalidate_revenue_cache_for_properties("t1", ["p1", "p2", "p3"])
    assert result == 3
    assert mock_delete.call_count == 3
    called_keys = [call[0][0] for call in mock_delete.call_args_list]
    assert set(called_keys) == {"revenue:t1:p1", "revenue:t1:p2", "revenue:t1:p3"}


@pytest.mark.asyncio
async def test_get_revenue_summary_cache_hit():
    """get_revenue_summary returns cached value and does not call DB or setex."""
    cached_data = {
        "property_id": "p1",
        "tenant_id": "t1",
        "total": "200.00",
        "currency": "USD",
        "count": 5,
    }
    mock_get = AsyncMock(return_value=json.dumps(cached_data))
    mock_setex = AsyncMock()
    mock_calculate = AsyncMock()
    with (
        patch("app.services.cache.redis_client", get=mock_get, setex=mock_setex),
        patch("app.services.reservations.calculate_total_revenue", mock_calculate),
    ):
        result = await get_revenue_summary("p1", "t1")
    assert result == cached_data
    mock_get.assert_called_once_with("revenue:t1:p1")
    mock_calculate.assert_not_called()
    mock_setex.assert_not_called()


@pytest.mark.asyncio
async def test_get_revenue_summary_cache_miss():
    """get_revenue_summary on cache miss calls calculate_total_revenue and caches result."""
    db_result = {
        "property_id": "p1",
        "tenant_id": "t1",
        "total": "100.00",
        "currency": "USD",
        "count": 2,
    }
    mock_get = AsyncMock(return_value=None)
    mock_setex = AsyncMock()
    mock_calculate = AsyncMock(return_value=db_result)
    with (
        patch("app.services.cache.redis_client", get=mock_get, setex=mock_setex),
        patch("app.services.reservations.calculate_total_revenue", mock_calculate),
    ):
        result = await get_revenue_summary("p1", "t1")
    assert result == db_result
    mock_get.assert_called_once_with("revenue:t1:p1")
    mock_calculate.assert_called_once_with("p1", "t1")
    mock_setex.assert_called_once_with("revenue:t1:p1", 300, json.dumps(db_result))
