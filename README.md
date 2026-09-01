CodeHire AI

AI-Powered Code Analysis & Programming Practice System

CodeHire AI is a Python Flask-based web application designed to help users practice programming, analyze coding performance, track results, and improve their technical skills through an interactive web interface.

🚀 Key Features

- 🔐 User Registration & Login
- 👤 Profile Management
- 📊 Interactive Dashboard
- 💻 Coding Practice & Code Analysis
- 📝 Coding Result & Performance Tracking
- 📚 Submission History
- 🔑 Forgot Password
- 📧 Email OTP Verification
- 🔒 Secure Password Reset Flow
- 🗃️ SQLite Database Support
- 📈 Performance & Skill Tracking
- 🤖 AI-Assisted Coding Analysis
- 🏆 Programming Practice & Readiness Tracking

🛠️ Technologies Used

Frontend

- HTML5
- CSS3
- JavaScript
- Bootstrap

Backend

- Python
- Flask

Database

- SQLite

APIs & Services

- Brevo Email API
- REST API integration using Python Requests

Other Tools & Libraries

- ReportLab – PDF generation
- Gunicorn – Production WSGI server
- Jinja2 – Flask template rendering

📂 Project Structure

CodeHire-AI/
│
├── app.py
├── requirements.txt
├── README.md
│
└── templates/
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── profile.html
    ├── history.html
    ├── result.html
    ├── forgot_password.html
    └── verify_otp.html

⚙️ How to Run Locally

1. Clone the repository

git clone https://github.com/keshavdev2005/CodeHire-AI.git

2. Open the project

cd CodeHire-AI

3. Install dependencies

pip install -r requirements.txt

4. Configure Environment Variables

Create a ".env" file and add the required API configuration.

Never upload ".env" or API keys to GitHub.

5. Run the Flask application

python app.py

Open the application in your browser at:

http://127.0.0.1:5000

🌐 Live Demo

CodeHire AI:
https://codehire-ai-in.onrender.com

The application is deployed using Render and connected with the GitHub repository for deployment.

🔐 Security

- Environment variables are used for sensitive API credentials.
- API keys are not stored directly in the source code.
- ".env" is excluded using ".gitignore".
- Password reset uses email-based OTP verification.

🎯 Project Objective

The main objective of CodeHire AI is to provide a practical platform where users can practice programming, analyze their coding performance, maintain their coding history, and monitor their technical skill development.

👨‍💻 Author

Keshav Dev

BCA Student | Python & Flask Developer | Aspiring Web Developer