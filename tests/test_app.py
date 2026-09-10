from datetime import datetime

import httpx
import pytest
from fastapi.testclient import TestClient

from app.client import (
    PortalAuthenticationError,
    PortalClient,
    PortalNotFoundError,
    PortalUnavailableError,
)
from app.main import app
from app.models import (
    normalize_meter,
    normalize_meter_detail,
    normalize_meter_energy,
    normalize_meter_geo,
    normalize_meter_list,
)


# ---------------------------------------------------------------------------
# Sample portal responses
# ---------------------------------------------------------------------------

METER_RESPONSE = {
    "meterId": "J100000",
    "serialNo": "SE33962",
    "make": "HPL",
    "phaseType": "single",
    "installStatus": "Decommissioned",
    "dtCode": "DT-001",
}


METER_LIST_RESPONSE = {
    "data": [
        METER_RESPONSE,
        {
            "meterId": "J100001",
            "serialNo": "GE84132",
            "make": "L&T",
            "phaseType": "single",
            "installStatus": "Installed",
            "dtCode": "DT-002",
        },
    ],
    "total": 403,
    "page": 1,
    "pageSize": 20,
}


METER_GEO_RESPONSE = {
    "data": {
        "latitude": "26.938961002479868",
        "longitude": "75.83095696146852",
    }
}


METER_ENERGY_RESPONSE = {
    "data": [
        {
            "timestamp": "23/06/2026 23:30",
            "kwh": "48438.74",
            "kvah": "52313.84",
            "voltR": "226",
        },
        {
            "timestamp": "24/06/2026 00:00",
            "kwh": "48439.12",
            "kvah": "52314.21",
            "voltR": "225",
        },
    ]
}


# This represents the SvelteKit serialized response observed
# from /meters/J100000/__data.json.
METER_DETAIL_RESPONSE = {
    "type": "data",
    "nodes": [
        None,
        {
            "type": "data",
            "data": [
                {"user": 1},
                {"name": 2, "email": 3},
                "Ops Desk",
                "operator@urja.local",
            ],
            "uses": {},
        },
        {
            "type": "data",
            "data": [
                {"meterId": 1, "detail": 2, "hierarchy": 21},
                "J100000",
                {"data": 3},
                [4, 6, 9, 12, 15, 18],
                {"parameterName": 5, "parameterValue": 1},
                "Meter ID",
                {"parameterName": 7, "parameterValue": 8},
                "Serial No",
                "SE33962",
                {"parameterName": 10, "parameterValue": 11},
                "Make",
                "HPL",
                {"parameterName": 13, "parameterValue": 14},
                "Phase Type",
                "single",
                {"parameterName": 16, "parameterValue": 17},
                "Installation Status",
                "Decommissioned",
                {"parameterName": 19, "parameterValue": 20},
                "Installation Type",
                "Whole Current",
                {
                    "Meter ID": 1,
                    "Installation Status": 17,
                    "Installation Type": 20,
                    "Zone": 22,
                    "Circle": 23,
                    "Division": 24,
                    "Subdivision": 25,
                    "Sub Station": 26,
                    "Feeder": 27,
                    "DT": 28,
                },
                "Jaipur Zone 1 (Z-01)",
                "Circle 1 (C-01)",
                "Division 1 (D-01)",
                "Subdivision 1 (SD-01)",
                "Substation 1 (SS-01)",
                "Feeder 1 (F-001)",
                "Malviya Nagar DT 1 (DT-001)",
            ],
            "uses": {"params": ["id"]},
        },
    ],
}


# ---------------------------------------------------------------------------
# Model / normalization tests
# ---------------------------------------------------------------------------


def test_normalize_meter():
    meter = normalize_meter(METER_RESPONSE)

    assert meter.meter_id == "J100000"
    assert meter.serial_number == "SE33962"
    assert meter.make == "HPL"
    assert meter.phase == "single"
    assert meter.status == "Decommissioned"
    assert meter.dt_code == "DT-001"


def test_normalize_meter_list():
    result = normalize_meter_list(METER_LIST_RESPONSE)

    assert len(result.items) == 2
    assert result.total == 403
    assert result.page == 1
    assert result.page_size == 20

    assert result.items[0].meter_id == "J100000"
    assert result.items[1].meter_id == "J100001"


def test_normalize_meter_detail():
    result = normalize_meter_detail(METER_DETAIL_RESPONSE)

    assert result.meter_id == "J100000"

    assert result.details.meter_id == "J100000"
    assert result.details.serial_number == "SE33962"
    assert result.details.make == "HPL"
    assert result.details.phase_type == "single"
    assert result.details.installation_status == "Decommissioned"
    assert result.details.installation_type == "Whole Current"

    assert result.hierarchy.zone == "Jaipur Zone 1 (Z-01)"
    assert result.hierarchy.circle == "Circle 1 (C-01)"
    assert result.hierarchy.division == "Division 1 (D-01)"
    assert result.hierarchy.subdivision == "Subdivision 1 (SD-01)"
    assert result.hierarchy.substation == "Substation 1 (SS-01)"
    assert result.hierarchy.feeder == "Feeder 1 (F-001)"
    assert result.hierarchy.dt == "Malviya Nagar DT 1 (DT-001)"


def test_normalize_meter_geo():
    result = normalize_meter_geo(
        METER_GEO_RESPONSE,
        "J100000",
    )

    assert result.meter_id == "J100000"
    assert result.latitude == pytest.approx(26.938961002479868)
    assert result.longitude == pytest.approx(75.83095696146852)


def test_normalize_meter_energy():
    result = normalize_meter_energy(
        METER_ENERGY_RESPONSE,
        "J100000",
    )

    assert result.meter_id == "J100000"
    assert len(result.readings) == 2

    first = result.readings[0]

    assert first.timestamp == datetime(2026, 6, 23, 23, 30)
    assert first.kwh == pytest.approx(48438.74)
    assert first.kvah == pytest.approx(52313.84)
    assert first.voltage_r == pytest.approx(226.0)


def test_normalize_meter_detail_rejects_invalid_response():
    with pytest.raises(ValueError):
        normalize_meter_detail({})


def test_normalize_meter_geo_rejects_invalid_response():
    with pytest.raises(ValueError):
        normalize_meter_geo(
            {"data": {}},
            "J100000",
        )


def test_normalize_meter_energy_rejects_invalid_response():
    with pytest.raises(ValueError):
        normalize_meter_energy(
            {"data": "invalid"},
            "J100000",
        )


# ---------------------------------------------------------------------------
# Portal client tests
# ---------------------------------------------------------------------------


def make_client(handler):
    client = PortalClient(
        base_url="https://example.com",
        email="test@example.com",
        password="test-password",
    )

    client.client = httpx.Client(
        transport=httpx.MockTransport(handler),
        base_url="https://example.com",
    )

    return client


def test_client_login_success():
    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/login"

        assert request.headers["x-sveltekit-action"] == "true"

        return httpx.Response(
            200,
            json={"success": True},
            headers={
                "set-cookie": (
                    "__Secure-better-auth.session_token=test-session;"
                    " Path=/; HttpOnly"
                )
            },
        )

    client = make_client(handler)

    client.login()

    assert client._authenticated is True
    assert "__Secure-better-auth.session_token" in client.client.cookies

    client.close()


def test_client_login_failure():
    def handler(request):
        return httpx.Response(
            401,
            json={"error": "invalid credentials"},
        )

    client = make_client(handler)

    with pytest.raises(PortalAuthenticationError):
        client.login()

    assert client._authenticated is False

    client.close()


def test_client_search_meters():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/portal/meters/search"

        assert request.url.params["q"] == "J100000"
        assert request.url.params["page"] == "2"

        return httpx.Response(
            200,
            json=METER_LIST_RESPONSE,
        )

    client = make_client(handler)

    # Avoid real login for this unit test.
    client._authenticated = True

    result = client.search_meters(
        query="J100000",
        page=2,
    )

    assert result["total"] == 403
    assert result["page"] == 1

    client.close()


def test_client_get_meter_data():
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/meters/J100000/__data.json"

        return httpx.Response(
            200,
            json=METER_DETAIL_RESPONSE,
        )

    client = make_client(handler)
    client._authenticated = True

    result = client.get_meter_data("J100000")

    assert result["type"] == "data"
    assert len(result["nodes"]) == 3

    client.close()


def test_client_get_meter_geo():
    def handler(request):
        assert request.url.path == "/portal/meters/J100000/geo"

        return httpx.Response(
            200,
            json=METER_GEO_RESPONSE,
        )

    client = make_client(handler)
    client._authenticated = True

    result = client.get_meter_geo("J100000")

    assert result["data"]["latitude"] == "26.938961002479868"

    client.close()


def test_client_get_meter_energy():
    def handler(request):
        assert request.url.path == "/portal/meters/J100000/energy"

        return httpx.Response(
            200,
            json=METER_ENERGY_RESPONSE,
        )

    client = make_client(handler)
    client._authenticated = True

    result = client.get_meter_energy("J100000")

    assert len(result["data"]) == 2

    client.close()


def test_client_404():
    def handler(request):
        return httpx.Response(
            404,
            json={"error": "not found"},
        )

    client = make_client(handler)
    client._authenticated = True

    with pytest.raises(PortalNotFoundError):
        client.get_meter_data("INVALID-METER")

    client.close()


def test_client_server_error():
    def handler(request):
        return httpx.Response(
            500,
            json={"error": "server error"},
        )

    client = make_client(handler)
    client._authenticated = True

    with pytest.raises(PortalUnavailableError):
        client.get_meter_data("J100000")

    client.close()


def test_client_timeout():
    def handler(request):
        raise httpx.ReadTimeout(
            "Request timed out",
            request=request,
        )

    client = make_client(handler)
    client._authenticated = True

    with pytest.raises(PortalUnavailableError):
        client.get_meter_data("J100000")

    client.close()


def test_client_reauthenticates_after_401():
    calls = []

    def handler(request):
        calls.append(request)

        if request.url.path == "/login":
            return httpx.Response(
                200,
                json={"success": True},
                headers={
                    "set-cookie": (
                        "__Secure-better-auth.session_token="
                        "test-session; Path=/; HttpOnly"
                    )
                },
            )

        if request.url.path == "/portal/meters/search":
            # First request represents expired session.
            if len(
                [
                    call
                    for call in calls
                    if call.url.path == "/portal/meters/search"
                ]
            ) == 1:
                return httpx.Response(401)

            return httpx.Response(
                200,
                json=METER_LIST_RESPONSE,
            )

        raise AssertionError(
            f"Unexpected path: {request.url.path}"
        )

    client = make_client(handler)
    client._authenticated = True

    result = client.search_meters()

    assert result["total"] == 403

    meter_requests = [
        call
        for call in calls
        if call.url.path == "/portal/meters/search"
    ]

    login_requests = [
        call
        for call in calls
        if call.url.path == "/login"
    ]

    assert len(meter_requests) == 2
    assert len(login_requests) == 1

    client.close()


# ---------------------------------------------------------------------------
# FastAPI API tests
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client(monkeypatch):
    """
    Replace the real portal client with a mocked PortalClient
    so API tests never call the real portal.
    """

    class FakePortalClient:
        def search_meters(self, query="", page=1):
            return METER_LIST_RESPONSE

        def get_meter_data(self, meter_id):
            if meter_id == "INVALID-METER":
                raise PortalNotFoundError()

            return METER_DETAIL_RESPONSE

        def get_meter_geo(self, meter_id):
            return METER_GEO_RESPONSE

        def get_meter_energy(self, meter_id):
            return METER_ENERGY_RESPONSE

    monkeypatch.setattr(
        "app.main.portal_client",
        FakePortalClient(),
    )

    with TestClient(app) as client:
        yield client


def test_health_endpoint(api_client):
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_meters_endpoint(api_client):
    response = api_client.get("/api/v1/meters")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 403
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["items"]) == 2


def test_search_meters_endpoint(api_client):
    response = api_client.get(
        "/api/v1/meters",
        params={"q": "J100000"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"][0]["meter_id"] == "J100000"


def test_pagination_endpoint(api_client):
    response = api_client.get(
        "/api/v1/meters",
        params={"page": 2},
    )

    assert response.status_code == 200


def test_get_meter_endpoint(api_client):
    response = api_client.get(
        "/api/v1/meters/J100000",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["meter_id"] == "J100000"
    assert data["details"]["serial_number"] == "SE33962"
    assert data["details"]["make"] == "HPL"
    assert data["hierarchy"]["zone"] == "Jaipur Zone 1 (Z-01)"


def test_get_meter_location_endpoint(api_client):
    response = api_client.get(
        "/api/v1/meters/J100000/location",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["meter_id"] == "J100000"
    assert data["latitude"] == pytest.approx(
        26.938961002479868
    )
    assert data["longitude"] == pytest.approx(
        75.83095696146852
    )


def test_get_meter_consumption_endpoint(api_client):
    response = api_client.get(
        "/api/v1/meters/J100000/consumption",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["meter_id"] == "J100000"
    assert len(data["readings"]) == 2

    assert data["readings"][0]["kwh"] == pytest.approx(
        48438.74
    )


def test_invalid_meter_returns_404(api_client):
    response = api_client.get(
        "/api/v1/meters/INVALID-METER",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Meter not found."
    }


def test_invalid_page_returns_422(api_client):
    response = api_client.get(
        "/api/v1/meters",
        params={"page": 0},
    )

    assert response.status_code == 422