"""Robust business analytics for customer and transaction datasets."""
import os
import re
import pandas as pd


def _norm(value):
    return re.sub(r'[^a-z0-9]', '', str(value).strip().lower())


def _find_column(df, candidates):
    normalized = {_norm(c): c for c in df.columns}
    for candidate in candidates:
        if _norm(candidate) in normalized:
            return normalized[_norm(candidate)]
    return None


def _read_dataset(input_file):
    ext = os.path.splitext(input_file)[1].lower()
    if ext == '.csv':
        return pd.read_csv(input_file)
    if ext in ('.xlsx', '.xls', '.xlsm', '.ods'):
        return pd.read_excel(input_file)
    if ext in ('.tsv', '.txt'):
        return pd.read_csv(input_file, sep='\t')
    if ext in ('.json', '.jsonl', '.ndjson'):
        try:
            return pd.read_json(input_file, lines=ext in ('.jsonl', '.ndjson'))
        except ValueError:
            return pd.read_json(input_file)
    raise ValueError('Unsupported file format. Use CSV, Excel, TSV/TXT or JSON.')


def _coalesce_alias_columns(df):
    """Merge equivalent columns from files that use inconsistent headers by row."""
    groups = {
        'customer_id': ['customer_id','customer id','cust_id','custid','client_id','client id','customer'],
        'gender': ['gender','sex','customer_gender','customer gender'],
        'product': ['product','product_name','product name','product_category','product category','item','item_name','item name','category'],
        'order_id': ['order_id','order id','invoice_no','invoice number','transaction_id','transaction id','invoice'],
        'order_status': ['order_status','order status','status','delivery_status','delivery status'],
        'sales_channel': ['sales_channel','sales channel','channel','purchase_channel','purchase channel','order_channel','order channel'],
        'total_amount': ['total_amount','total amount','total_spending','total spending','total_sales','total sales','revenue','sales','amount_spent','amount spent','amount'],
        'quantity': ['quantity','qty','units','units_sold'],
        'total_purchases': ['total_purchases','total purchases','purchase_frequency','purchase frequency','orders_count','order_count','total_orders'],
        'aov': ['average_order_value','average order value','aov','order_value'],
        'purchase_date': ['last_purchase_date','last purchase date','purchase_date','purchase date','order_date','order date','transaction_date'],
        'discount': ['discount_usage','discount usage','discount','discount_amount']
    }
    for canonical, aliases in groups.items():
        matches = []
        alias_keys = {_norm(a) for a in aliases}
        for column in list(df.columns):
            if _norm(column) in alias_keys:
                matches.append(column)
        if not matches:
            continue
        combined = df[matches[0]].copy()
        for column in matches[1:]:
            combined = combined.combine_first(df[column])
        df[canonical] = combined
    return df


def _customer_metrics(frame, cols):
    """Return customer-level metrics. Transactions are counted by distinct orders when available."""
    customer_col, purchase_count_col, order_col = cols['customer'], cols['purchase_count'], cols['order']
    if customer_col:
        valid = frame[customer_col].notna() & frame[customer_col].astype(str).str.strip().ne('')
        work = frame.loc[valid].copy()
        if work.empty:
            return 0, None, None, None
        if purchase_count_col:
            counts = pd.to_numeric(work[purchase_count_col], errors='coerce').fillna(0).groupby(work[customer_col]).sum()
        elif order_col:
            counts = work.groupby(work[customer_col])[order_col].nunique(dropna=True)
            # If order IDs are blank, fall back to transaction rows for that customer.
            counts = counts.where(counts > 0, work.groupby(work[customer_col]).size())
        else:
            counts = work.groupby(work[customer_col]).size()
    else:
        work = frame
        if purchase_count_col:
            counts = pd.to_numeric(work[purchase_count_col], errors='coerce').fillna(0)
        elif order_col:
            counts = pd.Series([max(1, work[order_col].nunique())])
        else:
            counts = pd.Series([len(work)]) if len(work) else pd.Series(dtype=float)
    total = int(len(counts))
    if not total:
        return 0, None, None, None
    first = int((counts <= 1).sum())
    regular = int((counts > 1).sum())
    rate = round(regular / total * 100, 2)
    return total, regular, first, rate


def _channel_kind(value):
    if pd.isna(value):
        return None
    v = _norm(value)
    if any(x in v for x in ('online', 'ecommerce', 'web', 'website', 'internet', 'mobileapp', 'apporder')):
        return 'online'
    if any(x in v for x in ('offline', 'instore', 'instorepurchase', 'shop', 'physicalstore', 'retailstore', 'walkin', 'store')):
        return 'offline'
    return None


def _analytics_for_frame(df, cols, include_channel=False):
    total_customers, regular, first, rate = _customer_metrics(df, cols)
    gender_col, product_col = cols['gender'], cols['product']
    spending_col, aov_col = cols['spending'], cols['aov']
    order_col, status_col = cols['order'], cols['status']
    result = {
        'available': True, 'total_customers': total_customers,
        'regular_customers': regular, 'first_time_customers': first,
        'repeat_purchase_rate': rate, 'total_sales': None,
        'average_order_value': None, 'male_customers': 0, 'female_customers': 0,
        'gender_counts': {}, 'top_products': [], 'product_by_gender': [],
        'delivered_orders': 0, 'cancelled_orders': 0,
        'pending_orders': 0, 'processing_orders': 0,
        'data_columns_used': {k: v for k, v in cols.items()}, 'notes': []
    }
    if gender_col:
        genders = df[gender_col].fillna('').astype(str).str.strip().str.lower()
        male_mask = genders.isin(['m', 'male', 'man', 'men', 'boy'])
        female_mask = genders.isin(['f', 'female', 'woman', 'women', 'girl'])
        if cols['customer']:
            customer_gender = pd.DataFrame({'customer': df[cols['customer']], 'gender': genders})
            customer_gender = customer_gender[customer_gender['customer'].notna()].drop_duplicates('customer', keep='last')
            g = customer_gender['gender']
            result['male_customers'] = int(g.isin(['m','male','man','men','boy']).sum())
            result['female_customers'] = int(g.isin(['f','female','woman','women','girl']).sum())
            result['gender_counts'] = {str(k): int(v) for k, v in g.value_counts().items() if k}
        else:
            result['male_customers'] = int(male_mask.sum())
            result['female_customers'] = int(female_mask.sum())
            result['gender_counts'] = {str(k): int(v) for k, v in genders[genders.ne('')].value_counts().items()}
    else:
        result['notes'].append('Gender counts unavailable: no recognized gender/sex column was found.')

    if spending_col:
        result['total_sales'] = round(float(pd.to_numeric(df[spending_col], errors='coerce').fillna(0).sum()), 2)
    if aov_col:
        values = pd.to_numeric(df[aov_col], errors='coerce').dropna()
        if len(values): result['average_order_value'] = round(float(values.mean()), 2)
    elif spending_col:
        values = pd.to_numeric(df[spending_col], errors='coerce').dropna()
        denominator = df[order_col].nunique() if order_col else len(values)
        if denominator: result['average_order_value'] = round(float(values.sum()) / denominator, 2)

    if product_col:
        tmp = pd.DataFrame({'product': df[product_col].fillna('Unknown').astype(str).str.strip()})
        tmp['product'] = tmp['product'].replace('', 'Unknown')
        tmp['quantity'] = pd.to_numeric(df[cols['quantity']], errors='coerce').fillna(1) if cols['quantity'] else 1
        tmp['sales'] = pd.to_numeric(df[spending_col], errors='coerce').fillna(0) if spending_col else 0
        top = tmp.groupby('product', as_index=False).agg(purchases=('quantity','sum'), sales=('sales','sum')).sort_values(['purchases','sales'], ascending=False).head(5)
        result['top_products'] = [{'product': r['product'], 'purchases': int(round(r['purchases'])), 'sales': round(float(r['sales']),2)} for _,r in top.iterrows()]
        if gender_col:
            pg = pd.DataFrame({'product': df[product_col].fillna('Unknown').astype(str), 'gender': df[gender_col].fillna('Unknown').astype(str).str.strip().str.title(), 'quantity': pd.to_numeric(df[cols['quantity']], errors='coerce').fillna(1) if cols['quantity'] else 1})
            pg = pg[pg['gender'].str.lower().isin(['male','female','m','f','man','woman'])]
            if len(pg):
                pg['gender'] = pg['gender'].replace({'M':'Male','F':'Female','Man':'Male','Woman':'Female'})
                grouped = pg.groupby(['gender','product'], as_index=False)['quantity'].sum().sort_values(['gender','quantity'], ascending=[True,False])
                result['product_by_gender'] = [{'gender': r['gender'], 'product': r['product'], 'purchases': int(round(r['quantity']))} for _,r in grouped.groupby('gender', sort=True).head(5).iterrows()]
    else:
        result['notes'].append('Product analysis unavailable: no recognized product column was found.')

    if status_col:
        status = df[status_col].fillna('').astype(str).str.strip().str.lower()
        result['delivered_orders'] = int(status.str.contains(r'deliver|received|complete|fulfilled', regex=True).sum())
        result['cancelled_orders'] = int(status.str.contains('cancel', regex=False).sum())
        result['pending_orders'] = int(status.str.contains(r'pending|await', regex=True).sum())
        result['processing_orders'] = int(status.str.contains(r'processing|shipped|dispatch', regex=True).sum())
    return result


def build_business_analytics(input_file):
    """Build customer, product, gender and channel analytics from CSV/Excel sales data."""
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Dataset not found: {input_file}")

    ext = os.path.splitext(input_file)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(input_file)
    elif ext in [".xlsx", ".xls", ".xlsm", ".ods"]:
        df = pd.read_excel(input_file)
    else:
        raise ValueError("Only CSV and Excel files are supported.")

    df = df.dropna(how="all").copy()
    if df.empty:
        raise ValueError("The dataset is empty.")

    customer_col = _find_column(df, [
        "Customer ID", "CustomerID", "Customer_Id", "Cust_ID", "Cust ID",
        "ClientID", "Client ID", "User ID", "UserID"
    ])
    gender_col = _find_column(df, ["Gender", "Sex", "Customer Gender", "Customer Sex"])
    channel_col = _find_column(df, ["Sales Channel", "Channel", "Purchase Channel", "Order Channel", "Platform"])
    product_col = _find_column(df, ["Product", "Product Name", "ProductName", "Product Category", "ProductCategory", "Item", "Item Name", "ItemName"])
    order_col = _find_column(df, ["Order ID", "OrderID", "Invoice No", "Invoice Number", "Transaction ID", "TransactionID", "Bill No"])
    quantity_col = _find_column(df, ["Quantity", "Qty", "Units", "Items Purchased"])
    spending_col = _find_column(df, ["Total Amount", "Total_Amount", "TotalAmount", "Total Sales", "TotalSales", "Revenue", "Sales", "Amount Spent", "AmountSpent", "Order Value"])
    aov_col = _find_column(df, ["Average Order Value", "AverageOrderValue", "AOV", "Average Purchase Value"])
    purchase_count_col = _find_column(df, ["Total Purchases", "TotalPurchases", "Purchase Frequency", "PurchaseFrequency", "Order Count", "OrderCount", "Orders"])
    date_col = _find_column(df, ["Last Purchase Date", "LastPurchaseDate", "Purchase Date", "PurchaseDate", "Order Date", "Order_Date", "OrderDate", "Transaction Date"])
    status_col = _find_column(df, ["Order Status", "Order_Status", "OrderStatus", "Status", "Delivery Status"])
    last_days_col = _find_column(df, ["Last Purchase Days", "Days Since Last Purchase", "LastPurchaseDays", "DaysSinceLastPurchase"])

    def clean_text(series):
        return series.fillna("").astype(str).str.strip()

    # Give rows with missing customer IDs a unique internal key so they do not merge.
    if customer_col:
        customer_keys = clean_text(df[customer_col])
        customer_keys = pd.Series(
            [value if value else f"__missing_customer_row_{i}" for i, value in enumerate(customer_keys)],
            index=df.index,
        )
    else:
        customer_keys = pd.Series([f"__row_{i}" for i in range(len(df))], index=df.index)

    order_counts = pd.Series(1, index=df.index, dtype="int64")
    if purchase_count_col:
        explicit_counts = pd.to_numeric(df[purchase_count_col], errors="coerce").fillna(0).clip(lower=0)
        order_counts = explicit_counts.astype(float)
    elif order_col:
        orders = clean_text(df[order_col])
        # Rows with a blank order number still count as a transaction.
        order_counts = pd.Series(
            [1 if not value else value for value in orders], index=df.index
        ).groupby(customer_keys).transform(lambda values: values.nunique()).astype(float)
        # For per-row metrics, use one unit per transaction; customer totals below use unique orders.
        order_counts = pd.Series(1, index=df.index, dtype="int64")

    def per_customer_orders(frame, keys):
        if frame.empty:
            return pd.Series(dtype=float)
        if purchase_count_col:
            counts = pd.to_numeric(frame[purchase_count_col], errors="coerce").fillna(0).clip(lower=0)
            return pd.DataFrame({"key": keys.loc[frame.index], "count": counts}).groupby("key")["count"].sum()
        if order_col:
            tmp = pd.DataFrame({"key": keys.loc[frame.index], "order": clean_text(frame[order_col])}, index=frame.index)
            tmp["order"] = [v if v else f"__blank_order_{i}" for i, v in enumerate(tmp["order"])]
            return tmp.groupby("key")["order"].nunique().astype(float)
        return keys.loc[frame.index].value_counts().astype(float)

    def customer_gender_counts(frame, keys):
        if not gender_col:
            return {"male_customers": 0, "female_customers": 0}
        temp = pd.DataFrame({"key": keys.loc[frame.index], "gender": clean_text(frame[gender_col]).str.lower()}, index=frame.index)
        temp = temp[temp["gender"].ne("")]
        if temp.empty:
            return {"male_customers": 0, "female_customers": 0}
        # One gender per customer: use the most frequent non-empty value for that customer.
        customer_gender = temp.groupby("key")["gender"].agg(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0])
        male_values = {"male", "m", "man", "boy"}
        female_values = {"female", "f", "woman", "girl"}
        return {
            "male_customers": int(customer_gender.isin(male_values).sum()),
            "female_customers": int(customer_gender.isin(female_values).sum()),
        }

    def product_rows(frame):
        if not product_col or frame.empty:
            return []
        products = clean_text(frame[product_col]).replace("", "Unknown")
        if quantity_col:
            quantity = pd.to_numeric(frame[quantity_col], errors="coerce").fillna(0).clip(lower=0)
        else:
            quantity = pd.Series(1, index=frame.index, dtype=float)
        sales = pd.to_numeric(frame[spending_col], errors="coerce").fillna(0) if spending_col else pd.Series(0, index=frame.index, dtype=float)
        temp = pd.DataFrame({"product": products, "purchases": quantity, "sales": sales})
        grouped = temp.groupby("product", as_index=False).agg(purchases=("purchases", "sum"), sales=("sales", "sum"))
        grouped = grouped.sort_values(["purchases", "sales"], ascending=False).head(5)
        return [{"product": str(row.product), "purchases": int(round(row.purchases)), "sales": round(float(row.sales), 2)} for row in grouped.itertuples(index=False)]

    def channel_label(value):
        value = str(value or "").strip().lower().replace("_", "-")
        if value in {"online", "ecommerce", "e-commerce", "web", "website", "app", "mobile", "online store", "digital"}:
            return "online"
        if value in {"offline", "in-store", "instore", "in store", "shop", "store", "retail", "physical", "walk-in", "walk in"}:
            return "offline"
        return "unclassified"

    def channel_metrics(frame):
        keys = customer_keys.loc[frame.index]
        purchase_totals = per_customer_orders(frame, customer_keys)
        regular_count = int((purchase_totals > 1).sum())
        first_count = int((purchase_totals <= 1).sum())
        genders = customer_gender_counts(frame, customer_keys)
        statuses = clean_text(frame[status_col]).str.lower() if status_col else pd.Series("", index=frame.index)
        if order_col:
            order_ids = clean_text(frame[order_col])
            status_frame = pd.DataFrame({"order": order_ids, "status": statuses}, index=frame.index)
            status_frame["order"] = [v if v else f"__row_{i}" for i, v in enumerate(status_frame["order"])]
            status_frame = status_frame.drop_duplicates("order", keep="last")
            statuses = status_frame["status"]
        delivered = int(statuses.str.contains(r"deliver|received|complete|completed|success", regex=True).sum())
        cancelled = int(statuses.str.contains(r"cancel|refund", regex=True).sum())
        pending = int(statuses.str.contains(r"pending|await", regex=True).sum())
        processing = int(statuses.str.contains(r"process|ship|dispatch|packed", regex=True).sum())
        sales = pd.to_numeric(frame[spending_col], errors="coerce").fillna(0) if spending_col else pd.Series(dtype=float)
        if aov_col:
            aov = pd.to_numeric(frame[aov_col], errors="coerce").dropna()
            average_order_value = round(float(aov.mean()), 2) if len(aov) else None
        else:
            average_order_value = round(float(sales.mean()), 2) if len(sales) else None
        if gender_col and product_col and not frame.empty:
            temp = pd.DataFrame({"gender": clean_text(frame[gender_col]).str.title(), "product": clean_text(frame[product_col]).replace("", "Unknown")}, index=frame.index)
            temp = temp[temp["gender"].str.lower().isin(["male", "female", "m", "f", "man", "woman"])]
            if quantity_col:
                temp["purchases"] = pd.to_numeric(frame.loc[temp.index, quantity_col], errors="coerce").fillna(0).clip(lower=0)
            else:
                temp["purchases"] = 1
            pg = temp.groupby(["gender", "product"], as_index=False)["purchases"].sum().sort_values("purchases", ascending=False)
            by_gender = [{"gender": str(r.gender), "product": str(r.product), "purchases": int(round(r.purchases))} for r in pg.itertuples(index=False)]
        else:
            by_gender = []
        return {
            "total_customers": int(keys.nunique()),
            "regular_customers": regular_count,
            "first_time_customers": first_count,
            "repeat_purchase_rate": round((regular_count / max(1, int(keys.nunique()))) * 100, 2),
            "male_customers": genders["male_customers"],
            "female_customers": genders["female_customers"],
            "total_sales": round(float(sales.sum()), 2) if len(sales) else None,
            "average_order_value": average_order_value,
            "delivered_orders": delivered,
            "cancelled_orders": cancelled,
            "pending_orders": pending,
            "processing_orders": processing,
            "top_products": product_rows(frame),
            "product_by_gender": by_gender,
        }

    overall = channel_metrics(df)
    result = {
        "available": True,
        **overall,
        "product_by_customer_type": [],
        "data_columns_used": {
            "customer": customer_col, "gender": gender_col, "channel": channel_col,
            "product": product_col, "order": order_col, "quantity": quantity_col,
            "spending": spending_col, "purchase_count": purchase_count_col,
            "date": date_col, "status": status_col,
        },
        "notes": [],
        "channel_mode": "unknown",
        "offline_analytics": None,
        "online_analytics": None,
        "channel_detection": {"unclassified_rows": int(len(df))},
    }

    # Customer-type product preferences
    if product_col:
        counts = per_customer_orders(df, customer_keys)
        types = counts.map(lambda count: "Regular Customer" if count > 1 else "First-Time Customer")
        pref = pd.DataFrame({"key": customer_keys, "product": clean_text(df[product_col]).replace("", "Unknown")}, index=df.index)
        pref["customer_type"] = pref["key"].map(types).fillna("First-Time Customer")
        if quantity_col:
            pref["purchases"] = pd.to_numeric(df[quantity_col], errors="coerce").fillna(0).clip(lower=0)
        else:
            pref["purchases"] = 1
        grouped = pref.groupby(["customer_type", "product"], as_index=False)["purchases"].sum().sort_values("purchases", ascending=False)
        result["product_by_customer_type"] = [{"customer_type": str(r.customer_type), "product": str(r.product), "purchases": int(round(r.purchases))} for r in grouped.itertuples(index=False)]

    if channel_col:
        labels = clean_text(df[channel_col]).map(channel_label)
        offline = df.loc[labels == "offline"]
        online = df.loc[labels == "online"]
        unclassified = int((labels == "unclassified").sum())
        has_offline, has_online = not offline.empty, not online.empty
        if has_offline and has_online:
            result["channel_mode"] = "mixed"
        elif has_offline:
            result["channel_mode"] = "offline"
        elif has_online:
            result["channel_mode"] = "online"
        result["offline_analytics"] = channel_metrics(offline) if has_offline else None
        result["online_analytics"] = channel_metrics(online) if has_online else None
        result["channel_detection"] = {"offline_rows": int(len(offline)), "online_rows": int(len(online)), "unclassified_rows": unclassified}
    else:
        result["notes"].append("Channel-specific analytics require a Sales Channel or Channel column.")

    if not gender_col:
        result["notes"].append("Gender analytics require a Gender or Sex column.")
    if not customer_col:
        result["notes"].append("No customer ID column was found; each row is treated as a separate customer.")
    if not product_col:
        result["notes"].append("Best-selling product analysis requires a Product or Item column.")
    if date_col:
        result["date_available"] = bool(pd.to_datetime(df[date_col], errors="coerce").notna().any())
    else:
        result["date_available"] = False
    if last_days_col:
        days = pd.to_numeric(df[last_days_col], errors="coerce")
        result["inactive_customers"] = int(days.groupby(customer_keys).max().gt(90).sum())
    elif date_col:
        dates = pd.to_datetime(df[date_col], errors="coerce")
        last_dates = dates.groupby(customer_keys).max().dropna()
        if not last_dates.empty:
            cutoff = pd.Timestamp.today().normalize() - pd.Timedelta(days=90)
            result["inactive_customers"] = int((last_dates < cutoff).sum())
        else:
            result["inactive_customers"] = None
    else:
        result["inactive_customers"] = None
    return result
