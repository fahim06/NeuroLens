#!/usr/bin/env bash
# Rollback Script
# Rolls back to a previous model version
# Exit codes: 0=success, 1=rollback failed

set -euo pipefail

# ============================================
# Configuration
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

REGISTRY_DIR="${REGISTRY_DIR:-$PROJECT_ROOT/models/registry}"
TARGET_VERSION="${TARGET_VERSION:-}"
DRY_RUN="${DRY_RUN:-false}"

# ============================================
# Logging
# ============================================
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $*"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*" >&2
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $*"
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

Rollback to a previous model version.

Options:
    -v, --version VERSION     Target version/run_id to rollback to
    -l, --list                List available versions
    -n, --dry-run             Show what would be done without executing
    -h, --help                Show this help message

Examples:
    $(basename "$0") -l                           # List available versions
    $(basename "$0") -v run_20260201_120000       # Rollback to specific version
    $(basename "$0") -v run_20260201_120000 -n    # Dry run
EOF
}

# ============================================
# List Versions
# ============================================
list_versions() {
    log_info "Available model versions:"
    echo ""
    
    if [[ ! -d "$REGISTRY_DIR" ]]; then
        log_warn "No registry found at $REGISTRY_DIR"
        return
    fi
    
    python -c "
import os
import json

registry_dir = '$REGISTRY_DIR'

entries = []
for f in os.listdir(registry_dir):
    if f.endswith('.json') and f not in ['production.json', 'staged.json']:
        with open(f'{registry_dir}/{f}') as ef:
            e = json.load(ef)
            entries.append(e)

# Sort by registration time
entries.sort(key=lambda x: x.get('registered_at', ''), reverse=True)

# Get current production
current_prod = None
prod_path = f'{registry_dir}/production.json'
if os.path.exists(prod_path):
    with open(prod_path) as f:
        current_prod = json.load(f).get('run_id')

print(f'{'VERSION':<30} {'STAGE':<12} {'REGISTERED':<20} {'ACCURACY'}')
print('-' * 80)

for e in entries:
    run_id = e.get('run_id', 'unknown')
    stage = e.get('stage', 'unknown')
    registered = e.get('registered_at', 'unknown')[:19]
    accuracy = e.get('metrics', {}).get('accuracy', 'N/A')
    if isinstance(accuracy, float):
        accuracy = f'{accuracy:.3f}'
    
    marker = ' *' if run_id == current_prod else ''
    print(f'{run_id:<30} {stage:<12} {registered:<20} {accuracy}{marker}')

print('')
print('* = current production')
"
}

# ============================================
# Parse Arguments
# ============================================
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            TARGET_VERSION="$2"
            shift 2
            ;;
        -l|--list)
            list_versions
            exit 0
            ;;
        -n|--dry-run)
            DRY_RUN="true"
            shift
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
# Validate Target
# ============================================
validate_target() {
    if [[ -z "$TARGET_VERSION" ]]; then
        log_error "Target version required. Use -v or --version"
        usage
        exit 1
    fi
    
    local entry_path="$REGISTRY_DIR/$TARGET_VERSION.json"
    
    if [[ ! -f "$entry_path" ]]; then
        log_error "Version not found in registry: $TARGET_VERSION"
        log_info "Use -l to list available versions"
        exit 1
    fi
    
    log_info "Target version found: $TARGET_VERSION"
}

# ============================================
# Perform Rollback
# ============================================
perform_rollback() {
    log_info "Rolling back to $TARGET_VERSION..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY RUN - No changes will be made"
    fi
    
    python -c "
import os
import sys
import json
from datetime import datetime

target = '$TARGET_VERSION'
registry_dir = '$REGISTRY_DIR'
dry_run = '$DRY_RUN' == 'true'

# Load target entry
entry_path = f'{registry_dir}/{target}.json'
with open(entry_path) as f:
    target_entry = json.load(f)

# Get current production
prod_path = f'{registry_dir}/production.json'
current_prod = None
if os.path.exists(prod_path):
    with open(prod_path) as f:
        current_prod = json.load(f).get('run_id')

if current_prod == target:
    print(f'Target {target} is already in production')
    sys.exit(0)

print(f'Current production: {current_prod or \"none\"}')
print(f'Rolling back to: {target}')

if dry_run:
    print('\\nDRY RUN - Would perform:')
    print(f'  1. Demote current production ({current_prod}) to archived')
    print(f'  2. Promote {target} to production')
    print(f'  3. Update production.json pointer')
    sys.exit(0)

# Demote current production
if current_prod:
    current_path = f'{registry_dir}/{current_prod}.json'
    if os.path.exists(current_path):
        with open(current_path) as f:
            current_entry = json.load(f)
        current_entry['stage'] = 'archived'
        current_entry['demoted_at'] = datetime.now().isoformat()
        current_entry['demoted_reason'] = f'Rolled back to {target}'
        with open(current_path, 'w') as f:
            json.dump(current_entry, f, indent=2)
        print(f'Demoted {current_prod} to archived')

# Promote target to production
target_entry['stage'] = 'production'
target_entry['promoted_at'] = datetime.now().isoformat()
target_entry['promoted_reason'] = 'Rollback'
with open(entry_path, 'w') as f:
    json.dump(target_entry, f, indent=2)

# Update production pointer
with open(prod_path, 'w') as f:
    json.dump({
        'run_id': target,
        'version': target_entry.get('version'),
        'updated_at': datetime.now().isoformat(),
        'reason': 'rollback',
    }, f, indent=2)

print(f'Promoted {target} to production')

# Create rollback log
log_path = f'{registry_dir}/rollback_log.json'
log_entries = []
if os.path.exists(log_path):
    with open(log_path) as f:
        log_entries = json.load(f)

log_entries.append({
    'timestamp': datetime.now().isoformat(),
    'from_version': current_prod,
    'to_version': target,
    'reason': 'manual_rollback',
})

with open(log_path, 'w') as f:
    json.dump(log_entries, f, indent=2)

print('Rollback logged')
"
    
    if [[ $? -ne 0 ]]; then
        log_error "Rollback failed"
        exit 1
    fi
    
    if [[ "$DRY_RUN" != "true" ]]; then
        log_success "Rollback completed successfully"
    fi
}

# ============================================
# Notify
# ============================================
notify_rollback() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return
    fi
    
    log_info "Sending rollback notification..."
    
    # In production, this would send Slack/email notifications
    echo "ROLLBACK NOTIFICATION"
    echo "====================="
    echo "Service: NeuroLens ML Model"
    echo "Action: Rollback to $TARGET_VERSION"
    echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo "====================="
}

# ============================================
# Main
# ============================================
main() {
    log_info "========================================="
    log_info "NeuroLens Model Rollback"
    log_info "========================================="
    
    validate_target
    perform_rollback
    notify_rollback
    
    log_info "========================================="
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "Dry run complete - no changes made"
    else
        log_success "Rollback complete: production -> $TARGET_VERSION"
    fi
    log_info "========================================="
}

main
