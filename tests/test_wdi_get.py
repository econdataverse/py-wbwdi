import polars as pl
import pytest

from wbwdi import wdi_get

from .conftest import page


def obs(iso2, iso3, indicator, date, value):
    return {
        "indicator": {"id": indicator, "value": indicator},
        "country": {"id": iso2, "value": iso2},
        "countryiso3code": iso3,
        "date": date,
        "value": value,
        "unit": "",
        "obs_status": "",
        "decimal": 1,
    }


GDP = "NY.GDP.PCAP.KD"
POP = "SP.POP.TOTL"

ENTITIES = [
    {
        "id": "WLD",
        "iso2Code": "1W",
        "name": "World",
        "region": {"id": "NA", "iso2code": "NA", "value": "Aggregates"},
        "adminregion": {"id": "", "iso2code": "", "value": ""},
        "incomeLevel": {"id": "NA", "iso2code": "NA", "value": "Aggregates"},
        "lendingType": {"id": "", "iso2code": "", "value": "Aggregates"},
        "capitalCity": "",
        "longitude": "",
        "latitude": "",
    }
]


def test_long_format(mock_api):
    mock_api.add(
        f"en/country/US;CA/indicator/{GDP}",
        page(
            [
                obs("US", "USA", GDP, "2021", 2.0),
                obs("US", "USA", GDP, "2020", 1.0),
                obs("CA", "CAN", GDP, "2020", None),
            ]
        ),
    )

    result = wdi_get(["US", "CA"], GDP, start_year=2020, end_year=2021, progress=False)

    assert result.columns == ["entity_id", "indicator_id", "year", "value"]
    assert result.schema["year"] == pl.Int32
    assert result.schema["value"] == pl.Float64
    assert result.rows() == [
        ("CAN", GDP, 2020, None),
        ("USA", GDP, 2020, 1.0),
        ("USA", GDP, 2021, 2.0),
    ]
    assert mock_api.requests[0].query["date"] == "2020:2021"


def test_missing_iso3_codes_are_looked_up(mock_api):
    mock_api.add(
        f"en/country/1W/indicator/{GDP}",
        page([obs("1W", "", GDP, "2020", 1.0)]),
    )
    mock_api.add("en/countries/all", page(ENTITIES))

    result = wdi_get("1W", GDP, progress=False)

    assert result["entity_id"].to_list() == ["WLD"]


def test_multiple_indicators_wide(mock_api):
    mock_api.add(
        f"en/country/USA/indicator/{GDP}",
        page([obs("US", "USA", GDP, "2020", 1.0)]),
    )
    mock_api.add(
        f"en/country/USA/indicator/{POP}",
        page([obs("US", "USA", POP, "2020", 3.0)]),
    )

    result = wdi_get("USA", [GDP, POP], format="wide", progress=False)

    assert result.columns == ["entity_id", "year", GDP, POP]
    assert result.rows() == [("USA", 2020, 1.0, 3.0)]


def test_quarterly_data(mock_api):
    indicator = "DT.DOD.DECT.CD.TL.US"
    mock_api.add(
        f"en/country/NGA/indicator/{indicator}",
        page(
            [
                obs("NG", "NGA", indicator, "2020Q2", 2.0),
                obs("NG", "NGA", indicator, "2020Q1", 1.0),
            ]
        ),
    )

    long = wdi_get("NGA", indicator, 2020, 2021, frequency="quarter", progress=False)
    wide = wdi_get(
        "NGA",
        indicator,
        2020,
        2021,
        frequency="quarter",
        format="wide",
        progress=False,
    )

    assert mock_api.requests[0].query["date"] == "2020Q1:2021Q4"
    assert long.columns == ["entity_id", "indicator_id", "year", "quarter", "value"]
    assert long["quarter"].to_list() == [1, 2]
    assert wide.columns == ["entity_id", "year", "quarter", indicator]
    assert wide.height == 2


def test_monthly_data(mock_api):
    indicator = "DPANUSSPB"
    mock_api.add(
        f"en/country/AUT/indicator/{indicator}",
        page(
            [
                obs("AT", "AUT", indicator, "2012M12", 2.0),
                obs("AT", "AUT", indicator, "2012M01", 1.0),
            ]
        ),
    )

    result = wdi_get("AUT", indicator, 2012, 2012, frequency="month", progress=False)

    assert mock_api.requests[0].query["date"] == "2012M01:2012M12"
    assert result.columns == ["entity_id", "indicator_id", "year", "month", "value"]
    assert result["month"].to_list() == [1, 12]


def test_date_format_is_detected_per_row(mock_api):
    mock_api.add(
        f"en/country/USA/indicator/{GDP}",
        page(
            [
                obs("US", "USA", GDP, "2020", 1.0),
                obs("US", "USA", GDP, "2020Q1", 2.0),
            ]
        ),
    )

    result = wdi_get("USA", GDP, progress=False)

    assert result["quarter"].to_list() == [None, 1]


def test_empty_result(mock_api):
    mock_api.add(f"en/country/USA/indicator/{GDP}", [{"page": 1, "pages": 0}, None])

    long = wdi_get("USA", GDP, progress=False)
    wide = wdi_get("USA", GDP, format="wide", progress=False)

    assert long.height == 0
    assert long.columns == ["entity_id", "indicator_id", "year", "value"]
    assert wide.height == 0
    assert wide.columns == ["entity_id", "year"]


@pytest.fixture
def gdp_2019_2021(mock_api):
    mock_api.add(
        f"en/country/USA/indicator/{GDP}",
        page([obs("US", "USA", GDP, str(y), float(y)) for y in (2019, 2020, 2021)]),
    )
    return mock_api


def test_only_start_year(gdp_2019_2021):
    result = wdi_get("USA", GDP, start_year=2020, progress=False)

    assert result["year"].to_list() == [2020, 2021]
    assert "date" not in gdp_2019_2021.requests[0].query


def test_only_end_year(gdp_2019_2021):
    result = wdi_get("USA", GDP, end_year=2020, progress=False)

    assert result["year"].to_list() == [2019, 2020]
    assert "date" not in gdp_2019_2021.requests[0].query


def test_most_recent_only_overrides_years(gdp_2019_2021):
    result = wdi_get(
        "USA",
        GDP,
        start_year=2020,
        end_year=2020,
        most_recent_only=True,
        progress=False,
    )

    query = gdp_2019_2021.requests[0].query
    assert query["mrv"] == "1"
    assert "date" not in query
    assert result.height == 3


def test_progress_messages(gdp_2019_2021, capsys):
    wdi_get("USA", GDP)
    assert f"Sending requests for indicator {GDP}" in capsys.readouterr().err


def test_valid_source(gdp_2019_2021):
    gdp_2019_2021.add(
        "en/sources",
        page(
            [
                {
                    "id": "2",
                    "lastupdated": "2025-01-01",
                    "name": "WDI",
                    "code": "WDI",
                    "dataavailability": "Y",
                    "metadataavailability": "Y",
                    "concepts": "3",
                }
            ]
        ),
    )

    wdi_get("USA", GDP, source=2, progress=False)

    assert gdp_2019_2021.requests[-1].query["source"] == "2"

    with pytest.raises(ValueError, match="`source` is not supported"):
        wdi_get("USA", GDP, source=999999, progress=False)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"most_recent_only": "FALSCH"}, "`most_recent_only` must be either"),
        ({"progress": None}, "`progress` must be either"),
        ({"frequency": "daily"}, "`frequency` must be either"),
        ({"format": "compact"}, "`format` must be either"),
        ({"start_year": "2020"}, "`start_year` must be an integer"),
        ({"end_year": 2020.5}, "`end_year` must be an integer"),
        ({"start_year": 2021, "end_year": 2020}, "`start_year` must be less"),
        ({"entities": []}, "`entities` must be a non-empty"),
        ({"indicators": [""]}, "`indicators` must be a non-empty"),
    ],
)
def test_invalid_arguments(kwargs, message):
    arguments = {"entities": "USA", "indicators": GDP, **kwargs}
    with pytest.raises(ValueError, match=message):
        wdi_get(**arguments)


@pytest.mark.online
def test_wdi_get_online():
    result = wdi_get(
        ["US", "CAN", "WLD"], [GDP, POP], start_year=2020, end_year=2021, progress=False
    )
    assert set(result["entity_id"]) == {"USA", "CAN", "WLD"}
    assert set(result["indicator_id"]) == {GDP, POP}
    assert result.height == 12


@pytest.mark.online
def test_wdi_get_all_entities_online():
    result = wdi_get("all", GDP, start_year=2020, end_year=2020, progress=False)
    assert result.height > 200
    assert result["entity_id"].str.len_chars().eq(3).all()


@pytest.mark.online
def test_wdi_get_quarterly_online():
    result = wdi_get(
        "NGA",
        "DT.DOD.DECT.CD.TL.US",
        start_year=2020,
        end_year=2021,
        frequency="quarter",
        format="wide",
        progress=False,
    )
    assert result.columns[:3] == ["entity_id", "year", "quarter"]


@pytest.mark.online
def test_wdi_get_invalid_indicator_online():
    with pytest.raises(RuntimeError, match="Error code: 120"):
        wdi_get("US", "INVALID.INDICATOR", progress=False)
