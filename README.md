# coveredon_test — minimal Baserow test plugin

Proves the plugin install path works on our Baserow 2.3.3 DMZ instance.

Installs a single unauthenticated API endpoint:

    GET /api/coveredon-test/ping/
    -> {"plugin": "coveredon_test", "status": "ok", "baserow_version": "2.3.3"}

## Install (on the DMZ host, as topflight)

```bash
# 1. stop the container
docker stop baserow

# 2. install the plugin into the container
docker start baserow
docker exec baserow ./baserow.sh install-plugin \
  --git https://github.com/MkInc42/coveredon-baserow-test-plugin.git

# 3. restart so the backend picks it up
docker restart baserow

# 4. verify
curl http://baserow.dmz.local:8682/api/coveredon-test/ping/
```

Expected: `{"plugin":"coveredon_test","status":"ok","baserow_version":"2.3.3"}`

## Uninstall

```bash
docker exec baserow ./baserow.sh uninstall-plugin coveredon_test
docker restart baserow
```
