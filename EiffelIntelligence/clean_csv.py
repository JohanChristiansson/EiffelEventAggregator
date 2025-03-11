import csv
import re

def clean_and_format_csv(input_file, output_file):
    # Define headers
    headers = [
        "Timestamp", "Queue 1 Length", "Queue 2 Length", "Acknowledged Events/Sec Queue 1", 
        "Acknowledged Events/Sec Queue 2", "CPU Usage (%)", "Disk Usage (%)", "Disk Used (GB)", 
        "Disk Free (GB)", "Memory Usage (%)", "Memory Used (GB)", "Memory Free (GB)"
    ]

    # Open input and output files
    with open(input_file, "r") as infile, open(output_file, "w", newline="") as outfile:
        reader = infile.readlines()
        writer = csv.writer(outfile)

        # Write headers to the new CSV
        writer.writerow(headers)

        for line in reader:
            # Extract values using regex
            match = re.match(
                r'(.+?), Queue 1 Length: (\d+), Queue 2 Length: (\d+), Events/Sec Queue 1: (\d+), '
                r'Events/Sec Queue 2: (\d+), CPU Usage: ([\d.]+)%, Disk Usage: ([\d.]+)%, '
                r'Disk Used: ([\d.]+) GB, Disk Free: ([\d.]+) GB, Memory Usage: ([\d.]+)%, '
                r'Memory Used: ([\d.]+) GB, Memory Free: ([\d.]+) GB',
                line.strip()
            )

            if match:
                # Convert matched values to a list and write to CSV
                writer.writerow(match.groups())

    print(f"Formatted CSV saved as {output_file}")

if __name__ == "__main__":
    input_file = "resource_usage.csv"  # Change this to your actual file name
    output_file = "formatted_resource_usage.csv"
    clean_and_format_csv(input_file, output_file)