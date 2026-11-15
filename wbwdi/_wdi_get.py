import sys
from typing import Any, Literal

import polars as pl

from ._http import perform_request
from ._wdi_get_entities import wdi_get_entities
from ._wdi_get_sources import wdi_get_sources

FREQUENCY_SUFFIXES: dict[str, tuple[str, str]] = {
    "annual": ("", ""),
    "quarter": ("Q1", "Q4"),
    "month": ("M01", "M12"),
}

EMPTY_SCHEMA = {
    "entity_id": pl.Utf8,
    "indicator_id": pl.Utf8,
    "year": pl.Int32,
    "value": pl.Float64,
}


def wdi_get(
    entities: str | list[str],
    indicators: str | list[str],
    start_year: int | None = None,
    end_year: int | None = None,
    most_recent_only: bool = False,
    frequency: Literal["annual", "quarter", "month"] = "annual",
    language: str = "en",
    per_page: int = 1000,
    progress: bool = True,
    source: int | None = None,
    format: Literal["long", "wide"] = "long",
) -> pl.DataFrame:
    """Download World Bank indicator data for specific entities and time periods.

    Retrieves indicator data from the World Bank API for a set of entities and
    indicators and returns it in a tidy format. Multiple indicators are requested
    one at a time and combined into a single DataFrame.

    Parameters
    ----------
    entities
        One or more ISO 3 (or ISO 2) country or region codes, or ``"all"`` to
        retrieve data for all entities.
    indicators
        One or more World Bank indicator IDs, e.g.
        ``["NY.GDP.PCAP.KD", "SP.POP.TOTL"]``.
    start_year
        First year of the data. If only `start_year` is given, all years from
        `start_year` onwards are returned.
    end_year
        Last year of the data. If only `end_year` is given, all years up to and
        including `end_year` are returned.
    most_recent_only
        Whether to download only the most recent value. If ``True``, it overrides
        `start_year` and `end_year`.
    frequency
        Frequency of the data: ``"annual"``, ``"quarter"``, or ``"month"``.
    language
        Language of the request. See `wdi_get_languages()` for options.
    per_page
        Number of results per page. Must be between 1 and 32,500.
    progress
        Whether to print progress messages to stderr.
    source
        Data source ID. See `wdi_get_sources()` for options.
    format
        Whether to return the data in ``"long"`` or ``"wide"`` format.

    Returns
    -------
    pl.DataFrame
        In long format, a DataFrame with the columns:

        - ``entity_id``: ISO 3 code of the country or region.
        - ``indicator_id``: ID of the indicator, e.g. ``"NY.GDP.PCAP.KD"``.
        - ``year``: Year of the observation.
        - ``quarter``: Quarter of the observation (only for quarterly data).
        - ``month``: Month of the observation (only for monthly data).
        - ``value``: Value of the indicator.

        In wide format, the ``indicator_id`` and ``value`` columns are replaced
        by one column per indicator.

    Raises
    ------
    ValueError
        If an argument is invalid.
    RuntimeError
        If a request fails or the API returns an error.

    Examples
    --------
    Download a single indicator for multiple entities:

    ```python
    from wbwdi import wdi_get

    wdi_get(["USA", "CAN", "GBR"], "NY.GDP.PCAP.KD")
    ```

    Download a single indicator for a specific time frame:

    ```python
    wdi_get(["USA", "CAN", "GBR"], "DPANUSSPB", start_year=2012, end_year=2013)
    ```

    Download monthly or quarterly data:

    ```python
    wdi_get("AUT", "DPANUSSPB", start_year=2012, end_year=2015, frequency="month")
    wdi_get(
        "NGA", "DT.DOD.DECT.CD.TL.US", start_year=2012, end_year=2015,
        frequency="quarter",
    )
    ```

    Download multiple indicators in wide format:

    ```python
    wdi_get(["USA", "CAN", "GBR"], ["NY.GDP.PCAP.KD", "SP.POP.TOTL"], format="wide")
    ```

    Download the most recent value only:

    ```python
    wdi_get("USA", "SP.POP.TOTL", most_recent_only=True)
    ```

    Convert the result to pandas or Arrow:

    ```python
    wdi_get("USA", "SP.POP.TOTL").to_pandas()
    wdi_get("USA", "SP.POP.TOTL").to_arrow()
    ```
    """
    entities = [entities] if isinstance(entities, str) else list(entities)
    indicators = [indicators] if isinstance(indicators, str) else list(indicators)

    validate_codes(entities, "entities")
    validate_codes(indicators, "indicators")
    validate_bool(most_recent_only, "most_recent_only")
    validate_bool(progress, "progress")
    validate_year(start_year, "start_year")
    validate_year(end_year, "end_year")
    validate_frequency(frequency)
    validate_format(format)
    validate_source(source)

    if most_recent_only:
        start_year = end_year = None
    elif start_year is not None and end_year is not None and start_year > end_year:
        raise ValueError("`start_year` must be less than or equal to `end_year`.")

    date = create_date(start_year, end_year, frequency)

    data = pl.concat(
        [
            get_indicator(
                indicator,
                entities,
                date,
                most_recent_only,
                language,
                per_page,
                progress,
                source,
            )
            for indicator in indicators
        ],
        how="diagonal",
    )

    if start_year is not None and end_year is None:
        data = data.filter(pl.col("year") >= start_year)
    if end_year is not None and start_year is None:
        data = data.filter(pl.col("year") <= end_year)

    data = harmonize_entity_ids(data)

    time_columns = [c for c in ("year", "quarter", "month") if c in data.columns]
    data = data.select(["entity_id", "indicator_id", *time_columns, "value"]).sort(
        ["indicator_id", "entity_id", *time_columns]
    )

    if format == "wide":
        data = to_wide(data, ["entity_id", *time_columns])

    return data


def validate_codes(codes: list[str], name: str) -> None:
    if not codes or not all(isinstance(c, str) and c for c in codes):
        raise ValueError(f"`{name}` must be a non-empty string or list of strings.")


def validate_bool(value: Any, name: str) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"`{name}` must be either True or False.")


def validate_year(year: Any, name: str) -> None:
    if year is not None and (not isinstance(year, int) or isinstance(year, bool)):
        raise ValueError(f"`{name}` must be an integer or None.")


def validate_frequency(frequency: str) -> None:
    if frequency not in FREQUENCY_SUFFIXES:
        raise ValueError("`frequency` must be either 'annual', 'quarter', or 'month'.")


def validate_format(format: str) -> None:
    if format not in ("long", "wide"):
        raise ValueError("`format` must be either 'long' or 'wide'.")


def validate_source(source: int | None) -> None:
    if source is None:
        return
    if source not in wdi_get_sources()["source_id"].to_list():
        raise ValueError("`source` is not supported. Please call `wdi_get_sources()`.")


def create_date(
    start_year: int | None, end_year: int | None, frequency: str
) -> str | None:
    """Build the API date range; only possible when both bounds are known."""
    if start_year is None or end_year is None:
        return None
    first, last = FREQUENCY_SUFFIXES[frequency]
    return f"{start_year}{first}:{end_year}{last}"


def get_indicator(
    indicator: str,
    entities: list[str],
    date: str | None,
    most_recent_only: bool,
    language: str,
    per_page: int,
    progress: bool,
    source: int | None,
) -> pl.DataFrame:
    if progress:
        print(f"Sending requests for indicator {indicator}", file=sys.stderr)

    records = perform_request(
        resource=f"country/{';'.join(entities)}/indicator/{indicator}",
        language=language,
        per_page=per_page,
        date=date,
        most_recent_only=most_recent_only,
        source=source,
        progress=progress,
    )
    return parse_indicator(records)


def parse_indicator(records: list[dict[str, Any]]) -> pl.DataFrame:
    """Turn raw indicator records into a tidy DataFrame."""
    data = pl.DataFrame(
        {
            "indicator_id": [r["indicator"]["id"] for r in records],
            "entity_iso2code": [r["country"]["id"] for r in records],
            "entity_iso3code": [r.get("countryiso3code") or None for r in records],
            "date": [str(r["date"]) for r in records],
            "value": [
                float(r["value"]) if r.get("value") is not None else None
                for r in records
            ],
        },
        schema={
            "indicator_id": pl.Utf8,
            "entity_iso2code": pl.Utf8,
            "entity_iso3code": pl.Utf8,
            "date": pl.Utf8,
            "value": pl.Float64,
        },
    ).with_columns(
        year=pl.col("date").str.slice(0, 4).cast(pl.Int32),
        quarter=pl.col("date").str.extract(r"Q(\d)", 1).cast(pl.Int32),
        month=pl.col("date").str.extract(r"M(\d{1,2})", 1).cast(pl.Int32),
    )

    # Only keep sub-annual columns when the data actually has them
    drop = ["date"] + [
        c for c in ("quarter", "month") if data[c].null_count() == data.height
    ]
    return data.drop(drop)


def harmonize_entity_ids(data: pl.DataFrame) -> pl.DataFrame:
    """Use ISO 3 codes as `entity_id`, falling back to a lookup by ISO 2 code."""
    if data.height == 0:
        return data.drop(
            "entity_iso2code", "entity_iso3code", strict=False
        ).with_columns(entity_id=pl.lit(None, dtype=pl.Utf8))

    if data["entity_iso3code"].null_count() > 0:
        lookup = wdi_get_entities().select(
            pl.col("entity_iso2code"), pl.col("entity_id").alias("entity_iso3lookup")
        )
        data = data.join(lookup, on="entity_iso2code", how="left")
    else:
        data = data.with_columns(entity_iso3lookup=pl.lit(None, dtype=pl.Utf8))

    return data.with_columns(
        entity_id=pl.coalesce("entity_iso3code", "entity_iso3lookup", "entity_iso2code")
    ).drop("entity_iso2code", "entity_iso3code", "entity_iso3lookup")


def to_wide(data: pl.DataFrame, index: list[str]) -> pl.DataFrame:
    if data.height == 0:
        return data.select(index)
    return data.pivot(on="indicator_id", index=index, values="value")
