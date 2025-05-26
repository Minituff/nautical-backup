import subprocess
import re

ACCEPTED_UNITS = ["B", "KB", "MB", "GB", "TB"]


def get_folder_size(path):
    """
    Get the size of a folder in bytes. Requires the `du` command to be available on the system.
    """
    result = subprocess.run(["du", "-sb", str(path)], capture_output=True, text=True)
    size = int(result.stdout.split()[0])
    return size


def separate_number_and_unit(input_str: str) -> tuple[float, str]:
    """
    Separates the numeric value and unit from an input string.
    Accepted units: B, KB, MB, GB, TB (case-insensitive).
    Returns (number: float, unit: str) or raises ValueError if invalid.
    """
    pattern = r"^\s*([\d.]+)\s*([KMGTP]?B)\s*$"
    match = re.match(pattern, input_str.strip(), re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid input: '{input_str}'. Expected format like '10GB', '500 MB', etc.")
    number, unit = match.groups()
    unit = unit.upper()
    if unit not in ACCEPTED_UNITS:
        raise ValueError(f"Unit '{unit}' not accepted. Allowed units: {ACCEPTED_UNITS}")
    return float(number), unit


def convert_bytes(input_bytes: int | float, target_unit="B") -> float:
    """
    Converts a byte value to the specified target unit ('B', 'KB', 'MB', 'GB', 'TB').
    """
    unit_factors = {u: 1024**i for i, u in enumerate(ACCEPTED_UNITS)}

    target_unit = target_unit.upper()
    if target_unit not in unit_factors:
        raise ValueError(f"Unsupported unit: {target_unit}")

    return input_bytes / unit_factors[target_unit]


if __name__ == "__main__":
    # Example usage
    print(get_folder_size("."), "B")  # Prints the size of the current directory in bytes
    print(convert_bytes(get_folder_size("."), "MB"), "MB")
    print(convert_bytes(get_folder_size("."), "GB"), "GB")
    print(convert_bytes(10737418240, "MB"), "MB")  # Converts 10GB to MB
    print(convert_bytes(524288000, "GB"), "GB")  # Converts 500MB to GB
    print(convert_bytes(1099511627776, "KB"), "KB")  # Converts 1TB to KB

    test_cases = ["10GB", "500 MB", "1.5tb", "1024kb", "42 B", "100XB"]
    for case in test_cases:
        try:
            num, unit = separate_number_and_unit(case)
            print(f"Input: '{case}' -> Number: {num}, Unit: {unit}")
        except ValueError as e:
            print(f"Input: '{case}' -> Error: {e}")
