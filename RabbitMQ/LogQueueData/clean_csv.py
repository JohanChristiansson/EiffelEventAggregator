import re
import csv

def clean_log_data(input_file, output_file):

    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = infile.readlines()
        writer = csv.writer(outfile)
        
        #Keep the header as is
        first_line = reader[0].strip()
        writer.writerow(first_line.split(','))
        reader = reader[1:]

        for line in reader:
            line = line.strip()
            if line: 
                #Handle the date seperately
                parts = line.split(",")  
                timestamp = parts[0].strip()
                values = [timestamp]
                
                for part in parts[1:]:
                    matches = re.findall(r"(\d+(\.\d+)?)", part) 
                    for match in matches:
                        values.append(match[0].strip())
        
                writer.writerow(values)

if __name__ == "__main__":
    input_file = 'resource_usage.csv'
    output_file = 'cleaned_log_data.csv' 
    clean_log_data(input_file, output_file)
    print(f"Log data cleaned and saved to {output_file}.")
