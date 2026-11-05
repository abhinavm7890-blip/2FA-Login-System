<<<<<<< HEAD
from flask import Flask, render_template_string, request, redirect, session
import pyotp
import qrcode
import io
import base64
import bcrypt

app = Flask(__name__)

# Secret key used by Flask sessions
import os

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "development-only-change-this"
)


# ============================================================
# USER LOGIN DETAILS
# ============================================================

USERNAME = "admin"

# Original password: 1234
# NEVER store the real password directly.
PASSWORD_HASH = bcrypt.hashpw(
    b"1234",
    bcrypt.gensalt()
)


# ============================================================
# TOTP SECRET
# ============================================================
# IMPORTANT:
# Keep this secret the same after the QR code is scanned.
# In a real application, store this securely in a database.

TOTP_SECRET = "6MG4Y3GPB5DUXLV7NEIELCS24ZEO4W7W"

totp = pyotp.TOTP(TOTP_SECRET)


# ============================================================
# GENERATE QR CODE
# ============================================================

def generate_qr_code():

    provisioning_uri = totp.provisioning_uri(
        name=USERNAME,
        issuer_name="My 2FA Login"
    )

    qr = qrcode.make(provisioning_uri)

    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")

    return base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")


# ============================================================
# LOGIN PAGE
# ============================================================

LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>

    <style>
        body {
            background: #111;
            color: white;
            font-family: Arial;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }

        .box {
            background: #222;
            padding: 40px;
            border-radius: 15px;
            width: 350px;
            text-align: center;
        }

        input {
            width: 90%;
            padding: 12px;
            margin: 10px;
            border-radius: 6px;
            border: none;
        }

        button {
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            background: #4CAF50;
            color: white;
            cursor: pointer;
        }

        .error {
            color: #ff5555;
        }
    </style>
</head>

<body>

<div class="box">

    <h1>Login</h1>

    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}

    <form method="POST">

        <input
            type="text"
            name="username"
            placeholder="Username"
            required
        >

        <input
            type="password"
            name="password"
            placeholder="Password"
            required
        >

        <br>

        <button type="submit">
            Login
        </button>

    </form>

</div>

</body>
</html>
"""


# ============================================================
# 2FA PAGE
# ============================================================

TWO_FA_PAGE = """
<!DOCTYPE html>
<html>
<head>

    <title>2FA Verification</title>

    <style>

        body {
            background: #111;
            color: white;
            font-family: Arial;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .box {
            background: #222;
            padding: 40px;
            border-radius: 15px;
            width: 500px;
            text-align: center;
        }

        img {
            width: 300px;
            height: 300px;
            background: white;
            padding: 10px;
        }

        input {
            width: 90%;
            padding: 15px;
            margin: 15px;
            font-size: 24px;
            text-align: center;
            letter-spacing: 8px;
        }

        button {
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            background: #4CAF50;
            color: white;
            cursor: pointer;
        }

        .error {
            color: #ff5555;
        }

    </style>

</head>

<body>

<div class="box">

    <h1>Two-Factor Authentication</h1>

    <p>
        Scan this QR code using Google Authenticator.
    </p>

    <img
        src="data:image/png;base64,{{ qr_code }}"
    >

    <p>
        Then enter the 6-digit code:
    </p>

    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}

    <form method="POST">

        <input
            type="text"
            name="code"
            maxlength="6"
            pattern="[0-9]{6}"
            placeholder="000000"
            required
        >

        <br>

        <button type="submit">
            Verify
        </button>

    </form>

</div>

</body>
</html>
"""


# ============================================================
# SUCCESS PAGE
# ============================================================

SUCCESS_PAGE = """
<!DOCTYPE html>
<html>

<head>
    <title>Login Successful</title>

    <style>
        body {
            background: #111;
            color: white;
            font-family: Arial;
            text-align: center;
            padding-top: 150px;
        }

        .success {
            color: #4CAF50;
        }
    </style>

</head>

<body>

    <h1 class="success">
        Login Successful!
    </h1>

    <p>
        Username, password and TOTP verification completed.
    </p>

</body>

</html>
"""


# ============================================================
# LOGIN ROUTE
# ============================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # Check username
        if username != USERNAME:
            return render_template_string(
                LOGIN_PAGE,
                error="Invalid username or password."
            )

        # Check password using bcrypt
        password_correct = bcrypt.checkpw(
            password.encode("utf-8"),
            PASSWORD_HASH
        )

        if not password_correct:
            return render_template_string(
                LOGIN_PAGE,
                error="Invalid username or password."
            )

        # Password is correct.
        # Move user to 2FA step.
        session["password_verified"] = True

        return redirect("/2fa")

    return render_template_string(
        LOGIN_PAGE,
        error=None
    )


# ============================================================
# 2FA ROUTE
# ============================================================

@app.route("/2fa", methods=["GET", "POST"])
def two_fa():

    # User must pass password first
    if not session.get("password_verified"):
        return redirect("/")

    if request.method == "POST":

        code = request.form["code"]

        # Verify TOTP code
        if totp.verify(code):

            session["authenticated"] = True

            return redirect("/success")

        return render_template_string(
            TWO_FA_PAGE,
            qr_code=generate_qr_code(),
            error="Invalid authentication code."
        )

    return render_template_string(
        TWO_FA_PAGE,
        qr_code=generate_qr_code(),
        error=None
    )


# ============================================================
# SUCCESS ROUTE
# ============================================================

@app.route("/success")
def success():

    if not session.get("authenticated"):
        return redirect("/")

    return render_template_string(SUCCESS_PAGE)


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
=======
from flask import Flask, render_template_string, request, redirect, session
import pyotp
import qrcode
import io
import base64
import bcrypt

app = Flask(__name__)

# Secret key used by Flask sessions
app.secret_key = "change-this-to-a-random-secret-key"


# ============================================================
# USER LOGIN DETAILS
# ============================================================

USERNAME = "admin"

# Original password: 1234
# NEVER store the real password directly.
PASSWORD_HASH = bcrypt.hashpw(
    b"1234",
    bcrypt.gensalt()
)


# ============================================================
# TOTP SECRET
# ============================================================
# IMPORTANT:
# Keep this secret the same after the QR code is scanned.
# In a real application, store this securely in a database.

TOTP_SECRET = "6MG4Y3GPB5DUXLV7NEIELCS24ZEO4W7W"

totp = pyotp.TOTP(TOTP_SECRET)


# ============================================================
# GENERATE QR CODE
# ============================================================

def generate_qr_code():

    provisioning_uri = totp.provisioning_uri(
        name=USERNAME,
        issuer_name="My 2FA Login"
    )

    qr = qrcode.make(provisioning_uri)

    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")

    return base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")


# ============================================================
# LOGIN PAGE
# ============================================================

LOGIN_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>

    <style>
        body {
            background: #111;
            color: white;
            font-family: Arial;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }

        .box {
            background: #222;
            padding: 40px;
            border-radius: 15px;
            width: 350px;
            text-align: center;
        }

        input {
            width: 90%;
            padding: 12px;
            margin: 10px;
            border-radius: 6px;
            border: none;
        }

        button {
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            background: #4CAF50;
            color: white;
            cursor: pointer;
        }

        .error {
            color: #ff5555;
        }
    </style>
</head>

<body>

<div class="box">

    <h1>Login</h1>

    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}

    <form method="POST">

        <input
            type="text"
            name="username"
            placeholder="Username"
            required
        >

        <input
            type="password"
            name="password"
            placeholder="Password"
            required
        >

        <br>

        <button type="submit">
            Login
        </button>

    </form>

</div>

</body>
</html>
"""


# ============================================================
# 2FA PAGE
# ============================================================

TWO_FA_PAGE = """
<!DOCTYPE html>
<html>
<head>

    <title>2FA Verification</title>

    <style>

        body {
            background: #111;
            color: white;
            font-family: Arial;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .box {
            background: #222;
            padding: 40px;
            border-radius: 15px;
            width: 500px;
            text-align: center;
        }

        img {
            width: 300px;
            height: 300px;
            background: white;
            padding: 10px;
        }

        input {
            width: 90%;
            padding: 15px;
            margin: 15px;
            font-size: 24px;
            text-align: center;
            letter-spacing: 8px;
        }

        button {
            padding: 12px 30px;
            border: none;
            border-radius: 6px;
            background: #4CAF50;
            color: white;
            cursor: pointer;
        }

        .error {
            color: #ff5555;
        }

    </style>

</head>

<body>

<div class="box">

    <h1>Two-Factor Authentication</h1>

    <p>
        Scan this QR code using Google Authenticator.
    </p>

    <img
        src="data:image/png;base64,{{ qr_code }}"
    >

    <p>
        Then enter the 6-digit code:
    </p>

    {% if error %}
        <p class="error">{{ error }}</p>
    {% endif %}

    <form method="POST">

        <input
            type="text"
            name="code"
            maxlength="6"
            pattern="[0-9]{6}"
            placeholder="000000"
            required
        >

        <br>

        <button type="submit">
            Verify
        </button>

    </form>

</div>

</body>
</html>
"""


# ============================================================
# SUCCESS PAGE
# ============================================================

SUCCESS_PAGE = """
<!DOCTYPE html>
<html>

<head>
    <title>Login Successful</title>

    <style>
        body {
            background: #111;
            color: white;
            font-family: Arial;
            text-align: center;
            padding-top: 150px;
        }

        .success {
            color: #4CAF50;
        }
    </style>

</head>

<body>

    <h1 class="success">
        Login Successful!
    </h1>

    <p>
        Username, password and TOTP verification completed.
    </p>

</body>

</html>
"""


# ============================================================
# LOGIN ROUTE
# ============================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # Check username
        if username != USERNAME:
            return render_template_string(
                LOGIN_PAGE,
                error="Invalid username or password."
            )

        # Check password using bcrypt
        password_correct = bcrypt.checkpw(
            password.encode("utf-8"),
            PASSWORD_HASH
        )

        if not password_correct:
            return render_template_string(
                LOGIN_PAGE,
                error="Invalid username or password."
            )

        # Password is correct.
        # Move user to 2FA step.
        session["password_verified"] = True

        return redirect("/2fa")

    return render_template_string(
        LOGIN_PAGE,
        error=None
    )


# ============================================================
# 2FA ROUTE
# ============================================================

@app.route("/2fa", methods=["GET", "POST"])
def two_fa():

    # User must pass password first
    if not session.get("password_verified"):
        return redirect("/")

    if request.method == "POST":

        code = request.form["code"]

        # Verify TOTP code
        if totp.verify(code):

            session["authenticated"] = True

            return redirect("/success")

        return render_template_string(
            TWO_FA_PAGE,
            qr_code=generate_qr_code(),
            error="Invalid authentication code."
        )

    return render_template_string(
        TWO_FA_PAGE,
        qr_code=generate_qr_code(),
        error=None
    )


# ============================================================
# SUCCESS ROUTE
# ============================================================

@app.route("/success")
def success():

    if not session.get("authenticated"):
        return redirect("/")

    return render_template_string(SUCCESS_PAGE)


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    import os

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
>>>>>>> 3e6f3707fd90caa207f45d3413eb007bf0a74d7b
