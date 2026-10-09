"""
hospitals.py — Hospital capacity endpoints.
Delegates entirely to capacity_service. No business logic here.
"""

from fastapi import APIRouter, HTTPException
from app.schemas.hospital import HospitalListResponse, HospitalDetailResponse
from app.schemas.common import DataStatus
from app.services.capacity_service import list_hospitals, get_hospital, HospitalNotFoundError

router = APIRouter()


@router.get(
    "/hospitals",
    response_model=HospitalListResponse,
    tags=["Hospitals"],
    summary="List all hospitals with current capacity",
)
def list_hospitals_route():
    hospitals, source = list_hospitals()
    return HospitalListResponse(
        data=hospitals,
        meta={"count": len(hospitals), "page": 1, "page_size": len(hospitals)},
        status=DataStatus.from_source(source),
    )


@router.get(
    "/hospitals/{hospital_id}",
    response_model=HospitalDetailResponse,
    tags=["Hospitals"],
    summary="Get full detail for a single hospital",
    responses={404: {"description": "Hospital not found"}},
)
def get_hospital_route(hospital_id: str):
    hospital, source = get_hospital(hospital_id)
    if not hospital:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Hospital '{hospital_id}' not found", "code": "HOSPITAL_NOT_FOUND"},
        )
    return HospitalDetailResponse(data=hospital, status=DataStatus.from_source(source))
