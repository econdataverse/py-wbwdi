import polars as pl

from ._http import perform_request


def wdi_get_languages() -> pl.DataFrame:
    """Download the languages supported by the World Bank API.

    Returns
    -------
    pl.DataFrame
        A DataFrame with the columns:

        - ``language_code``: Language code, e.g. ``"en"``.
        - ``language_name``: Name of the language, e.g. ``"English"``.
        - ``native_form``: Native name of the language.

    Notes
    -----
    Data is retrieved from <https://api.worldbank.org/v2/languages>.

    Examples
    --------
    ```python
    from wbwdi import wdi_get_languages

    wdi_get_languages()
    ```
    """
    languages_raw = perform_request("languages")

    return (
        pl.DataFrame(languages_raw)
        .rename(
            {
                "code": "language_code",
                "name": "language_name",
                "nativeForm": "native_form",
            }
        )
        .with_columns(
            language_name=pl.col("language_name").str.strip_chars_end(),
            native_form=pl.col("native_form").str.strip_chars_end(),
        )
    )
