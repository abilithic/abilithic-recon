"""Engine -> UI event sink. Engine never imports Qt; it only calls these hooks.

The GUI worker provides an implementation that re-emits each call as a Qt signal
(marshalling to the UI thread). A headless CLI provides a printing implementation.
"""
from __future__ import annotations

from typing import Protocol


class EventSink(Protocol):
    def on_phase(self, phase: str) -> None: ...
    def on_progress(self, done: int, total: int) -> None: ...
    def on_log(self, level: str, message: str) -> None: ...
    def on_partial_asset(self, asset_dict: dict) -> None: ...


class NullSink:
    def on_phase(self, phase: str) -> None: pass
    def on_progress(self, done: int, total: int) -> None: pass
    def on_log(self, level: str, message: str) -> None: pass
    def on_partial_asset(self, asset_dict: dict) -> None: pass


class PrintSink:
    def on_phase(self, phase: str) -> None:
        print(f"[phase] {phase}")

    def on_progress(self, done: int, total: int) -> None:
        print(f"[progress] {done}/{total}")

    def on_log(self, level: str, message: str) -> None:
        print(f"[{level}] {message}")

    def on_partial_asset(self, asset_dict: dict) -> None:
        print(f"[asset] {asset_dict.get('hostname')}")
