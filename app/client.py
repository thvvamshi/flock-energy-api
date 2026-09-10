import httpx


class PortalError(Exception):
    """Base exception for errors communicating with the legacy portal."""


class PortalAuthenticationError(PortalError):
    """Raised when authentication fails."""


class PortalNotFoundError(PortalError):
    """Raised when the requested portal resource does not exist."""


class PortalUnavailableError(PortalError):
    """Raised when the portal cannot be reached or responds unsuccessfully."""


class PortalClient:
    """HTTP adapter for the legacy Urja Meter Ops portal."""

    def __init__(
        self,
        base_url: str,
        email: str,
        password: str,
        timeout: float = 10.0,
    ) -> None:
        self.email = email
        self.password = password

        self.client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            follow_redirects=True,
        )

        self._authenticated = False

    def login(self) -> None:
        """Authenticate against the legacy portal."""

        try:
            response = self.client.post(
                "/login",
                data={
                    "email": self.email,
                    "password": self.password,
                },
                headers={
                    "X-SvelteKit-Action": "true",
                    "Accept": "application/json",
                    "Origin": str(self.client.base_url).rstrip("/"),
                    "Referer": (
                        f"{str(self.client.base_url).rstrip('/')}/login"
                    ),
                },
            )

            response.raise_for_status()

        except httpx.TimeoutException as exc:
            self._authenticated = False
            raise PortalUnavailableError(
                "Portal login timed out."
            ) from exc

        except httpx.HTTPStatusError as exc:
            self._authenticated = False

            if exc.response.status_code in {401, 403}:
                raise PortalAuthenticationError(
                    "Portal authentication failed."
                ) from exc

            raise PortalUnavailableError(
                "Portal login failed."
            ) from exc

        except httpx.RequestError as exc:
            self._authenticated = False
            raise PortalUnavailableError(
                "Unable to reach the portal."
            ) from exc

        if "__Secure-better-auth.session_token" not in self.client.cookies:
            self._authenticated = False
            raise PortalAuthenticationError(
                "Portal login did not create a session."
            )

        self._authenticated = True

    def _get(
        self,
        path: str,
        *,
        params: dict | None = None,
    ) -> httpx.Response:
        """Perform an authenticated GET with one re-login attempt."""

        if not self._authenticated:
            self.login()

        try:
            response = self.client.get(
                path,
                params=params,
            )

        except httpx.TimeoutException as exc:
            raise PortalUnavailableError(
                "Portal request timed out."
            ) from exc

        except httpx.RequestError as exc:
            raise PortalUnavailableError(
                "Unable to reach the portal."
            ) from exc

        # The session may have expired.
        # Re-authenticate once and retry the original request.
        if response.status_code == 401:
            self._authenticated = False

            self.login()

            try:
                response = self.client.get(
                    path,
                    params=params,
                )

            except httpx.TimeoutException as exc:
                raise PortalUnavailableError(
                    "Portal request timed out."
                ) from exc

            except httpx.RequestError as exc:
                raise PortalUnavailableError(
                    "Unable to reach the portal."
                ) from exc

        if response.status_code == 404:
            raise PortalNotFoundError(
                "Requested portal resource was not found."
            )

        try:
            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            raise PortalUnavailableError(
                "Portal returned an unexpected error."
            ) from exc

        return response

    def search_meters(
        self,
        query: str = "",
        page: int = 1,
    ) -> dict:
        """Fetch a page of meters from the legacy portal."""

        response = self._get(
            "/portal/meters/search",
            params={
                "q": query,
                "page": page,
            },
        )

        try:
            return response.json()

        except ValueError as exc:
            raise PortalUnavailableError(
                "Portal returned invalid JSON."
            ) from exc

    def get_meter_data(
        self,
        meter_id: str,
    ) -> dict:
        """Fetch meter detail data from the SvelteKit route."""

        response = self._get(
            f"/meters/{meter_id}/__data.json",
        )

        try:
            return response.json()

        except ValueError as exc:
            raise PortalUnavailableError(
                "Portal returned invalid meter detail JSON."
            ) from exc

    def get_meter_geo(
        self,
        meter_id: str,
    ) -> dict:
        """Fetch meter location."""

        response = self._get(
            f"/portal/meters/{meter_id}/geo",
        )

        try:
            return response.json()

        except ValueError as exc:
            raise PortalUnavailableError(
                "Portal returned invalid meter location JSON."
            ) from exc

    def get_meter_energy(
        self,
        meter_id: str,
    ) -> dict:
        """Fetch meter energy readings."""

        response = self._get(
            f"/portal/meters/{meter_id}/energy",
        )

        try:
            return response.json()

        except ValueError as exc:
            raise PortalUnavailableError(
                "Portal returned invalid meter energy JSON."
            ) from exc

    def close(self) -> None:
        """Close the underlying HTTP client."""

        self.client.close()