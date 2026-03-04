"""Tests for revenue cache (tenant-scoped keys and invalidation)."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.cache import invalidate_revenue_cache, invalidate_revenue_cache_for_properties


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
