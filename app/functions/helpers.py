import subprocess


def get_folder_size(path):
    """
    Get the size of a folder in bytes. Requires the `du` command to be available on the system.
    """
    result = subprocess.run(["du", "-sb", str(path)], capture_output=True, text=True)
    size = int(result.stdout.split()[0])
    return size


def convert_bytes(input_bytes: int, target_unit="B") -> float:
    """
    Converts a byte value to the specified target unit ('B', 'KB', 'MB', 'GB', 'TB').
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_factors = {u: 1024**i for i, u in enumerate(units)}

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
