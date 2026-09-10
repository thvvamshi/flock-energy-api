from datetime import datetime

from pydantic import BaseModel


class Meter(BaseModel):
    meter_id: str
    serial_number: str | None = None
    make: str | None = None
    phase: str | None = None
    status: str | None = None
    dt_code: str | None = None


class MeterListResponse(BaseModel):
    items: list[Meter]
    total: int
    page: int
    page_size: int


class MeterDetails(BaseModel):
    meter_id: str
    serial_number: str | None = None
    make: str | None = None
    phase_type: str | None = None
    installation_status: str | None = None
    installation_type: str | None = None


class MeterHierarchy(BaseModel):
    zone: str | None = None
    circle: str | None = None
    division: str | None = None
    subdivision: str | None = None
    substation: str | None = None
    feeder: str | None = None
    dt: str | None = None


class MeterDetailResponse(BaseModel):
    meter_id: str
    details: MeterDetails
    hierarchy: MeterHierarchy


class Location(BaseModel):
    meter_id: str
    latitude: float
    longitude: float


class ConsumptionReading(BaseModel):
    timestamp: datetime
    kwh: float
    kvah: float
    voltage_r: float


class ConsumptionResponse(BaseModel):
    meter_id: str
    readings: list[ConsumptionReading]


def normalize_meter(data: dict) -> Meter:
    return Meter(
        meter_id=data["meterId"],
        serial_number=data.get("serialNo"),
        make=data.get("make"),
        phase=data.get("phaseType"),
        status=data.get("installStatus"),
        dt_code=data.get("dtCode"),
    )


def normalize_meter_list(data: dict) -> MeterListResponse:
    return MeterListResponse(
        items=[
            normalize_meter(item)
            for item in data.get("data", [])
        ],
        total=data["total"],
        page=data["page"],
        page_size=data["pageSize"],
    )


def normalize_meter_detail(data: dict) -> MeterDetailResponse:
    """
    Convert the SvelteKit serialized meter detail response
    into the clean API representation.
    """

    nodes = data.get("nodes", [])

    if len(nodes) < 3 or not nodes[2]:
        raise ValueError("Invalid meter detail response")

    values = nodes[2].get("data", [])

    if not isinstance(values, list) or not values:
        raise ValueError("Invalid meter detail data")

    root = values[0]

    meter_id = values[root["meterId"]]

    detail_container = values[root["detail"]]
    detail_refs = values[detail_container["data"]]

    details: dict[str, str] = {}

    for ref in detail_refs:
        parameter = values[ref]

        parameter_name = values[parameter["parameterName"]]
        parameter_value = values[parameter["parameterValue"]]

        details[parameter_name] = parameter_value

    hierarchy_map = values[root["hierarchy"]]

    hierarchy = MeterHierarchy(
        zone=values[hierarchy_map["Zone"]],
        circle=values[hierarchy_map["Circle"]],
        division=values[hierarchy_map["Division"]],
        subdivision=values[hierarchy_map["Subdivision"]],
        substation=values[hierarchy_map["Sub Station"]],
        feeder=values[hierarchy_map["Feeder"]],
        dt=values[hierarchy_map["DT"]],
    )

    meter_details = MeterDetails(
        meter_id=meter_id,
        serial_number=details.get("Serial No"),
        make=details.get("Make"),
        phase_type=details.get("Phase Type"),
        installation_status=details.get("Installation Status"),
        installation_type=details.get("Installation Type"),
    )

    return MeterDetailResponse(
        meter_id=meter_id,
        details=meter_details,
        hierarchy=hierarchy,
    )


def normalize_meter_geo(
    data: dict,
    meter_id: str,
) -> Location:
    """Convert the portal geo response into the clean API model."""

    geo = data.get("data")

    if not isinstance(geo, dict):
        raise ValueError("Invalid meter geo response")

    if "latitude" not in geo or "longitude" not in geo:
        raise ValueError("Invalid meter geo data")

    try:
        latitude = float(geo["latitude"])
        longitude = float(geo["longitude"])

    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Invalid meter coordinates"
        ) from exc

    return Location(
        meter_id=meter_id,
        latitude=latitude,
        longitude=longitude,
    )


def normalize_meter_energy(
    data: dict,
    meter_id: str,
) -> ConsumptionResponse:
    """Convert the portal energy response into the clean API model."""

    readings_data = data.get("data")

    if not isinstance(readings_data, list):
        raise ValueError("Invalid meter energy response")

    readings: list[ConsumptionReading] = []

    for item in readings_data:
        if not isinstance(item, dict):
            raise ValueError("Invalid meter energy reading")

        try:
            timestamp = datetime.strptime(
                item["timestamp"],
                "%d/%m/%Y %H:%M",
            )

            kwh = float(item["kwh"])
            kvah = float(item["kvah"])
            voltage_r = float(item["voltR"])

        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid meter energy reading"
            ) from exc

        readings.append(
            ConsumptionReading(
                timestamp=timestamp,
                kwh=kwh,
                kvah=kvah,
                voltage_r=voltage_r,
            )
        )

    return ConsumptionResponse(
        meter_id=meter_id,
        readings=readings,
    )