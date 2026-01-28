# OpenShift runbook

This project runs on **CSC OpenShift** as a one-off Job (manual trigger). The container starts, runs the ETL, and exits. No CronJob by default; add one later if you want scheduled runs.

**Prerequisites:** `oc` CLI, access to the OpenShift project `inaturalist-etl`, and a local `.env` file with Allas and Laji.fi credentials (see `.env.example`).

---

## One-time setup

### 1. Log in and select project

You can get the login command and token from the OpenShift web UI at https://console.rahti.csc.fi/project-details/ns/inaturalist-etl, selecting username > Copy login command.

```bash
oc login https://<openshift-api-url> --token=<your-token>
oc project inaturalist-etl
```

Get the login command and token from the OpenShift web UI (e.g. CSC Pouta / Rahti).

### 2. Create the env Secret from your `.env`

Secrets hold credentials; the Job loads them as environment variables.

```bash
oc -n inaturalist-etl create secret generic inaturalist-etl-env --from-env-file=.env
```

If the secret already exists and you need to update it (e.g. new tokens):

```bash
oc -n inaturalist-etl delete secret inaturalist-etl-env
oc -n inaturalist-etl create secret generic inaturalist-etl-env --from-env-file=.env
```

---

## Run the ETL manually

### 3. Create the Job

Creating the Job **starts the process immediately** (Kubernetes schedules a pod and runs the container).

```bash
oc -n inaturalist-etl apply -f job-manual.yml
```

### 4. Watch logs

Stream logs from the Job’s pod (run this right after step 3 to follow the run):

```bash
oc -n inaturalist-etl logs -f job/inaturalist-etl-manual
```

### 5. Check status

See if the Job and its pod are running or finished:

```bash
oc -n inaturalist-etl get jobs
oc -n inaturalist-etl get pods
```

---

## Run again later

Jobs are immutable. To run the ETL again:

1. Delete the previous Job (keeps the secret; only the Job is removed).
2. Create a new Job with the same YAML.

```bash
oc -n inaturalist-etl delete job inaturalist-etl-manual
oc -n inaturalist-etl apply -f job-manual.yml
oc -n inaturalist-etl logs -f job/inaturalist-etl-manual
```

---

## Useful commands (reference)

| Command | Purpose |
|--------|---------|
| `oc project inaturalist-etl` | Switch to the ETL project |
| `oc -n inaturalist-etl get pods` | List pods (see running/completed) |
| `oc -n inaturalist-etl get jobs` | List Jobs |
| `oc -n inaturalist-etl describe pod <pod-name>` | Pod details and events (e.g. image pull errors) |
| `oc -n inaturalist-etl logs job/inaturalist-etl-manual` | Print logs (no follow) |
| `oc -n inaturalist-etl delete job inaturalist-etl-manual` | Remove the Job (and its pods) |

---

## Image and releases

- **Image:** `ghcr.io/luomus/inaturalist-etl:latest`
- **Build:** Pushed automatically on push to `main` (GitHub Actions → GHCR). See [Actions](https://github.com/luomus/inaturalist-etl/actions).
- **Local test before deploying:**  
  `docker pull ghcr.io/luomus/inaturalist-etl:latest`  
  `docker run --rm --env-file .env ghcr.io/luomus/inaturalist-etl:latest`

---

## Files involved

- **`job-manual.yml`** – OpenShift Job definition: image, secret name, restart policy. Edit to change image tag or resource limits.
- **`.env`** – Local only; never commit. Used to create/update the Secret and for local Docker runs.
- **`examples/`** – Optional; `template.yml` and `oc-process.sh` are for a branch-based CronJob setup and are not required for this manual Job workflow.
