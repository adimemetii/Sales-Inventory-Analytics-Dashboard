"""Fast translation and smoke-test checks for the Streamlit dashboard."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.i18n import TRANSLATIONS


def check_translation_keys() -> None:
    languages = set(TRANSLATIONS)
    expected = set(TRANSLATIONS["en"])
    assert languages == {"en", "sq", "de"}, f"Unexpected languages: {languages}"
    for lang, values in TRANSLATIONS.items():
        assert set(values) == expected, f"{lang} does not have the same translation keys"
        assert all(str(value).strip() for value in values.values()), f"{lang} has empty translations"


def scan_source() -> list[str]:
    """Find obvious literal UI strings left in Streamlit calls.

    The dashboard still contains data-driven labels and Markdown fragments by
    design; this scan reports only direct literal calls that should be moved to
    the translation layer.
    """

    findings: list[str] = []
    for filename in ("app.py", "utils/charts.py", "utils/styling.py"):
        path = ROOT / filename
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in {"caption", "warning", "error", "info", "download_button", "tabs"}:
                continue
            if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
                continue
            value = node.args[0].value.strip()
            if value and not value.startswith("<"):
                findings.append(f"{filename}:{node.lineno}: literal {node.func.attr} text: {value[:80]}")
    return findings


def check_app_languages() -> None:
    from streamlit.testing.v1 import AppTest

    app_path = str(ROOT / "app.py")
    for language in ("en", "sq", "de"):
        app = AppTest.from_file(app_path)
        app.session_state["lang"] = language
        app.session_state["locale"] = language
        app.run(timeout=90)
        assert not app.exception, f"AppTest exception for {language}: {app.exception}"


def main() -> int:
    check_translation_keys()
    findings = scan_source()
    if findings:
        print("Literal UI scan findings (data-driven or legacy text may remain):")
        for finding in findings:
            print(f"- {finding}")
    check_app_languages()
    print("i18n keys PASS")
    print("AppTest en/sq/de PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
