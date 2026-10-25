import pandas as pd
import os


def analyze_dataset(file_path):

    # Check file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    # Get file extension
    extension = os.path.splitext(file_path)[1].lower()

    # Read dataset
    if extension == ".csv":
        df = pd.read_csv(file_path)
    elif extension in [".xlsx", ".xls", ".xlsm", ".ods"]:
        df = pd.read_excel(file_path)
    elif extension in [".tsv", ".txt"]:
        df = pd.read_csv(file_path, sep="\t")
    elif extension in [".json", ".jsonl", ".ndjson"]:
        try:
            df = pd.read_json(file_path, lines=extension in [".jsonl", ".ndjson"])
        except ValueError:
            df = pd.read_json(file_path)
    else:
        raise ValueError("Unsupported format. Use CSV, Excel, TSV/TXT or JSON.")

    # -----------------------------
    # BASIC DATASET INFORMATION
    # -----------------------------

    total_rows = len(df)
    total_columns = len(df.columns)

    # -----------------------------
    # MISSING VALUES
    # -----------------------------

    total_missing_values = int(
        df.isnull().sum().sum()
    )

    # -----------------------------
    # DUPLICATE ROWS
    # -----------------------------

    duplicate_rows = int(
        df.duplicated().sum()
    )

    # -----------------------------
    # COLUMN INFORMATION
    # -----------------------------

    columns = []

    for column in df.columns:

        column_info = {
            "name": column,
            "data_type": str(df[column].dtype),
            "missing_values": int(
                df[column].isnull().sum()
            ),
            "unique_values": int(
                df[column].nunique()
            )
        }

        columns.append(column_info)

    # -----------------------------
    # NUMERICAL COLUMNS
    # -----------------------------

    numerical_columns = df.select_dtypes(
        include="number"
    ).columns.tolist()

    # -----------------------------
    # CATEGORICAL COLUMNS
    # -----------------------------

    categorical_columns = df.select_dtypes(
        include=["object", "category"]
    ).columns.tolist()

    # -----------------------------
    # NUMERICAL STATISTICS
    # -----------------------------

    statistics = {}

    for column in numerical_columns:

        statistics[column] = {
            "minimum": float(
                df[column].min()
            ),
            "maximum": float(
                df[column].max()
            ),
            "average": float(
                df[column].mean()
            ),
            "median": float(
                df[column].median()
            ),
            "standard_deviation": float(
                df[column].std()
            )
        }

    # -----------------------------
    # DATASET MEMORY USAGE
    # -----------------------------

    memory_usage = int(
        df.memory_usage(deep=True).sum()
    )

    # -----------------------------
    # FINAL RESULT
    # -----------------------------

    result = {

        "total_rows": total_rows,

        "total_columns": total_columns,

        "total_missing_values":
            total_missing_values,

        "duplicate_rows":
            duplicate_rows,

        "numerical_columns":
            numerical_columns,

        "categorical_columns":
            categorical_columns,

        "memory_usage_bytes":
            memory_usage,

        "columns":
            columns,

        "statistics":
            statistics
    }

    return result