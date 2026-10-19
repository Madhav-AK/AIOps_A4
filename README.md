AI OPs Assignment 4 Submission
- By Madhav AK
- DA24B012

This README file goes through all major submission points.

- Assignment specification can be found as `Assignment 4.pdf` in the main directory.
- Video Submission Link:

- `app.py` contains the Streamlit image-captioning application and Prometheus instrumentation.
- `prometheus.yml` configures Prometheus to scrape the application and node_exporter.
- `rules.yml` contains the CPU recording rule and alert rule.
- `alertmanager.yml` sends alerts to the configured webhook.
- `grafana_dashboard_export.json` is the exported Grafana dashboard.
- `example_images` contains sample images and a ZIP for testing single and bulk modes.

The application uses `Salesforce/blip-image-captioning-base` on the CPU.

Application metrics are exposed on a separate HTTP server at `http://localhost:18000/metrics`.

### Setup

```bash
cd /home/madhav/AIOps_A4
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The model is downloaded from Hugging Face when it is used for the first time.

### Streamlit Application

```bash
cd /home/madhav/AIOps_A4
source .venv/bin/activate
streamlit run app.py
```

- The application is available at `http://localhost:8501`
- The application metrics are available at `http://localhost:18000/metrics` after the Streamlit page has been opened.

### Prometheus and Node Exporter

Open separate terminals in `/home/madhav/AIOps_A4` and run:

```bash
# Terminal 1: node_exporter
./node_exporter-1.12.1.linux-amd64/node_exporter

# Terminal 2: Prometheus
./prometheus-3.15.0.linux-amd64/prometheus \
  --config.file=prometheus.yml \
  --storage.tsdb.path=prometheus-data
```

### Alertmanager

```bash
./alertmanager-0.34.1.linux-amd64/alertmanager --config.file=alertmanager.yml
```

Alertmanager is available at `http://localhost:9093`.

### Grafana

Same way we did it in class:

```bash
# First time:
docker pull grafana/grafana-enterprise
docker run -d -p 3000:3000 \
  --add-host=host.docker.internal:host-gateway \
  --name=grafana grafana/grafana-enterprise

# Later runs:
docker start grafana
```