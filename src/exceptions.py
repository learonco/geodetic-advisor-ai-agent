"""Custom exception classes for the Geodetic Advisor AI Agent.

Hierarchy:
    GeodeticAdvisorError
    ├── ValidationError
    │   ├── InvalidEpsgCodeError
    │   ├── InvalidBboxError
    │   ├── InvalidCoordinateError
    │   └── InvalidQueryFormatError
    ├── EpsgLookupError
    ├── CoordinateTransformError
    ├── CrsSearchError
    ├── AgentInvocationError
    ├── ResponseParsingError
    └── NominatimError
        ├── NominatimTimeoutError
        ├── NominatimHttpError
        ├── NominatimConnectionError
        └── AreaNotFoundError
"""


class GeodeticAdvisorError(Exception):
    """Base exception for all Geodetic Advisor errors."""


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

class ValidationError(GeodeticAdvisorError):
    """Raised when input data fails validation."""


class InvalidEpsgCodeError(ValidationError):
    """Raised when an EPSG code is not a valid integer.

    Attributes:
        code: The invalid code that was provided.
    """

    def __init__(self, code: object) -> None:
        self.code = code
        super().__init__(f"'{code}' is not a valid integer EPSG code.")


class InvalidBboxError(ValidationError):
    """Raised when a bounding box field cannot be parsed.

    Attributes:
        field: The name of the offending field (e.g. 'west').
        value: The invalid value that was provided.
    """

    def __init__(self, field: str, value: object) -> None:
        self.field = field
        self.value = value
        super().__init__(f"Invalid bounding box field '{field}': cannot parse '{value}' as a float.")


class InvalidCoordinateError(ValidationError):
    """Raised when a coordinate value is out of range or not numeric.

    Attributes:
        axis: The coordinate axis ('x', 'y', or 'z').
        value: The invalid value that was provided.
    """

    def __init__(self, axis: str, value: object) -> None:
        self.axis = axis
        self.value = value
        super().__init__(f"Invalid coordinate for axis '{axis}': {value!r}.")


class InvalidQueryFormatError(ValidationError):
    """Raised when a tool query string does not match the expected format.

    Attributes:
        received: The raw query string that was provided.
        expected: Description of the expected format.
    """

    def __init__(self, received: str, *, expected: str = "") -> None:
        self.received = received
        self.expected = expected
        msg = f"Query format is invalid: received '{received}'."
        if expected:
            msg += f" Expected format: '{expected}'."
        super().__init__(msg)


# ---------------------------------------------------------------------------
# Tool-level errors
# ---------------------------------------------------------------------------

class EpsgLookupError(GeodeticAdvisorError):
    """Raised when a CRS cannot be retrieved for a given EPSG code.

    Attributes:
        epsg_code: The EPSG numeric code that failed to resolve.
    """

    def __init__(self, epsg_code: int, detail: str = "") -> None:
        self.epsg_code = epsg_code
        msg = f"Could not look up EPSG:{epsg_code}."
        if detail:
            msg += f" {detail}"
        super().__init__(msg)


class CoordinateTransformError(GeodeticAdvisorError):
    """Raised when a coordinate transformation fails.

    Attributes:
        from_epsg: Source EPSG code.
        to_epsg: Target EPSG code.
    """

    def __init__(self, from_epsg: int, to_epsg: int, detail: str = "") -> None:
        self.from_epsg = from_epsg
        self.to_epsg = to_epsg
        msg = f"Coordinate transformation from EPSG:{from_epsg} to EPSG:{to_epsg} failed."
        if detail:
            msg += f" {detail}"
        super().__init__(msg)


class CrsSearchError(GeodeticAdvisorError):
    """Raised when a CRS database search fails unexpectedly."""


# ---------------------------------------------------------------------------
# Nominatim / network errors
# ---------------------------------------------------------------------------

class NominatimError(GeodeticAdvisorError):
    """Base exception for errors originating from the Nominatim geocoding service.

    Attributes:
        area_name: The geographic area name that was queried.
    """

    def __init__(self, area_name: str, detail: str = "") -> None:
        self.area_name = area_name
        msg = f"Nominatim error while searching for '{area_name}'."
        if detail:
            msg += f" {detail}"
        super().__init__(msg)


class NominatimTimeoutError(NominatimError):
    """Raised when the Nominatim request times out."""

    def __init__(self, area_name: str) -> None:
        super().__init__(area_name, "The request timed out.")


class NominatimHttpError(NominatimError):
    """Raised when Nominatim returns a non-successful HTTP status.

    Attributes:
        status_code: The HTTP status code returned by the server.
    """

    def __init__(self, area_name: str, *, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(area_name, f"HTTP {status_code} response.")


class NominatimConnectionError(NominatimError):
    """Raised when a network-level error prevents reaching Nominatim.

    Attributes:
        cause: The underlying exception that triggered this error.
    """

    def __init__(self, area_name: str, *, cause: BaseException | None = None) -> None:
        self.cause = cause
        detail = str(cause) if cause else ""
        super().__init__(area_name, detail)


class AreaNotFoundError(NominatimError):
    """Raised when Nominatim returns no results for the queried area name."""

    def __init__(self, area_name: str) -> None:
        super().__init__(area_name, f"No results found for '{area_name}'.")


# ---------------------------------------------------------------------------
# WebUI / agent layer errors
# ---------------------------------------------------------------------------

class AgentInvocationError(GeodeticAdvisorError):
    """Raised when invoking the LangChain agent fails.

    Attributes:
        query: The user query that triggered the failure.
        cause: The underlying exception, if available.
    """

    def __init__(self, query: str, *, cause: BaseException | None = None) -> None:
        self.query = query
        self.cause = cause
        msg = "Failed to invoke the geodetic agent."
        if cause:
            msg += f" {cause}"
        super().__init__(msg)


class ResponseParsingError(GeodeticAdvisorError):
    """Raised when the agent response cannot be parsed into the expected format.

    Attributes:
        raw_response: The raw response object that could not be parsed.
        detail: Additional context about the parsing failure.
    """

    def __init__(self, raw_response: object, detail: str = "") -> None:
        self.raw_response = raw_response
        self.detail = detail
        msg = "Could not parse the agent response."
        if detail:
            msg += f" {detail}"
        super().__init__(msg)
