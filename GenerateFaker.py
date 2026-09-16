"""
================================================================================
Synthetic Customer Data Generator for SQL & Data Analytics Pipeline
================================================================================
Description:
This script uses the Faker library and Pandas to generate 2,000 realistic,
unique synthetic customer records.

Columns Generated:
- FirstName
- LastName
- Email (Guaranteed Unique)
- Phone
- City
- Country
- Gender
- RegistrationDate

Note: CustomerID is intentionally excluded so SQL Server / PostgreSQL / MySQL
will automatically generate it using AUTO_INCREMENT / IDENTITY.
"""

import random
from faker import Faker
import pandas as pd

# Constants & Configuration
NUM_CUSTOMERS = 2000
OUTPUT_FILE = "customers.csv"
RANDOM_SEED = 42

# Initialize Faker with fixed seed for reproducible results
fake = Faker()
Faker.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)


def generate_customer_data(target_count: int = NUM_CUSTOMERS) -> pd.DataFrame:
    """
    Generates a specified number of realistic synthetic customer records with unique emails.
    """
    customers = []
    seen_emails = set()

    print(f"Generating {target_count} unique customer records...")

    while len(customers) < target_count:
        # Realistic gender and name generation
        gender = random.choice(["Male", "Female"])
        if gender == "Male":
            first_name = fake.first_name_male()
            last_name = fake.last_name_male()
        else:
            first_name = fake.first_name_female()
            last_name = fake.last_name_female()

        # Generate unique email address
        # Combine name with domain and ensure global uniqueness
        base_email = f"{first_name.lower()}.{last_name.lower()}@{fake.free_email_domain()}"
        
        # Clean any non-standard characters from email
        clean_email = "".join(c for c in base_email if c.isalnum() or c in ".-_@")
        
        # Handle collision if email already exists
        email = clean_email
        counter = 1
        while email in seen_emails or not email:
            email = f"{first_name.lower()}.{last_name.lower()}{counter}@{fake.free_email_domain()}"
            counter += 1

        seen_emails.add(email)

        # Generate phone number, location, and registration date
        phone = fake.phone_number()
        city = fake.city()
        country = fake.country()
        
        # Registration date within the last 3 years up to today (YYYY-MM-DD format)
        reg_date = fake.date_between(start_date="-3y", end_date="today").strftime("%Y-%m-%d")

        customers.append({
            "FirstName": first_name,
            "LastName": last_name,
            "Email": email,
            "Phone": phone,
            "City": city,
            "Country": country,
            "Gender": gender,
            "RegistrationDate": reg_date
        })

    # Create Pandas DataFrame
    df = pd.DataFrame(customers)
    return df


def validate_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Checks for duplicates and missing values to ensure data quality.
    """
    print("\n--- Validating Data Quality ---")
    
    # 1. Check & remove duplicates
    initial_count = len(df)
    df.drop_duplicates(inplace=True)
    df.drop_duplicates(subset=["Email"], keep="first", inplace=True)
    duplicate_rows = initial_count - len(df)

    # 2. Check for missing values
    missing_count = df.isnull().sum().sum()
    if missing_count > 0:
        print(f"[Warning] Found {missing_count} missing values. Handling them...")
        df.dropna(inplace=True)

    # 3. Print required statistics
    print(f"• Total Customers Generated : {len(df)}")
    print(f"• Unique Emails Count        : {df['Email'].nunique()}")
    print(f"• Duplicate Rows Removed    : {duplicate_rows}")
    print(f"• Missing Values Remaining  : {df.isnull().sum().sum()}")

    return df


def save_dataset(df: pd.DataFrame, filename: str = OUTPUT_FILE) -> None:
    """
    Exports the DataFrame to CSV without index, formatted for SQL table ingestion.
    """
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"\n[Success] Dataset exported successfully to '{filename}'")


def main():
    """
    Main pipeline orchestrator.
    """
    print("=" * 60)
    print("Starting Synthetic Customer Data Generator")
    print("=" * 60)

    # 1. Generate Data
    df = generate_customer_data(target_count=NUM_CUSTOMERS)

    # 2. Validate & Clean Data
    df = validate_and_clean(df)

    # 3. Export to CSV
    save_dataset(df, OUTPUT_FILE)

    # 4. Preview Dataset & Schema
    print("\n--- Dataset Preview (First 5 Rows) ---")
    print(df.head())

    print("\n--- Dataset Information ---")
    print(df.info())

    print("\n" + "=" * 60)
    print("Generation complete! Ready to import into SQL 'Customers' table.")
    print("=" * 60)


if __name__ == "__main__":
    main()
