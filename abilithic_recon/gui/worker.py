"""QThread worker that runs the engine and marshals events to the UI thread.

The engine runs entirely inside this thread. It NEVER touches widgets; it only
emits Qt signals, which Qt delivers safely on the GUI thread.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from ..core.cancel import CancelToken
from ..engine import orchestrator


class _SignalSink(QObject):
    phase = Signal(str)
    progress = Signal(int, int)
    log = Signal(str, str)
    partial = Signal(dict)

    def on_phase(self, phase): self.phase.emit(phase)
    def on_progress(self, done, total): self.progress.emit(done, total)
    def on_log(self, level, message): self.log.emit(level, message)
    def on_partial_asset(self, asset_dict): self.partial.emit(asset_dict)


class ScanWorker(QThread):
    finished_ok = Signal(object)   # ScanResult
    failed = Signal(str)

    # re-exposed for the window to connect to
    phase = Signal(str)
    progress = Signal(int, int)
    log = Signal(str, str)

    def __init__(self, domain, mode, cfg, translator, parent=None):
        super().__init__(parent)
        self._domain = domain
        self._mode = mode
        self._cfg = cfg
        self._tr = translator
        self._token = CancelToken()
        self._sink = _SignalSink()
        self._sink.phase.connect(self.phase)
        self._sink.progress.connect(self.progress)
        self._sink.log.connect(self.log)

    def cancel(self):
        self._token.cancel()

    def run(self):
        try:
            result = orchestrator.run(
                self._domain, self._mode, self._cfg,
                token=self._token, sink=self._sink, i18n=self._tr)
            self.finished_ok.emit(result)
        except ValueError as e:
            self.failed.emit(str(e))
        except Exception as e:  # never crash the UI
            self.failed.emit(repr(e))
