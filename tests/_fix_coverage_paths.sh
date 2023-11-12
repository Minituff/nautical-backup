echo "Fixing coverage paths..."

# Define the path to your coverage.xml file
COVERAGE_FILE="tests/coverage/coverage.xml"

# Define the original and desired path prefixes
ORIGINAL_PATH_PREFIX="../app/"
DESIRED_PATH_PREFIX="app/"

# Use sed to replace the path in the filename attribute
sed -i "s|filename=\"$ORIGINAL_PATH_PREFIX|filename=\"$DESIRED_PATH_PREFIX|g" "$COVERAGE_FILE"


echo "Fixed coverage paths!"