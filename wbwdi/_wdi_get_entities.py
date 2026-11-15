import polars as pl

from ._http import perform_request


def wdi_get_entities(language: str = "en", per_page: int = 1000) -> pl.DataFrame:
    """Download all countries and regions from the World Bank API.

    Retrieves the entities (countries and aggregates) supported by the World Bank
    API, including their region, income level, lending type, capital city, and
    coordinates.

    Parameters
    ----------
    language
        Language code for the API response, e.g. ``"en"``, ``"es"``, or ``"fr"``.
        See `wdi_get_languages()` for options.
    per_page
        Number of records per request. Must be between 1 and 32,500.

    Returns
    -------
    pl.DataFrame
        A DataFrame with the columns:

        - ``entity_id``: ISO 3 code of the entity.
        - ``entity_name``: Name of the entity.
        - ``entity_iso2code``: ISO 2 code of the entity.
        - ``entity_type``: Either ``"country"`` or ``"aggregate"``.
        - ``capital_city``: Name of the capital city.
        - ``region_id``, ``region_name``, ``region_iso2code``: Region.
        - ``admin_region_id``, ``admin_region_name``, ``admin_region_iso2code``:
          Administrative region.
        - ``income_level_id``, ``income_level_name``, ``income_level_iso2code``:
          Income level.
        - ``lending_type_id``, ``lending_type_name``, ``lending_type_iso2code``:
          Lending type.
        - ``longitude``: Longitude of the capital city.
        - ``latitude``: Latitude of the capital city.

    Notes
    -----
    Data is retrieved from <https://api.worldbank.org/v2/countries>.

    Examples
    --------
    ```python
    from wbwdi import wdi_get_entities

    wdi_get_entities()
    wdi_get_entities(language="es")
    ```
    """
    entities_raw = perform_request("countries/all", language, per_page)

    entities = (
        pl.DataFrame(entities_raw)
        .rename(
            {"id": "entity_id", "iso2Code": "entity_iso2code", "name": "entity_name"}
        )
        .unnest("region")
        .rename(
            {"id": "region_id", "iso2code": "region_iso2code", "value": "region_name"}
        )
        .unnest("adminregion")
        .rename(
            {
                "id": "admin_region_id",
                "iso2code": "admin_region_iso2code",
                "value": "admin_region_name",
            }
        )
        .unnest("incomeLevel")
        .rename(
            {
                "id": "income_level_id",
                "iso2code": "income_level_iso2code",
                "value": "income_level_name",
            }
        )
        .unnest("lendingType")
        .rename(
            {
                "id": "lending_type_id",
                "iso2code": "lending_type_iso2code",
                "value": "lending_type_name",
            }
        )
        .rename({"capitalCity": "capital_city"})
        .with_columns(
            pl.col(pl.Utf8).str.strip_chars().replace("", None),
        )
        .with_columns(
            longitude=pl.col("longitude").cast(pl.Float64),
            latitude=pl.col("latitude").cast(pl.Float64),
            entity_type=pl.when(pl.col("region_name") == "Aggregates")
            .then(pl.lit("aggregate"))
            .otherwise(pl.lit("country")),
        )
    )

    return entities.select(
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
    )
