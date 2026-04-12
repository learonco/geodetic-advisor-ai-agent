"""Unit tests for src/exceptions.py — custom exception classes."""

import pytest

from src.exceptions import (
    GeodeticAdvisorError,
    ValidationError,
    InvalidEpsgCodeError,
    InvalidBboxError,
    InvalidCoordinateError,
    InvalidQueryFormatError,
    EpsgLookupError,
    CoordinateTransformError,
    CrsSearchError,
    NominatimError,
    NominatimTimeoutError,
    NominatimHttpError,
    NominatimConnectionError,
    AreaNotFoundError,
    AgentInvocationError,
    ResponseParsingError,
)


class TestBaseException:
    def test_geodetic_advisor_error_is_exception(self):
        assert issubclass(GeodeticAdvisorError, Exception)

    def test_geodetic_advisor_error_message(self):
        err = GeodeticAdvisorError("base error")
        assert str(err) == "base error"

    def test_can_raise_and_catch(self):
        with pytest.raises(GeodeticAdvisorError):
            raise GeodeticAdvisorError("test")


class TestValidationErrors:
    def test_validation_error_inherits_base(self):
        assert issubclass(ValidationError, GeodeticAdvisorError)

    def test_invalid_epsg_code_error_inherits_validation(self):
        assert issubclass(InvalidEpsgCodeError, ValidationError)

    def test_invalid_bbox_error_inherits_validation(self):
        assert issubclass(InvalidBboxError, ValidationError)

    def test_invalid_coordinate_error_inherits_validation(self):
        assert issubclass(InvalidCoordinateError, ValidationError)

    def test_invalid_query_format_error_inherits_validation(self):
        assert issubclass(InvalidQueryFormatError, ValidationError)

    def test_invalid_epsg_code_stores_code(self):
        err = InvalidEpsgCodeError("abc")
        assert err.code == "abc"
        assert "abc" in str(err)

    def test_invalid_bbox_stores_field(self):
        err = InvalidBboxError("west", "not-a-number")
        assert err.field == "west"
        assert err.value == "not-a-number"
        assert "west" in str(err)

    def test_invalid_coordinate_stores_value(self):
        err = InvalidCoordinateError("x", 999.0)
        assert err.axis == "x"
        assert err.value == 999.0

    def test_invalid_query_format_stores_expected(self):
        err = InvalidQueryFormatError("1,2,3", expected="x,y,from_epsg,to_epsg")
        assert err.received == "1,2,3"
        assert err.expected == "x,y,from_epsg,to_epsg"


class TestToolErrors:
    def test_epsg_lookup_error_inherits_base(self):
        assert issubclass(EpsgLookupError, GeodeticAdvisorError)

    def test_coordinate_transform_error_inherits_base(self):
        assert issubclass(CoordinateTransformError, GeodeticAdvisorError)

    def test_crs_search_error_inherits_base(self):
        assert issubclass(CrsSearchError, GeodeticAdvisorError)

    def test_epsg_lookup_error_stores_code(self):
        err = EpsgLookupError(9999)
        assert err.epsg_code == 9999

    def test_coordinate_transform_error_stores_codes(self):
        err = CoordinateTransformError(4326, 32634)
        assert err.from_epsg == 4326
        assert err.to_epsg == 32634

    def test_crs_search_error_message(self):
        err = CrsSearchError("no results for query")
        assert "no results" in str(err)


class TestNominatimErrors:
    def test_nominatim_error_inherits_base(self):
        assert issubclass(NominatimError, GeodeticAdvisorError)

    def test_timeout_inherits_nominatim(self):
        assert issubclass(NominatimTimeoutError, NominatimError)

    def test_http_error_inherits_nominatim(self):
        assert issubclass(NominatimHttpError, NominatimError)

    def test_connection_error_inherits_nominatim(self):
        assert issubclass(NominatimConnectionError, NominatimError)

    def test_area_not_found_inherits_nominatim(self):
        assert issubclass(AreaNotFoundError, NominatimError)

    def test_nominatim_timeout_stores_area(self):
        err = NominatimTimeoutError("Madrid")
        assert err.area_name == "Madrid"
        assert "Madrid" in str(err)

    def test_nominatim_http_error_stores_status_code(self):
        err = NominatimHttpError("Madrid", status_code=503)
        assert err.status_code == 503
        assert err.area_name == "Madrid"
        assert "503" in str(err)

    def test_nominatim_connection_error_stores_cause(self):
        cause = ConnectionRefusedError("refused")
        err = NominatimConnectionError("Madrid", cause=cause)
        assert err.cause is cause
        assert err.area_name == "Madrid"

    def test_area_not_found_stores_area(self):
        err = AreaNotFoundError("Atlantis")
        assert err.area_name == "Atlantis"
        assert "Atlantis" in str(err)


class TestWebUIErrors:
    def test_agent_invocation_error_inherits_base(self):
        assert issubclass(AgentInvocationError, GeodeticAdvisorError)

    def test_response_parsing_error_inherits_base(self):
        assert issubclass(ResponseParsingError, GeodeticAdvisorError)

    def test_agent_invocation_error_stores_query_and_cause(self):
        cause = RuntimeError("timeout")
        err = AgentInvocationError("Find CRS for Spain", cause=cause)
        assert err.query == "Find CRS for Spain"
        assert err.cause is cause
        assert "timeout" in str(err)

    def test_agent_invocation_error_without_cause(self):
        err = AgentInvocationError("test query")
        assert err.query == "test query"
        assert err.cause is None

    def test_response_parsing_error_stores_raw_response(self):
        raw = {"unexpected": "format"}
        err = ResponseParsingError(raw, detail="missing 'messages' key")
        assert err.raw_response is raw
        assert err.detail == "missing 'messages' key"
        assert "messages" in str(err)

    def test_response_parsing_error_without_detail(self):
        err = ResponseParsingError(None)
        assert err.raw_response is None
        assert "Could not parse" in str(err)


class TestExceptionCatchHierarchy:
    """Verify that catching a parent class also catches child exceptions."""

    def test_catch_base_catches_all(self):
        for exc_cls in [
            ValidationError, InvalidEpsgCodeError, EpsgLookupError,
            NominatimTimeoutError, AreaNotFoundError,
            AgentInvocationError, ResponseParsingError,
        ]:
            with pytest.raises(GeodeticAdvisorError):
                raise exc_cls("test") if exc_cls not in (
                    InvalidEpsgCodeError,
                ) else exc_cls("bad_code")

    def test_catch_nominatim_catches_children(self):
        for exc_cls in [NominatimTimeoutError, NominatimHttpError, AreaNotFoundError]:
            with pytest.raises(NominatimError):
                if exc_cls is NominatimHttpError:
                    raise exc_cls("area", status_code=500)
                else:
                    raise exc_cls("area")

    def test_catch_validation_catches_children(self):
        for exc_cls in [InvalidEpsgCodeError, InvalidBboxError, InvalidCoordinateError, InvalidQueryFormatError]:
            with pytest.raises(ValidationError):
                if exc_cls is InvalidEpsgCodeError:
                    raise exc_cls("bad")
                elif exc_cls is InvalidBboxError:
                    raise exc_cls("west", "x")
                elif exc_cls is InvalidCoordinateError:
                    raise exc_cls("x", 0)
                else:
                    raise exc_cls("q", expected="fmt")
