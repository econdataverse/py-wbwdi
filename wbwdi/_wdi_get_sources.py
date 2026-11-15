import polars as pl

from ._http import perform_request


def wdi_get_sources(language: str = "en") -> pl.DataFrame:
    """Download data sources from the World Bank API.

    Parameters
    ----------
    language
        Language code for the API response. See `wdi_get_languages()` for options.

    Returns
    -------
    pl.DataFrame
        A DataFrame with the columns:

        - ``source_id``: Identifier of the data source.
        - ``source_code``: Code of the data source.
        - ``source_name``: Name of the data source, e.g.
          ``"World Development Indicators"``.
        - ``update_date``: Date of the last update.
        - ``is_data_available``: Whether data is available.
        - ``is_metadata_available``: Whether metadata is available.
        - ``concepts``: Number of concepts defined for the data source.

    Notes
    -----
    Data is retrieved from <https://api.worldbank.org/v2/sources>.

    Examples
    --------
    ```python
    from wbwdi import wdi_get_sources

    wdi_get_sources()
    ```
    """
    sources_raw = perform_request("sources", language=language)

    return (
        pl.DataFrame(sources_raw)
        .rename(
            {
                "id": "source_id",
                "code": "source_code",
                "name": "source_name",
                "lastupdated": "update_date",
                "dataavailability": "is_data_available",
                "metadataavailability": "is_metadata_available",
            }
        )
        .with_columns(
            source_id=pl.col("source_id").cast(pl.Int64),
            source_name=pl.col("source_name").str.strip_chars(),
            update_date=pl.col("update_date").str.to_date(),
            is_data_available=pl.col("is_data_available") == "Y",
            is_metadata_available=pl.col("is_metadata_available") == "Y",
            concepts=pl.col("concepts").cast(pl.Int64),
        )
        .select(
            "source_id",
            "source_code",
            "source_name",
            "update_date",
            "is_data_available",
            "is_metadata_available",
            "concepts",
        )
    )
