from __future__ import annotations

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    Qt,
    Property,
    Signal,
)

from MOMM_backend.enums import EntryType
from MOMM_backend.models import MainModlist


class MainListModel(QAbstractListModel):
    countChanged = Signal()

    NameRole = int(Qt.ItemDataRole.UserRole) + 1
    EntryTypeRole = NameRole + 1
    HasDllRole = NameRole + 2
    ActiveRole = NameRole + 3
    ReviewStatusRole = NameRole + 4
    CompatibilityRole = NameRole + 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries = []

    def roleNames(self):
        return {
            self.NameRole: b"name",
            self.EntryTypeRole: b"entryType",
            self.HasDllRole: b"hasDll",
            self.ActiveRole: b"active",
            self.ReviewStatusRole: b"reviewStatus",
            self.CompatibilityRole: b"compatibility",
        }

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._entries)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._entries):
            return None

        entry = self._entries[index.row()]

        if role == self.NameRole:
            return entry.name

        if role == self.EntryTypeRole:
            return entry.entry_type.value

        if role == self.HasDllRole:
            return entry.has_dll

        if role == self.ActiveRole:
            return entry.active

        if role == self.ReviewStatusRole:
            return entry.review_status.value

        if role == self.CompatibilityRole:
            return {
                engine_id: {
                    "compatible": state.compatible,
                    "active": state.active,
                }
                for engine_id, state in entry.compatibility.items()
            }

        return None

    @Property(int, notify=countChanged)
    def count(self):
        return len(self._entries)

    def set_main_list(self, main_list: MainModlist | None):
        self.beginResetModel()
        self._entries = (
            [entry.clone() for entry in main_list.entries]
            if main_list is not None
            else []
        )
        self.endResetModel()
        self.countChanged.emit()
