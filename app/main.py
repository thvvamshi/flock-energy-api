from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.client import (
    PortalAuthenticationError,
    PortalClient,
    PortalNotFoundError,
    PortalUnavailableError,
)
from app.config import get_settings
from app.models import (
    ConsumptionResponse,
    Location,
    MeterDetailResponse,
    MeterListResponse,
    normalize_meter_detail,
    normalize_meter_energy,
    normalize_meter_geo,
    normalize_meter_list,
)


settings = get_settings()

portal_client = PortalClient(
    base_url=settings.urja_base_url,
    email=settings.urja_email,
    password=settings.urja_password,
    timeout=settings.request_timeout,
)


app = FastAPI(
    title="Flock Energy API",
    description="Clean REST API wrapper around the Urja Meter Ops portal.",
    version="0.1.0",
)


@app.exception_handler(PortalAuthenticationError)
def handle_authentication_error(
    request: Request,
    exc: PortalAuthenticationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={
            "detail": "Upstream portal authentication failed."
        },
    )


@app.exception_handler(PortalNotFoundError)
def handle_not_found_error(
    request: Request,
    exc: PortalNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Meter not found."
        },
    )


@app.exception_handler(PortalUnavailableError)
def handle_unavailable_error(
    request: Request,
    exc: PortalUnavailableError,
) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={
            "detail": "Upstream portal is unavailable."
        },
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/api/v1/meters",
    response_model=MeterListResponse,
)
def list_meters(
    q: str = Query(default=""),
    page: int = Query(default=1, ge=1),
) -> MeterListResponse:
    data = portal_client.search_meters(
        query=q,
        page=page,
    )

    try:
        return normalize_meter_list(data)

    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Invalid meter list response "
                "from upstream portal."
            ),
        ) from exc


@app.get(
    "/api/v1/meters/{meter_id}",
    response_model=MeterDetailResponse,
)
def get_meter(
    meter_id: str,
) -> MeterDetailResponse:
    try:
        data = portal_client.get_meter_data(meter_id)

        return normalize_meter_detail(data)

    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Invalid meter detail response "
                "from upstream portal."
            ),
        ) from exc


@app.get(
    "/api/v1/meters/{meter_id}/location",
    response_model=Location,
)
def get_meter_location(
    meter_id: str,
) -> Location:
    try:
        data = portal_client.get_meter_geo(meter_id)

        return normalize_meter_geo(
            data,
            meter_id,
        )

    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Invalid meter location response "
                "from upstream portal."
            ),
        ) from exc


@app.get(
    "/api/v1/meters/{meter_id}/consumption",
    response_model=ConsumptionResponse,
)
def get_meter_consumption(
    meter_id: str,
) -> ConsumptionResponse:
    try:
        data = portal_client.get_meter_energy(meter_id)

        return normalize_meter_energy(
            data,
            meter_id,
        )

    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Invalid meter consumption response "
                "from upstream portal."
            ),
        ) from exc