from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ...database import supabase
from ...core.auth import authenticate_request

router = APIRouter()


@router.get("/cities")
async def get_available_cities(current_user=Depends(authenticate_request)):
    """
    Get available cities from the current tenant's properties.
    Requires authentication; returns only cities for the authenticated user's tenant.
    """
    try:
        tenant_id = getattr(current_user, 'tenant_id', None)
        if not tenant_id:
            return {'cities': [], 'total': 0}

        query = (
            supabase.table('properties')
            .select('city')
            .eq('tenant_id', tenant_id)
            .neq('city', '')
            .not_.is_('city', 'null')
            .eq('status', 'active')
        )
        result = query.execute()

        city_counts = {}
        for row in (result.data or []):
            city = row.get('city')
            if city:
                city_name = city.lower().strip()
                if city_name:
                    city_counts[city_name] = city_counts.get(city_name, 0) + 1

        cities = []
        for city_name, count in sorted(city_counts.items()):
            cities.append({
                'id': city_name,
                'name': city_name.title(),
                'property_count': count
            })

        return {
            'cities': cities,
            'total': len(cities)
        }

    except Exception as e:
        print(f"Error fetching cities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch cities")

@router.get("/cities/user-accessible")
async def get_user_accessible_cities(
    current_user = Depends(authenticate_request)
):
    """
    Get cities that the current user has access to.
    Admins get all cities, regular users get their assigned cities.
    """
    try:
        user_id = current_user.id
        user_email = current_user.email
        
        # Check if user is admin (same logic as auth.py)
        is_admin = current_user.is_admin
        
        # Resolve tenant so Ocean vs Sunset see only their properties/cities
        tenant_id = getattr(current_user, 'tenant_id', None)

        if is_admin:
            # Admin gets all available cities for their tenant only
            query = supabase.table('properties').select('city').neq('city', '').not_.is_('city', 'null').eq('status', 'active')
            if tenant_id:
                query = query.eq('tenant_id', tenant_id)
            result = query.execute()
            city_counts = {}
            for row in (result.data or []):
                city = row.get('city')
                if city:
                    city_name = city.lower().strip()
                    if city_name:
                        city_counts[city_name] = city_counts.get(city_name, 0) + 1
        else:
            # Regular user gets only their assigned cities that have active properties
            # First get user's accessible cities
            user_cities_result = supabase.table('users_city') \
                .select('city_name') \
                .eq('user_id', user_id) \
                .execute()
            
            accessible_cities = [row['city_name'].lower() for row in user_cities_result.data]
            
            if accessible_cities:
                # Get properties in accessible cities (scoped to user's tenant)
                query = supabase.table('properties').select('city').neq('city', '').not_.is_('city', 'null').eq('status', 'active')
                if tenant_id:
                    query = query.eq('tenant_id', tenant_id)
                result = query.execute()
                city_counts = {}
                for row in (result.data or []):
                    city = row.get('city')
                    if city:
                        city_name = city.lower().strip()
                        if city_name in accessible_cities:
                            city_counts[city_name] = city_counts.get(city_name, 0) + 1
            else:
                city_counts = {}
        
        cities = []
        for city_name, count in sorted(city_counts.items()):
            cities.append({
                'id': city_name,
                'name': city_name.title(),
                'property_count': count
            })
        
        return {
            'cities': cities,
            'total': len(cities),
            'is_admin': is_admin
        }
        
    except Exception as e:
        print(f"Error fetching user accessible cities: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch accessible cities")
