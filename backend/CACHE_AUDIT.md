# Cache key audit (Phase 3)

Cache keys that include tenant (or user) context so data is not shared across tenants:

| Location | Key pattern | Tenant-scoped |
|----------|-------------|---------------|
| `app/services/cache.py` | `revenue:{tenant_id}:{property_id}` | Yes |
| `app/api/v1/company_settings.py` | `company_settings:{tenant_id}` | Yes |
| `app/api/v1/city_access_fast.py` | `city_access:v2:{tenant_id}:{user_id}`, `global_cities:v2:{tenant_id}` | Yes |
| `app/api/v1/users_lightning.py` | `users:lightning:{tenant_id}` | Yes |
| `app/api/v1/bootstrap.py` | `bootstrap:{user_id}:{tenant_id}`, `tenant:{tenant_id}` | Yes |
| `app/core/token_service.py` | `hostaway:{tenant_id}:{city}`, `stripe:*:{tenant_id}` | Yes when tenant_id present |
| `app/core/redis_cache.py` (GuestPortal) | `_make_key(..., tenant_id=...)` | Yes |

Keys that are **not** tenant-scoped (by design or to revisit):

| Location | Key pattern | Note |
|----------|-------------|------|
| `app/core/token_access_auto.py` | `hostaway_api:{city}` | In-memory; per-city only. Consider tenant if tokens differ per tenant. |
| `app/core/token_access.py` | `hostaway_api_{city}` | Same as above. |
| `app/core/token_service.py` | `sendgrid:api` | Global key. |

City access and health invalidation now use `clear_city_access_cache_for_user` and `clear_city_access_cache_for_tenant` (Redis); `tenant_cache` is no longer used for city cache get/invalidate.
