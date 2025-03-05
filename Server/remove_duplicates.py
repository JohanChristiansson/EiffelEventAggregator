def remove_duplicates(input_file, output_file):
    try:
        # Open the input file to read the data
        with open(input_file, 'r') as infile:
            lines = infile.readlines()
        
        # Remove duplicates by converting the list to a set
        unique_lines = set(lines)
        
        # Open the output file to write the unique data
        with open(output_file, 'w') as outfile:
            outfile.writelines(unique_lines)
        
        print(f"Duplicates removed. Data written to {output_file}")
    
    except FileNotFoundError:
        print(f"The file {input_file} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
input_file = 'event_log.txt'  # Replace with the path to your input file
output_file = 'real_event_log.txt'  # Replace with the path to your output file

remove_duplicates(input_file, output_file)
