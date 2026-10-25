AI CUSTOMER SEGMENTATION PLATFORM - RUN GUIDE

EASIEST WAY (Windows)
1. Extract this ZIP completely to a normal folder (do not run it inside the ZIP).
2. Install Python 3.10 or newer. During installation, enable "Add Python to PATH".
3. Double-click run_project.bat. First launch installs the packages and may take a few minutes.
4. When the server starts, open http://127.0.0.1:5000 in Chrome.
5. Upload a customer dataset and run analysis/cleaning/segmentation from the dashboard.
6. To stop the server, click the terminal window and press Ctrl+C.

MANUAL POWERShell METHOD
cd path\to\AI_Customer_Segmentation_Platform
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe backend\app.py

FIXES IN THIS VERSION
- Business analytics always reads the latest uploaded dataset rather than stale cleaned output.
- Regular/first-time customer counts derive from customer-level order counts when no explicit purchase-count column exists.
- Male/female counts are computed from gender/sex aliases and count distinct customers when a customer ID exists.
- Recognizes common channel names such as Online, Web, App, Offline, Shop and In-store.
- Mixed channel data shows Offline Analytics first, then Online Analytics; unclassified channel rows are disclosed.
- Adds order status counts, product sales summaries and gender-specific product preference data.
- Adds supported upload/read formats: CSV, Excel, TSV/TXT and JSON/JSONL.

NOTES
- The analytics use rules and the data in your uploaded file; they do not call an external generative AI service.
- A customer can be classified as regular only if the dataset contains multiple transaction/order rows, distinct order IDs, or a usable purchase-count field.
- Gender values other than Male/Female (or M/F) are not forced into either category.

LOGIN AND DATABASE
------------------
1. Start the app using run_project.bat.
2. Open http://127.0.0.1:5000. You will see the login page.
3. Choose Create account to register with your name, email, and a password of at least 8 characters.
4. After registering, you will be redirected to the dashboard.
5. Use My History to see dataset uploads, cleaning, and segmentation activity saved for your account.
6. Log out when finished.

SQLite database: data/app_database.sqlite3
User-specific upload and processing folders: data/users/<user_id>/
Passwords are stored as secure hashes. Do not delete the database if you want to retain user accounts and history.
