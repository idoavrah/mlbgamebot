.PHONY: help parse parse-year parse-month parse-day run-website install sync-site-data docker-build docker-push docker-run

# Default target
help:
	@echo "MLB Game Bot - Commands"
	@echo "======================="
	@echo "make parse                                   : Parse data for the defaults (Yesterday)"
	@echo "make parse-year YEAR=2025                    : Parse data for a specific year"
	@echo "make parse-month YEAR=2025 MONTH=10          : Parse data for a specific month"
	@echo "make parse-day YEAR=2025 MONTH=10 DAY=04     : Parse data for a specific day"
	@echo "make run-website                             : Run the website locally on port 8000"
	@echo "make install                                 : Install backend dependencies"
	@echo "make sync-site-data                          : Sync site files to GCS bucket (no overwrite)"
	@echo "make docker-build                            : Build the Docker image"
	@echo "make docker-push                             : Build and push image to Artifact Registry"
	@echo "make docker-run                              : Run the Docker image locally with data mount"

# Default parse (Yesterday)
parse:
	@echo "Parsing default (Yesterday)..."
	@cd backend && python3 gamebot.py

# Parse for a specific year
parse-year:
	@echo "Parsing for year $(YEAR)..."
	@cd backend && LOAD_YEAR=$(YEAR) python3 gamebot.py

# Parse for a specific month
parse-month:
	@echo "Parsing for $(YEAR)-$(MONTH)..."
	@cd backend && LOAD_YEAR=$(YEAR) LOAD_MONTH=$(MONTH) python3 gamebot.py

# Parse for a specific day
parse-day:
	@echo "Parsing for $(YEAR)-$(MONTH)-$(DAY)..."
	@cd backend && LOAD_YEAR=$(YEAR) LOAD_MONTH=$(MONTH) LOAD_DAY=$(DAY) python3 gamebot.py

# Run the website
run-website:
	@echo "Starting local server at http://localhost:8000"
	@python3 -m http.server 8000

# Install dependencies
install:
	@pip3 install -r requirements.txt

# Sync site data to GCS bucket (last 15m)
GCS_BUCKET := gs://mlb.idodo.dev
sync-site-data:
	@echo "Syncing site data changed in the last 15 minutes to $(GCS_BUCKET)..."
	@find index.html style.css app.js favorites.js images data \
		-type f -mmin -15 \
		! \( -name "*.json" ! -name "games.json" \) \
		-exec gcloud storage cp {} $(GCS_BUCKET)/{} \;
	@echo "Sync complete."

# Docker
IMAGE_URI := me-west1-docker.pkg.dev/ido-infrastructure/mlbgamebot/mlbgamebot:1.0.3
IMAGE_NAME_BASE := me-west1-docker.pkg.dev/ido-infrastructure/mlbgamebot/mlbgamebot
IMAGE_LATEST    := $(IMAGE_NAME_BASE):latest

docker-build:
	@echo "Building multi-arch image $(IMAGE_URI)..."
	@podman manifest rm $(IMAGE_URI) || true
	@podman manifest create $(IMAGE_URI)
	@podman build --platform linux/amd64,linux/arm64 --manifest $(IMAGE_URI) .

docker-push: docker-build
	@echo "Pushing multi-arch image $(IMAGE_URI)..."
	@podman manifest push $(IMAGE_URI)
	@echo "Pushing latest tag $(IMAGE_LATEST)..."
	@podman manifest push $(IMAGE_URI) docker://$(IMAGE_LATEST)

docker-run:
	@echo "Running image $(IMAGE_URI)..."
	@podman run --rm -v $(shell pwd)/data:/app/data $(IMAGE_URI)
