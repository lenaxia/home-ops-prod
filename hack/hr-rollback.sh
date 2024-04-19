#!/bin/bash

# Define a log file location in a directory with appropriate write permissions
LOGFILE="$HOME/helm_flux_rollback.log"

# Function to log messages with a timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOGFILE"
}

# Function to roll back a Helm release to its last successful deployment
rollback_release() {
    local release=$1
    local namespace=$2

    # Fetch the helm history and extract the last successful revision
    log "Checking history for $release in $namespace with schema errors..."
    last_successful=$(helm history "$release" -n "$namespace" --max 10 | grep -i "deployed" | tail -1 | awk '{print $1}')
    if [ -z "$last_successful" ]; then
        log "ERROR: No successful deployment found for $release in $namespace."
        return 1
    fi

    # Rollback to the last successful version
    log "Rolling back $release in $namespace to revision $last_successful..."
    if helm rollback "$release" "$last_successful" -n "$namespace"; then
        log "Rollback successful for $release in $namespace."
    else
        log "ERROR: Rollback failed for $release in $namespace."
        return 1
    fi
    
    # Reconcile the Helm release through Flux
    log "Reconciling $release in $namespace..."
    if flux reconcile hr "$release" -n "$namespace"; then
        log "Reconciliation successful for $release in $namespace."
    else
        log "ERROR: Reconciliation failed for $release in $namespace."
        return 1
    fi
}

# Main program starts here
log "Starting to process Helm releases with schema errors..."

# Verify connectivity with the Kubernetes API
if ! kubectl cluster-info; then
    log "ERROR: Unable to reach Kubernetes cluster. Check your connection and configurations."
    exit 1
fi

# Fetch all Helm releases using Flux, check for schema error messages
flux get hr --all-namespaces | grep "values don't meet the specifications of the schema(s) in the following chart(s)" | while read -r line; do
    namespace=$(echo "$line" | awk '{print $1}')
    release=$(echo "$line" | awk '{print $2}')

    # Check if release and namespace are extracted correctly
    if [ -n "$release" ] && [ -n "$namespace" ]; then
        if ! rollback_release "$release" "$namespace"; then
            log "Failed to process $release in $namespace."
        fi
    else
        log "ERROR: Could not parse release and namespace from flux output: $line"
    fi
done

log "Processing complete for Helm releases with schema errors."

