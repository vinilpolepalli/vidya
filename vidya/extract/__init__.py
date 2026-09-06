"""Extractors turn a source (HTML page, Canvas API JSON, iCal feed, email) into
a Reading. They are the only place that knows what a source looks like; the
rest of the pipeline works on Readings."""

from .html import extract_html  # noqa: F401
