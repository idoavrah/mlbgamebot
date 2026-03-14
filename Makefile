.PHONY: help parse parse-year parse-month parse-day run-website build-website clean install sync-site-data deploy-website migrate-manifest docker-build docker-push docker-run
GCS_BUCKET := gs://mlb.idodo.dev

# Default target
help:
	@echo "MLB Game Bot - Commands"
	@echo "======================="
	@echo "make clean                                   : Remove build artifacts (dist/)"
	@echo "make install                                 : Install backend dependencies"
	@echo "make parse                                   : Parse data for the defaults (Yesterday)"
	@echo "make parse-year YEAR=2025                    : Parse data for a specific year"
	@echo "make parse-month YEAR=2025 MONTH=10          : Parse data for a specific month"
	@echo "make parse-day YEAR=2025 MONTH=10 DAY=04     : Parse data for a specific day"
	@echo "make run-website                             : Run the website locally on port 8000"
	@echo "make build-website                           : Minify website assets into dist/"
	@echo "make deploy-website                          : Robust sync of all site assets to GCS"
	@echo "make docker-build                            : Build the Docker image"
	@echo "make docker-push                             : Build and push image to Artifact Registry"
	@echo "make docker-run                              : Run the Docker image locally with data mount"

clean:
	@echo "Cleaning up dist/..."
	@rm -rf dist/

# Install dependencies
install:
	@pip3 install -r requirements.txt

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
	@echo "Starting local server at http://127.0.0.1:8000"
	@python3 -m http.server 8000

build-website: clean
	@echo "Building website (minifying assets)..."
	@mkdir -p dist/images
	@npx -y terser app.js -o dist/app.js --compress --mangle
	@npx -y terser favorites.js -o dist/favorites.js --compress --mangle
	@npx -y clean-css-cli -o dist/style.css style.css
	@npx -y html-minifier-terser --collapse-whitespace --remove-comments --remove-optional-tags --remove-redundant-attributes --remove-script-type-attributes --remove-tag-whitespace --use-short-doctype index.html -o dist/index.html
	@npx -y html-minifier-terser --collapse-whitespace --remove-comments --remove-optional-tags --remove-redundant-attributes --remove-script-type-attributes --remove-tag-whitespace --use-short-doctype privacy.html -o dist/privacy.html
	@cp -r images/* dist/images/
	@echo "Build complete. Minified assets are in dist/"

deploy-website: build-website
	@echo "Deploying website to $(GCS_BUCKET)..."
	@./scripts/deploy-website.sh --bucket $(GCS_BUCKET) $(if $(DRY_RUN),--dry-run,)

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
