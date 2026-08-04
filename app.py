from flask import Flask, render_template, request, redirect, url_for, Response, session,send_file
import sqlite3
import csv
import ast
from datetime import datetime
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "codehireai123"

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

    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username, email, password)
    )

    conn.commit()
    conn.close()

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
@app.route("/delete_history")
def delete_history():
    
    if "username" not in session:
        return redirect(url_for("home"))


    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("DELETE FROM analysis_history")

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

@app.route("/change_password", methods=["POST"])
def change_password():

    if "username" not in session:
        return redirect(url_for("home"))

    old_password = request.form["old_password"]
    new_password = request.form["new_password"]
    confirm_password = request.form["confirm_password"]

    if new_password != confirm_password:
        return "New Password and Confirm Password do not match."

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute(
        "SELECT password FROM users WHERE username=?",
        (session["username"],)
    )

    user = c.fetchone()

    if not user:
        conn.close()
        return "User not found."

    if user[0] != old_password:
        conn.close()
        return "Current Password is incorrect."

    c.execute(
        "UPDATE users SET password=? WHERE username=?",
        (new_password, session["username"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("profile"))

@app.route("/download_pdf")
def download_pdf():

    if "username" not in session:
        return redirect(url_for("home"))

    filename = f"{session['username']}_CodeHireAI_Report.pdf"

    pdf = canvas.Canvas(filename)
    width, height = 595, 842

    # Header
    pdf.setFillColorRGB(0.15,0.39,0.92)
    pdf.rect(0,height-70,width,70,fill=1)

    pdf.setFillColorRGB(1,1,1)
    pdf.setFont("Helvetica-Bold",22)
    pdf.drawString(170,height-42,"CodeHire AI")

    pdf.setFont("Helvetica",11)
    pdf.drawString(210,height-60,"Professional Analysis Report")

    conn=sqlite3.connect("users.db")
    c=conn.cursor()

    c.execute("""
    SELECT language,score,complexity,analysis_time,code,feedback
    FROM analysis_history
    WHERE username=?
    ORDER BY id DESC
    LIMIT 1
    """,(session["username"],))

    data=c.fetchone()
    conn.close()

    y=730

    pdf.setFillColorRGB(0,0,0)
    pdf.setFont("Helvetica-Bold",14)
    pdf.drawString(50,y,"User Details")

    y-=25

    pdf.setFont("Helvetica",11)

    pdf.drawString(50,y,f"Username : {session['username']}")
    y-=20

    pdf.drawString(50,y,f"Email : {session['email']}")
    y-=20

    pdf.drawString(50,y,f"Generated : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
    y-=35

    if data:

        pdf.setFont("Helvetica-Bold",14)
        pdf.drawString(50,y,"Analysis Summary")
        y-=25

        pdf.setFont("Helvetica",11)

        pdf.drawString(50,y,f"Language : {data[0]}")
        y-=20

        pdf.drawString(50,y,f"Score : {data[1]}")
        y-=20

        pdf.drawString(50,y,f"Complexity : {data[2]}")
        y-=20

        pdf.drawString(50,y,f"Analysis Time : {data[3]}")
        y-=35

        pdf.setFont("Helvetica-Bold",13)
        pdf.drawString(50,y,"Submitted Code")
        y-=20

        pdf.setFont("Courier",9)

        for line in str(data[4]).split("\n")[:10]:
            pdf.drawString(55,y,line[:90])
            y-=12

        y-=15

        pdf.setFont("Helvetica-Bold",13)
        pdf.drawString(50,y,"AI Feedback")
        y-=20

        pdf.setFont("Helvetica",10)

        for line in str(data[5]).split("\n")[:15]:
            pdf.drawString(55,y,line[:95])
            y-=12

    pdf.setFont("Helvetica-Oblique",9)

    pdf.drawString(
        150,
        25,
        "Generated by CodeHire AI | Professional Code Evaluation System"
    )

    pdf.save()

    return send_file(filename,as_attachment=True)

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
    print(c. rowcount)

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)