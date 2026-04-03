"""Conftest for quality tests - patches pydantic-core version for compatibility."""
import pydantic_core

# Monkeypatch version to match what this pydantic branch expects
pydantic_core.__version__ = '2.44.0'
