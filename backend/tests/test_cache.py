"""Tests for revenue cache (tenant-scoped keys and invalidation)."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.cache import invalidate_revenue_cache


@pytest.mark.asyncio
async def test_invalidate_revenue_cache_success():
    """invalidate_revenue_cache calls redis delete with correct key and returns True."""
    mock_delete = AsyncMock(return_value=1)
    with patch("app.services.cache.redis_client", delete=mock_delete):
        result = await invalidate_revenue_cache("t1", "p1")
    assert result is True
    mock_delete.assert_called_once_with("revenue:t1:p1")
