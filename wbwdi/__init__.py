"""Seamless access to World Bank World Development Indicators with Polars."""

from ._wdi_get import wdi_get
from ._wdi_get_entities import wdi_get_entities
from ._wdi_get_income_levels import wdi_get_income_levels
from ._wdi_get_indicators import wdi_get_indicators
from ._wdi_get_languages import wdi_get_languages
from ._wdi_get_lending_types import wdi_get_lending_types
from ._wdi_get_regions import wdi_get_regions
from ._wdi_get_sources import wdi_get_sources
from ._wdi_get_topics import wdi_get_topics
from ._wdi_search import wdi_search

__all__ = [
    "wdi_get",
    "wdi_get_entities",
    "wdi_get_income_levels",
    "wdi_get_indicators",
    "wdi_get_languages",
    "wdi_get_lending_types",
    "wdi_get_regions",
    "wdi_get_sources",
    "wdi_get_topics",
    "wdi_search",
]
