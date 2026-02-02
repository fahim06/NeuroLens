#!/usr/bin/env bash
# Register Model Script
# Registers a validated model to the model registry
# Exit codes: 0=success, 1=registration failed

set -euo pipefail

# ============================================
# Configuration
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

MODEL_DIR="${MODEL_DIR:-$PROJECT_ROOT/models}"
REGISTRY_DIR="${REGISTRY_DIR:-$PROJECT_ROOT/models/registry}"
RUN_ID="${RUN_ID:-}"
PROMOTE_TO="${PROMOTE_TO:-staged}"

# ============================================
# Logging
# ============================================
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $*"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*" >&2
}

log_success() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $*"
}

# ============================================
# Usage
# ============================================
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Register a trained model to the model registry.

Options:
    -r, --run-id RUN_ID       Specific run ID to register (default: latest)
    -p, --promote-to STAGE    Stage to promote to: staged|production (default: staged)
    -h, --help                Show this help message

Examples:
    $(basename "$0")                              # Register latest run as staged
    $(basename "$0") -r run_20260201_120000       # Register specific run
    $(basename "$0") -p production                # Register as production
EOF
}

# ============================================
# Parse Arguments
# ============================================
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--run-id)
            RUN_ID="$2"
            shift 2
            ;;
        -p|--promote-to)
            PROMOTE_TO="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# ============================================
# Find Run
# ============================================
find_run() {
    if [[ -n "$RUN_ID" ]]; then
        if [[ ! -d "$MODEL_DIR/$RUN_ID" ]]; then
            log_error "Run not found: $RUN_ID"
            exit 1
        fi
        return
    fi
    
    # Find latest run
    RUN_ID=$(ls -1 "$MODEL_DIR" 2>/dev/null | grep "^run_" | sort -r | head -n1)
    
    if [[ -z "$RUN_ID" ]]; then
        log_error "No training runs found in $MODEL_DIR"
        exit 1
    fi
    
    log_info "Using latest run: $RUN_ID"
}

# ============================================
# Validate Run
# ============================================
validate_run() {
    local metadata_path="$MODEL_DIR/$RUN_ID/training_metadata.json"
    
    if [[ ! -f "$metadata_path" ]]; then
        log_error "Training metadata not found: $metadata_path"
        exit 1
    fi
    
    # Check if validation passed
    local status
    status=$(python -c "
import json
with open('$metadata_path') as f:
    data = json.load(f)
print(data.get('status', 'unknown'))
")
    
    if [[ "$status" != "trained" && "$status" != "validated" ]]; then
        log_error "Run $RUN_ID has invalid status: $status"
        exit 1
    fi
    
    log_info "Run $RUN_ID is valid for registration"
}

# ============================================
# Register Model
# ============================================
register_model() {
    log_info "Registering model $RUN_ID as $PROMOTE_TO..."
    
    mkdir -p "$REGISTRY_DIR"
    
    python -c "
import os
import sys
import json
import shutil
from datetime import datetime

run_id = '$RUN_ID'
model_dir = '$MODEL_DIR'
registry_dir = '$REGISTRY_DIR'
promote_to = '$PROMOTE_TO'

# Load training metadata
metadata_path = f'{model_dir}/{run_id}/training_metadata.json'
with open(metadata_path) as f:
    training_meta = json.load(f)

# Create registry entry
version = datetime.now().strftime('%Y%m%d.%H%M%S')
entry = {
    'version': version,
    'run_id': run_id,
    'model_name': training_meta.get('model_name', 'unknown'),
    'stage': promote_to,
    'registered_at': datetime.now().isoformat(),
    'training_timestamp': training_meta.get('timestamp'),
    'metrics': training_meta.get('metrics', {}),
    'artifact_path': f'{model_dir}/{run_id}',
}

# Save registry entry
entry_path = f'{registry_dir}/{run_id}.json'
with open(entry_path, 'w') as f:
    json.dump(entry, f, indent=2)

print(f'Registered: {entry_path}')

# Update stage pointer
stage_pointer = f'{registry_dir}/{promote_to}.json'
with open(stage_pointer, 'w') as f:
    json.dump({
        'run_id': run_id,
        'version': version,
        'updated_at': datetime.now().isoformat(),
    }, f, indent=2)

print(f'Updated stage pointer: {stage_pointer}')

# Archive previous production if promoting to production
if promote_to == 'production':
    archive_dir = f'{registry_dir}/archive'
    os.makedirs(archive_dir, exist_ok=True)
    
    # Find previous production entries
    for f in os.listdir(registry_dir):
        if f.endswith('.json') and f not in ['production.json', 'staged.json', f'{run_id}.json']:
            entry_file = f'{registry_dir}/{f}'
            with open(entry_file) as ef:
                e = json.load(ef)
            if e.get('stage') == 'production':
                # Archive it
                e['stage'] = 'archived'
                e['archived_at'] = datetime.now().isoformat()
                with open(entry_file, 'w') as ef:
                    json.dump(e, ef, indent=2)
                print(f'Archived previous production: {f}')
"
    
    if [[ $? -ne 0 ]]; then
        log_error "Registration failed"
        exit 1
    fi
    
    log_success "Model registered successfully"
}

# ============================================
# Main
# ============================================
main() {
    log_info "========================================="
    log_info "NeuroLens Model Registration"
    log_info "========================================="
    
    find_run
    validate_run
    register_model
    
    log_info "========================================="
    log_success "Registration complete: $RUN_ID -> $PROMOTE_TO"
    log_info "========================================="
}

main
