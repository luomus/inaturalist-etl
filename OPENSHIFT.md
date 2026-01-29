# OpenShift runbook

This project runs on **CSC OpenShift**. The ETL runs at set interval via a CronJob. You can also run it manually with a one-off Job.

**Prerequisites:**
- `oc` CLI
- access to the OpenShift project `inaturalist-etl`
- a local `.env` file with Allas and Laji.fi credentials (see `.env.example`)

## One-time setup

**Log in and select project**

You can get the login command and token from the OpenShift web UI at https://console.rahti.csc.fi/project-details/ns/inaturalist-etl, selecting username > Copy login command.

```bash
oc login https://<openshift-api-url> --token=<your-token>
oc project inaturalist-etl
```

**Create the env Secret from your `.env`**

Secrets hold credentials; the CronJob and manual Job load them as environment variables.

```bash
oc -n inaturalist-etl create secret generic inaturalist-etl-env --from-env-file=.env
```

If the secret already exists and you need to update it (e.g. new tokens):

```bash
oc -n inaturalist-etl delete secret inaturalist-etl-env
oc -n inaturalist-etl create secret generic inaturalist-etl-env --from-env-file=.env
```

## Deploying a new version (after code changes)

When you change the Python code and want that version running on OpenShift:

**Test locally** (build and run with Docker so you use the same image flow as production):

See README.md for testing locally.

**Publish the new image**  

Commit and push to `main`.

GitHub Actions builds and pushes `ghcr.io/luomus/inaturalist-etl:latest` to GHCR. Wait for the [Actions](https://github.com/luomus/inaturalist-etl/actions) workflow to succeed.

**Run the new version on OpenShift**  

The Job uses `imagePullPolicy: Always` and tag `:latest`, so the next Job run will pull the updated image. No change to `job-manual.yml` or `cronjob.yml` needed.

## Automatic run (CronJob)

Deploy the CronJob so the ETL runs as defined in `cronjob.yml`.

```bash
oc -n inaturalist-etl apply -f cronjob.yml
```

Check the CronJob and Jobs created by it (replace `<job-name>` with the name from `get jobs`, e.g. `inaturalist-etl-12345678`):

```bash
oc -n inaturalist-etl get cronjobs
oc -n inaturalist-etl get jobs
oc -n inaturalist-etl get pods
```

To see logs of the latest run:

```bash
oc -n inaturalist-etl logs job/<job-name>
```

Or list pods, find the one for the run you care about, then:

```bash
oc -n inaturalist-etl logs -f <pod-name>
```

Details (if something failed):

```bash
oc -n inaturalist-etl describe job <job-name>
oc -n inaturalist-etl describe pod <pod-name>
```

## Run the ETL manually (one-off)

For an ad-hoc run (e.g. after deploying a new image or testing):

Create the Job (this **starts the process immediately**):

```bash
oc -n inaturalist-etl apply -f job-manual.yml
```

Watch logs:

```bash
oc -n inaturalist-etl logs -f job/inaturalist-etl-manual
```

To run again later, delete the Job and create a new one (Jobs are immutable):

```bash
oc -n inaturalist-etl delete job inaturalist-etl-manual
oc -n inaturalist-etl apply -f job-manual.yml
oc -n inaturalist-etl logs -f job/inaturalist-etl-manual
```

## Useful commands (reference)

| Command | Purpose |
|--------|---------|
| `oc project inaturalist-etl` | Switch to the ETL project |
| `oc -n inaturalist-etl get cronjobs` | List CronJobs |
| `oc -n inaturalist-etl get jobs` | List Jobs (from CronJob and manual) |
| `oc -n inaturalist-etl get pods` | List pods (see running/completed) |
| `oc -n inaturalist-etl logs job/<job-name>` | Logs of a Job (from `get jobs`) |
| `oc -n inaturalist-etl logs -f job/inaturalist-etl-manual` | Stream logs of manual Job |
| `oc -n inaturalist-etl describe pod <pod-name>` | Pod details and events (e.g. image pull errors) |
| `oc -n inaturalist-etl delete job inaturalist-etl-manual` | Remove the manual Job (and its pods) |
| `oc -n inaturalist-etl delete cronjob inaturalist-etl` | Stop hourly runs (remove CronJob) |

## Image and releases

- **Image:** `ghcr.io/luomus/inaturalist-etl:latest`
- **Build:** Pushed automatically on push to `main` (GitHub Actions → GHCR). See [Actions](https://github.com/luomus/inaturalist-etl/actions).
- **Local test before deploying:**  
  `docker pull ghcr.io/luomus/inaturalist-etl:latest`  
  `docker run --rm --env-file .env ghcr.io/luomus/inaturalist-etl:latest`

## Files involved

- **`cronjob.yml`** – CronJob: runs the ETL every hour. Edit to change schedule (e.g. `"0 */2 * * *"` for every 2 hours) or resource limits.
- **`job-manual.yml`** – One-off Job for manual runs. Same image and secret as the CronJob.
- **`.env`** – Local only; never commit. Used to create/update the Secret and for local Docker runs.
