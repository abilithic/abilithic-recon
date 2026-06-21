"""Model/view table for assets (scales to thousands of rows; sortable/filterable)."""
from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QColor

from ..core.models import Asset
from .theme import SEV_COLORS, ACCENT, MUTED

# logical column ids -> i18n key
COLUMNS = [
    ("hostname", "col.subdomain"),
    ("resolve", "col.resolve"),
    ("live", "col.live"),
    ("ip", "col.ip"),
    ("geo", "col.geo"),
    ("tech", "col.tech"),
    ("tls", "col.tls"),
    ("severity", "col.severity"),
]


class AssetTableModel(QAbstractTableModel):
    def __init__(self, translator):
        super().__init__()
        self._rows: list[Asset] = []
        self._tr = translator

    def set_assets(self, assets: list[Asset]):
        self.beginResetModel()
        self._rows = list(assets)
        self.endResetModel()

    def asset_at(self, row: int) -> Asset | None:
        return self._rows[row] if 0 <= row < len(self._rows) else None

    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._tr(COLUMNS[section][1])
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        a = self._rows[index.row()]
        col = COLUMNS[index.column()][0]
        if role == Qt.DisplayRole:
            return self._cell(a, col)
        if role == Qt.ForegroundRole:
            if col == "live" and a.live_status == "ALIVE":
                return QColor(ACCENT)
            if col == "severity":
                return QColor(SEV_COLORS.get(self._severity(a), MUTED))
        if role == Qt.UserRole:  # for numeric sort on some columns
            if col == "tls" and a.tls and a.tls.days_left is not None:
                return a.tls.days_left
            if col == "severity":
                return {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(
                    self._severity(a), -1)
        return None

    def _cell(self, a: Asset, col: str):
        if col == "hostname":
            return a.hostname
        if col == "resolve":
            return a.resolve_status
        if col == "live":
            return a.live_status
        if col == "ip":
            return ", ".join(a.ips)
        if col == "geo":
            return ", ".join(g.country for g in a.geo if g.country)
        if col == "tech":
            return ", ".join(a.fingerprint.tech)
        if col == "tls":
            return str(a.tls.days_left) if (a.tls and a.tls.days_left is not None) else ""
        if col == "severity":
            return self._severity(a)
        return ""

    def _severity(self, a: Asset) -> str:
        return getattr(a, "_severity", "INFO")


class AssetProxy(QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setSortRole(Qt.UserRole)
        self.setFilterKeyColumn(0)

    def lessThan(self, left, right):
        l = self.sourceModel().data(left, Qt.UserRole)
        r = self.sourceModel().data(right, Qt.UserRole)
        if l is not None and r is not None:
            return l < r
        return super().lessThan(left, right)
