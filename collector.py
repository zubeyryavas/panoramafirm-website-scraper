import pandas as pd
import re

# Simple regex for email validation
EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

def is_valid_email(email):
    if pd.isna(email):
        return False
    return re.match(EMAIL_REGEX, email) is not None


def filter_valid_emails(input_path, output_path):
    df = pd.read_csv(input_path)
    total_records = len(df)

    df_valid = df[df['Email'].apply(is_valid_email)]
    valid_records = len(df_valid)

    df_valid.to_csv(output_path, index=False)

    print(f"Total records in input file: {total_records}")
    print(f"Valid records collected: {valid_records}")

if __name__ == "__main__":
    input_file = "spa_and_wellness.csv"   # your input file path here
    output_file = "spa_and_wellness_with_emails.csv" # your output file path here

    filter_valid_emails(input_file, output_file)
    print(f"Filtered file saved to {output_file}")
