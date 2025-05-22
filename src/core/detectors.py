"""
Core ▸ detectors.py
Detecta tipo de proyecto devolviendo un score 0–1.
Puedes extender con más detectores simplemente
añadiendo otra sub-clase de Detector.
"""

from __future__ import annotations
import os
from abc import ABC, abstractmethod


class Detector(ABC):
    @abstractmethod
    def match(self, root: str) -> float: ...

    @abstractmethod
    def name(self) -> str: ...


# ───────── Flutter ─────────
class FlutterDetector(Detector):
    def match(self, root: str) -> float:
        try:
            files = os.listdir(root)
        except Exception:
            return 0.0

        score = 0.0
        if "pubspec.yaml" in files:
            score += 0.7
        if os.path.isdir(os.path.join(root, "lib")):
            score += 0.2
        if any(os.path.isdir(os.path.join(root, d)) for d in ("android", "ios")):
            score += 0.1
        return min(score, 1.0)

    def name(self) -> str:
        return "Flutter"


# ───────── Node.js ─────────
class NodeDetector(Detector):
    def match(self, root: str) -> float:
        try:
            return 1.0 if "package.json" in os.listdir(root) else 0.0
        except Exception:
            return 0.0

    def name(self) -> str:
        return "Node.js"


# ───────── Python ─────────
class PythonDetector(Detector):
    def match(self, root: str) -> float:
        try:
            files = os.listdir(root)
        except Exception:
            return 0.0

        score = 0.0
        if {"requirements.txt", "setup.py", "pyproject.toml"} & set(files):
            score += 0.6
        if any(f.endswith(".py") for f in files):
            score += 0.3
        if {"venv", ".venv", "__pycache__"} & set(files):
            score += 0.1
        return min(score, 1.0)

    def name(self) -> str:
        return "Python"


DETECTORS: list[Detector] = [FlutterDetector(), NodeDetector(), PythonDetector()]
