
# ✦ Segmind — AI-Driven Customer Segmentation Platform

Segmind is a modern SaaS platform designed to transform raw customer data into meaningful business insights. Upload CSV or Excel files, clean and process customer data, identify valuable customer segments, and visualize insights through interactive dashboards.

🚀 **Live Demo:** [Try Segmind](https://ai-driven-customer-segmentation-2arg.onrender.com/)

> **Note:** The application is hosted on Render's free tier. If the service has been inactive, the initial request may take approximately 30–50 seconds to start.

---

## 🎨 UI Preview

### 1. Landing Page

![Segmind Landing Page](./Images/Landing.png)

*A modern SaaS landing page featuring a clean layout, gradient accents, and CSS-powered dashboard previews.*

### 2. Sign In

![Segmind Login Page](./Images/Login.png)

*A clean authentication interface with responsive layouts, form validation, and error handling.*

### 3. Create Account

![Segmind Registration Page](./Images/Register.png)

*A multi-step registration experience featuring password strength validation and email OTP verification.*

---

## ✨ Features

### 🔐 Authentication and Security
- Secure authentication using JWT stored in HttpOnly cookies.
- CSRF protection for state-changing requests.
- Server-side session revocation.
- Password hashing using bcrypt.
- Email verification using six-digit OTPs.
- Forgot-password workflow with OTP verification and password reset.
- Backend validation for authentication and password management.

### 📊 Customer Segmentation
- Upload customer datasets in CSV or Excel format.
- Clean and preprocess customer data.
- Identify meaningful customer segments.
- Generate insights to support data-driven decisions.
- Visualize segmentation results through dashboards.

> **Note:** Customer segmentation and dashboard features should reflect the functionality currently implemented in the application.

### 🎨 User Interface
- Responsive design for desktop, tablet, and mobile.
- Modern styling with gradients, glassmorphism, and subtle animations.
- Interactive form validation and user feedback.
- Vanilla HTML, CSS, and JavaScript without external UI frameworks.

---

## 🛠️ Tech Stack

### Backend
- **Language:** Python 3
- **Framework:** Flask
- **Authentication:** Flask-JWT-Extended
- **ORM:** Flask-SQLAlchemy
- **Database Migrations:** Flask-Migrate
- **Database:** Neon PostgreSQL
- **Email Service:** Brevo API
- **Production Server:** Gunicorn
- **Containerization:** Docker

### Frontend
- HTML5
- CSS3
- Vanilla JavaScript (ES6+)
- Inter font
- Flask Templates and Static Files

### Deployment
- Render
- Neon PostgreSQL
- Docker

---

## 📁 Project Structure

```text
AI-Driven-Customer-Segmentation
|   README.md
|   
+---Backend
|   |   .env
|   |   .env.example
|   |   .gitignore
|   |   app.py
|   |   config.py
|   |   Dockerfile
|   |   execution.txt
|   |   extensions.py
|   |   init_db.py
|   |   postman_collection.json
|   |   requirements.txt
|   |   
|   +---common
|   |   |   decorators.py
|   |   |   exceptions.py
|   |   |   responses.py
|   |   |   utils.py
|   |   |   validators.py
|   |   |   __init__.py
|   |   |   
|   |   \---__pycache__
|   |           exceptions.cpython-314.pyc
|   |           responses.cpython-314.pyc
|   |           utils.cpython-314.pyc
|   |           validators.cpython-314.pyc
|   |           __init__.cpython-314.pyc
|   |           
|   +---Documentation
|   |       Phase 1 authentication.txt
|   |       Phase1_Authentication_Postman_Collection.json
|   |       
|   +---instance
|   +---migrations
|   |       alembic.ini
|   |       env.py
|   |       README
|   |       script.py.mako
|   |       
|   +---modules
|   |   +---auth
|   |   |   |   models.py
|   |   |   |   repository.py
|   |   |   |   routes.py
|   |   |   |   schemas.py
|   |   |   |   service.py
|   |   |   |   tokens.py
|   |   |   |   __init__.py
|   |   |   |   
|   |   |   \---__pycache__
|   |   |           models.cpython-314.pyc
|   |   |           repository.cpython-314.pyc
|   |   |           routes.cpython-314.pyc
|   |   |           schemas.cpython-314.pyc
|   |   |           service.cpython-314.pyc
|   |   |           tokens.cpython-314.pyc
|   |   |           __init__.cpython-314.pyc
|   |   |           
|   |   +---email
|   |   |   |   service.py
|   |   |   |   __init__.py
|   |   |   |   
|   |   |   +---templates
|   |   |   |       password_changed.html
|   |   |   |       password_reset.html
|   |   |   |       verification.html
|   |   |   |       
|   |   |   \---__pycache__
|   |   |           service.cpython-314.pyc
|   |   |           __init__.cpython-314.pyc
|   |   |           
|   |   \---users
|   |       |   models.py
|   |       |   repository.py
|   |       |   routes.py
|   |       |   schemas.py
|   |       |   service.py
|   |       |   __init__.py
|   |       |   
|   |       \---__pycache__
|   |               models.cpython-314.pyc
|   |               repository.cpython-314.pyc
|   |               routes.cpython-314.pyc
|   |               schemas.cpython-314.pyc
|   |               service.cpython-314.pyc
|   |               __init__.cpython-314.pyc
|   |               
|   +---routes
|   |   |   health_routes.py
|   |   |   pages.py
|   |   |   __init__.py
|   |   |   
|   |   \---__pycache__
|   |           health_routes.cpython-314.pyc
|   |           pages.cpython-314.pyc
|   |           __init__.cpython-314.pyc
|   |           
|   +---static
|   |   +---css
|   |   |       base.css
|   |   |       landing.css
|   |   |       login.css
|   |   |       register.css
|   |   |       
|   |   \---js
|   |           forgot-password.js
|   |           landing.js
|   |           login-page.js
|   |           register-page.js
|   |           
|   +---templates
|   |       dashboard.html
|   |       forgot-password.html
|   |       index.html
|   |       login.html
|   |       register.html
|   |       
|   \---tests
|           conftest.py
|           test_cookie_security.py
|           test_email_verification.py
|           test_login.py
|           test_logout.py
|           test_password_reset.py
|           test_registration.py
|           test_users.py
|           
\---Images
        Landing.png
        Login.png
        Register.png
        
PS C:\Users\mohan\Downloads\temp\AI-Driven-Customer-Segmentation> 
```

> Keep `.env` out of version control. The structure above is illustrative; adjust it to match your actual repository.

---

## 💻 Local Development

### Prerequisites

Make sure you have the following installed:

- Python 3
- Git
- PostgreSQL-compatible database (for example, Neon PostgreSQL)
- A Brevo account and API key for email verification

### 1. Clone the Repository

```bash
git clone https://github.com/mohankumaronly/AI-Driven-Customer-Segmentation.git
cd AI-Driven-Customer-Segmentation/Backend
```

### 2. Create a Virtual Environment

**Windows — PowerShell:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows — Command Prompt:**

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file inside the `Backend/` directory.

Add the following configuration and replace the placeholder values with your own credentials:

```env
FLASK_DEBUG=True

SECRET_KEY=replace-with-a-strong-secret-key
JWT_SECRET_KEY=replace-with-a-different-strong-secret

DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DATABASE?sslmode=require

JWT_COOKIE_SECURE=False
JWT_COOKIE_SAMESITE=Lax

FRONTEND_URL=http://127.0.0.1:5000

BREVO_API_KEY=your-brevo-api-key
BREVO_SENDER_EMAIL=your-verified-sender@example.com
BREVO_SENDER_NAME=Segmind
```

**Important:**
- Use strong, randomly generated secret keys.
- Replace the database URL with your actual database connection string.
- Ensure your application loads these variables from `.env`.
- The variable names must match those used by your Flask application.
- Keep `.env` private and never commit real credentials to GitHub.

### 5. Initialize the Database

If your project uses Flask-Migrate, apply the existing migrations:

```bash
flask db upgrade
```

Run this command from the `Backend/` directory after configuring the Flask application environment.

If migrations have not been created yet, initialize them according to your project's database setup.

### 6. Start the Application

If `app.py` contains the application entry point:

```bash
python app.py
```

Otherwise, if the application is configured for Flask's CLI:

```bash
flask --app app run --debug
```

Open the following URL in your browser:

**http://127.0.0.1:5000**

---

## 🚀 Deployment on Render

The application can be deployed to Render using the included Dockerfile.

### Deployment Steps

1. Push your project to GitHub.
2. Create a new Web Service in Render.
3. Connect your GitHub repository.
4. Set the **Root Directory** to `Backend` if the Dockerfile and application dependencies are located there.
5. Select Docker as the runtime if deploying with the Dockerfile.
6. Configure the required environment variables in the Render dashboard.
7. Deploy the service and review the application logs.

### Production Environment

Configure production values appropriate for your application:

```env
FLASK_DEBUG=False
JWT_COOKIE_SECURE=True
JWT_COOKIE_SAMESITE=None
```

**Production checklist:**
- Use HTTPS.
- Set strong, unique secret keys.
- Configure a valid production database URL.
- Configure the verified Brevo sender and API key.
- Ensure cookie settings are compatible with your frontend and deployment domains.
- Configure CSRF protection for all relevant state-changing requests.
- Never expose API keys or database credentials in frontend code or logs.

> **Important:** `JWT_COOKIE_SAMESITE=None` generally requires `JWT_COOKIE_SECURE=True`. Cross-site cookie authentication may also require correct CORS, credential, and CSRF configuration. Use the cookie settings appropriate for your actual deployment architecture.

---

## 🛡️ Security Considerations

Segmind incorporates security measures intended to protect user accounts and application sessions.

- **Password Hashing:** Passwords are hashed using bcrypt.
- **HttpOnly Cookies:** Authentication tokens are stored in cookies that client-side JavaScript cannot directly access.
- **CSRF Protection:** Requests that modify server-side state should be protected against cross-site request forgery.
- **Email Verification:** OTP-based email verification helps confirm ownership of email addresses.
- **Password Reset:** Password recovery should validate OTPs and enforce appropriate expiration and retry limits.
- **Secret Management:** Sensitive configuration values should be stored in environment variables and deployment secrets.

Security descriptions should match the protections implemented and tested in the current codebase.

---

## 🗺️ Roadmap

Potential future improvements include:

- Enhanced customer segmentation algorithms.
- Interactive analytics and visualization dashboards.
- Exportable segmentation reports.
- Additional data validation and preprocessing tools.
- More advanced customer behavior insights.
- Expanded automated testing and monitoring.

---

## 🤝 Contributing

Contributions, bug reports, and feature suggestions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Push your branch.
5. Open a pull request describing your changes.

---

## 📄 License

Add the appropriate license information here if the project has a license. If no license has been selected, review your licensing requirements before distributing the project.

---

## 👨‍💻 Author

**Mohan Kumar**

GitHub: [@mohankumaronly](https://github.com/mohankumaronly)

**Live Application:** [Segmind — AI-Driven Customer Segmentation](https://ai-driven-customer-segmentation-2arg.onrender.com/)

---

*Built with ❤️ for data-driven businesses.*
