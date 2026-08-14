# Deployment

## Local

Run the FastAPI app with the built-in simulator:

```powershell
uvicorn web.main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000`.

## Docker Compose

Docker Compose runs the simulator and monitor as separate services:

```powershell
docker compose up --build
```

Dashboard: `http://127.0.0.1:8000`

Modbus simulator: `127.0.0.1:15020`

## Render

The repository includes `render.yaml` for a free Docker web service. Render will run FastAPI with the internal simulator enabled. SQLite is stored in the container filesystem for demo use; production deployments should use a durable database and explicit retention policy.

No paid service is required for the demo configuration.
