"""UI reporting abstraction for progress feedback."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class UIReporter(ABC):
    """Abstract base class for UI reporting."""

    @abstractmethod
    def report_language_start(self, language: str) -> None:
        """Report starting processing for a language."""
        pass

    @abstractmethod
    def report_screenshot_start(self, index: int, total: int, name: str) -> None:
        """Report starting processing for a screenshot."""
        pass

    @abstractmethod
    def report_screenshot_success(self, paths: list[Path]) -> None:
        """Report successful screenshot generation."""
        pass

    @abstractmethod
    def report_screenshot_error(self, error: Exception) -> None:
        """Report screenshot generation error."""
        pass


class ConsoleReporter(UIReporter):
    """Console-based UI reporter."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def report_language_start(self, language: str) -> None:
        """Report starting processing for a language."""
        print(f"\n🌍 Processing: {language}")

    def report_screenshot_start(self, index: int, total: int, name: str) -> None:
        """Report starting processing for a screenshot."""
        if self.verbose:
            print(f"\n  Processing screenshot {index}/{total}: {name}")
        else:
            print(f"  [{index}/{total}] {name}... ", end="", flush=True)

    def report_screenshot_success(self, paths: list[Path]) -> None:
        """Report successful screenshot generation."""
        if self.verbose:
            for path in paths:
                resolution_dir = path.parent.name
                print(f"    ✓ {resolution_dir}/{path.name}")
                logger.debug(f"Generated: {path}")
        else:
            print("✓")

    def report_screenshot_error(self, error: Exception) -> None:
        """Report screenshot generation error."""
        if not self.verbose:
            print("✗")
        logger.error(f"Failed to generate screenshot: {error}")
