import polars as pl

from ._http import perform_request


def wdi_get_indicators(language: str = "en", per_page: int = 32500) -> pl.DataFrame:
    """Download all available World Bank indicators.

    Retrieves the list of all indicators supported by the World Bank API,
    including their source and associated topics.

    Parameters
    ----------
    language
        Language code for the API response. See `wdi_get_languages()` for options.
    per_page
        Number of results per page. Must be between 1 and 32,500.

    Returns
    -------
    pl.DataFrame
        A DataFrame with the columns:

        - ``indicator_id``: ID of the indicator, e.g. ``"NY.GDP.PCAP.KD"``.
        - ``indicator_name``: Name of the indicator.
        - ``source_id``: ID of the data source.
        - ``source_name``: Name of the data source.
        - ``source_note``: Notes about the indicator.
        - ``source_organization``: Organization that provides the data.
        - ``topics``: List of structs with the fields ``topic_id`` and
          ``topic_name``.

    Notes
    -----
    Data is retrieved from <https://api.worldbank.org/v2/indicators>.

    Examples
    --------
    ```python
    from wbwdi import wdi_get_indicators

    wdi_get_indicators()
    wdi_get_indicators(language="es")
    ```
    """
    indicators_raw = perform_request("indicators", language=language, per_page=per_page)

    indicators = (
        pl.DataFrame(indicators_raw)
        .rename({"id": "indicator_id", "name": "indicator_name"})
        .unnest("source")
        .rename(
            {
                "id": "source_id",
                "value": "source_name",
                "sourceNote": "source_note",
                "sourceOrganization": "source_organization",
            }
        )
        .drop("unit")
        .with_columns(
            source_id=pl.col("source_id").cast(pl.Int64),
            source_note=pl.col("source_note").replace("", None),
            source_organization=pl.col("source_organization").replace("", None),
        )
    )

    topics = (
        indicators.select("indicator_id", "topics")
        .explode("topics")
        .unnest("topics")
        .rename({"id": "topic_id", "value": "topic_name"})
        .with_columns(
            topic_id=pl.col("topic_id").cast(pl.Int64),
            topic_name=pl.col("topic_name").str.strip_chars(),
        )
        .group_by("indicator_id", maintain_order=True)
        .agg(topics=pl.struct("topic_id", "topic_name"))
    )

    return indicators.drop("topics").join(topics, on="indicator_id", how="left")
