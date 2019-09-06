# logging import bug when using ddtrace's patch_all()

# Problem statement

The gunicorn service fails to listen and start workers.

## Expected output

```bash
srft-test       | [s6-init] making user provided files available at /var/run/s6/etc...exited 0.
srft-test       | [s6-init] ensuring user provided files have correct perms...exited 0.
srft-test       | [fix-attrs.d] applying ownership & permissions fixes...
srft-test       | [fix-attrs.d] done.
srft-test       | [cont-init.d] executing container initialization scripts...
srft-test       | [cont-init.d] done.
srft-test       | [services.d] starting services
srft-test       | [services.d] done.
srft-test       | {"message": "Starting gunicorn 19.9.0", "logger": "wsgi", "level": "info", "timestamp": "2019-02-13T18:29:09.352518Z"}
srft-test       | {"message": "Listening at: http://0.0.0.0:80 (185)", "logger": "wsgi", "level": "info", "timestamp": "2019-02-13T18:29:09.353846Z"}
srft-test       | {"message": "Using worker: gevent", "logger": "wsgi", "level": "info", "timestamp": "2019-02-13T18:29:09.354148Z"}
srft-test       | {"message": "Booting worker with pid: 196", "logger": "wsgi", "level": "info", "timestamp": "2019-02-13T18:29:09.359503Z"}
srft-test       | {"message": "Booting worker with pid: 197", "logger": "wsgi", "level": "info", "timestamp": "2019-02-13T18:29:09.408602Z"}
srft-test       | {"message": "Booting worker with pid: 198", "logger": "wsgi", "level": "info", "timestamp": "2019-02-13T18:29:09.486338Z"}
srft-test       | {"message": "Booting worker with pid: 199", "logger": "wsgi", "level": "info", "timestamp": "2019-02-13T18:29:09.576785Z"}
srft-test       | {"message": "Booting worker with pid: 200", "logger": "wsgi", "level": "info", "timestamp": "2019-02-13T18:29:09.635723Z"}
srft-test       | {"message": "Booting worker with pid: 202", "logger": "wsgi", "level": "info", "timestamp": "2019-02-13T18:29:09.717828Z"}
srft-test       | {"message": "Booting worker with pid: 201", "logger": "wsgi", "level": "info", "timestamp": "2019-02-13T18:29:09.729812Z"}
srft-test       | {"message": "Booting worker with pid: 203", "logger": "wsgi", "level": "info", "timestamp": "2019-02-13T18:29:09.792592Z"}
srft-test       | {"message": "Booting worker with pid: 204", "logger": "wsgi", "level": "info", "timestamp": "2019-02-13T18:29:09.876548Z"}
srft-test       | {"message": "Booting worker with pid: 205", "logger": "wsgi", "level": "info", "timestamp": "2019-02-13T18:29:09.955908Z"}
^CGracefully stopping... (press Ctrl+C again to force)
```

## Actual output

```bash
srft-test       | [s6-init] making user provided files available at /var/run/s6/etc...exited 0.
srft-test       | [s6-init] ensuring user provided files have correct perms...exited 0.
srft-test       | [fix-attrs.d] applying ownership & permissions fixes...
srft-test       | [fix-attrs.d] done.
srft-test       | [cont-init.d] executing container initialization scripts...
srft-test       | [cont-init.d] done.
srft-test       | [services.d] starting services
srft-test       | [services.d] done.
^CGracefully stopping... (press Ctrl+C again to force)
```

### Start the project

```bash
docker-compose down -v || true
docker-compose up
```

### Send a test request

```bash
curl -Nvs http://localhost:5000/healthcheck
# or open http://localhost:5000/healthcheck in a browser
# you should get a 200 'ok' response if the server is listening properly
```

### Try workaround 1

1. Change USE_DDTRACE_RUN env variable to false in docker-compose.yml
1. Then retry test

### Try workaround 2

1. Revert any changes to docker-compose.yml
1. Change LOGGER_CLASS env variable to applogging.StructuredLogger
1. Then retry test

## How this document describes an error

The log statements in the startup routine describe when the server has started listening for requests and when worker greenlets are ready to handle requests. Because the log statements are missing in the actual result and the test case fails to establish a connection it can be determined that the gunicorn startup/listen routine is never called. Because the process never halts or crashes a similar deduction can be made that a race condition or deadlock must exist under this specific configuration.

## Conclusion

1. Either python module imports have a bug or the ddtrace patcher has a bug that leads to an import deadlock given this example architecture.
1. Looking for feedback on how to fix this issue.
1. [Issue opened with vendor](https://github.com/DataDog/dd-trace-py/issues/827) - STATUS = RESOLVED

# Resolution

1. Use a version of ddtrace >= 0.21.0

### If you are interested in running the ddagent sidecar at the same time:

```bash
#!/bin/bash

set -euo pipefail

docker rm -f dd-agent || true

docker run -d --name dd-agent \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /proc/:/host/proc/:ro \
  -v /sys/fs/cgroup/:/host/sys/fs/cgroup:ro \
  -e API_KEY=$DD_API_KEY \
  -e DD_APM_ENABLED=true \
  -p 8126:8126/tcp \
  datadog/docker-dd-agent
```

Note that the environment variable DD_AGENT_HOST in your docker-compose.yml file
needs to match your docker daemon client's DNS name or internal IP.
