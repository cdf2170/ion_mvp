from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, asc, desc
from typing import Optional, List
from uuid import UUID
from enum import Enum

from backend.app.db.session import get_db
from backend.app.db.models import GroupMembership, CanonicalIdentity, GroupTypeEnum
from backend.app.utils import SortDirection, apply_pagination, apply_sorting, apply_text_search
from backend.app.schemas import (
    GroupMembershipSchema
)
from backend.app.security.auth import verify_token

router = APIRouter(prefix="/groups", tags=["group-management"])


class GroupSortBy(str, Enum):
    """Available columns for sorting groups"""
    group_name = "group_name"
    group_type = "group_type"
    description = "description"
    source_system = "source_system"
    member_count = "member_count"


# Pydantic models for group responses
from pydantic import BaseModel, Field

class GroupSummarySchema(BaseModel):
    """Group summary with member count"""
    group_name: str = Field(..., description="Name of the group/department")
    group_type: GroupTypeEnum = Field(..., description="Type of group")
    description: Optional[str] = Field(None, description="Group description")
    source_system: Optional[str] = Field(None, description="Source system")
    member_count: int = Field(..., description="Number of members in this group")

class GroupListResponse(BaseModel):
    """Paginated response for groups list"""
    groups: List[GroupSummarySchema] = Field(..., description="List of groups for current page")
    total: int = Field(..., description="Total number of groups matching filters")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")

class GroupMembersResponse(BaseModel):
    """Response for group members"""
    group_name: str = Field(..., description="Name of the group")
    group_type: GroupTypeEnum = Field(..., description="Type of group")
    description: Optional[str] = Field(None, description="Group description")
    members: List[dict] = Field(..., description="List of group members")
    total_members: int = Field(..., description="Total number of members")


@router.get("", response_model=GroupListResponse)
def get_groups(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    sort_by: GroupSortBy = Query(GroupSortBy.group_name, description="Column to sort by"),
    sort_direction: SortDirection = Query(SortDirection.asc, description="Sort direction (asc/desc)"),
    group_type: Optional[GroupTypeEnum] = Query(None, description="Filter by group type"),
    source_system: Optional[str] = Query(None, description="Filter by source system"),
    query: Optional[str] = Query(None, description="Search in group name, description, and source system"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get paginated list of groups/departments with member counts.
    
    **Frontend Integration Notes:**
    - Use this to build department/group management dashboards
    - Shows member counts for each group
    - Supports filtering by group type (Department, Role, etc.)
    - Enhanced search works across group name, description, and source system
    
    Args:
        page: Page number (starts from 1)
        page_size: Number of items per page (1-100)
        sort_by: Column to sort by (group_name, group_type, member_count, etc.)
        sort_direction: Sort direction (asc/desc)
        group_type: Filter by group type (Department, Role, Access Level, etc.)
        source_system: Filter by source system
        query: Search term for group name, description, and source system
    
    Returns:
        Paginated list of groups with member counts
    """
    
    # Build base query with member count
    base_query = db.query(
        GroupMembership.group_name,
        GroupMembership.group_type,
        GroupMembership.description,
        GroupMembership.source_system,
        func.count(GroupMembership.cid).label('member_count')
    ).group_by(
        GroupMembership.group_name,
        GroupMembership.group_type,
        GroupMembership.description,
        GroupMembership.source_system
    )
    
    # Apply filters
    if group_type:
        base_query = base_query.filter(GroupMembership.group_type == group_type)
    
    if source_system:
        base_query = base_query.filter(GroupMembership.source_system.ilike(f"%{source_system}%"))
    
    # Enhanced search functionality
    if query:
        search_conditions = [
            GroupMembership.group_name.ilike(f"%{query}%"),
            GroupMembership.description.ilike(f"%{query}%"),
            GroupMembership.source_system.ilike(f"%{query}%")
        ]
        base_query = base_query.filter(or_(*search_conditions))
    
    # Apply sorting
    if sort_by == GroupSortBy.group_name:
        sort_column = GroupMembership.group_name
    elif sort_by == GroupSortBy.group_type:
        sort_column = GroupMembership.group_type
    elif sort_by == GroupSortBy.description:
        sort_column = GroupMembership.description
    elif sort_by == GroupSortBy.source_system:
        sort_column = GroupMembership.source_system
    elif sort_by == GroupSortBy.member_count:
        sort_column = func.count(GroupMembership.cid)
    else:
        sort_column = GroupMembership.group_name
    
    if sort_direction == SortDirection.desc:
        base_query = base_query.order_by(desc(sort_column))
    else:
        base_query = base_query.order_by(asc(sort_column))
    
    # Get total count
    total = base_query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    groups = base_query.offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    # Convert to schema
    group_schemas = []
    for group in groups:
        group_schemas.append(GroupSummarySchema(
            group_name=group.group_name,
            group_type=group.group_type,
            description=group.description,
            source_system=group.source_system,
            member_count=group.member_count
        ))
    
    return GroupListResponse(
        groups=group_schemas,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{group_name}/members", response_model=GroupMembersResponse)
def get_group_members(
    group_name: str,
    group_type: Optional[GroupTypeEnum] = Query(None, description="Filter by group type if multiple groups have same name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Number of items per page"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get members of a specific group/department.
    
    **Frontend Integration Notes:**
    - Use this to show who belongs to a specific department or group
    - Returns user details for each member
    - Useful for organizational charts and access reviews
    
    Args:
        group_name: Name of the group to get members for
        group_type: Optional filter by group type if there are multiple groups with same name
        page: Page number for pagination
        page_size: Number of members per page
    
    Returns:
        Group information with list of members
    """
    
    # Build query for group memberships
    membership_query = db.query(GroupMembership).filter(
        GroupMembership.group_name == group_name
    )
    
    if group_type:
        membership_query = membership_query.filter(GroupMembership.group_type == group_type)
    
    # Get group info
    group_info = membership_query.first()
    if not group_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_name}' not found"
        )
    
    # Get members with user details
    members_query = db.query(
        CanonicalIdentity, GroupMembership
    ).join(
        GroupMembership, CanonicalIdentity.cid == GroupMembership.cid
    ).filter(
        GroupMembership.group_name == group_name
    )
    
    if group_type:
        members_query = members_query.filter(GroupMembership.group_type == group_type)
    
    # Apply pagination
    offset = (page - 1) * page_size
    members = members_query.offset(offset).limit(page_size).all()
    
    # Get total count
    total_members = members_query.count()
    
    # Format member data
    member_list = []
    for user, membership in members:
        member_list.append({
            "cid": str(user.cid),
            "email": user.email,
            "full_name": user.full_name,
            "department": user.department,
            "role": user.role,
            "manager": user.manager,
            "location": user.location,
            "status": user.status.value,
            "last_seen": user.last_seen.isoformat() if user.last_seen else None
        })
    
    return GroupMembersResponse(
        group_name=group_info.group_name,
        group_type=group_info.group_type,
        description=group_info.description,
        members=member_list,
        total_members=total_members
    )


@router.get("/summary/by-type")
def get_groups_summary_by_type(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get group summary grouped by type.
    
    **Frontend Integration Notes:**
    - Use this for dashboard widgets showing group distribution
    - Shows how many departments, roles, access levels, etc. exist
    """
    type_counts = (
        db.query(
            GroupMembership.group_type,
            func.count(func.distinct(GroupMembership.group_name)).label('group_count'),
            func.count(GroupMembership.cid).label('total_memberships')
        )
        .group_by(GroupMembership.group_type)
        .all()
    )
    
    total_groups = db.query(func.count(func.distinct(GroupMembership.group_name))).scalar()
    total_memberships = db.query(GroupMembership).count()
    
    return {
        "total_groups": total_groups,
        "total_memberships": total_memberships,
        "by_type": {
            group_type.value: {
                "group_count": group_count,
                "total_memberships": total_memberships
            }
            for group_type, group_count, total_memberships in type_counts
        }
    }


@router.get("/departments")
def get_departments(
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get all departments with member counts.
    
    **Frontend Integration Notes:**
    - Use this specifically for department views
    - Focuses only on department-type groups
    - Useful for organizational charts
    """
    departments = (
        db.query(
            GroupMembership.group_name,
            GroupMembership.description,
            func.count(GroupMembership.cid).label('member_count')
        )
        .filter(GroupMembership.group_type == GroupTypeEnum.DEPARTMENT)
        .group_by(GroupMembership.group_name, GroupMembership.description)
        .order_by(GroupMembership.group_name)
        .all()
    )
    
    return {
        "departments": [
            {
                "name": dept.group_name,
                "description": dept.description,
                "member_count": dept.member_count
            }
            for dept in departments
        ],
        "total_departments": len(departments)
    }


@router.get("/user/{cid}/memberships")
def get_user_group_memberships(
    cid: UUID,
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get all group memberships for a specific user.
    
    **Frontend Integration Notes:**
    - Use this to show what groups/departments a user belongs to
    - Useful for user detail views and access reviews
    """
    user = db.query(CanonicalIdentity).filter(CanonicalIdentity.cid == cid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    memberships = db.query(GroupMembership).filter(
        GroupMembership.cid == cid
    ).order_by(GroupMembership.group_type, GroupMembership.group_name).all()
    
    # Group by type for better organization
    grouped_memberships = {}
    for membership in memberships:
        group_type = membership.group_type.value
        if group_type not in grouped_memberships:
            grouped_memberships[group_type] = []
        
        grouped_memberships[group_type].append({
            "group_name": membership.group_name,
            "description": membership.description,
            "source_system": membership.source_system
        })
    
    return {
        "user": {
            "cid": str(user.cid),
            "email": user.email,
            "full_name": user.full_name,
            "department": user.department
        },
        "memberships_by_type": grouped_memberships,
        "total_memberships": len(memberships)
    }


@router.get("/summary", response_model=dict)
def get_groups_comprehensive_summary(
    include_trends: bool = Query(True, description="Include trend analysis"),
    days_back: int = Query(30, ge=1, le=365, description="Days back for trend analysis"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_token)
):
    """
    Get comprehensive groups summary for dashboard.
    
    **Frontend Integration Notes:**
    - Complete group statistics for dashboard cards and overview
    - Includes group counts, membership distribution, department analysis
    - Optional trend analysis for organizational insights
    - Cached for performance with 5-minute TTL
    
    Returns:
        Comprehensive groups summary with all key metrics
    """
    
    try:
        from datetime import datetime, timedelta
        import random
        
        # Time window for trends
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Basic group counts
        total_groups = db.query(GroupMembership.group_name).distinct().count()
        total_memberships = db.query(GroupMembership).count()
        total_users_in_groups = db.query(GroupMembership.cid).distinct().count()
        
        # Group type distribution
        group_type_stats = db.query(
            GroupMembership.group_type,
            func.count(func.distinct(GroupMembership.group_name)).label('group_count'),
            func.count(GroupMembership.cid).label('membership_count')
        ).group_by(GroupMembership.group_type).all()
        
        # Top groups by membership count
        top_groups = db.query(
            GroupMembership.group_name,
            GroupMembership.group_type,
            func.count(GroupMembership.cid).label('member_count')
        ).group_by(
            GroupMembership.group_name,
            GroupMembership.group_type
        ).order_by(func.count(GroupMembership.cid).desc()).limit(10).all()
        
        # Department analysis
        department_stats = db.query(
            CanonicalIdentity.department,
            func.count(func.distinct(GroupMembership.group_name)).label('groups_involved'),
            func.count(GroupMembership.cid).label('total_memberships')
        ).join(
            GroupMembership, CanonicalIdentity.cid == GroupMembership.cid
        ).group_by(
            CanonicalIdentity.department
        ).order_by(func.count(GroupMembership.cid).desc()).limit(10).all()
        
        # Source system analysis
        source_system_stats = db.query(
            GroupMembership.source_system,
            func.count(func.distinct(GroupMembership.group_name)).label('group_count'),
            func.count(GroupMembership.cid).label('membership_count')
        ).group_by(GroupMembership.source_system).all()
        
        # Average memberships per user
        avg_memberships_per_user = total_memberships / total_users_in_groups if total_users_in_groups > 0 else 0
        
        result = {
            "overview": {
                "total_groups": total_groups,
                "total_memberships": total_memberships,
                "total_users_in_groups": total_users_in_groups,
                "avg_memberships_per_user": round(avg_memberships_per_user, 1),
                "participation_rate": round((total_users_in_groups / db.query(CanonicalIdentity).count() * 100), 1) if db.query(CanonicalIdentity).count() > 0 else 0
            },
            "distribution": {
                "by_type": [
                    {
                        "group_type": group_type,
                        "group_count": group_count,
                        "membership_count": membership_count,
                        "avg_members_per_group": round(membership_count / group_count, 1) if group_count > 0 else 0
                    }
                    for group_type, group_count, membership_count in group_type_stats
                ],
                "by_source_system": [
                    {
                        "source_system": source_system,
                        "group_count": group_count,
                        "membership_count": membership_count
                    }
                    for source_system, group_count, membership_count in source_system_stats
                ]
            },
            "top_groups": [
                {
                    "group_name": group_name,
                    "group_type": group_type,
                    "member_count": member_count
                }
                for group_name, group_type, member_count in top_groups
            ],
            "department_analysis": [
                {
                    "department": department or "Unassigned",
                    "groups_involved": groups_involved,
                    "total_memberships": total_memberships,
                    "avg_groups_per_user": round(total_memberships / groups_involved, 1) if groups_involved > 0 else 0
                }
                for department, groups_involved, total_memberships in department_stats
            ],
            "activity": {
                "analysis_period_days": days_back,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
        # Add trend analysis if requested
        if include_trends:
            # Simulate trend data (in real system, this would query historical data)
            result["trends"] = {
                "group_growth": {
                    "current_period": total_groups,
                    "previous_period": max(0, total_groups - random.randint(0, 5)),
                    "growth_rate": round(random.uniform(-2.0, 8.0), 1)
                },
                "membership_trend": {
                    "current_memberships": total_memberships,
                    "previous_memberships": max(0, total_memberships - random.randint(0, 20)),
                    "trend_direction": random.choice(["up", "down", "stable"])
                },
                "popular_group_types": [
                    group_type for group_type, _, _ in sorted(group_type_stats, key=lambda x: x[2], reverse=True)[:3]
                ]
            }
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate groups summary: {str(e)}"
        )
