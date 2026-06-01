# LuaTools (ltsteamplugin)

Plugin for the [Millennium](https://github.com/SteamClientHomebrew/Millennium) Steam client modding framework. Injects a UI into the Steam WebKit client to manage download sources, install `.lua` scripts, apply game fixes, themes, and translations.

> **Note:** This is a community plugin. [Millennium will not offer support for this plugin on their Discord server.](https://discord.gg/luatools) — use the LuaTools Discord for help.

---

## Requirements

| Requirement | Details |
|---|---|
| **Steam (desktop client)** | Windows or Linux |
| **Millennium** | [Install guide](https://docs.steambrew.app/users/installing) |
| **Python 3** | Only needed for locale maintenance scripts (optional for end users) |

---

## Installation (end users)

### Option A — Release ZIP (recommended)

1. Install [Millennium](https://docs.steambrew.app/users/installing) if you have not already.
2. Download the latest release from [GitHub Releases](https://github.com/piqseu/ltsteamplugin/releases/latest) (`ltsteamplugin.zip`).
3. Extract the ZIP contents into your Millennium plugins folder:

   **Windows (typical paths — use whichever exists on your system):**

   ```
   C:\Program Files (x86)\Steam\plugins\ltsteamplugin\
   C:\Program Files (x86)\Steam\millennium\plugins\ltsteamplugin\
   ```

   **Linux:**

   ```
   ~/.local/share/millennium/plugins/ltsteamplugin/
   ```

   The folder must contain `plugin.json` at its root (alongside `backend/`, `public/`, etc.).

4. **Restart Steam completely** (close the client, not just the window).
5. Open **Steam → Settings → Plugins**, enable **LuaTools**, click **Save Changes**, and restart Steam again if prompted.

The plugin also supports in-app auto-updates from GitHub Releases (see `backend/update.json`).

### Option B — Clone from source

Same as above, but clone this repository into the plugins folder instead of extracting a ZIP:

```bash
git clone https://github.com/piqseu/ltsteamplugin.git ltsteamplugin
```

Then restart Steam and enable the plugin in Millennium settings.

---

## Verifying it works

After enabling the plugin and restarting Steam:

1. Open any **store page** for a game — LuaTools UI elements should appear on the page.
2. Open **Steam → Settings** — a LuaTools settings section should be available (themes, language, API sources, etc.).
3. Check Millennium logs if something fails: `%STEAM%/ext/logs` (Windows) or `~/.local/share/millennium/logs` (Linux).

---

## Project structure

```
ltsteamplugin/
├── plugin.json          # Millennium plugin manifest
├── public/
│   ├── luatools.js      # Frontend UI (~8k lines, injected into Steam WebKit)
│   ├── steamdb-webkit.css
│   └── themes/          # CSS themes + themes.json
├── backend/
│   ├── main.lua         # Entry point — lifecycle + IPC API exports
│   ├── downloads.lua    # Download & install .lua scripts
│   ├── fixes.lua        # Game fix check/apply
│   ├── api_manifest.lua # Download source (API) management
│   ├── auto_update.lua  # GitHub release updater
│   ├── settings/        # Settings schema & persistence
│   ├── locales/         # i18n JSON files (~30 languages)
│   ├── scripts/         # downloader.ps1 / downloader.sh (async downloads)
│   └── data/            # Default settings (settings.json)
├── scripts/
│   └── validate_locales.py
└── .millennium/Dist/    # Millennium framework shims (bundled)
```

### Architecture

```
Steam WebKit UI  →  public/luatools.js
                        ↓ Millennium IPC (callServerMethod)
                   backend/main.lua
                        ↓
              downloads / fixes / settings / api_manifest
                        ↓
              Steam filesystem (config/stplug-in, game folders)
```

On load, the backend copies `luatools.js` and `steamdb-webkit.css` into `{Steam}/steamui/webkit/` and injects them into the Steam browser.

---

## Development setup

### 1. Place the repo in the plugins folder

The simplest workflow is to clone directly into your plugins directory:

**Windows (PowerShell, run as Administrator if needed):**

```powershell
cd "C:\Program Files (x86)\Steam\plugins"
git clone https://github.com/piqseu/ltsteamplugin.git ltsteamplugin
```

**Linux:**

```bash
cd ~/.local/share/millennium/plugins
git clone https://github.com/piqseu/ltsteamplugin.git ltsteamplugin
```

Alternatively, clone anywhere and create a **symlink** to the plugins folder.

### 2. Edit and reload

| What you change | How to apply |
|---|---|
| `backend/*.lua` | **Full Steam restart** required |
| `public/luatools.js` or CSS | **Full Steam restart** (files are copied to `steamui/webkit/` on load) |
| `backend/locales/*.json` | Restart Steam (or reload via settings if already running) |

There is no separate build step — the plugin runs directly from source. Legacy Python files under `backend/` are reference-only and are being removed; the active backend is **Lua** (`plugin.json` → `"backendType": "lua"`).

### 3. Restart Steam quickly (Windows)

```cmd
backend\restart_steam.cmd
```

This kills `steam.exe` and relaunches it with `-clearbeta`.

### 4. Sync translation files

When you add or change strings in `public/luatools.js`, run:

```bash
python scripts/validate_locales.py
```

This script:

- Scans `luatools.js` for `lt("...")` and `t("key", "fallback")` calls
- Adds missing keys to `backend/locales/en.json`
- Propagates new keys to all other locale files (with `"translation missing"` placeholder)

Commit the updated locale files together with your JS changes.

---

## Configuration

Default settings live in `backend/data/settings.json`. User overrides are persisted at runtime in the same file. Key options:

| Setting | Description |
|---|---|
| `general.language` | UI language (falls back to `en`) |
| `general.theme` | Active CSS theme (`original`, `dark`, `dracula`, …) |
| `general.fastDownload` | Use async PowerShell/Bash downloader |
| `general.morrenusApiKey` | Optional API key for Morrenus/hubcapmanifest stats |

Open **Steam → Settings → LuaTools** to change these in the UI.

---

## Known issues (v8.x)

- `UnFixGame` and `GetInstalledFixes` are **stubs** — not yet ported from the Python backend.
- `fixes.uninstall_fix` is referenced in `main.lua` but not implemented in `fixes.lua`.
- `public/luatools-icon.png` is missing from the repository (icon fallback may not work).
- Legacy Python files (`manager.py`, `options.py`, etc.) remain as reference and will be removed.

See [v8.0.1 release notes](https://github.com/piqseu/ltsteamplugin/releases/tag/v8.0.1) for install-specific notes.

---

## Contributing

1. Fork the repository and create a feature branch.
2. Keep changes focused — small PRs are easier to review.
3. Run `python scripts/validate_locales.py` if you touch `luatools.js` strings.
4. Test manually in Steam after backend or frontend changes.
5. Open a PR against `main` with a clear description and test plan.

Good first contributions: documentation, locale translations, replacing `alert()` with the existing `ShowLuaToolsAlert()` modal, bug fixes, completing Lua port stubs.

---

## Links

- [Releases](https://github.com/piqseu/ltsteamplugin/releases)
- [LuaTools Discord](https://discord.gg/luatools)
- [Millennium docs](https://docs.steambrew.app/)
- [Millennium plugin development](https://docs.steambrew.app/developers/plugins/learn)

---

## License / redistribution

The releases are open source. Please do not redistribute this project under a different name or brand.
