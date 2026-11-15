import polars as pl

from ._http import perform_request


def wdi_get_lending_types(language: str = "en") -> pl.DataFrame:
    """Download lending types from the World Bank API.

    Lending types classify countries by the financial terms available to them
    from the World Bank.

    Parameters
    ----------
    language
        Language code for the API response. See `wdi_get_languages()` for options.

    Returns
    -------
    pl.DataFrame
        A DataFrame with the columns:

        - ``lending_type_id``: Identifier of the lending type.
        - ``lending_type_iso2code``: ISO 2 code of the lending type.
        - ``lending_type_name``: Name of the lending type, e.g. ``"IBRD"``.

    Notes
    -----
    Data is retrieved from <https://api.worldbank.org/v2/lendingTypes>.

    Examples
    --------
    ```python
    from wbwdi import wdi_get_lending_types

    wdi_get_lending_types()
    ```
    """
    lending_types_raw = perform_request("lendingTypes", language=language)

    return pl.DataFrame(lending_types_raw).rename(
        {
            "id": "lending_type_id",
            "iso2code": "lending_type_iso2code",
            "value": "lending_type_name",
        }
    )
