"""Department CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin, require_staff_or_admin, get_current_user
from app.crud import department as department_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate

router = APIRouter()


@router.get("", response_model=list[DepartmentRead], summary="List departments")
def list_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DepartmentRead]:
    """List hospital departments."""
    return department_crud.list_departments(db, skip=skip, limit=limit)


@router.get("/{department_id}", response_model=DepartmentRead, summary="Get a department")
def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DepartmentRead:
    """Fetch one department by ID."""
    department = department_crud.get_by_id(db, department_id)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department


@router.post(
    "",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a department",
)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff_or_admin),
) -> DepartmentRead:
    """Create a new department (staff/admin)."""
    if department_crud.get_by_name(db, payload.name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department name already exists")
    return department_crud.create_department(db, payload)


@router.put("/{department_id}", response_model=DepartmentRead, summary="Update a department (full)")
def update_department_put(
    department_id: int,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff_or_admin),
) -> DepartmentRead:
    """Update a department via PUT (staff/admin)."""
    department = department_crud.get_by_id(db, department_id)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department_crud.update_department(db, department, payload)


@router.patch("/{department_id}", response_model=DepartmentRead, summary="Update a department (partial)")
def update_department_patch(
    department_id: int,
    payload: DepartmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff_or_admin),
) -> DepartmentRead:
    """Update a department via PATCH (staff/admin)."""
    department = department_crud.get_by_id(db, department_id)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return department_crud.update_department(db, department, payload)


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a department")
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_staff_or_admin),
) -> None:
    """Delete a department (staff/admin)."""
    department = department_crud.get_by_id(db, department_id)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    department_crud.delete_department(db, department)
