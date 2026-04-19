"""Geodetic domain models.

This module defines Pydantic models for geodetic data structures used throughout
the application, including bounding boxes and CRS results.
"""

from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator


class BoundingBox(BaseModel):
    """Geographic bounding box in decimal degrees.

    Attributes:
        west: Western longitude boundary (-180 to 180).
        south: Southern latitude boundary (-90 to 90).
        east: Eastern longitude boundary (-180 to 180).
        north: Northern latitude boundary (-90 to 90).
    """

    west: float
    south: float
    east: float
    north: float

    @field_validator("south", "north")
    @classmethod
    def validate_latitude(cls, v: float, info) -> float:
        """Validate latitude is within -90 to 90 range."""
        if not -90.0 <= v <= 90.0:
            raise ValueError(f"{info.field_name} must be between -90 and 90, got {v}")
        return v

    @field_validator("west", "east")
    @classmethod
    def validate_longitude(cls, v: float, info) -> float:
        """Validate longitude is within -180 to 180 range."""
        if not -180.0 <= v <= 180.0:
            raise ValueError(f"{info.field_name} must be between -180 and 180, got {v}")
        return v

    @model_validator(mode="after")
    def validate_south_less_than_north(self) -> BoundingBox:
        """Validate south is less than or equal to north."""
        if self.south > self.north:
            raise ValueError(f"south ({self.south}) must be <= north ({self.north})")
        return self


class CRSResult(BaseModel):
    """A Coordinate Reference System search result.

    Attributes:
        epsg_code: EPSG numeric code as a string (e.g. "4326").
        crs_name: Human-readable CRS name (e.g. "WGS 84").
        area_bbox: Geographic area of use bounding box, if available.
    """

    epsg_code: str
    crs_name: str
    area_bbox: BoundingBox | None = None
