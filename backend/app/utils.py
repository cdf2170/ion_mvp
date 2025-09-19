"""
Utility functions for pagination, sorting, and search across all endpoints.
This provides a consistent, reusable approach that can be easily copied between routers.
"""

from enum import Enum
from typing import Optional, List, Any, Dict
from sqlalchemy.orm import Session, Query
from sqlalchemy import asc, desc, or_
from fastapi import Query as FastAPIQuery


class SortDirection(str, Enum):
    """Universal sort direction enum for all endpoints"""
    asc = "asc"
    desc = "desc"


def apply_pagination(
    query: Query,
    page: int,
    page_size: int
) -> tuple[List[Any], int, int]:
    """
    Apply pagination to a SQLAlchemy query and return results with metadata.
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        page_size: Number of items per page
    
    Returns:
        Tuple of (results, total_count, total_pages)
    """
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return results, total, total_pages


def apply_sorting(
    query: Query,
    sort_by: str,
    sort_direction: SortDirection,
    sort_mapping: Dict[str, Any]
) -> Query:
    """
    Apply sorting to a SQLAlchemy query based on column mapping.
    
    Args:
        query: SQLAlchemy query object
        sort_by: Column name to sort by
        sort_direction: Sort direction (asc/desc)
        sort_mapping: Dictionary mapping sort_by values to SQLAlchemy columns
    
    Returns:
        Updated query with sorting applied
    """
    if sort_by in sort_mapping:
        sort_column = sort_mapping[sort_by]
        if sort_direction == SortDirection.desc:
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
    
    return query


def apply_text_search(
    query: Query,
    search_query: Optional[str],
    search_columns: List[Any]
) -> Query:
    """
    Apply text search across multiple columns.
    
    Args:
        query: SQLAlchemy query object
        search_query: Search term
        search_columns: List of SQLAlchemy columns to search in
    
    Returns:
        Updated query with search conditions applied
    """
    if search_query:
        search_conditions = [
            column.ilike(f"%{search_query}%") for column in search_columns
        ]
        query = query.filter(or_(*search_conditions))
    
    return query


# Standard pagination parameters for FastAPI endpoints
PaginationParams = {
    "page": FastAPIQuery(1, ge=1, description="Page number"),
    "page_size": FastAPIQuery(20, ge=1, le=100, description="Number of items per page"),
}

# Standard sorting parameters
SortingParams = {
    "sort_direction": FastAPIQuery(SortDirection.asc, description="Sort direction (asc/desc)"),
}

# Standard search parameters
SearchParams = {
    "query": FastAPIQuery(None, description="Search term"),
}
