from __future__ import annotations

import json
import re
from pathlib import Path

PLACEHOLDER = "translation missing"
DEFAULT_LOCALE = "en"


def load_locale(path: Path) -> tuple[dict, dict]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return {}, {}
    except Exception as exc:
        raise RuntimeError(f"Failed to parse locale file {path}: {exc}") from exc

    meta = data.get("_meta")
    if not isinstance(meta, dict):
        meta = {}

    strings = data.get("strings")
    if not isinstance(strings, dict):
        strings = {
            key: value
            for key, value in data.items()
            if key != "_meta" and isinstance(value, str)
        }

    return meta, strings


def write_locale(path: Path, meta: dict, strings: dict) -> None:
    payload = {
        "_meta": dict(meta or {}),
        "strings": {key: strings[key] for key in sorted(strings.keys())},
    }
    payload["_meta"]["code"] = payload["_meta"].get("code") or path.stem
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def extract_keys_from_js(js_path: Path) -> dict[str, str]:
    """Extract translation keys from JS source.

    Recognises two call patterns used in luatools.js:
      lt("text")           -> key = "text",  english value = "text"
      t("key", "fallback") -> key = "key",   english value = "fallback"

    Keys built dynamically (e.g. t("settings." + var + ".label", ...))
    cannot be statically extracted and are handled by existing locale entries.
    """
    text = js_path.read_text(encoding="utf-8")

    keys: dict[str, str] = {}

    # Match lt("...") and lt('...')
    for m in re.finditer(r'''\blt\(\s*"([^"]+)"\s*\)''', text):
        keys[m.group(1)] = m.group(1)
    for m in re.finditer(r"""\blt\(\s*'([^']+)'\s*\)""", text):
        keys[m.group(1)] = m.group(1)

    # Match t("key", "fallback") and t('key', 'fallback')
    for m in re.finditer(r'''\bt\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)''', text):
        keys[m.group(1)] = m.group(2)
    for m in re.finditer(r"""\bt\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)""", text):
        keys[m.group(1)] = m.group(2)

    return keys


def ensure_locales(base_dir: Path, js_keys: dict[str, str]) -> int:
    en_path = base_dir / f"{DEFAULT_LOCALE}.json"
    meta_en, strings_en = load_locale(en_path)
    if not strings_en:
        raise RuntimeError(f"Default locale file {en_path} is empty or missing.")

    # Add keys found in JS but missing from en.json
    en_changed = False
    for key, value in sorted(js_keys.items()):
        if key not in strings_en:
            strings_en[key] = value
            en_changed = True
            print(f"  + en.json: \"{key}\"")

    if en_changed:
        write_locale(en_path, meta_en, strings_en)
        print(f"Updated en.json")
    else:
        # Rewrite to ensure sorted keys
        write_locale(en_path, meta_en, strings_en)

    # Sync other locale files against en.json
    updated_files = 0

    for locale_path in sorted(base_dir.glob("*.json")):
        if locale_path.name == f"{DEFAULT_LOCALE}.json":
            continue

        meta, strings = load_locale(locale_path)
        changed = False

        # Add keys present in en.json but missing from this locale
        for key in strings_en:
            if key not in strings:
                strings[key] = PLACEHOLDER
                changed = True

        # Remove keys not in en.json (stale translations)
        extra_keys = [k for k in strings if k not in strings_en]
        for key in extra_keys:
            del strings[key]
            changed = True

        if changed:
            write_locale(locale_path, meta, strings)
            updated_files += 1
            print(f"Updated {locale_path.name}")

    return updated_files


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    locales_dir = repo_root / "backend" / "locales"
    js_path = repo_root / "public" / "luatools.js"

    if not locales_dir.exists():
        raise RuntimeError(f"Locales directory not found: {locales_dir}")
    if not js_path.exists():
        raise RuntimeError(f"JS source not found: {js_path}")

    print(f"Scanning {js_path.name} for translation keys...")
    js_keys = extract_keys_from_js(js_path)
    print(f"Found {len(js_keys)} keys in JS source.\n")

    updated = ensure_locales(locales_dir, js_keys)
    if updated == 0:
        print("\nAll locale files are up to date.")
    else:
        print(f"\nUpdated {updated} locale file(s).")


if __name__ == "__main__":
    main()
