import datetime

import polars as pl
import pytest

from wbwdi import (
    wdi_get_entities,
    wdi_get_income_levels,
    wdi_get_indicators,
    wdi_get_languages,
    wdi_get_lending_types,
    wdi_get_regions,
    wdi_get_sources,
    wdi_get_topics,
)

from .conftest import api_error, page

ENTITY_COLUMNS = [
    "entity_id",
    "entity_name",
    "entity_iso2code",
    "entity_type",
    "capital_city",
    "region_id",
    "region_name",
    "region_iso2code",
    "admin_region_id",
    "admin_region_name",
    "admin_region_iso2code",
    "income_level_id",
    "income_level_name",
    "income_level_iso2code",
    "lending_type_id",
    "lending_type_name",
    "lending_type_iso2code",
    "longitude",
    "latitude",
]


def test_wdi_get_entities(mock_api):
    mock_api.add(
        "en/countries/all",
        page(
            [
                {
                    "id": "ABW",
                    "iso2Code": "AW",
                    "name": "Aruba",
                    "region": {
                        "id": "LCN",
                        "iso2code": "ZJ",
                        "value": "Latin America & Caribbean ",
                    },
                    "adminregion": {"id": "", "iso2code": "", "value": ""},
                    "incomeLevel": {
                        "id": "HIC",
                        "iso2code": "XD",
                        "value": "High income",
                    },
                    "lendingType": {
                        "id": "LNX",
                        "iso2code": "XX",
                        "value": "Not classified",
                    },
                    "capitalCity": "Oranjestad",
                    "longitude": "-70.0167",
                    "latitude": "12.5167",
                },
                {
                    "id": "AFE",
                    "iso2Code": "ZH",
                    "name": "Africa Eastern and Southern",
                    "region": {"id": "NA", "iso2code": "NA", "value": "Aggregates"},
                    "adminregion": {"id": "", "iso2code": "", "value": ""},
                    "incomeLevel": {
                        "id": "NA",
                        "iso2code": "NA",
                        "value": "Aggregates",
                    },
                    "lendingType": {"id": "", "iso2code": "", "value": "Aggregates"},
                    "capitalCity": "",
                    "longitude": "",
                    "latitude": "",
                },
            ]
        ),
    )

    result = wdi_get_entities()

    assert result.columns == ENTITY_COLUMNS
    assert result["entity_type"].to_list() == ["country", "aggregate"]
    assert result["region_name"].to_list() == [
        "Latin America & Caribbean",
        "Aggregates",
    ]
    assert result["longitude"].to_list() == [-70.0167, None]
    assert result["capital_city"].to_list() == ["Oranjestad", None]
    assert result["admin_region_id"].to_list() == [None, None]


def test_wdi_get_indicators(mock_api):
    mock_api.add(
        "en/indicators",
        page(
            [
                {
                    "id": "A",
                    "name": "Indicator A",
                    "unit": "",
                    "source": {"id": "2", "value": "WDI"},
                    "sourceNote": "",
                    "sourceOrganization": "World Bank",
                    "topics": [{"id": "11", "value": "Poverty "}],
                }
            ]
        ),
    )

    result = wdi_get_indicators()

    assert result.columns == [
        "indicator_id",
        "indicator_name",
        "source_id",
        "source_name",
        "source_note",
        "source_organization",
        "topics",
    ]
    assert result["source_id"].to_list() == [2]
    assert result["source_note"].to_list() == [None]
    assert result["topics"].to_list() == [[{"topic_id": 11, "topic_name": "Poverty"}]]


def test_wdi_get_income_levels(mock_api):
    mock_api.add(
        "en/incomeLevels", page([{"id": "HIC", "iso2code": "XD", "value": "High"}])
    )
    result = wdi_get_income_levels()
    assert result.rows() == [("HIC", "XD", "High")]
    assert result.columns == [
        "income_level_id",
        "income_level_iso2code",
        "income_level_name",
    ]


def test_wdi_get_languages(mock_api):
    mock_api.add(
        "languages",
        page([{"code": "en", "name": "English ", "nativeForm": "English "}]),
    )
    result = wdi_get_languages()
    assert result.rows() == [("en", "English", "English")]
    assert result.columns == ["language_code", "language_name", "native_form"]


def test_wdi_get_lending_types(mock_api):
    mock_api.add(
        "en/lendingTypes", page([{"id": "IBD", "iso2code": "XF", "value": "IBRD"}])
    )
    result = wdi_get_lending_types()
    assert result.rows() == [("IBD", "XF", "IBRD")]
    assert result.columns == [
        "lending_type_id",
        "lending_type_iso2code",
        "lending_type_name",
    ]


def test_wdi_get_regions(mock_api):
    mock_api.add(
        "en/region",
        page(
            [
                {"id": "", "code": "AFE", "iso2code": "ZH", "name": "Africa E&S "},
                {"id": "1", "code": "EAS", "iso2code": "Z4", "name": "East Asia"},
            ]
        ),
    )
    result = wdi_get_regions()
    assert result.columns == [
        "region_id",
        "region_code",
        "region_iso2code",
        "region_name",
    ]
    assert result["region_id"].to_list() == [None, 1]
    assert result["region_name"].to_list() == ["Africa E&S", "East Asia"]


def test_wdi_get_sources(mock_api):
    mock_api.add(
        "en/sources",
        page(
            [
                {
                    "id": "11",
                    "lastupdated": "2013-02-22",
                    "name": "Africa Development Indicators ",
                    "code": "ADI",
                    "description": "",
                    "url": "",
                    "dataavailability": "Y",
                    "metadataavailability": "N",
                    "concepts": "3",
                }
            ]
        ),
    )
    result = wdi_get_sources()
    assert result.rows() == [
        (
            11,
            "ADI",
            "Africa Development Indicators",
            datetime.date(2013, 2, 22),
            True,
            False,
            3,
        )
    ]


def test_wdi_get_topics(mock_api):
    mock_api.add(
        "en/topics",
        page([{"id": "1", "value": " Agriculture ", "sourceNote": "Note "}]),
    )
    result = wdi_get_topics()
    assert result.rows() == [(1, "Agriculture", "Note")]
    assert result.columns == ["topic_id", "topic_name", "topic_note"]


def test_invalid_language(mock_api):
    mock_api.add("xx/topics", api_error("150", "Unsupported language."))
    with pytest.raises(RuntimeError, match="Error code: 150"):
        wdi_get_topics(language="xx")


def test_invalid_per_page():
    with pytest.raises(ValueError, match="`per_page` must be an integer"):
        wdi_get_entities(per_page="xx")
    with pytest.raises(ValueError, match="`per_page` must be an integer"):
        wdi_get_indicators(per_page=0)


@pytest.mark.online
@pytest.mark.parametrize(
    ("function", "columns"),
    [
        (wdi_get_entities, set(ENTITY_COLUMNS)),
        (
            wdi_get_income_levels,
            {"income_level_id", "income_level_iso2code", "income_level_name"},
        ),
        (wdi_get_languages, {"language_code", "language_name", "native_form"}),
        (
            wdi_get_lending_types,
            {"lending_type_id", "lending_type_iso2code", "lending_type_name"},
        ),
        (
            wdi_get_regions,
            {"region_id", "region_code", "region_iso2code", "region_name"},
        ),
        (
            wdi_get_sources,
            {
                "source_id",
                "source_code",
                "source_name",
                "update_date",
                "is_data_available",
                "is_metadata_available",
                "concepts",
            },
        ),
        (wdi_get_topics, {"topic_id", "topic_name", "topic_note"}),
    ],
)
def test_metadata_online(function, columns):
    result = function()
    assert isinstance(result, pl.DataFrame)
    assert result.height > 0
    assert set(result.columns) == columns


@pytest.mark.online
def test_wdi_get_indicators_online():
    result = wdi_get_indicators()
    assert result.height > 1000
    assert "topics" in result.columns


@pytest.mark.online
def test_invalid_language_online():
    with pytest.raises(RuntimeError, match="Error code: 150"):
        wdi_get_income_levels(language="xx")
