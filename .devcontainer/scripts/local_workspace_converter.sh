#!/bin/bash

# This script is used to convert the local workspace folder to the format expected by the Rancher CLI.
# Original format: "c:sers\599247\Projects\ml-asc"

echo "Original format: $LOCAL_WORKSPACE_FOLDER"

# Convert to the desired format: "/c:/Users/James/Projects/nautical"

export LOCAL_WORKSPACE_FOLDER=$(echo "$LOCAL_WORKSPACE_FOLDER" | \
    sed -e 's/\\/\//g' \
    -e 's/^c:sers/c:Users/' \
    -e 's/^c:/\/c:/')

# Example Docker mount - "/c:/Users/James/Projects/nautical/app:/app"
#  Would become -->    - ${LOCAL_WORKSPACE_FOLDER:-.}/app:/app

# echo "Expected format : /c:/Users/James/Projects/nautical"
echo "Converted format: $LOCAL_WORKSPACE_FOLDER"

# Load the file into the ZSH and BASH shells

for file in ~/.zshrc ~/.bashrc; do
    echo "export LOCAL_WORKSPACE_FOLDER=\"${LOCAL_WORKSPACE_FOLDER}\"" >> "$file"
done


 