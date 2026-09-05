# Baserow 2.3.3 Plugin Development & Install — Complete Runbook

> Proven live on 2026-09-05 against `baserow/baserow:2.3.3` all-in-one image
> running rootless Docker on the DMZ host (`ext-host-co` / 192.168.133.110).
> Endpoint verified: `GET /api/coveredon-test/ping/` → 200 with JSON payload.

## Environment facts (2.3.3 all-in-one image)

| Fact | Value |
|---|---|
| Image | `baserow/baserow:2.3.3` |
| Python (backend venv) | **3.14** (`requires-python ==3.14.*`, base image `python:3.14.6-slim-trixie`) |
| Venv path | `/baserow/venv` — built with **uv sync** |
| pip in venv | **NOT present by default** (uv venvs ship without pip) |
| System python | 3.14 (separate from venv — its pip installs to the WRONG place) |
| Plugin dir | `/baserow/data/plugins/` (docker volume `baserow_data` — survives container recreation) |
| Install scripts | `/baserow/plugins/install_plugin.sh`, `uninstall_plugin.sh`, `list_plugins.sh` |
| Plugin discovery | `backend/src/baserow/config/settings/base.py`: any dir under `/baserow/plugins` (env `BASEROW_PLUGIN_DIR`) containing a `backend/` subdir is added to `INSTALLED_APPS` by **folder name** |
| API registration | Plugin class (subclass of `baserow.core.registries.Plugin`) registered in `plugin_registry`; `get_api_urls()` routes appear under `/api/` |
| Frontend build | Only runs if `web-frontend/` dir exists in the plugin; needs `yarn` build (skipped for backend-only plugins) |

## CRITICAL: the official installer is broken for backend plugins

`install_plugin.sh` calls **naked `pip3`**, which in this image resolves to the
SYSTEM python's pip — NOT the uv-built `/baserow/venv`. Result: wheel installs
to system user-site (`Defaulting to user installation...`), invisible to the
backend. On restart Django tries `import <plugin_module>` from the venv, fails,
and **the whole backend crash-loops (502/500 on every endpoint)**.

Recovery from that state (proven):

```bash
docker exec baserow ./baserow.sh uninstall-plugin <plugin_name>
docker restart baserow
```

(`uninstall-plugin` pip-uninstalls AND deletes the plugin folder. Note the venv
path is NOT `/baserow/venv/bin/pip` — pip doesn't exist there until you add it.)

## ✅ WORKING install recipe (attempt #2, verified)

Step order matters. `<module>` = plugin folder name (also the Django app name).

```bash
# 1. Lay down plugin files + ownership fix (safe, backend not restarted yet)
docker exec baserow ./baserow.sh install-plugin \
  --url https://api.github.com/repos/OWNER/REPO/tarball
# (--git does NOT work: the image ships without the git binary)

# 2. Bootstrap pip into the uv venv (one-time per container)
docker exec -u root baserow /baserow/venv/bin/python -m ensurepip

# 3. Install the plugin INTO the real venv
docker exec baserow /baserow/venv/bin/python -m pip install \
  /baserow/data/plugins/<module>/backend

# 4. Restart so Django picks it up
docker restart baserow

# 5. Verify (backend takes ~20-30s to boot)
curl http://baserow.dmz.local:8682/api/<module>/ping/
```

## Required repo layout (validated)

```
repo-root/
├── README.md
└── plugins/
    └── <module_name>/            # folder name = Django app name
        └── backend/
            ├── setup.py          # name="<anything>", packages from src/
            └── src/
                └── <module_name>/
                    ├── __init__.py
                    ├── apps.py           # AppConfig.ready() registers Plugin
                    ├── plugins.py         # Plugin subclass w/ get_api_urls()
                    └── api/
                        ├── __init__.py
                        ├── urls.py       # app_name = "<module_name>.api"
                        └── views.py      # DRF APIViews
```

Note for `--url` installs: the GitHub tarball wraps everything in
`<owner>-<repo>-<sha>/` — the script handles that (expects `*/plugins/*/`).

## Minimal code skeleton (all of it — this is a complete plugin)

`apps.py`:
```python
from baserow.core.registries import plugin_registry
from django.apps import AppConfig

class <Camel>Config(AppConfig):
    name = "<module_name>"
    def ready(self):
        from .plugins import <Camel>Plugin
        plugin_registry.register(<Camel>Plugin())
```

`plugins.py`:
```python
from baserow.core.registries import Plugin
from django.urls import path, include
from .api import urls as api_urls

class <Camel>Plugin(Plugin):
    type = "<module_name>"
    def get_api_urls(self):
        return [path("<module_name>/", include(api_urls, namespace=self.type))]
```

`api/urls.py`:
```python
from django.urls import re_path
from .views import PingView

app_name = "<module_name>.api"
urlpatterns = [re_path(r"ping/$", PingView.as_view(), name="ping")]
```

`setup.py` must have `package_dir={"": "src"}`, `find_packages("src")`,
`install_requires=[]` (avoid deps — they'd need network at build time).

## Uninstall

```bash
docker exec baserow ./baserow.sh uninstall-plugin <module_name>
docker exec baserow /baserow/venv/bin/python -m pip uninstall -y <pip_name> || true
docker restart baserow
```

## Gotchas learned the hard way

1. **`--git` flag never works** — the image has no `git` binary. Use `--url`
   with a tarball, and the repo must be public (or serve the tarball yourself).
2. **Never let `install_plugin.sh`'s pip be the only install step** — it always
   goes to system user-site on this image. Treat it as "lay down files" only.
3. **Plugin crash = total backend outage** (502 on everything, including
   health). It's a Django INSTALLED_APPS import failure — fix by removing the
   wheel from the venv and/or uninstalling the plugin.
4. **The `plugins/` dir is on the data volume** — after container recreation
   from stock image, plugins re-install on startup (files persist, wheel in
   venv does NOT — re-run steps 2-3 of the recipe after any container rebuild).
5. **Backend boot takes ~20-30s** — don't panic-check before that.
6. **`uninstall-plugin` does its own pip uninstall** — a separate venv pip
   uninstall is only needed if you installed manually (recipe step 3).
7. **pyproject vs setup.py**: keep `setup.py` as the only build config
   (`pyproject.toml` presence makes pip use build isolation, which is fine, but
   setup.py alone keeps it simple).

## What's NOT available (checked 2026-09-05)

- `plugin-boilerplate` repo is outdated (≤2.0.6 only) — structure above is
  hand-verified against 2.3.3 source instead.
- Custom Client Scripts (`BASEROW_EXTRA_CLIENT_SCRIPT_URLS`) — Enterprise-licensed.
- Chart/pie dashboard widgets — premium-gated (HTTP 402 on create via API).
- Plugins in general: experimental, no sandboxing, CLI-only management.

## Version check before any future plugin work

```bash
docker exec baserow cat /baserow/backend/src/baserow/__init__.py  # or similar version probe
```

Compare against this runbook: it is verified for **2.3.3** only. Re-verify the
plugin discovery logic in `backend/src/baserow/config/settings/base.py` and the
`Plugin`/`plugin_registry` API in `backend/src/baserow/core/registries.py` on
the target version before reusing.

## Updating an installed plugin (learned live, 2026-09-05)

- `install-plugin` WITHOUT `--overwrite` silently keeps OLD files ("not overwriting").
- `pip install <repo-tarball-url>` fails: setup.py is nested under plugins/<module>/
  backend in the archive, not at the root. Always refresh via install-plugin
  --overwrite, then pip install the LOCAL path /baserow/data/plugins/<module>/backend.
- Repo-tarball URLs work for install-plugin but NOT for pip directly.
- In-container HTTP calls to Baserow API: use http://localhost:8000/api (backend direct).
  http://localhost/api via Caddy returns Baserow 404 URL_NOT_FOUND because of Host-header
  routing (Host: localhost is not an allowed host) — even though the same path works
  externally via baserow.dmz.local:8682.
