# Pagination, Sorting, and Search Implementation Guide

This guide shows how to implement consistent pagination, sorting, and enhanced search across all API endpoints using the reusable utilities.

## Overview

We've created a standardized approach that includes:
- **Pagination**: Page-based navigation with configurable page sizes
- **Sorting**: Sort by any column with asc/desc direction
- **Enhanced Search**: Search across multiple fields with intelligent matching
- **Filtering**: Multiple filter options for refined results

## Quick Start (Copy-Paste Template)

### 1. Import Required Dependencies

```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, asc, desc
from typing import Optional, List
from uuid import UUID
from enum import Enum

from backend.app.db.session import get_db
from backend.app.utils import SortDirection, apply_pagination, apply_sorting, apply_text_search
from backend.app.security.auth import verify_token
```

### 2. Define Sort Columns Enum

```python
class YourModelSortBy(str, Enum):
    """Available columns for sorting your model"""
    # Add your model's sortable columns here
    name = "name"
    created_at = "created_at"
    updated_at = "updated_at"
    status = "status"
    # ... add more columns as needed
```

### 3. Create the Endpoint

```python
@router.get("", response_model=YourListResponse)
def get_your_models(
    # Standard pagination parameters
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    
    # Standard sorting parameters
    sort_by: YourModelSortBy = Query(YourModelSortBy.name, description="Column to sort by"),
    sort_direction: SortDirection = Query(SortDirection.asc, description="Sort direction (asc/desc)"),
    
    # Your model-specific filters
    status: Optional[StatusEnum] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    
    # Enhanced search
    query: Optional[str] = Query(None, description="Search in name, description, etc."),
    
    # Standard dependencies
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get paginated list with filtering, search, and sorting.
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page (1-100)
        sort_by: Column to sort by
        sort_direction: Sort direction (asc/desc)
        status: Filter by status
        category: Filter by category
        query: Search term
    
    Returns:
        Paginated list with filtering and sorting applied
    """
    
    # Build base query with any necessary joins
    base_query = db.query(YourModel)
    
    # Apply filters
    if status:
        base_query = base_query.filter(YourModel.status == status)
    
    if category:
        base_query = base_query.filter(YourModel.category.ilike(f"%{category}%"))
    
    # Enhanced search functionality
    if query:
        search_columns = [
            YourModel.name,
            YourModel.description,
            # Add more searchable columns
        ]
        base_query = apply_text_search(base_query, query, search_columns)
    
    # Apply sorting
    sort_mapping = {
        YourModelSortBy.name: YourModel.name,
        YourModelSortBy.created_at: YourModel.created_at,
        YourModelSortBy.updated_at: YourModel.updated_at,
        YourModelSortBy.status: YourModel.status,
        # Add more sort mappings
    }
    base_query = apply_sorting(base_query, sort_by.value, sort_direction, sort_mapping)
    
    # Apply pagination using utility function
    results, total, total_pages = apply_pagination(base_query, page, page_size)
    
    return YourListResponse(
        items=[YourSchema.model_validate(item) for item in results],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
```

## Real Examples

### 1. Devices Endpoint (Complete Implementation)

See `/backend/app/routers/devices.py` for the complete implementation with:
- Sort by: name, last_seen, compliant, ip_address, mac_address, vlan, os_version, status, owner info
- Enhanced search: device name, IP, MAC, owner info, groups
- Filters: compliance, owner, status, VLAN, tags

### 2. Users Endpoint (Simplified Implementation)

See `/backend/app/routers/users.py` for the updated implementation with:
- Sort by: email, full_name, department, role, last_seen, status, created_at
- Enhanced search: email, name, department, role, manager, location
- Filters: status, department, role, location

## Advanced Features

### Multi-table Search with Joins

```python
# For searching across related tables
base_query = db.query(Device).join(CanonicalIdentity, Device.owner_cid == CanonicalIdentity.cid)

# Search in both device and user fields
if query:
    search_conditions = [
        Device.name.ilike(f"%{query}%"),
        Device.ip_address.cast(str).ilike(f"%{query}%"),
        CanonicalIdentity.full_name.ilike(f"%{query}%"),
        CanonicalIdentity.email.ilike(f"%{query}%"),
    ]
    
    # Add subquery for group search
    group_subquery = db.query(GroupMembership.cid).filter(
        GroupMembership.group_name.ilike(f"%{query}%")
    ).subquery()
    search_conditions.append(Device.owner_cid.in_(group_subquery))
    
    base_query = base_query.filter(or_(*search_conditions))
```

### Custom Sort Logic

```python
# For complex sorting (e.g., sorting by related table columns)
sort_mapping = {
    DeviceSortBy.owner_email: CanonicalIdentity.email,
    DeviceSortBy.owner_name: CanonicalIdentity.full_name,
    DeviceSortBy.owner_department: CanonicalIdentity.department,
}
```

## Frontend Integration

### Query Parameters

All endpoints support these standard query parameters:

```javascript
const params = {
    page: 1,
    page_size: 20,
    sort_by: 'name',
    sort_direction: 'asc',
    query: 'search term',
    // ... model-specific filters
};
```

### Response Format

All endpoints return consistent response format:

```json
{
    "items": [...],      // Array of model objects
    "total": 150,        // Total count matching filters
    "page": 1,           // Current page number
    "page_size": 20,     // Items per page
    "total_pages": 8     // Total number of pages
}
```

### Table Sorting Implementation

For frontend tables with clickable column headers:

```javascript
const handleSort = (column) => {
    if (sortBy === column) {
        // Same column clicked - toggle direction
        setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
        // New column clicked - default to ascending
        setSortBy(column);
        setSortDirection('asc');
    }
};
```

## Benefits

1. **Consistency**: All endpoints work the same way
2. **Copy-Paste Friendly**: Easy to implement in new routers
3. **Frontend Friendly**: Predictable API responses
4. **Performance**: Efficient database queries with proper indexing
5. **Extensible**: Easy to add new sort columns and search fields

## Performance Tips

1. **Add Database Indexes**: For frequently sorted/searched columns
2. **Limit Page Sizes**: Max 100 items per page
3. **Use Efficient Joins**: Only join tables when necessary for search/sort
4. **Consider Caching**: For expensive aggregation queries

## Migration Checklist

To migrate an existing endpoint:

1. ✅ Add required imports
2. ✅ Create SortBy enum for your model
3. ✅ Update endpoint parameters
4. ✅ Replace query logic with utility functions
5. ✅ Update response format
6. ✅ Test with frontend
7. ✅ Add database indexes if needed
