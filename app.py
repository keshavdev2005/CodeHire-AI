from flask import Flask, render_template, request, redirect, url_for, Response, session,send_file, jsonify
import sqlite3
import csv
import ast
import os
import random
import requests
from datetime import datetime
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = "codehireai123"

def send_otp_email(receiver_email, otp):
    api_key = os.getenv("BREVO_API_KEY")

    if not api_key:
        print("ERROR: BREVO_API_KEY not found")
        return False

    data = {
        "sender": {
            "name": "CodeHire AI",
            "email": "codehireai26@gmail.com"
        },
        "to": [
            {
                "email": receiver_email
            }
        ],
        "subject": "CodeHire AI - Email Verification OTP",
        "htmlContent": f"""
        <html>
        <body>
            <h2>CodeHire AI</h2>
            <p>Your verification OTP is:</p>
            <h1>{otp}</h1>
            <p>This OTP is valid for this registration attempt.</p>
        </body>
        </html>
        """
    }

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        },
        json=data,
        timeout=15
    )
    print("Brevo response:", response.status_code, response.text)

    return response.status_code in (200, 201)

def init_db():
    import os
    print(os.path.abspath("users.db"))
    conn = sqlite3.connect("users.db")
    
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            password TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT,
            score TEXT,
            complexity TEXT,
            analysis_time TEXT,
            username TEXT, 
            code TEXT,
            feedback TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    username = request.form["username"].strip()
    email = request.form["email"].strip()
    password = request.form["password"]

    otp = str(random.randint(100000, 999999))

    if not send_otp_email(email, otp):
        return "OTP could not be sent. Please check Brevo configuration."

    session["pending_username"] = username
    session["pending_email"] = email
    session["pending_password"] = password
    session["pending_otp"] = otp

    return render_template(
        "verify_otp.html",
        email=email
    )

@app.route("/verify_otp", methods=["POST"])
def verify_otp():

    entered_otp = request.form["otp"].strip()

    if entered_otp != session.get("pending_otp"):
        return render_template(
            "verify_otp.html",
            email=session.get("pending_email"),
            error="Invalid OTP. Please try again."
        )

    username = session["pending_username"]
    email = session["pending_email"]
    password = session["pending_password"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username, email, password)
    )

    conn.commit()
    conn.close()

    session.pop("pending_username", None)
    session.pop("pending_email", None)
    session.pop("pending_password", None)
    session.pop("pending_otp", None)

    return redirect(url_for("home"))


@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    print("Username =", repr(username))
    print("Password =", repr(password))

    conn = sqlite3.connect("users.db")
    import os
    print("DB =", os.path.abspath("users.db"))
    c = conn.cursor()
    c.execute("SELECT username, password FROM users")
    print("All Users =", c.fetchall())

    c.execute(
        "SELECT * FROM users WHERE LOWER(username)=LOWER(?) AND password=?",
        (username. strip(),
    password.strip())
    )

    user = c.fetchone()

    conn.close()

    if user:
        session["username"] = user[1]
        session["email"] = user[2]
        return redirect(url_for("dashboard"))

    return "Invalid Credentials"
@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect(url_for("home"))

    username = session["username"]
    email = session["email"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Only current user's analyses
    c.execute(
        "SELECT COUNT(*) FROM analysis_history WHERE username=?",
        (username,)
    )
    total = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM analysis_history WHERE username=? AND language='Python'",
        (username,)
    )
    python_count = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM analysis_history WHERE username=? AND language='Java'",
        (username,)
    )
    java_count = c.fetchone()[0]

    c.execute(
        "SELECT COUNT(*) FROM analysis_history WHERE username=? AND language='C++'",
        (username,)
    )
    cpp_count = c.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        username=username,
        email=email,
        total=total,
        python_count=python_count,
        java_count=java_count,
        cpp_count=cpp_count
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
    
    


import ast

def analyze_code(code):

    # Programming Language Detection
    if "#include" in code and "cout" in code:
        language = "C++"
    elif "#include" in code and "printf" in code:
        language = "C"
    elif "public class" in code or "System.out.println" in code:
        language = "Java"
    elif "console.log(" in code:
        language = "JavaScript"
    else:
        language = "Python"

    # Python Syntax Check
    if language == "Python":
        try:
            ast.parse(code)
        except SyntaxError as e:
            return (
                f"Syntax Error Detected!\n{e}",
                "0/10",
                "Feedback: Fix the Python syntax error before running the program."
            )

    # Basic Statistics
    line_count = len(code.splitlines())
    char_count = len(code)
    word_count = len(code.split())

    # Feature Detection
    function_count = (
        code.count("def ")
        + code.count("int ")
        + code.count("void ")
        + code.count("float ")
        + code.count("double ")
    )

    loop_count = code.count("for") + code.count("while")

    conditional_count = (
        code.count("if")
        + code.count("elif")
        + code.count("else")
        + code.count("switch")
    )

    complexity_score = (
        function_count
        + loop_count
        + conditional_count
    )

    if complexity_score <= 2:
        complexity_level = "Easy"
    elif complexity_score <= 5:
        complexity_level = "Medium"
    else:
        complexity_level = "Hard"

    analysis_id = datetime.now().strftime("AI%Y%m%d%H%M%S")
    current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    suggestions = []
    # Suggestions
    if function_count == 0:
        suggestions.append("Use functions to improve code reusability.")

    if loop_count == 0:
        suggestions.append("Consider using loops for repetitive tasks.")

    if conditional_count == 0:
        suggestions.append("Add conditional statements for better decision making.")

    if "#" not in code and "//" not in code:
        suggestions.append("Add comments to improve code readability.")

    if complexity_level == "Hard":
        suggestions.append("Try to simplify complex logic.")

    if len(suggestions) == 0:
        suggestions.append("Excellent! Your code follows good practices.")

    # Score Calculation
    score = 5

    if function_count > 0:
        score += 1

    if loop_count > 0:
        score += 1

    if conditional_count > 0:
        score += 1

    if "#" in code or "//" in code:
        score += 1

    if score > 10:
        score = 10

    # Output Detection
    if (
        "print(" in code
        or "printf(" in code
        or "cout" in code
        or "System.out.println" in code
        or "console.log(" in code
    ):
        result = "Good! Output statement detected."
    else:
        result = "No output statement found."

    # Feedback
    feedback = "Feedback: Code analysis completed successfully."

    feedback += f"\nProgramming Language Detected: {language}"
    feedback += f"\nLines of Code: {line_count}"
    feedback += f"\nCharacters: {char_count}"
    feedback += f"\nWords: {word_count}"
    feedback += f"\nFunctions: {function_count}"
    feedback += f"\nLoops: {loop_count}"
    feedback += f"\nConditional Statements: {conditional_count}"
    feedback += f"\nCode Complexity Score: {complexity_score}"
    feedback += f"\nComplexity Level: {complexity_level}"

    feedback += "\n\nAI Suggestions:"
    for suggestion in suggestions:
        feedback += f"\n- {suggestion}"

    feedback += f"\n\nAnalysis Time: {current_time}"
    feedback += f"\nAnalysis ID: {analysis_id}"

    return result, f"{score}/10", feedback

def run_code(language, code, stdin):

    stdin = stdin or ""

    language_ids = {
        "c": 50,
        "cpp": 54,
        "java": 62,
        "javascript": 63,
        "python": 71
    }

    language_id = language_ids.get(language)

    if not language_id:
        return "Unsupported language."

    # Judge0 Java uses Main.java.
    # Convert user's public class name to Main.
    if language == "java":

        import re

        code = re.sub(
            r'\bpublic\s+class\s+[A-Za-z_][A-Za-z0-9_]*',
            'public class Main',
            code,
            count=1
        )

        # If there is no public class but there is a normal class,
        # convert the first class to Main.
        if "public class Main" not in code:

            code = re.sub(
                r'\bclass\s+[A-Za-z_][A-Za-z0-9_]*',
                'class Main',
                code,
                count=1
            )

    url = (
        "https://ce.judge0.com/"
        "submissions/"
        "?base64_encoded=false&wait=true"
    )

    data = {
        "source_code": code,
        "language_id": language_id,
        "stdin": stdin,
        "cpu_time_limit": 2,
        "wall_time_limit": 5
    }

    try:

        response = requests.post(
            url,
            json=data,
            headers={
                "Content-Type": "application/json"
            },
            timeout=20
        )

        if response.status_code not in (200, 201):

            return (
                "Execution service error:\n"
                + response.text
            )

        result = response.json()

        output = result.get("stdout") or ""
        error = result.get("stderr") or ""
        compile_output = (
            result.get("compile_output") or ""
        )
        message = result.get("message") or ""

        status = (
            result.get("status", {})
            .get("description", "")
        )

        if compile_output:
            return compile_output

        if error:
            return error

        if output:
            return output

        if message:
            return message

        return (
            status
            or "Program finished with no output."
        )

    except requests.RequestException as e:

        return (
            "Execution error:\n"
            + str(e)
        )

@app.route("/run-code", methods=["POST"])
def run_code_route():

    if "username" not in session:
        return jsonify({
            "output": "Please login first."
        }), 401

    language = request.form.get("language", "python")
    code = request.form.get("code", "")
    stdin = request.form.get("stdin", "")

    if not code.strip():
        return jsonify({
            "output": "Please write some code first."
        })

    output = run_code(
        language,
        code,
        stdin
    )
    session["last_code_output"] = output
    return jsonify({
        "output": output
    })


@app.route("/evaluate", methods=["POST"])
def evaluate():
    if "username" not in session:
        return redirect(url_for("home"))

    code = request.form["code"]

    result, score, feedback = analyze_code(code)

    language = "Unknown"
    if "Programming Language Detected:" in feedback:
        language = feedback.split("Programming Language Detected: ")[1].split("\n")[0]

    complexity = "Unknown"
    if "Complexity Level:" in feedback:
        complexity = feedback.split("Complexity Level: ")[1].split("\n")[0]

    analysis_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
        INSERT INTO analysis_history
        (username, language, score, complexity, analysis_time, code, feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        session["username"],
        language,
        score,
        complexity,
        analysis_time,
        code,
        feedback
    ))

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        result=result,
        score=score,
        feedback=feedback,
        code=code,
        language=language,
        complexity=complexity
    )

@app.route("/history")
def history():

    if "username" not in session:
        return redirect(url_for("home"))

    search = request.args.get("search", "")

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    if search:
        c.execute("""
            SELECT id, language, score, complexity, analysis_time
            FROM analysis_history
            WHERE username=? AND language LIKE ?
            ORDER BY id DESC
        """, (session["username"], '%' + search + '%'))

    else:
        c.execute("""
            SELECT id, language, score, complexity, analysis_time
            FROM analysis_history
            WHERE username=?
            ORDER BY id DESC
        """, (session["username"],))

    history = c.fetchall()

    conn.close()

    return render_template("history.html", history=history, search=search)
@app.route("/delete_history/<int:id>")
def delete_history(id):

    if "username" not in session:
        return redirect(url_for("home"))

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute(
        "DELETE FROM analysis_history WHERE id=? AND username=?",
        (id, session["username"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("history"))
@app.route("/export_csv")
def export_csv():
    if "username" not in session:
        return redirect(url_for("home"))

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
    SELECT id, language, score, complexity, analysis_time
    FROM analysis_history
    ORDER BY id DESC
    """)

    rows = c.fetchall()
    conn.close()

    def generate():
        yield "ID,Language,Score,Complexity,Analysis Time\n"
        for row in rows:
           yield f'{row[0]},"{row[1]}","{row[2]}","{row[3]}","{row[4]}"\n'
    return Response(
        generate(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=analysis_history.csv"
        }
    )
@app.route("/profile")
def profile():

    if "username" not in session:
        return redirect(url_for("home"))

    return render_template(
        "profile.html",
        username=session["username"],
        email=session["email"]
    )
conn = sqlite3.connect("users.db")
c = conn.cursor()

c.execute("PRAGMA table_info(analysis_history)")
print("Columns:", c.fetchall())

conn.close()

@app.route("/update_profile", methods=["POST"])
def update_profile():

    if "username" not in session:
        return redirect(url_for("home"))

    new_username = request.form["username"]
    new_email = request.form["email"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute(
        """
        UPDATE users
        SET username=?, email=?
        WHERE username=?
        """,
        (new_username, new_email, session["username"])
    )

    conn.commit()
    conn.close()

    session["username"] = new_username
    session["email"] = new_email

    return redirect(url_for("profile"))

@app.route("/download_pdf")
def download_pdf():

    if "username" not in session:
        return redirect(url_for("home"))

    import sqlite3
    import re
    from html import escape
    from datetime import datetime

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.units import mm

    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        KeepTogether
    )

    # ============================================================
    # DATABASE
    # ============================================================

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
        SELECT
            language,
            score,
            complexity,
            analysis_time,
            code,
            feedback
        FROM analysis_history
        WHERE username=?
        ORDER BY id DESC
        LIMIT 1
    """, (session["username"],))

    data = c.fetchone()

    conn.close()

    # ============================================================
    # SAFE FILE NAME
    # ============================================================

    username_safe = re.sub(
        r"[^A-Za-z0-9_-]",
        "_",
        str(session.get("username", "user"))
    )

    filename = (
        f"{username_safe}_CodeHireAI_Report.pdf"
    )

    # ============================================================
    # PAGE SETTINGS
    # ============================================================

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=29 * mm,
        bottomMargin=18 * mm
    )

    page_width, page_height = A4

    # ============================================================
    # COLORS
    # ============================================================

    DARK_BLUE = colors.HexColor("#0F172A")
    BLUE = colors.HexColor("#2563EB")
    LIGHT_BLUE = colors.HexColor("#EFF6FF")

    LIGHT_GRAY = colors.HexColor("#F8FAFC")
    CODE_BG = colors.HexColor("#F1F5F9")
    OUTPUT_BG = colors.HexColor("#F0FDF4")

    BORDER = colors.HexColor("#CBD5E1")
    OUTPUT_BORDER = colors.HexColor("#86EFAC")

    TEXT = colors.HexColor("#1E293B")
    MUTED = colors.HexColor("#64748B")

    WHITE = colors.white

    # ============================================================
    # STYLES
    # ============================================================

    styles = getSampleStyleSheet()

    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=DARK_BLUE,
        spaceBefore=5,
        spaceAfter=5
    )

    normal_style = ParagraphStyle(
        "NormalStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=10.5,
        textColor=TEXT
    )

    small_style = ParagraphStyle(
        "SmallStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=TEXT
    )

    code_style = ParagraphStyle(
        "CodeStyle",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=6.5,
        leading=8,
        textColor=TEXT
    )

    output_style = ParagraphStyle(
        "OutputStyle",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#166534")
    )

    score_style = ParagraphStyle(
        "ScoreStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=15,
        textColor=BLUE,
        alignment=TA_CENTER
    )

    center_style = ParagraphStyle(
        "CenterStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=MUTED,
        alignment=TA_CENTER
    )

    suggestion_style = ParagraphStyle(
        "SuggestionStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=TEXT
    )

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=25,
        textColor=BLUE,
        alignment=TA_LEFT,
        spaceAfter=2
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        textColor=MUTED,
        alignment=TA_LEFT
    )

    # ============================================================
    # HEADER / FOOTER
    # ============================================================

    def draw_page(canvas_obj, doc_obj):

        canvas_obj.saveState()

        # --------------------------------------------------------
        # HEADER
        # --------------------------------------------------------

        canvas_obj.setFillColor(DARK_BLUE)

        canvas_obj.roundRect(
            16 * mm,
            page_height - 25 * mm,
            page_width - 32 * mm,
            18 * mm,
            4,
            fill=1,
            stroke=0
        )

        canvas_obj.setFillColor(BLUE)

        canvas_obj.setFont(
            "Helvetica-Bold",
            15
        )

        canvas_obj.drawString(
            22 * mm,
            page_height - 15 * mm,
            "CodeHire AI"
        )

        canvas_obj.setFillColor(WHITE)

        canvas_obj.setFont(
            "Helvetica",
            7
        )

        canvas_obj.drawRightString(
            page_width - 22 * mm,
            page_height - 15 * mm,
            "Professional Code Analysis Report"
        )

        # --------------------------------------------------------
        # FOOTER
        # --------------------------------------------------------

        canvas_obj.setStrokeColor(BORDER)

        canvas_obj.line(
            16 * mm,
            12 * mm,
            page_width - 16 * mm,
            12 * mm
        )

        canvas_obj.setFillColor(MUTED)

        canvas_obj.setFont(
            "Helvetica",
            6.8
        )

        canvas_obj.drawString(
            16 * mm,
            7 * mm,
            "CodeHire AI | Professional Code Evaluation System"
        )

        canvas_obj.drawRightString(
            page_width - 16 * mm,
            7 * mm,
            f"Page {doc_obj.page}"
        )

        canvas_obj.restoreState()

    # ============================================================
    # STORY
    # ============================================================

    story = []

    # ============================================================
    # REPORT TITLE
    # ============================================================

    story.append(
        Spacer(
            1,
            2 * mm
        )
    )

    story.append(
        Paragraph(
            "CodeHire AI",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Professional Code Analysis Report",
            subtitle_style
        )
    )

    story.append(
        Spacer(
            1,
            4 * mm
        )
    )

    # ============================================================
    # 1. REPORT TYPE
    # ============================================================

    report_type_section = []

    report_type_section.append(
        Paragraph(
            "1. Report Type",
            section_style
        )
    )

    generated_time = datetime.now().strftime(
        "%d-%m-%Y %H:%M:%S"
    )

    report_data = [
        [
            Paragraph(
                "<b>Report Type</b>",
                normal_style
            ),
            Paragraph(
                "Code Analysis",
                normal_style
            ),
            Paragraph(
                "<b>Generated</b>",
                normal_style
            ),
            Paragraph(
                escape(generated_time),
                small_style
            )
        ]
    ]

    report_table = Table(
        report_data,
        colWidths=[
            32 * mm,
            48 * mm,
            28 * mm,
            62 * mm
        ]
    )

    report_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                LIGHT_BLUE
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                colors.HexColor("#93C5FD")
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    report_type_section.append(
        report_table
    )

    story.append(
        KeepTogether(report_type_section)
    )

    # ============================================================
    # 2. USER DETAILS
    # ============================================================

    user_section = []

    user_section.append(
        Paragraph(
            "2. User Details",
            section_style
        )
    )

    user_details = [
        [
            Paragraph(
                "<b>Username</b>",
                normal_style
            ),
            Paragraph(
                escape(
                    str(
                        session.get(
                            "username",
                            "N/A"
                        )
                    )
                ),
                normal_style
            )
        ],
        [
            Paragraph(
                "<b>Email</b>",
                normal_style
            ),
            Paragraph(
                escape(
                    str(
                        session.get(
                            "email",
                            "N/A"
                        )
                    )
                ),
                normal_style
            )
        ]
    ]

    user_table = Table(
        user_details,
        colWidths=[
            42 * mm,
            128 * mm
        ]
    )

    user_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                LIGHT_GRAY
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                BORDER
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.4,
                BORDER
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    user_section.append(
        user_table
    )

    story.append(
        KeepTogether(user_section)
    )

    # ============================================================
    # 3. ANALYSIS SUMMARY
    # ============================================================

    if data:

        language = str(data[0])
        score = str(data[1])
        complexity = str(data[2])
        analysis_time = str(data[3])

        summary_section = []

        summary_section.append(
            Paragraph(
                "3. Analysis Summary",
                section_style
            )
        )

        summary_data = [
            [
                Paragraph(
                    "<b>Programming Language</b>",
                    normal_style
                ),
                Paragraph(
                    escape(language),
                    normal_style
                ),
                Paragraph(
                    "<b>Score</b>",
                    normal_style
                ),
                Paragraph(
                    escape(score),
                    score_style
                )
            ],
            [
                Paragraph(
                    "<b>Complexity Level</b>",
                    normal_style
                ),
                Paragraph(
                    escape(complexity),
                    normal_style
                ),
                Paragraph(
                    "<b>Analysis Time</b>",
                    normal_style
                ),
                Paragraph(
                    escape(analysis_time),
                    small_style
                )
            ]
        ]

        summary_table = Table(
            summary_data,
            colWidths=[
                43 * mm,
                42 * mm,
                30 * mm,
                55 * mm
            ]
        )

        summary_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    LIGHT_GRAY
                ),
                (
                    "BACKGROUND",
                    (2, 0),
                    (2, -1),
                    LIGHT_GRAY
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    BLUE
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ])
        )

        summary_section.append(
            summary_table
        )

        story.append(
            KeepTogether(summary_section)
        )

        # ========================================================
        # 4. SUBMITTED CODE
        # ========================================================

        code_section = []

        code_section.append(
            Paragraph(
                "4. Submitted Code",
                section_style
            )
        )

        code = str(data[4])

        code_lines = code.splitlines()

        code_lines = code_lines[:40]

        code_html = "<br/>".join(
            escape(line)
            for line in code_lines
        )

        if not code_html:
            code_html = "No code submitted."

        code_para = Paragraph(
            code_html,
            code_style
        )

        code_table = Table(
            [[code_para]],
            colWidths=[
                170 * mm
            ]
        )

        code_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    CODE_BG
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ])
        )

        code_section.append(
            code_table
        )

        story.append(
            KeepTogether(code_section)
        )

        # ========================================================
        # 5. PROGRAM OUTPUT
        # ========================================================

        output_section = []

        output_section.append(
            Paragraph(
                "5. Program Output",
                section_style
            )
        )

        program_output = session.get(
            "last_code_output",
            "No output available."
        )

        output_lines = str(
            program_output
        ).splitlines()

        output_lines = output_lines[:30]

        output_html = "<br/>".join(
            escape(line)
            for line in output_lines
        )

        if not output_html:
            output_html = "No output available."

        output_para = Paragraph(
            output_html,
            output_style
        )

        output_table = Table(
            [[output_para]],
            colWidths=[
                170 * mm
            ]
        )

        output_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    OUTPUT_BG
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    OUTPUT_BORDER
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ])
        )

        output_section.append(
            output_table
        )

        story.append(
            KeepTogether(output_section)
        )

        # ========================================================
        # 6. AI FEEDBACK
        # ========================================================

        feedback_section = []

        feedback_section.append(
            Paragraph(
                "6. AI Feedback",
                section_style
            )
        )

        feedback = str(data[5])

        feedback_lines = feedback.splitlines()

        normal_feedback = []
        suggestions = []

        inside_suggestions = False

        for line in feedback_lines:

            clean_line = line.strip()

            if clean_line.lower() == "ai suggestions:":
                inside_suggestions = True
                continue

            if clean_line.startswith(
                "Analysis Time:"
            ):
                inside_suggestions = False
                continue

            if clean_line.startswith(
                "Analysis ID:"
            ):
                inside_suggestions = False
                continue

            if inside_suggestions:

                if clean_line.startswith("- "):

                    suggestions.append(
                        clean_line[2:].strip()
                    )

            else:

                if clean_line:

                    normal_feedback.append(
                        clean_line
                    )

        feedback_html = "<br/>".join(
            escape(line)
            for line in normal_feedback
        )

        if not feedback_html:
            feedback_html = (
                "Code analysis completed successfully."
            )

        feedback_para = Paragraph(
            feedback_html,
            normal_style
        )

        feedback_table = Table(
            [[feedback_para]],
            colWidths=[
                170 * mm
            ]
        )

        feedback_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_BLUE
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    colors.HexColor("#93C5FD")
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                )
            ])
        )

        feedback_section.append(
            feedback_table
        )

        story.append(
            KeepTogether(feedback_section)
        )

        # ========================================================
        # 7. AI SUGGESTIONS
        # ========================================================

        if suggestions:

            suggestion_section = []

            suggestion_section.append(
                Paragraph(
                    "7. AI Suggestions",
                    section_style
                )
            )

            suggestion_rows = []

            for index, suggestion in enumerate(
                suggestions,
                start=1
            ):

                suggestion_rows.append(
                    [
                        Paragraph(
                            f"<b>{index}</b>",
                            center_style
                        ),
                        Paragraph(
                            escape(suggestion),
                            suggestion_style
                        )
                    ]
                )

            suggestion_table = Table(
                suggestion_rows,
                colWidths=[
                    12 * mm,
                    158 * mm
                ]
            )

            suggestion_table.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        LIGHT_BLUE
                    ),
                    (
                        "BACKGROUND",
                        (1, 0),
                        (1, -1),
                        WHITE
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.6,
                        BORDER
                    ),
                    (
                        "INNERGRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        BORDER
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE"
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        6
                    )
                ])
            )

            suggestion_section.append(
                suggestion_table
            )

            story.append(
                KeepTogether(suggestion_section)
            )

        # ========================================================
        # 8. ANALYSIS ID
        # ========================================================

        analysis_id_section = []

        analysis_id_section.append(
            Paragraph(
                "8. Analysis ID",
                section_style
            )
        )

        match = re.search(
            r"Analysis ID:\s*(AI\d+)",
            feedback
        )

        if match:

            analysis_id = match.group(1)

        else:

            analysis_id = "N/A"

        id_table = Table(
            [[
                Paragraph(
                    "<b>Analysis ID</b>",
                    normal_style
                ),
                Paragraph(
                    escape(analysis_id),
                    normal_style
                )
            ]],
            colWidths=[
                40 * mm,
                130 * mm
            ]
        )

        id_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    LIGHT_GRAY
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    BORDER
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ])
        )

        analysis_id_section.append(
            id_table
        )

        story.append(
            KeepTogether(
                analysis_id_section
            )
        )

        # ========================================================
        # REPORT END
        # ========================================================

        story.append(
            Spacer(
                1,
                4 * mm
            )
        )

        story.append(
            Paragraph(
                "This report was generated automatically by CodeHire AI.",
                center_style
            )
        )

    else:

        story.append(
            Spacer(
                1,
                8 * mm
            )
        )

        story.append(
            Paragraph(
                "No analysis history found.",
                normal_style
            )
        )

    # ============================================================
    # BUILD PDF
    # ============================================================

    doc.build(
        story,
        onFirstPage=draw_page,
        onLaterPages=draw_page
    )

    # ============================================================
    # SEND PDF
    # ============================================================

    return send_file(
        filename,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "GET":
        return render_template("forgot_password.html")

    username = request.form["username"]
    new_password = request.form["new_password"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute(
        "UPDATE users SET password=? WHERE LOWER(username)=LOWER(?)",
        (new_password, username)
    )

    print(c.rowcount)

    conn.commit()
    conn.close()

    return redirect(url_for("home"))
if __name__ == "__main__":
    app.run(debug=True)