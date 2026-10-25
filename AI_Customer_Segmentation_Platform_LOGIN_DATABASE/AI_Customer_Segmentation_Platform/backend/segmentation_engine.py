# ============================================================
# AI CUSTOMER SEGMENTATION ENGINE
# ============================================================

import os
import json
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


# ============================================================
# MAIN SEGMENTATION FUNCTION
# ============================================================

def segment_customers(
    input_file,
    output_file,
    report_file
):

    # --------------------------------------------------------
    # 1. READ CLEANED DATASET
    # --------------------------------------------------------

    df = pd.read_csv(input_file)


    if df.empty:

        raise ValueError(
            "The cleaned dataset is empty."
        )


    # --------------------------------------------------------
    # 2. SELECT NUMERICAL FEATURES
    # --------------------------------------------------------

    numerical_columns = df.select_dtypes(
        include=["number"]
    ).columns.tolist()


    if len(numerical_columns) < 2:

        raise ValueError(
            "At least two numerical columns are required "
            "for customer segmentation."
        )


    # --------------------------------------------------------
    # 3. REMOVE ID-LIKE COLUMNS
    # --------------------------------------------------------

    feature_columns = []


    for column in numerical_columns:

        column_lower = column.lower()


        # Ignore common ID columns
        if (
            column_lower == "id"
            or column_lower.endswith("id")
            or "customerid" in column_lower
            or "customer_id" in column_lower
        ):

            continue


        # Ignore columns with almost unique values
        unique_ratio = (
            df[column].nunique()
            / len(df)
        )


        if unique_ratio > 0.95:

            continue


        feature_columns.append(
            column
        )


    # --------------------------------------------------------
    # 4. FALLBACK
    # --------------------------------------------------------

    if len(feature_columns) < 2:

        feature_columns = numerical_columns[:]


    # --------------------------------------------------------
    # 5. PREPARE FEATURES
    # --------------------------------------------------------

    feature_data = df[
        feature_columns
    ].copy()


    # Convert values to numeric
    for column in feature_columns:

        feature_data[column] = pd.to_numeric(
            feature_data[column],
            errors="coerce"
        )


    # Replace invalid values
    feature_data = feature_data.replace(
        [float("inf"), float("-inf")],
        pd.NA
    )


    # Fill remaining values
    feature_data = feature_data.fillna(
        feature_data.median()
    )


    # --------------------------------------------------------
    # 6. SCALE FEATURES
    # --------------------------------------------------------

    scaler = StandardScaler()


    scaled_features = scaler.fit_transform(
        feature_data
    )


    # --------------------------------------------------------
    # 7. FIND BEST NUMBER OF CLUSTERS
    # --------------------------------------------------------

    max_clusters = min(
        8,
        len(df) - 1
    )


    if max_clusters < 2:

        raise ValueError(
            "Not enough records for customer segmentation."
        )


    scores = []


    for k in range(
        2,
        max_clusters + 1
    ):

        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10
        )


        labels = model.fit_predict(
            scaled_features
        )


        score = silhouette_score(
            scaled_features,
            labels
        )


        scores.append({

            "clusters": k,

            "silhouette_score": round(
                float(score),
                4
            )

        })


    # --------------------------------------------------------
    # 8. SELECT BEST CLUSTER COUNT
    # --------------------------------------------------------

    best_result = max(
        scores,
        key=lambda item:
            item["silhouette_score"]
    )


    best_k = best_result[
        "clusters"
    ]


    # --------------------------------------------------------
    # 9. FINAL K-MEANS MODEL
    # --------------------------------------------------------

    final_model = KMeans(

        n_clusters=best_k,

        random_state=42,

        n_init=10

    )


    cluster_labels = final_model.fit_predict(
        scaled_features
    )


    # --------------------------------------------------------
    # 10. ADD SEGMENTS TO DATASET
    # --------------------------------------------------------

    result_df = df.copy()


    # Use simple segment numbers
    result_df["CustomerSegment"] = (
        cluster_labels + 1
    )


    # --------------------------------------------------------
    # 11. CREATE SEGMENT PROFILES
    # --------------------------------------------------------

    segment_profiles = []


    for segment in sorted(
        result_df["CustomerSegment"].unique()
    ):

        segment_data = result_df[
            result_df["CustomerSegment"]
            == segment
        ]


        profile = {

            "segment":
                int(segment),

            "customer_count":
                int(len(segment_data))

        }


        # Calculate averages
        for column in feature_columns:

            profile[
                "avg_" + column
            ] = round(

                float(
                    segment_data[column].mean()
                ),

                2

            )


        segment_profiles.append(
            profile
        )


    # --------------------------------------------------------
    # 12. CREATE SEGMENT SUMMARY
    # --------------------------------------------------------

    segment_summary = {

        "total_customers":
            int(len(result_df)),

        "number_of_segments":
            int(best_k),

        "features_used":
            feature_columns,

        "best_silhouette_score":
            best_result[
                "silhouette_score"
            ],

        "cluster_evaluation":
            scores,

        "segment_profiles":
            segment_profiles

    }


    # --------------------------------------------------------
    # 13. SAVE SEGMENTED DATASET
    # --------------------------------------------------------

    output_directory = os.path.dirname(
        output_file
    )


    if output_directory:

        os.makedirs(
            output_directory,
            exist_ok=True
        )


    result_df.to_csv(
        output_file,
        index=False
    )


    # --------------------------------------------------------
    # 14. SAVE AI SEGMENTATION REPORT
    # --------------------------------------------------------

    report_directory = os.path.dirname(
        report_file
    )


    if report_directory:

        os.makedirs(
            report_directory,
            exist_ok=True
        )


    with open(
        report_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            segment_summary,
            file,
            indent=4
        )


    # --------------------------------------------------------
    # 15. RETURN RESULT
    # --------------------------------------------------------

    return segment_summary

