# This file is necessary since the bashcov will not run at the root of the container.
# The paths in the coverage.xml file must match the git paths otherwise it will be invalid.

echo "Fixing coverage paths..."

# Define the path to your coverage.xml file
COVERAGE_FILE="$PWD/coverage/coverage.xml"

# Define the original and desired path prefixes
ORIGINAL_PATH_PREFIX="../app/"
DESIRED_PATH_PREFIX="pkg/"

cat "$COVERAGE_FILE" | grep filename

# Use sed to replace the path in the filename attribute
sed -i "s|filename=\"$ORIGINAL_PATH_PREFIX|filename=\"$DESIRED_PATH_PREFIX|g" "$COVERAGE_FILE"

echo "Fixed coverage paths!"
cat "$COVERAGE_FILE" | grep filename
