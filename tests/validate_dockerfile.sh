#!/bin/bash

echo "Validating Dockerfile supports both amd64 and arm64 architectures..."

# Read the Dockerfile and find the FROM line
from_line=$(grep '^FROM ' Dockerfile)

# Extract the image name and SHA hash
if [[ $from_line =~ FROM[[:space:]]+([^@]+)@([^[:space:]]+) ]]; then
  image_name="${BASH_REMATCH[1]}"
  sha_from_dockerfile="${BASH_REMATCH[2]}"
  full_image_name="$image_name@$sha_from_dockerfile"

  echo "Image Name: '$image_name'"
  echo "Full Image Name: '$full_image_name'"
  echo "SHA from image:  '$sha_from_dockerfile'"
else
  echo "FAIL: 'FROM' line with SHA not found in Dockerfile"
fi

# Run the docker command to get the SHA from mquery
mquery_output=$(docker run --rm mplatform/mquery:latest@sha256:938c26673f9b81f1c574e5911b79c4a9accf6aa918af575c94c9d488121db63c $image_name --platforms linux/amd64,linux/arm64)
sha_from_mquery=$(echo "$mquery_output" | grep -oP '(?<=digest: )[^\)]+')

echo "SHA from mquery: '$sha_from_mquery'"

# Compare the two SHAs
if [[ "$sha_from_dockerfile" == "$sha_from_mquery" ]]; then
  echo "PASS: SHAs match. All is well."
else
  echo "FAIL: SHAs do not match. Check your Dockerfile."
  exit 1
fi

# Check for the presence of linux/amd64 and linux/arm64 in the output
if echo "$mquery_output" | grep -q "linux/amd64" && echo "$mquery_output" | grep -q "linux/arm64"; then
  echo "PASS: Both linux/amd64 and linux/arm64 are supported."
else
  echo "FAIL: One of linux/amd64 or linux/arm64 is not supported."
  exit 1
fi