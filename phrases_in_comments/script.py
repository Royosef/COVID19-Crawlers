import csv

jurnal = 'kikar'

def create_individual_csv_files(input_csv):
    with open(input_csv, mode='r', newline='', encoding='utf-8-sig') as infile:
        reader = csv.reader(infile)

        for row in reader:
            filename = f'COVID19-Crawlers/phrases_in_comments/{jurnal}/{(row[0].replace('?', ''))}_{jurnal}.csv'
            with open(filename, mode='w', newline='', encoding='utf-8-sig') as outfile:
                writer = csv.writer(outfile)
                writer.writerow([row[0]])  # Write headers in the first row
                
                for sample in row[1:]:
                    writer.writerow([sample])  # Write the rest of the data

if __name__ == "__main__":
    input_csv = f'{jurnal}_comments_output_3.csv'  # Change this to your input CSV file path
    create_individual_csv_files(input_csv)
