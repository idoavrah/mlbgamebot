#!/bin/bash
set -e

# Default values
BUCKET=${GCS_BUCKET:-"gs://mlb.idodo.dev"}
DRY_RUN=false
CACHE_CONTROL_STATIC="public, max-age=3600"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true ;;
        --bucket) BUCKET="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

SOURCE_ROOT="."
if [ -d "dist" ]; then
    echo "Found dist/ directory, deploying minified assets..."
    SOURCE_ROOT="dist"
fi

echo "Deploying to $BUCKET..."

echo "Syncing root static assets from $SOURCE_ROOT..."
for file in index.html style.css app.js favorites.js; do
    if [ -f "$SOURCE_ROOT/$file" ]; then
        echo "Processing $file..."
        if [ "$DRY_RUN" = true ]; then
            echo "[dry-run] gcloud storage cp $SOURCE_ROOT/$file $BUCKET/$file"
            echo "[dry-run] gcloud storage objects update $BUCKET/$file --cache-control=\"$CACHE_CONTROL_STATIC\""
        else
            gcloud storage cp "$SOURCE_ROOT/$file" "$BUCKET/$file"
            gcloud storage objects update "$BUCKET/$file" --cache-control="$CACHE_CONTROL_STATIC" || true
        fi
    fi
done

if [ -d "$SOURCE_ROOT/images" ]; then
    echo "Syncing images folder from $SOURCE_ROOT/images..."
    if [ "$DRY_RUN" = true ]; then
        gcloud storage rsync --dry-run "$SOURCE_ROOT/images" "$BUCKET/images"
    else
        gcloud storage rsync "$SOURCE_ROOT/images" "$BUCKET/images"
        gcloud storage objects update "$BUCKET/images/**" --cache-control="$CACHE_CONTROL_STATIC" || true
    fi
fi

echo "Deployment complete."
