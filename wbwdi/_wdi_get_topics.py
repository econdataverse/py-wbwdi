import polars as pl

from ._http import perform_request


def wdi_get_topics(language: str = "en") -> pl.DataFrame:
    """Download topics from the World Bank API.

    Topics are the broad subject areas covered by the World Bank's datasets.

    Parameters
    ----------
    language
        Language code for the API response. See `wdi_get_languages()` for options.

    Returns
    -------
    pl.DataFrame
        A DataFrame with the columns:

        - ``topic_id``: Identifier of the topic.
        - ``topic_name``: Name of the topic, e.g. ``"Education"``.
        - ``topic_note``: Description of the topic.

    Notes
    -----
    Data is retrieved from <https://api.worldbank.org/v2/topics>.

    Examples
    --------
    ```python
    from wbwdi import wdi_get_topics

    wdi_get_topics()
    ```
    """
    topics_raw = perform_request("topics", language=language)

    return (
        pl.DataFrame(topics_raw)
        .rename({"id": "topic_id", "value": "topic_name", "sourceNote": "topic_note"})
        .with_columns(
            topic_id=pl.col("topic_id").cast(pl.Int64),
            topic_name=pl.col("topic_name").str.strip_chars(),
            topic_note=pl.col("topic_note").str.strip_chars(),
        )
    )
