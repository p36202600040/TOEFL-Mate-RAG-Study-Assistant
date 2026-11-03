"""Test validasi konfigurasi tanpa membaca nilai rahasia."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config


def test_current_settings_are_valid():
    config.validate_settings()


def test_invalid_settings_are_rejected(monkeypatch):
    monkeypatch.setattr(config, "TOP_K", 0)
    with pytest.raises(ValueError, match="TOP_K"):
        config.validate_settings()
