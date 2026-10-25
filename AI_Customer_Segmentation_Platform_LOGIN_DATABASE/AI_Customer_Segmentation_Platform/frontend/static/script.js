/* =========================================================
   AI CUSTOMER SEGMENTATION PLATFORM
   MAIN JAVASCRIPT
========================================================= */


/* =========================================================
   PAGE LOAD
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    console.log("script.js loaded successfully");

    // Start with only the upload form visible. Later stages are revealed by buttons.
    hideWorkflowSections();

});

/* =========================================================
   STEP-BY-STEP WORKFLOW HELPERS
========================================================= */

const WORKFLOW_SECTION_IDS = [
    "analysisSection",
    "cleanedAnalysisSection",
    "segmentationSection",
    "businessAnalyticsSection",
    "powerbiSection"
];

function hideWorkflowSections() {
    WORKFLOW_SECTION_IDS.forEach(function (id) {
        const section = document.getElementById(id);
        if (section) section.classList.add("hidden");
    });
}

function showWorkflowSections(sectionIds, scrollToId) {
    hideWorkflowSections();

    (Array.isArray(sectionIds) ? sectionIds : [sectionIds]).forEach(function (id) {
        const section = document.getElementById(id);
        if (section) section.classList.remove("hidden");
    });

    const target = document.getElementById(scrollToId || (Array.isArray(sectionIds) ? sectionIds[0] : sectionIds));
    if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
}


/* =========================================================
   HELPER - SHOW STATUS
========================================================= */

function showStatus(elementId, message, type = "") {

    const element = document.getElementById(elementId);

    if (!element) {
        console.error("Element not found:", elementId);
        return;
    }

    element.textContent = message;
    element.className = "status";

    if (type) {
        element.classList.add(type);
    }

}


/* =========================================================
   UPLOAD DATASET
========================================================= */

async function uploadDataset() {

    console.log("Upload button clicked");

    const fileInput =
        document.getElementById("datasetFile");

    const uploadButton =
        document.getElementById("uploadButton");


    if (!fileInput) {

        console.error("datasetFile element not found");

        return;
    }


    if (!uploadButton) {

        console.error("uploadButton element not found");

        return;
    }


    /* -----------------------------------------------------
       CHECK FILE
    ----------------------------------------------------- */

    if (
        !fileInput.files ||
        fileInput.files.length === 0
    ) {

        showStatus(
            "uploadStatus",
            "Please select a dataset first.",
            "error"
        );

        return;
    }


    const file = fileInput.files[0];


    console.log(
        "Selected file:",
        file.name
    );


    /* -----------------------------------------------------
       CHECK FILE TYPE
    ----------------------------------------------------- */

    const allowedExtensions = [
        ".csv",
        ".xlsx",
        ".xls"
    ];


    const fileName =
        file.name.toLowerCase();


    const validExtension =
        allowedExtensions.some(
            extension =>
                fileName.endsWith(extension)
        );


    if (!validExtension) {

        showStatus(
            "uploadStatus",
            "Please select a CSV or Excel file.",
            "error"
        );

        return;
    }


    /* -----------------------------------------------------
       FORM DATA
    ----------------------------------------------------- */

    const formData = new FormData();

    formData.append(
        "dataset",
        file
    );


    /* -----------------------------------------------------
       BUTTON STATE
    ----------------------------------------------------- */

    uploadButton.disabled = true;

    uploadButton.textContent =
        "Uploading...";


    showStatus(
        "uploadStatus",
        "Uploading dataset..."
    );


    try {

        /* -------------------------------------------------
           SEND FILE TO FLASK
        ------------------------------------------------- */

        const response = await fetch(
            "/upload",
            {
                method: "POST",
                body: formData
            }
        );


        console.log(
            "Upload response status:",
            response.status
        );


        const result =
            await response.json();


        console.log(
            "Upload response:",
            result
        );


        /* -------------------------------------------------
           CHECK RESPONSE
        ------------------------------------------------- */

        if (
            !response.ok ||
            !result.success
        ) {

            throw new Error(
                result.error ||
                "Dataset upload failed."
            );

        }


        /* -------------------------------------------------
           SUCCESS
        ------------------------------------------------- */

        showStatus(
            "uploadStatus",
            "Dataset uploaded successfully!",
            "success"
        );


        /* -------------------------------------------------
           START ANALYSIS
        ------------------------------------------------- */

        await analyzeDataset();


    } catch (error) {

        console.error(
            "UPLOAD ERROR:",
            error
        );


        showStatus(
            "uploadStatus",
            "Upload failed: " + error.message,
            "error"
        );


    } finally {

        uploadButton.disabled = false;

        uploadButton.textContent =
            "Upload Dataset";

    }

}


/* =========================================================
   ANALYZE DATASET
========================================================= */

async function analyzeDataset() {

    console.log(
        "Starting dataset analysis..."
    );


    try {

        const response =
            await fetch("/analyze");


        const result =
            await response.json();


        console.log(
            "Analysis response:",
            result
        );


        if (
            !response.ok ||
            !result.success
        ) {

            throw new Error(
                result.error ||
                "Dataset analysis failed."
            );

        }


        /* -------------------------------------------------
           SHOW ANALYSIS SECTION
        ------------------------------------------------- */

        showWorkflowSections("analysisSection", "analysisSection");
        const analysisSection = document.getElementById("analysisSection");


        /* -------------------------------------------------
           GET ANALYSIS DATA
        ------------------------------------------------- */

        const analysis =
            result.analysis || {};


        /* -------------------------------------------------
           DATASET NAME
        ------------------------------------------------- */

        const datasetName =
            document.getElementById(
                "datasetName"
            );


        if (datasetName) {

            datasetName.textContent =
                result.filename ||
                "Dataset";

        }


        /* -------------------------------------------------
           TOTAL ROWS
        ------------------------------------------------- */

        setText(
            "totalRows",
            getValue(
                analysis,
                [
                    "total_rows",
                    "rows",
                    "row_count"
                ]
            )
        );


        /* -------------------------------------------------
           TOTAL COLUMNS
        ------------------------------------------------- */

        setText(
            "totalColumns",
            getValue(
                analysis,
                [
                    "total_columns",
                    "columns",
                    "column_count"
                ]
            )
        );


        /* -------------------------------------------------
           MISSING VALUES
        ------------------------------------------------- */

        setText(
            "missingValues",
            getValue(
                analysis,
                [
                    "missing_values",
                    "missing",
                    "total_missing"
                ]
            )
        );


        /* -------------------------------------------------
           DUPLICATE ROWS
        ------------------------------------------------- */

        setText(
            "duplicateRows",
            getValue(
                analysis,
                [
                    "duplicate_rows",
                    "duplicates",
                    "total_duplicates"
                ]
            )
        );


        /* -------------------------------------------------
           NUMERICAL COLUMNS
        ------------------------------------------------- */

        const numericalColumns =
            getArray(
                analysis,
                [
                    "numerical_columns",
                    "numeric_columns"
                ]
            );


        setText(
            "numericalCount",
            numericalColumns.length
        );


        fillList(
            "numericalList",
            numericalColumns
        );


        /* -------------------------------------------------
           CATEGORICAL COLUMNS
        ------------------------------------------------- */

        const categoricalColumns =
            getArray(
                analysis,
                [
                    "categorical_columns",
                    "category_columns"
                ]
            );


        setText(
            "categoricalCount",
            categoricalColumns.length
        );


        fillList(
            "categoricalList",
            categoricalColumns
        );


        /* -------------------------------------------------
           COLUMN TABLE
        ------------------------------------------------- */

        buildColumnTable(
            analysis
        );


        /* -------------------------------------------------
           AI INSIGHT
        ------------------------------------------------- */

        const insight =
            getValue(
                analysis,
                [
                    "ai_insight",
                    "insight",
                    "message"
                ]
            );


        if (insight) {

            setText(
                "aiInsight",
                insight
            );

        } else {

            setText(
                "aiInsight",
                "Dataset analysis completed successfully."
            );

        }


        /* -------------------------------------------------
           SCROLL TO ANALYSIS
        ------------------------------------------------- */

        if (analysisSection) {

            analysisSection.scrollIntoView({
                behavior: "smooth"
            });

        }


    } catch (error) {

        console.error(
            "ANALYSIS ERROR:",
            error
        );


        showStatus(
            "uploadStatus",
            "Analysis failed: " +
            error.message,
            "error"
        );

    }

}


/* =========================================================
   AI DATA CLEANING
========================================================= */

async function startCleaning() {

    console.log(
        "Starting AI data cleaning..."
    );


    const button =
        document.getElementById(
            "cleanButton"
        );


    if (button) {

        button.disabled = true;

        button.textContent =
            "Cleaning dataset...";

    }


    showStatus(
        "cleaningStatus",
        "AI cleaning in progress..."
    );


    try {

        const response =
            await fetch(
                "/clean",
                {
                    method: "POST"
                }
            );


        const result =
            await response.json();


        console.log(
            "Cleaning response:",
            result
        );


        if (
            !response.ok ||
            !result.success
        ) {

            throw new Error(
                result.error ||
                "Data cleaning failed."
            );

        }


        showStatus(
            "cleaningStatus",
            "AI data cleaning completed successfully.",
            "success"
        );


        /* -------------------------------------------------
           ANALYZE CLEANED DATA
        ------------------------------------------------- */

        await analyzeCleanedDataset();


    } catch (error) {

        console.error(
            "CLEANING ERROR:",
            error
        );


        showStatus(
            "cleaningStatus",
            "Cleaning failed: " +
            error.message,
            "error"
        );


    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "Continue to AI Data Cleaning →";

        }

    }

}


/* =========================================================
   ANALYZE CLEANED DATASET
========================================================= */

async function analyzeCleanedDataset() {

    console.log(
        "Analyzing cleaned dataset..."
    );


    try {

        const response =
            await fetch(
                "/analyze-cleaned"
            );


        const result =
            await response.json();


        console.log(
            "Cleaned analysis:",
            result
        );


        if (
            !response.ok ||
            !result.success
        ) {

            throw new Error(
                result.error ||
                "Cleaned analysis failed."
            );

        }


        showWorkflowSections("cleanedAnalysisSection", "cleanedAnalysisSection");
        const section = document.getElementById("cleanedAnalysisSection");


        const analysis =
            result.analysis || {};


        setText(
            "cleanedRows",
            getValue(
                analysis,
                [
                    "total_rows",
                    "rows",
                    "row_count"
                ]
            )
        );


        setText(
            "cleanedColumns",
            getValue(
                analysis,
                [
                    "total_columns",
                    "columns",
                    "column_count"
                ]
            )
        );


        setText(
            "cleanedMissing",
            getValue(
                analysis,
                [
                    "missing_values",
                    "missing",
                    "total_missing"
                ]
            )
        );


        setText(
            "cleanedDuplicates",
            getValue(
                analysis,
                [
                    "duplicate_rows",
                    "duplicates",
                    "total_duplicates"
                ]
            )
        );


        setText(
            "remainingMissing",
            getValue(
                analysis,
                [
                    "missing_values",
                    "missing",
                    "total_missing"
                ],
                0
            )
        );


        const summary =
            getValue(
                analysis,
                [
                    "ai_insight",
                    "insight",
                    "message"
                ]
            );


        if (summary) {

            setText(
                "cleaningSummary",
                summary
            );

        } else {

            setText(
                "cleaningSummary",
                "AI cleaning completed successfully."
            );

        }


        section.scrollIntoView({
            behavior: "smooth"
        });


    } catch (error) {

        console.error(
            "CLEANED ANALYSIS ERROR:",
            error
        );


        showStatus(
            "cleaningStatus",
            "Cleaned analysis failed: " +
            error.message,
            "error"
        );

    }

}


/* =========================================================
   AI CUSTOMER SEGMENTATION
========================================================= */

async function startSegmentation() {

    console.log(
        "Starting AI customer segmentation..."
    );


    const button =
        document.getElementById(
            "segmentationButton"
        );


    if (button) {

        button.disabled = true;

        button.textContent =
            "Running AI Segmentation...";

    }


    try {

        const response =
            await fetch(
                "/segment",
                {
                    method: "POST"
                }
            );


        const result =
            await response.json();


        console.log(
            "Segmentation response:",
            result
        );


        if (
            !response.ok ||
            !result.success
        ) {

            throw new Error(
                result.error ||
                "Segmentation failed."
            );

        }


        /* -------------------------------------------------
           SHOW SEGMENTATION SECTION
        ------------------------------------------------- */

        showWorkflowSections(
            ["segmentationSection", "businessAnalyticsSection"],
            "segmentationSection"
        );
        const section = document.getElementById("segmentationSection");


        const segmentation =
            result.segmentation || {};


        console.log(
            "Segmentation data:",
            segmentation
        );


        /* -------------------------------------------------
           TOTAL SEGMENTS
        ------------------------------------------------- */

        setText(
            "segmentCount",
            getValue(
                segmentation,
                [
                    "segment_count",
                    "number_of_segments",
                    "n_clusters",
                    "clusters"
                ],
                0
            )
        );


        /* -------------------------------------------------
           CUSTOMERS
        ------------------------------------------------- */

        setText(
            "segmentedCustomers",
            getValue(
                segmentation,
                [
                    "customer_count",
                    "customers_analyzed",
                    "total_customers",
                    "total_rows"
                ],
                0
            )
        );


        /* -------------------------------------------------
           ALGORITHM
        ------------------------------------------------- */

        setText(
            "algorithmName",
            getValue(
                segmentation,
                [
                    "algorithm",
                    "algorithm_name",
                    "method"
                ],
                "K-Means"
            )
        );


        /* -------------------------------------------------
           FEATURES
        ------------------------------------------------- */

        const features =
            getArray(
                segmentation,
                [
                    "features",
                    "features_used",
                    "segmentation_features"
                ]
            );


        fillFeatureTags(
            "segmentationFeatures",
            features
        );


        /* -------------------------------------------------
           SEGMENT TABLE
        ------------------------------------------------- */

        buildSegmentTable(
            segmentation
        );

        /* -------------------------------------------------
           LOAD SHOP OWNER BUSINESS INSIGHTS
        ------------------------------------------------- */

        await loadBusinessAnalytics();


        /* -------------------------------------------------
           SCROLL TO SEGMENTATION
        ------------------------------------------------- */

        if (section) {

            section.scrollIntoView({
                behavior: "smooth"
            });

        }


    } catch (error) {

        console.error(
            "SEGMENTATION ERROR:",
            error
        );


        alert(
            "Segmentation failed: " +
            error.message
        );


    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "Continue to AI Customer Segmentation →";

        }

    }

}


/* =========================================================
   SHOP OWNER BUSINESS ANALYTICS
========================================================= */

async function loadBusinessAnalytics() {

    console.log("Loading shop owner business analytics...");

    try {

        const response = await fetch("/business-analytics");

        const result = await response.json();

        console.log("Business analytics response:", result);

        if (!response.ok || !result.success) {

            throw new Error(
                result.error ||
                "Business analytics failed."
            );

        }

        const data =
            result.business_analytics || {};

        const section = document.getElementById("businessAnalyticsSection");
        // Visibility is controlled by the workflow stage, not by data loading.

        setText(
            "businessTotalCustomers",
            data.total_customers ?? 0
        );

        setText(
            "regularCustomers",
            data.regular_customers ?? "N/A"
        );

        setText(
            "firstTimeCustomers",
            data.first_time_customers ?? "N/A"
        );

        setText(
            "businessTotalSales",
            formatBusinessNumber(data.total_sales)
        );

        setText(
            "businessAOV",
            formatBusinessNumber(data.average_order_value)
        );

        setText(
            "repeatPurchaseRate",
            data.repeat_purchase_rate !== null &&
            data.repeat_purchase_rate !== undefined
                ? data.repeat_purchase_rate + "%"
                : "N/A"
        );

        buildCustomerTypeSummary(data);
        renderGenderAndChannelAnalytics(data);

        buildTopProducts(data.top_products || []);

        buildProductPreferenceTable(
            data.product_by_customer_type || []
        );

        buildBusinessInsight(data);

    } catch (error) {

        console.error(
            "BUSINESS ANALYTICS ERROR:",
            error
        );

        setText(
            "businessInsight",
            "Business analytics could not be generated: " +
            error.message
        );

    }

}


/* =========================================================
   FORMAT BUSINESS NUMBER
========================================================= */

function formatBusinessNumber(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "N/A";
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
        return String(value);
    }

    return number.toLocaleString(
        "en-IN",
        {
            maximumFractionDigits: 2
        }
    );

}


/* =========================================================
   CUSTOMER TYPE SUMMARY
========================================================= */

function buildCustomerTypeSummary(data) {

    const container =
        document.getElementById(
            "customerTypeSummary"
        );

    if (!container) {
        return;
    }

    const regular =
        data.regular_customers;

    const firstTime =
        data.first_time_customers;

    if (
        regular === null ||
        regular === undefined ||
        firstTime === null ||
        firstTime === undefined
    ) {

        container.innerHTML =
            "<p>Purchase information is not available in this dataset.</p>";

        return;
    }

    const total =
        Number(regular) +
        Number(firstTime);

    const regularPercent =
        total > 0
            ? ((Number(regular) / total) * 100).toFixed(1)
            : 0;

    const firstTimePercent =
        total > 0
            ? ((Number(firstTime) / total) * 100).toFixed(1)
            : 0;

    container.innerHTML = `
        <div class="business-stat">
            <strong>Regular Customers</strong>
            <span>${formatBusinessNumber(regular)}
            (${regularPercent}%)</span>
        </div>

        <div class="business-stat">
            <strong>First-Time Customers</strong>
            <span>${formatBusinessNumber(firstTime)}
            (${firstTimePercent}%)</span>
        </div>
    `;

}


/* =========================================================
   TOP PRODUCTS
========================================================= */

function buildTopProducts(products) {

    const container =
        document.getElementById(
            "topProducts"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!products.length) {

        container.innerHTML =
            "<p>Product information is not available in this dataset.</p>";

        return;
    }

    const maxPurchases =
        Math.max(
            ...products.map(
                product =>
                    Number(product.purchases || 0)
            ),
            1
        );

    products.forEach(
        product => {

            const purchases =
                Number(
                    product.purchases || 0
                );

            const percentage =
                Math.max(
                    4,
                    (purchases / maxPurchases) * 100
                );

            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "business-bar-item";

            item.innerHTML = `
                <div class="business-bar-label">
                    <span>${escapeHTML(product.product)}</span>
                    <strong>${formatBusinessNumber(purchases)}</strong>
                </div>

                <div class="business-bar-track">
                    <div
                        class="business-bar-fill"
                        style="width:${percentage}%">
                    </div>
                </div>
            `;

            container.appendChild(item);

        }
    );

}


/* =========================================================
   PRODUCT PREFERENCE TABLE
========================================================= */

function buildProductPreferenceTable(rows) {

    const table =
        document.getElementById(
            "productPreferenceTable"
        );

    if (!table) {
        return;
    }

    table.innerHTML = "";

    if (!rows.length) {

        table.innerHTML = `
            <tr>
                <td colspan="3">
                    Product preference information is not available.
                </td>
            </tr>
        `;

        return;
    }

    rows.forEach(
        item => {

            const row =
                document.createElement(
                    "tr"
                );

            row.innerHTML = `
                <td>${escapeHTML(item.customer_type)}</td>
                <td>${escapeHTML(item.product)}</td>
                <td>${escapeHTML(
                    formatBusinessNumber(item.purchases)
                )}</td>
            `;

            table.appendChild(row);

        }
    );

}


/* =========================================================
   BUSINESS INSIGHT
========================================================= */

function buildBusinessInsight(data) {

    const element =
        document.getElementById(
            "businessInsight"
        );

    if (!element) {
        return;
    }

    const messages = [];

    if (
        data.regular_customers !== null &&
        data.regular_customers !== undefined
    ) {

        messages.push(
            `${formatBusinessNumber(data.regular_customers)} regular customers and ` +
            `${formatBusinessNumber(data.first_time_customers)} first-time customers ` +
            `were identified.`
        );

    }

    if (
        data.top_products &&
        data.top_products.length
    ) {

        messages.push(
            `${data.top_products[0].product} is the top-selling product/category ` +
            `based on recorded purchase volume.`
        );

    }

    if (
        data.repeat_purchase_rate !== null &&
        data.repeat_purchase_rate !== undefined
    ) {

        messages.push(
            `The repeat purchase rate is ${data.repeat_purchase_rate}%.`
        );

    }

    if (!messages.length) {

        element.textContent =
            "Upload a customer/sales dataset containing purchase and product information to generate shop-owner insights.";

    } else {

        element.textContent =
            messages.join(" ");

    }

}


/* =========================================================
   POWER BI DASHBOARD
========================================================= */

function preparePowerBI() {

    console.log(
        "Opening Power BI dashboard..."
    );


    const section =
        document.getElementById(
            "powerbiSection"
        );


    if (!section) {

        console.error(
            "powerbiSection not found in HTML"
        );

        return;
    }


    showWorkflowSections("powerbiSection", "powerbiSection");

}


/* =========================================================
   SET TEXT
========================================================= */

function setText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) {
        return;
    }


    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {

        element.textContent = "0";

    } else {

        element.textContent = value;

    }

}


/* =========================================================
   GET VALUE
========================================================= */

function getValue(
    object,
    keys,
    defaultValue = 0
) {

    if (!object) {
        return defaultValue;
    }


    for (const key of keys) {

        if (
            object[key] !== undefined &&
            object[key] !== null
        ) {

            return object[key];

        }

    }


    return defaultValue;

}


/* =========================================================
   GET ARRAY
========================================================= */

function getArray(
    object,
    keys
) {

    if (!object) {
        return [];
    }


    for (const key of keys) {

        if (Array.isArray(object[key])) {

            return object[key];

        }

    }


    return [];

}


/* =========================================================
   FILL LIST
========================================================= */

function fillList(
    elementId,
    items
) {

    const list =
        document.getElementById(
            elementId
        );


    if (!list) {
        return;
    }


    list.innerHTML = "";


    items.forEach(
        item => {

            const li =
                document.createElement(
                    "li"
                );


            li.textContent =
                String(item);


            list.appendChild(li);

        }
    );

}


/* =========================================================
   FEATURE TAGS
========================================================= */

function fillFeatureTags(
    elementId,
    features
) {

    const container =
        document.getElementById(
            elementId
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    features.forEach(
        feature => {

            const tag =
                document.createElement(
                    "span"
                );


            tag.className =
                "feature-tag";


            tag.textContent =
                String(feature);


            container.appendChild(tag);

        }
    );

}


/* =========================================================
   COLUMN TABLE
========================================================= */

function buildColumnTable(
    analysis
) {

    const table =
        document.getElementById(
            "columnTable"
        );


    if (!table) {
        return;
    }


    table.innerHTML = "";


    const columns =
        analysis.columns ||
        analysis.column_details ||
        [];


    if (!Array.isArray(columns)) {
        return;
    }


    columns.forEach(
        column => {

            const row =
                document.createElement(
                    "tr"
                );


            const name =
                column.name ||
                column.column ||
                "";


            const type =
                column.data_type ||
                column.dtype ||
                column.type ||
                "";


            const missing =
                column.missing ??
                column.missing_values ??
                0;


            const unique =
                column.unique ??
                column.unique_values ??
                0;


            row.innerHTML = `
                <td>${escapeHTML(name)}</td>
                <td>${escapeHTML(type)}</td>
                <td>${escapeHTML(missing)}</td>
                <td>${escapeHTML(unique)}</td>
            `;


            table.appendChild(row);

        }
    );

}


/* =========================================================
   SEGMENT TABLE
   IMPORTANT:
   Python uses "customer_count"
========================================================= */

function buildSegmentTable(
    segmentation
) {

    const table =
        document.getElementById(
            "segmentTable"
        );


    if (!table) {
        console.error("segmentTable not found");
        return;
    }


    table.innerHTML = "";


    /*
       Your Python code creates:

       segmentation.segment_profiles = [

           {
               "segment": 1,
               "customer_count": 50,
               "avg_Age": 30.5,
               "avg_Annual Income (k$)": 55.4,
               "avg_Spending Score (1-100)": 70.2
           }

       ]
    */


    const profiles =
        segmentation.segment_profiles ||
        segmentation.profiles ||
        segmentation.segments ||
        [];


    console.log(
        "Segment profiles received:",
        profiles
    );


    if (!Array.isArray(profiles)) {

        console.error(
            "Segment profiles is not an array:",
            profiles
        );

        return;
    }


    /* -----------------------------------------------------
       CREATE EACH SEGMENT ROW
    ----------------------------------------------------- */

    profiles.forEach(
        profile => {

            if (
                !profile ||
                typeof profile !== "object"
            ) {
                return;
            }


            /* ---------------------------------------------
               SEGMENT NUMBER
            --------------------------------------------- */

            const segment =
                profile.segment ??
                profile.cluster ??
                profile.id ??
                "";


            /* ---------------------------------------------
               CUSTOMER COUNT

               IMPORTANT:
               Python uses customer_count
            --------------------------------------------- */

            const customers =
                profile.customer_count ??
                profile.customers ??
                profile.customerCount ??
                profile.count ??
                0;


            /* ---------------------------------------------
               CREATE PROFILE DESCRIPTION
            --------------------------------------------- */

            let description = "";


            if (profile.profile) {

                description =
                    profile.profile;

            } else {

                const details = [];


                Object.keys(profile).forEach(
                    key => {

                        if (
                            key.startsWith("avg_") &&
                            profile[key] !== null &&
                            profile[key] !== undefined
                        ) {

                            let featureName =
                                key.substring(4);


                            featureName =
                                featureName.replace(
                                    /_/g,
                                    " "
                                );


                            details.push(
                                "Avg " +
                                featureName +
                                ": " +
                                profile[key]
                            );

                        }

                    }
                );


                if (details.length > 0) {

                    description =
                        details.join(" | ");

                } else {

                    description =
                        "Customer segment";

                }

            }


            /* ---------------------------------------------
               ADD ROW
            --------------------------------------------- */

            addSegmentRow(
                table,
                segment,
                customers,
                description
            );

        }
    );


    console.log(
        "Segment table created successfully."
    );

}


/* =========================================================
   ADD SEGMENT ROW
========================================================= */

function addSegmentRow(
    table,
    segment,
    customers,
    profile
) {

    const row =
        document.createElement(
            "tr"
        );


    row.innerHTML = `
        <td>${escapeHTML(
            segment ?? ""
        )}</td>

        <td>${escapeHTML(
            customers ?? 0
        )}</td>

        <td>${escapeHTML(
            profile ?? "Customer segment"
        )}</td>
    `;


    table.appendChild(row);

}


/* =========================================================
   ESCAPE HTML
========================================================= */

function escapeHTML(value) {

    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}

/* =========================================================
   GENDER + ONLINE/OFFLINE ANALYTICS
========================================================= */
function renderGenderAndChannelAnalytics(data) {
    const section = document.getElementById("businessAnalyticsSection");
    if (!section) return;
    let host = document.getElementById("channelAnalytics");
    if (!host) {
        host = document.createElement("div");
        host.id = "channelAnalytics";
        const kpis = section.querySelector(".kpi-grid");
        if (kpis && kpis.parentNode) kpis.insertAdjacentElement("afterend", host);
        else section.appendChild(host);
    }
    const fmt = value => formatBusinessNumber(value ?? 0);
    const panel = (title, d, note) => {
        if (!d) return `<div class="dashboard-card"><h3>${title}</h3><p>No rows were identified for this channel.</p></div>`;
        return `<div class="dashboard-card channel-panel"><h3>${title}</h3>
          <p class="channel-note">${note || "Metrics calculated from rows assigned to this channel."}</p>
          <div class="channel-kpis">
            <div><span>Total customers</span><strong>${fmt(d.total_customers)}</strong></div>
            <div><span>Regular customers</span><strong>${fmt(d.regular_customers)}</strong></div>
            <div><span>First-time customers</span><strong>${fmt(d.first_time_customers)}</strong></div>
            <div><span>Male customers</span><strong>${fmt(d.male_customers)}</strong></div>
            <div><span>Female customers</span><strong>${fmt(d.female_customers)}</strong></div>
            <div><span>Delivered / received</span><strong>${fmt(d.delivered_orders)}</strong></div>
            <div><span>Cancelled</span><strong>${fmt(d.cancelled_orders)}</strong></div>
            <div><span>Pending</span><strong>${fmt(d.pending_orders)}</strong></div>
            <div><span>Processing / shipped</span><strong>${fmt(d.processing_orders)}</strong></div>
          </div>
          <p><strong>Top products:</strong> ${(d.top_products || []).slice(0,3).map(x => `${escapeHTML(x.product)} (${fmt(x.purchases)})`).join(", ") || "Not available"}</p>
        </div>`;
    };
    const genderProducts = (data.product_by_gender || []).length ? `<div class="dashboard-card gender-panel"><h3>Product Preferences by Gender</h3><div class="channel-kpis">${(data.product_by_gender || []).map(item => `<div><span>${escapeHTML(item.gender)} · ${escapeHTML(item.product)}</span><strong>${fmt(item.purchases)} units</strong></div>`).join("")}</div></div>` : "";
    const gender = `<div class="dashboard-card gender-panel"><h3>Gender Summary</h3>
      <div class="channel-kpis">
        <div><span>Male customers</span><strong>${fmt(data.male_customers)}</strong></div>
        <div><span>Female customers</span><strong>${fmt(data.female_customers)}</strong></div>
      </div>
      <p>Gender totals count distinct customers when a customer ID is available.</p></div>`;
    let channels = "";
    if (data.channel_mode === "mixed") {
        channels = `<h3 class="channel-heading">Offline Analytics</h3>${panel("Offline / In-store", data.offline_analytics, "Offline, shop and in-store records only.")}
                    <h3 class="channel-heading">Online Analytics</h3>${panel("Online Store", data.online_analytics, "Online, web and app records only.")}`;
    } else if (data.channel_mode === "offline") {
        channels = `<h3 class="channel-heading">Offline Analytics</h3>${panel("Offline / In-store", data.offline_analytics, "Offline, shop and in-store records only.")}`;
    } else if (data.channel_mode === "online") {
        channels = `<h3 class="channel-heading">Online Analytics</h3>${panel("Online Store", data.online_analytics, "Online, web and app records only.")}`;
    } else {
        channels = `<p class="channel-note">Channel-specific analytics need a recognized Sales Channel / Channel column with Online or Offline values.</p>`;
    }
    const det = data.channel_detection || {};
    const unclassified = Number(det.unclassified_rows || 0);
    const note = (data.channel_mode === "mixed" && unclassified) ? `<p class="channel-note">${unclassified} row(s) had missing or unrecognized channel values and are excluded from channel-specific metrics.</p>` : "";
    host.innerHTML = gender + genderProducts + channels + note;
}
