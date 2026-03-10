# ITU-MiniTwit — Logging with Dozzle

This example shows how to add lightweight, real-time log viewing to the MiniTwit  application using **[Dozzle](https://dozzle.dev/)**, a zero-configuration Docker log viewer.

## What is Dozzle?

Dozzle is a small, open-source web application that streams logs from your Docker containers directly in a browser. It reads the Docker socket (`/var/run/docker.sock`), meaning the same pipe `docker logs` uses (containers write to `stdout` and `stderr`) and presents a clean, searchable UI on top of it.

It requires no changes to your application code, you just add it as a container.

## How to start the application

From the `itu-minitwit-logging/` directory, run:

```bash
docker compose up -d
```

> here the `-d` flag means "detach", so logs from the containers are not printed in the terminal, which can be very verbose.

After a moment, three containers should be running:
```bash
CONTAINER ID   IMAGE                                 COMMAND                  CREATED          STATUS          PORTS                    NAMES
0fe57d7450c7   amir20/dozzle:latest                  "/dozzle"                34 seconds ago   Up 33 seconds   0.0.0.0:8080->8080/tcp   itu-minitwit-logging-dozzle-1
61818bfbb139   itu-minitwit-logging-minitwitclient   "python ./minitwit_c…"   24 hours ago     Up 31 seconds   5000/tcp                 itu-minitwit-logging-minitwitclient-1
62089a7699a1   itu-minitwit-logging-minitwitserver   "python ./minitwit.py"   24 hours ago     Up 32 seconds   0.0.0.0:5001->5000/tcp   minitwit
```

## How to access the application

* MiniTwit frontend:  http://localhost:5001
* Dozzle log viewer: http://localhost:8080

## How to use the Dozzle UI

1. Open http://localhost:8080 in your browser.
2. The left sidebar lists all running containers on the Docker host. Click any container to open its live log stream.
3. Use find command (windows: `ctr`+`f` / Mac: `cmd`+`f`) to filter log lines by keyword in real time.
4. In the left sidebar, when you hover over a container, you can select `Pin as coloum` to watch several containers side-by-side, which can be useful for tracing a request as it moves through the minitwit server and client at the same time.
5. In the opened container logs at the top left, there is an icon with two red and blue dots. When pressing that you can filter by log level (`info`, `warn`, `error`) and for `stdout` or `stderr`.
6. Logs are streamed live; there is no refresh needed.

> **Note:** Dozzle shows logs for all containers visible to Docker, not only the ones defined in this compose file. You will also see the Dozzle container's own logs in the list.

## How to stop the application

```bash
docker compose down
```

## Configuration breakdown

```yaml
services:
  minitwitserver:
    restart: unless-stopped
    container_name: minitwit
    build:
      context: minitwit #the minitwit folder in the repo (will use the Dockerfile in there)
    ports:
      - "5001:5000"
    networks:
      - main

  minitwitclient:
    restart: unless-stopped
    build:
      context: minitwit_client #the minitwit_client folder in the repo (will use the Dockerfile in there)
    networks:
      - main
    depends_on:
      - minitwitserver

  dozzle:
    image: amir20/dozzle:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro #1
    ports:
      - "8080:8080" #2
    environment:
      DOZZLE_LEVEL: info #3
    restart: unless-stopped
    networks:
      - main

networks:
  main:
```

**(1) `/var/run/docker.sock`** — This is the Docker daemon's Unix socket. Mounting it gives Dozzle the ability to call the Docker API and read log streams from every container, the same way `docker logs` does. The `:ro` flag makes the mount read-only, meaning Dozzle cannot start, stop, or modify containers (only observe them). This is the minimal permission needed.

**(2) Port `8080`** — The Dozzle web UI listens here by default. Open `http://localhost:8080` in a browser to access it. You can change the host-side port (left of the colon) to anything you like without touching the container.

**(3) `DOZZLE_LEVEL: info`** — Controls the verbosity of Dozzle's own internal logs (what it prints to its stdout), not the logs of your application. Set to `debug` if you need to troubleshoot Dozzle itself.

### Other useful environment variables

| Variable | Default | Description |
|---|---|---|
| `DOZZLE_BASE` | `/` | Change the URL base path, e.g. `/dozzle` if running behind a reverse proxy |
| `DOZZLE_FILTER` | none | Only show containers matching a label filter, e.g. `name=minitwit` |
| `DOZZLE_AUTH_PROVIDER` | none | Enable authentication; see the [auth guide](https://dozzle.dev/guide/authentication) |
| `DOZZLE_ENABLE_ACTIONS` | `false` | Allow starting/stopping containers from the UI (disabled by default for safety) |

---

## Dozzle vs the ELK stack — when to use which

The `itu-minitwit-logging` example uses the ELFK stack (Elasticsearch, Logstash, Filebeat, Kibana). Both solve "I want to see my logs", but are good for different contexts:

| | **Dozzle** | **ELK stack** |
|---|---|---|
| **Setup complexity** | One container, zero config | 4–6 containers, multiple config files, an init step |
| **Resources** | ~10 MB RAM | ~1–2 GB RAM minimum |
| **Retention** | None: only shows live and recent logs buffered by Docker | Persistent: logs are stored in Elasticsearch indefinitely |
| **Search / querying** | Keyword filter on the current view | Full-text search, aggregations, dashboards, alerting |
| **Alerting** | No | Yes |
| **Code changes needed** | None | None (Filebeat reads Docker logs automatically) |

**Rule of thumb:**

* Use Dozzle when you want to watch what is happening right now, on a single machine, with no infrastructure overhead.
* Use ELK when you need to store, search, and analyse logs over time — for example, after your application is deployed in production and you want to investigate incidents that happened hours or days ago.
