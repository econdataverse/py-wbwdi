# Changelog

## v2.0.0 (unreleased)

Breaking changes:

- Removed `wdi_set_format()` and the `pandas` extra. All functions now always return a Polars DataFrame; call `.to_pandas()` or `.to_arrow()` on the result instead.
- Made the implementation modules private (e.g. `wbwdi._wdi_get`). Import functions from `wbwdi` directly.
- `wdi_get()` now returns the columns in the order `entity_id`, `indicator_id`, `year`, (`quarter`, `month`), `value`.
- Progress messages are now printed to stderr.

Dependencies:

- Replaced `httpx` with the standard library, so Polars is the only runtime dependency.

Bug fixes:

- Paginated requests no longer fetch the first page twice and now send the `User-Agent` header.
- HTTP errors with a non-JSON body now raise an informative `RuntimeError`.
- `wdi_get(..., format="wide")` keeps the `quarter` and `month` columns for sub-annual data.
- `wdi_get()` respects `start_year` or `end_year` when only one of them is given.
- `wdi_get()` detects the date format per row and returns an empty DataFrame instead of failing when the API returns no data.
- `wdi_get()` takes ISO 3 codes directly from the API response and only looks up entities when a code is missing.
- `most_recent_only=True` now overrides `start_year` and `end_year` as documented.

Other changes:

- Added a documentation website built with Great Docs.
- Added type hints and NumPy-style docstrings to all public functions.
- Added `ruff` linting and formatting, tests on Python 3.10–3.13, and offline tests that mock the World Bank API (live tests are marked `online`).
- Moved the repository to the EconDataverse GitHub organization.

## v1.0.1 (2025-03-30)

- Added `wdi_set_format()` function to enable `pandas` or `arrow` output.
- Ensured that `entity_id` in `wdi_get()` is always ISO-3 code. 

## v1.0.0 (2025-02-25)

- Enhanced the `wdi_get()` function to support monthly and quarterly frequencies for specific indicators, allowing for more granular data analysis.
- Addressed problems with API requests to ensure reliable data fetching and handling of responses.
- Provided detailed examples and use cases in the package vignettes to guide users in effectively utilizing the package's features.
- Improved function documentation to clearly explain parameters, return values, and usage examples.
- Added `most_recent_only` parameter to `wdi_get()`.
- Changed wording in functions and parameters from "geography"" to "entity".

## v0.1.0 (2025-02-01)

- Initial release that includes the functions `wdi_get()`, `wdi_get_topics()`, `wdi_get_sources()`, `wdi_get_regions()`, `wdi_get_lending_types()`, `wdi_get_languages()`, `wdi_get_indicators()`, `wdi_get_income_levels()`, `wdi_get_geographies()`
