import polars as pl


def wdi_search(
    data: pl.DataFrame,
    keywords: list[str],
    columns: list[str] | None = None,
) -> pl.DataFrame:
    """Search for keywords in DataFrame columns.

    Returns the rows of `data` where at least one keyword appears in at least
    one of the searched columns. The search is case-insensitive. List and struct
    columns are not supported.

    Parameters
    ----------
    data
        DataFrame to search, e.g. the result of `wdi_get_indicators()`.
    keywords
        Keywords to search for.
    columns
        Columns to search. If ``None``, all columns except list and struct
        columns are searched.

    Returns
    -------
    pl.DataFrame
        The rows of `data` that match at least one keyword, with the same
        columns as `data`.

    Raises
    ------
    TypeError
        If `keywords` or `columns` is not a list of strings.
    ValueError
        If `columns` contains a list or struct column.

    Examples
    --------
    ```python
    from wbwdi import wdi_get_indicators, wdi_search

    indicators = wdi_get_indicators()

    wdi_search(indicators, keywords=["inequality", "gender"])
    wdi_search(indicators, keywords=["inequality"], columns=["indicator_name"])
    ```
    """
    if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
        raise TypeError("`keywords` must be a list of strings.")

    if columns is not None and (
        not isinstance(columns, list) or not all(isinstance(c, str) for c in columns)
    ):
        raise TypeError("`columns` must be a list of strings or `None`.")

    if columns is None:
        columns = [c for c in data.columns if not is_nested(data[c].dtype)]
    else:
        for column in columns:
            if is_nested(data[column].dtype):
                raise ValueError(
                    f"Column '{column}' has unsupported type {data[column].dtype}. "
                    "Struct or list columns are currently not supported."
                )

    if not keywords or not columns:
        return data.head(0)

    return data.filter(
        pl.any_horizontal(
            pl.col(column)
            .cast(pl.Utf8)
            .str.contains_any(keywords, ascii_case_insensitive=True)
            .fill_null(False)
            for column in columns
        )
    )


def is_nested(dtype: pl.DataType) -> bool:
    return isinstance(dtype, (pl.List, pl.Struct))
