import polars as pl

from ._http import perform_request


def wdi_get_income_levels(language: str = "en") -> pl.DataFrame:
    """Download income levels from the World Bank API.

    Income levels categorize countries by their gross national income per capita.

    Parameters
    ----------
    language
        Language code for the API response. See `wdi_get_languages()` for options.

    Returns
    -------
    pl.DataFrame
        A DataFrame with the columns:

        - ``income_level_id``: Identifier of the income level.
        - ``income_level_iso2code``: ISO 2 code of the income level.
        - ``income_level_name``: Name of the income level, e.g. ``"High income"``.

    Notes
    -----
    Data is retrieved from <https://api.worldbank.org/v2/incomeLevels>.

    Examples
    --------
    ```python
    from wbwdi import wdi_get_income_levels

    wdi_get_income_levels()
    ```
    """
    income_levels_raw = perform_request("incomeLevels", language=language)

    return pl.DataFrame(income_levels_raw).rename(
        {
            "id": "income_level_id",
            "iso2code": "income_level_iso2code",
            "value": "income_level_name",
        }
    )
