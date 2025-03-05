def compare_files(file1, file2):
    """Compares two files and prints rows that exist in one file but not in the other."""
    with open(file1, "r") as f1, open(file2, "r") as f2:
        set1 = set(f1.read().splitlines())  # Read file1 as a set of lines
        set2 = set(f2.read().splitlines())  # Read file2 as a set of lines

    missing_in_file2 = set1 - set2  # Rows in file1 but not in file2
    missing_in_file1 = set2 - set1  # Rows in file2 but not in file1

    if missing_in_file2:
        print(f"❌ Rows in {file1} but missing in {file2}:")
        for row in missing_in_file2:
            print(row)

    if missing_in_file1:
        print(f"❌ Rows in {file2} but missing in {file1}:")
        for row in missing_in_file1:
            print(row)

    if not missing_in_file1 and not missing_in_file2:
        print("✅ Both files contain the same rows!")

# Example usage
compare_files("event_log.txt", "event_log_validated.txt")

