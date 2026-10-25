from data_cleaner import clean_dataset
import os


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ============================================================
# INPUT DATASET
# ============================================================

input_file = os.path.join(
    BASE_DIR,
    "data",
    "uploads",
    "AI_Customer_Segmentation_12000_Customers.csv"
)


# ============================================================
# OUTPUT DATASET
# ============================================================

output_file = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "cleaned_customers.csv"
)


# ============================================================
# REPORT
# ============================================================

report_file = os.path.join(
    BASE_DIR,
    "data",
    "reports",
    "cleaning_report.json"
)


# ============================================================
# RUN CLEANING
# ============================================================

print()
print("=" * 60)
print("AI DATA CLEANING ENGINE")
print("=" * 60)
print()

print("Cleaning dataset...")
print()


report = clean_dataset(
    input_file,
    output_file,
    report_file
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("===== BEFORE CLEANING =====")

print(
    "Rows:",
    report["before"]["rows"]
)

print(
    "Columns:",
    report["before"]["columns"]
)

print(
    "Missing Values:",
    report["before"]["missing_values"]
)

print(
    "Duplicate Rows:",
    report["before"]["duplicate_rows"]
)


print()
print("===== CLEANING ACTIONS =====")

print(
    "Duplicates Removed:",
    report["cleaning_actions"]
    ["duplicate_rows_removed"]
)

print(
    "Numerical Missing Values Filled:",
    report["cleaning_actions"]
    ["numerical_missing_values_filled"]
)

print(
    "Categorical Missing Values Filled:",
    report["cleaning_actions"]
    ["categorical_missing_values_filled"]
)

print(
    "Outliers Detected:",
    report["cleaning_actions"]
    ["outliers_detected"]
)


print()
print("===== AFTER CLEANING =====")

print(
    "Rows:",
    report["after"]["rows"]
)

print(
    "Columns:",
    report["after"]["columns"]
)

print(
    "Missing Values:",
    report["after"]["missing_values"]
)

print(
    "Duplicate Rows:",
    report["after"]["duplicate_rows"]
)


print()
print("Cleaned dataset saved to:")

print(output_file)

print()

print("Cleaning report saved to:")

print(report_file)

print()

print("=" * 60)
print("AI DATA CLEANING COMPLETED")
print("=" * 60)