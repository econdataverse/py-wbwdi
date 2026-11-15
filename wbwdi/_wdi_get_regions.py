import polars as pl

from ._http import perform_request


def wdi_get_regions(language: str = "en") -> pl.DataFrame:
    """Download regions from the World Bank API.

    Parameters
    ----------
    language
        Language code for the API response. See `wdi_get_languages()` for options.

    Returns
    -------
    pl.DataFrame
        A DataFrame with the columns:

        - ``region_id``: Numeric identifier of the region. Only available for
          the seven main geographic regions.
        - ``region_code``: Code of the region.
        - ``region_iso2code``: ISO 2 code of the region.
        - ``region_name``: Name of the region.

    Notes
    -----
    Data is retrieved from <https://api.worldbank.org/v2/region>.

    Examples
    --------
    ```python
    from wbwdi import wdi_get_regions

    wdi_get_regions()
    ```
    """
    regions_raw = perform_request("region", language=language)

    return (
        pl.DataFrame(regions_raw)
        .rename(
            {
                "id": "region_id",
                "code": "region_code",
                "iso2code": "region_iso2code",
                "name": "region_name",
            }
        )
        .with_columns(
            region_id=pl.col("region_id").replace("", None).cast(pl.Int64),
            region_name=pl.col("region_name").str.strip_chars(),
        )
    )
