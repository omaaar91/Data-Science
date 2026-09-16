"""
================================================================================
Synthetic Employee Data Generator for E-Commerce Analytics Pipeline
================================================================================
Description:
Generates 40 realistic synthetic employee records with corporate emails,
sales departments, job titles, base salaries, commission rates, and performance ratings.
"""

import random
from faker import Faker
import pandas as pd

# Configuration
NUM_EMPLOYEES = 40
OUTPUT_FILE = "employees.csv"
RANDOM_SEED = 42

fake = Faker()
Faker.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

JOB_ROLES = [
    {"title": "Junior Sales Associate", "dept": "Online Retail", "min_salary": 3200, "max_salary": 4000, "comm": 0.02},
    {"title": "Sales Representative", "dept": "Direct Sales", "min_salary": 4200, "max_salary": 5200, "comm": 0.03},
    {"title": "Senior Sales Executive", "dept": "Corporate Accounts", "min_salary": 5500, "max_salary": 6800, "comm": 0.04},
    {"title": "Key Account Manager", "dept": "Corporate Accounts", "min_salary": 6500, "max_salary": 8000, "comm": 0.05},
    {"title": "Customer Success Specialist", "dept": "Customer Success", "min_salary": 3800, "max_salary": 4800, "comm": 0.02},
    {"title": "Sales Team Lead", "dept": "Direct Sales", "min_salary": 7000, "max_salary": 8500, "comm": 0.05},
]


def generate_employees(target_count: int = NUM_EMPLOYEES) -> pd.DataFrame:
    employees = []
    seen_emails = set()

    for _ in range(target_count):
        gender = random.choice(["Male", "Female"])
        if gender == "Male":
            first_name = fake.first_name_male()
            last_name = fake.last_name_male()
        else:
            first_name = fake.first_name_female()
            last_name = fake.last_name_female()

        full_name = f"{first_name} {last_name}"

        # Corporate unique email
        base_email = f"{first_name.lower()}.{last_name.lower()}@ecombooks.com"
        clean_email = "".join(c for c in base_email if c.isalnum() or c in ".-_@")
        email = clean_email
        counter = 1
        while email in seen_emails:
            email = f"{first_name.lower()}.{last_name.lower()}{counter}@ecombooks.com"
            counter += 1
        seen_emails.add(email)

        # Phone: numeric int64 clean
        raw_phone = fake.phone_number()
        clean_phone = "".join(c for c in raw_phone.split("x")[0] if c.isdigit())
        phone = int(clean_phone) if clean_phone else random.randint(1000000000, 9999999999)

        # Role, department, salary & commission
        role_info = random.choice(JOB_ROLES)
        job_title = role_info["title"]
        department = role_info["dept"]
        salary = random.randint(role_info["min_salary"], role_info["max_salary"])
        commission_rate = role_info["comm"]

        # Hire date (within the last 4 years)
        hire_date = fake.date_between(start_date="-4y", end_date="-3m").strftime("%Y-%m-%d")

        # Performance score (out of 5.0)
        performance_score = round(random.uniform(3.2, 5.0), 1)

        # Office Location
        office_location = random.choice(["New York HQ", "London Branch", "Berlin Office", "Tokyo Hub", "Dubai Center"])

        employees.append({
            "FirstName": first_name,
            "LastName": last_name,
            "FullName": full_name,
            "Email": email,
            "Phone": phone,
            "Gender": gender,
            "JobTitle": job_title,
            "Department": department,
            "HireDate": hire_date,
            "Salary": salary,
            "CommissionRate": commission_rate,
            "PerformanceScore": performance_score,
            "OfficeLocation": office_location
        })

    df = pd.DataFrame(employees)
    return df


def main():
    print("=" * 60)
    print(f"Generating {NUM_EMPLOYEES} Synthetic Employees...")
    print("=" * 60)

    df = generate_employees(NUM_EMPLOYEES)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print(f"[Success] Saved {len(df)} employees to '{OUTPUT_FILE}'")
    print("\n--- Employees Preview ---")
    print(df.head())
    print("\n--- Summary Statistics ---")
    print(df.describe())


if __name__ == "__main__":
    main()
