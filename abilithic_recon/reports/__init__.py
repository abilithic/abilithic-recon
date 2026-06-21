"""Report builders. All render from a ScanResult - the single source of truth."""
from .json_report import save_json, load_json
from .csv_report import save_csv
from .html_report import save_html

__all__ = ["save_json", "load_json", "save_csv", "save_html"]
