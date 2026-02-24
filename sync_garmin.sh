#!/usr/bin/env bash
#
# sync_garmin.sh — Download and sync Garmin Connect data via GarminDB
#
# Usage:
#   ./sync_garmin.sh           # Incremental update (latest data only)
#   ./sync_garmin.sh --full    # Full re-download of all historical data
#   ./sync_garmin.sh --backup  # Backup databases before syncing
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
HEALTH_DATA_DIR="${SCRIPT_DIR}/HealthData"
DB_DIR="${HEALTH_DATA_DIR}/DBs"
LOG_FILE="${SCRIPT_DIR}/sync_$(date +%Y%m%d_%H%M%S).log"

# Activate virtual environment
if [[ ! -d "${VENV_DIR}" ]]; then
    echo "Error: Virtual environment not found at ${VENV_DIR}"
    echo "Run: python3.12 -m venv .venv && source .venv/bin/activate && pip install garmindb"
    exit 1
fi
source "${VENV_DIR}/bin/activate"

# Parse arguments
MODE="latest"
DO_BACKUP=false

for arg in "$@"; do
    case "${arg}" in
        --full)
            MODE="full"
            ;;
        --backup)
            DO_BACKUP=true
            ;;
        --help|-h)
            echo "Usage: $0 [--full] [--backup]"
            echo "  (no args)   Incremental update (latest data only)"
            echo "  --full      Full re-download of all historical data"
            echo "  --backup    Backup databases before syncing"
            exit 0
            ;;
        *)
            echo "Unknown argument: ${arg}"
            echo "Run $0 --help for usage"
            exit 1
            ;;
    esac
done

# Backup databases if requested
if [[ "${DO_BACKUP}" == true ]] && [[ -d "${DB_DIR}" ]]; then
    BACKUP_DIR="${DB_DIR}/backup_$(date +%Y%m%d_%H%M%S)"
    echo "Backing up databases to ${BACKUP_DIR}..."
    mkdir -p "${BACKUP_DIR}"
    cp "${DB_DIR}"/*.db "${BACKUP_DIR}/" 2>/dev/null || echo "No existing databases to backup"
    echo "Backup complete."
fi

# Run GarminDB
echo "Starting Garmin data sync (mode: ${MODE})..."
echo "Log file: ${LOG_FILE}"
echo "Started at: $(date)"

if [[ "${MODE}" == "full" ]]; then
    echo "Running full download (this may take 10-30+ minutes)..."
    garmindb_cli.py --all --download --import --analyze 2>&1 | tee "${LOG_FILE}"
else
    echo "Running incremental update..."
    garmindb_cli.py --all --download --import --analyze --latest 2>&1 | tee "${LOG_FILE}"
fi

echo ""
echo "Sync completed at: $(date)"
echo ""

# Show summary
if [[ -d "${DB_DIR}" ]]; then
    echo "Database files:"
    ls -lh "${DB_DIR}"/*.db 2>/dev/null || echo "  No database files found"
fi

if [[ -f "${HEALTH_DATA_DIR}/stats.txt" ]]; then
    echo ""
    echo "=== Stats Summary ==="
    cat "${HEALTH_DATA_DIR}/stats.txt"
fi
