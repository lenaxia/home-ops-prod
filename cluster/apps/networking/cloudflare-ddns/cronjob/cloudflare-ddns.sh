#!/usr/bin/env bash

# Robust Bash Scripting
set -o nounset
set -o errexit
set -o pipefail

# Function to log messages
log() {
    echo "$(date -u) - $1"
}

# Function to exit in case of an error
error_exit() {
    log "Error: $1"
    exit 1
}

# Fetch Current External IP
current_ipv4="$(curl -s https://ipv4.icanhazip.com/)" || error_exit "Failed to fetch current IPv4 address"

# Fetch Cloudflare Zone ID
zone_id=$(curl -s -X GET \
    "https://api.cloudflare.com/client/v4/zones?name=${SECRET_DEV_DOMAIN}&status=active" \
    -H "X-Auth-Email: ${SECRET_CLOUDFLARE_EMAIL}" \
    -H "X-Auth-Key: ${SECRET_CLOUDFLARE_TOKEN}" \
    -H "Content-Type: application/json" \
    | jq --raw-output ".result[0] | .id" || error_exit "Failed to fetch Cloudflare Zone ID")

# Fetch Current DNS Record
record_ipv4=$(curl -s -X GET \
    "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records?name=${SECRET_DEV_DOMAIN}&type=A" \
    -H "X-Auth-Email: ${SECRET_CLOUDFLARE_EMAIL}" \
    -H "X-Auth-Key: ${SECRET_CLOUDFLARE_TOKEN}" \
    -H "Content-Type: application/json" || error_exit "Failed to fetch current DNS record")

old_ip4=$(echo "$record_ipv4" | jq --raw-output '.result[0] | .content' || error_exit "Failed to parse current DNS record")

# Compare IPs and Update if Different
if [[ "${current_ipv4}" == "${old_ip4}" ]]; then
    log "IP Address '${current_ipv4}' has not changed"
    exit 0
fi

record_ipv4_identifier="$(echo "$record_ipv4" | jq --raw-output '.result[0] | .id' || error_exit "Failed to parse DNS record identifier")"

# Update DNS Record
update_ipv4=$(curl -s -X PUT \
    "https://api.cloudflare.com/client/v4/zones/${zone_id}/dns_records/${record_ipv4_identifier}" \
    -H "X-Auth-Email: ${SECRET_CLOUDFLARE_EMAIL}" \
    -H "X-Auth-Key: ${SECRET_CLOUDFLARE_TOKEN}" \
    -H "Content-Type: application/json" \
    --data "{\"id\":\"${zone_id}\",\"type\":\"A\",\"proxied\":false,\"name\":\"${SECRET_DEV_DOMAIN}\",\"content\":\"${current_ipv4}\"}" || error_exit "Failed to update DNS record")

if [[ "$(echo "$update_ipv4" | jq --raw-output '.success')" == "true" ]]; then
    log "Success - IP Address '${current_ipv4}' has been updated"
else
    error_exit "Updating IP Address '${current_ipv4}' has failed"
fi

