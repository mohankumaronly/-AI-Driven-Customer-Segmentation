import pandas as pd
import numpy as np
import os


# ============================================================
# AI DATA CLEANING ENGINE
# ============================================================

def clean_dataset(input_file, output_file, report_file):

    # --------------------------------------------------------
    # READ DATASET
    # --------------------------------------------------------

    extension = os.path.splitext(input_file)[1].lower()

    if extension == ".csv":
        df = pd.read_csv(input_file)
    elif extension in [".xlsx", ".xls", ".xlsm", ".ods"]:
        df = pd.read_excel(input_file)
    elif extension in [".tsv", ".txt"]:
        df = pd.read_csv(input_file, sep="\t")
    elif extension in [".json", ".jsonl", ".ndjson"]:
        try:
            df = pd.read_json(input_file, lines=extension in [".jsonl", ".ndjson"])
        except ValueError:
            df = pd.read_json(input_file)
    else:
        raise ValueError("Unsupported format. Use CSV, Excel, TSV/TXT or JSON.")


    # --------------------------------------------------------
    # BEFORE CLEANING STATISTICS
    # --------------------------------------------------------

    before_rows = len(df)
    before_columns = len(df.columns)

    before_missing = int(
        df.isnull().sum().sum()
    )

    before_duplicates = int(
        df.duplicated().sum()
    )


    # --------------------------------------------------------
    # COPY ORIGINAL DATA
    # --------------------------------------------------------

    cleaned_df = df.copy()


    # --------------------------------------------------------
    # 1. REMOVE DUPLICATE ROWS
    # --------------------------------------------------------

    duplicate_rows_removed = int(
        cleaned_df.duplicated().sum()
    )

    cleaned_df = cleaned_df.drop_duplicates()


    # --------------------------------------------------------
    # 2. HANDLE NUMERICAL MISSING VALUES
    # --------------------------------------------------------

    numerical_columns = cleaned_df.select_dtypes(
        include=np.number
    ).columns.tolist()


    numerical_missing_filled = 0


    for column in numerical_columns:

        missing_count = int(
            cleaned_df[column].isnull().sum()
        )

        if missing_count > 0:

            median_value = cleaned_df[column].median()

            cleaned_df[column] = (
                cleaned_df[column].fillna(
                    median_value
                )
            )

            numerical_missing_filled += missing_count


    # --------------------------------------------------------
    # 3. HANDLE CATEGORICAL MISSING VALUES
    # --------------------------------------------------------

    categorical_columns = cleaned_df.select_dtypes(
        include=["object", "category"]
    ).columns.tolist()


    categorical_missing_filled = 0


    for column in categorical_columns:

        missing_count = int(
            cleaned_df[column].isnull().sum()
        )

        if missing_count > 0:

            mode_values = cleaned_df[column].mode()

            if len(mode_values) > 0:

                replacement = mode_values.iloc[0]

            else:

                replacement = "Unknown"


            cleaned_df[column] = (
                cleaned_df[column].fillna(
                    replacement
                )
            )

            categorical_missing_filled += missing_count


    # --------------------------------------------------------
    # 4. OUTLIER DETECTION
    # --------------------------------------------------------

    outlier_summary = {}

    total_outliers = 0


    for column in numerical_columns:

        series = cleaned_df[column]

        if series.empty:
            continue


        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1


        if iqr == 0:

            outlier_count = 0

        else:

            lower_bound = (
                q1 - 1.5 * iqr
            )

            upper_bound = (
                q3 + 1.5 * iqr
            )


            outlier_mask = (
                (series < lower_bound) |
                (series > upper_bound)
            )


            outlier_count = int(
                outlier_mask.sum()
            )


        if outlier_count > 0:

            outlier_summary[column] = {
                "outliers": outlier_count
            }

            total_outliers += outlier_count


    # --------------------------------------------------------
    # 5. FINAL STATISTICS
    # --------------------------------------------------------

    after_rows = len(cleaned_df)

    after_columns = len(cleaned_df.columns)

    after_missing = int(
        cleaned_df.isnull().sum().sum()
    )

    after_duplicates = int(
        cleaned_df.duplicated().sum()
    )


    # --------------------------------------------------------
    # 6. SAVE CLEANED DATASET
    # --------------------------------------------------------

    output_directory = os.path.dirname(
        output_file
    )

    os.makedirs(
        output_directory,
        exist_ok=True
    )


    cleaned_df.to_csv(
        output_file,
        index=False
    )


    # --------------------------------------------------------
    # 7. CREATE CLEANING REPORT
    # --------------------------------------------------------

    report = {

        "status": "completed",

        "before": {

            "rows": before_rows,

            "columns": before_columns,

            "missing_values":
                before_missing,

            "duplicate_rows":
                before_duplicates

        },

        "cleaning_actions": {

            "duplicate_rows_removed":
                duplicate_rows_removed,

            "numerical_missing_values_filled":
                numerical_missing_filled,

            "categorical_missing_values_filled":
                categorical_missing_filled,

            "outliers_detected":
                total_outliers

        },

        "outlier_details":
            outlier_summary,

        "after": {

            "rows": after_rows,

            "columns": after_columns,

            "missing_values":
                after_missing,

            "duplicate_rows":
                after_duplicates

        }

    }


    # --------------------------------------------------------
    # SAVE REPORT
    # --------------------------------------------------------

    report_directory = os.path.dirname(
        report_file
    )

    os.makedirs(
        report_directory,
        exist_ok=True
    )


    import json

    with open(
        report_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )


    return report