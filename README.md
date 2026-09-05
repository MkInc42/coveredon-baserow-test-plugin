# coveredon_test — minimal Baserow test plugin

Proves the plugin install path works on our Baserow 2.3.3 DMZ instance (all-in-one image).

Installs a single unauthenticated API endpoint:

    GET /api/coveredon-test/ping/
    -> {"plugin": "coveredon_test", "status": "ok", "baserow_version": "2.3.3"}

## Attempt #2 — venv-aware install (after attempt #1 crashed the backend)

Root cause of attempt #1 failure: the 2.3.3 all-in-one image has no `/baserow/venv/bin/pip`
(uv-built venvs ship without pip), so `install_plugin.sh`'s naked `pip3` fell back to the
SYSTEM python's user-site — invisible to the backend, which imports from `/baserow/venv`.
Django then crashed at boot on `import coveredon_test`.

Fix: put the files in place with install-plugin (it also fixes ownership), then install the
wheel into the REAL venv using the venv's own python, then restart.

```bash
# 1. lay down the plugin files (safe; backend not restarted yet)
docker exec baserow ./baserow.sh install-plugin   --url https://api.github.com/repos/MkInc42/coveredon-baserow-test-plugin/tarball

# 2a. try installing into the real venv:
docker exec baserow /baserow/venv/bin/python -m pip install   /baserow/data/plugins/coveredon_test/backend

# 2b. if that errors "No module named pip", bootstrap pip into the venv first:
docker exec -u root baserow /baserow/venv/bin/python -m ensurepip
docker exec baserow /baserow/venv/bin/python -m pip install   /baserow/data/plugins/coveredon_test/backend

# 3. restart and verify
docker restart baserow
curl http://baserow.dmz.local:8682/api/coveredon-test/ping/
```

## Uninstall / recovery

```bash
docker exec baserow ./baserow.sh uninstall-plugin coveredon_test
docker exec baserow /baserow/venv/bin/python -m pip uninstall -y coveredon-test || true
docker restart baserow
```

## What attempt #1 taught us

- Plugin layout (`plugins/<name>/backend`), tarball install, and uninstall all work on 2.3.3.
- `install_plugin.sh` in the all-in-one image is broken for backend plugins: it calls naked
  `pip3`, which is the system python's pip, NOT the uv-built `/baserow/venv` the backend
  imports from. Result: wheel lands in user-site, Django crashes on `import coveredon_test`.
- `uninstall-plugin` cleanly restores service (it pip-uninstalls + deletes the folder).
