#!/bin/bash

# Define the list of modules to install. Replace these URLs with your actual module URLs.
modules_to_install=(
    "https://gitlab.com/khassel/MMM-RepoStats"
    "https://github.com/jalibu/MMM-RAIN-MAP"
    "https://github.com/jugler/MMM-OneBusAway"
)

cd /opt/magic_mirror/modules

# Loop through the list of modules and install each
for module_url in "${modules_to_install[@]}"; do
    echo "Installing $module_url"
    git clone "$module_url"
    folder=$(echo "$module_url" | sed -r 's|.*\/(.*)|\1|g' | xargs)
    cd "$folder"
    npm install --omit=dev || true
    cd ..
done

ls -la
