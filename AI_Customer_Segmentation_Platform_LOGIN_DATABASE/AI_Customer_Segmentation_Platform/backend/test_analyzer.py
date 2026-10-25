from data_analyzer import analyze_dataset
import os


# Get the main project folder
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Dataset path
file_path = os.path.join(
    BASE_DIR,
    "data",
    "uploads",
    "AI_Customer_Segmentation_12000_Customers.csv"
)

print("\n===== CUSTOMER DATASET ANALYSIS =====")

print("Dataset:")
print(os.path.basename(file_path))

print("\nAnalyzing dataset...")

result = analyze_dataset(file_path)

print("\n===== BASIC INFORMATION =====")

print("Total Rows:", result["total_rows"])
print("Total Columns:", result["total_columns"])
print("Total Missing Values:", result["total_missing_values"])
print("Duplicate Rows:", result["duplicate_rows"])


print("\n===== NUMERICAL COLUMNS =====")

for column in result["numerical_columns"]:
    print("-", column)


print("\n===== CATEGORICAL COLUMNS =====")

for column in result["categorical_columns"]:
    print("-", column)


print("\n===== COLUMN DETAILS =====")

for column in result["columns"]:

    print(
        column["name"],
        "| Type:", column["data_type"],
        "| Missing:", column["missing_values"],
        "| Unique:", column["unique_values"]
    )


print("\n===== NUMERICAL STATISTICS =====")

for column, stats in result["statistics"].items():

    print(
        column,
        "| Min:", round(stats["minimum"], 2),
        "| Max:", round(stats["maximum"], 2),
        "| Average:", round(stats["average"], 2),
        "| Median:", round(stats["median"], 2)
    )


print("\n===== ANALYSIS COMPLETED =====")