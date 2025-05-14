from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import string
import random



# Email Configuration
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "varshapanicker5@gmail.com"  # Use your email
EMAIL_PASSWORD = "wost xbou lqeo mdwv"  # Use a Gmail App Password

def send_email_notification(scheme_name, scheme_description):
    """Send email notifications to all registered users."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT email FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()

        recipient_emails = [user["email"] for user in users]

        if not recipient_emails:
            print("No recipients found.")
            return

        subject = "New Scheme Added - Zahara"
        message_body = f"""
        Hello,

        A new scheme has been added on Zahara:

        *Scheme Name:* {scheme_name}
        *Description:* {scheme_description}

        Visit the platform to explore more.

        Regards,
        Zahara Team
        """

        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = ", ".join(recipient_emails)  
        msg["Subject"] = subject
        msg.attach(MIMEText(message_body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, recipient_emails, msg.as_string())

        print("Emails sent successfully!")

    except Exception as e:
        print("Error sending email:", str(e))


app = Flask(__name__)
app.secret_key = "your_secret_key"  # Secret key for session management
CORS(app)  # Allows frontend to communicate with backend

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # Change if needed
    "password": "root123",  # Change this to your MySQL password
    "database": "zaharadb"
}

# Function to get a fresh database connection
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/')
def index():
    return render_template('index.html') 

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/adminlogin')
def adminlogin():
    return render_template('adminlogin.html')

@app.route('/add')
def add():
    return render_template('add.html')

@app.route('/users')
def users():
    return render_template('users.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/explore')
def explore():
    return render_template('explore.html')

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')



# Signup Route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify({"error": "All fields are required!"}), 400
    
    hashed_password = generate_password_hash(password)
    
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", 
                       (name, email, hashed_password))
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({"message": "Signup successful! Redirecting to login..."}), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": "Email already exists!"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Login Route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Both email and password are required!"}), 400

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user and check_password_hash(user['password'], password):
            session["user"] = user['email']  # Store email in session
            session["user_id"] = user['id']  # Store user ID in session
            return jsonify({"message": "Login successful! Redirecting...", "user_id": user["id"]}), 200
        else:
            return jsonify({"error": "Invalid email or password!"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@app.route('/my_schemes', methods=['GET'])
def my_schemes():
    """Fetch and return the schemes added by the logged-in user."""
    if "user_id" not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session["user_id"]

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch schemes selected by the user
        cursor.execute("""
            SELECT schemes.id, schemes.name, schemes.description
            FROM UserScheme
            JOIN schemes ON UserScheme.scheme_id = schemes.id
            WHERE UserScheme.user_id = %s
        """, (user_id,))

        user_schemes = cursor.fetchall()
        conn.close()

        return jsonify({"schemes": user_schemes}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Logout Route
@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


@app.route("/get_sche", methods=["GET"])
def get_schemes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM schemes")  # Adjust table name as needed
    schemes = cursor.fetchall()
    conn.close()
    return jsonify(schemes)

@app.route("/filter_schemes", methods=["POST"])
def filter_schemes():
    filters = request.json
    query = "SELECT * FROM schemes WHERE 1=1"
    params = []

    if filters["age"]:
        query += " AND (age IN ({}) OR age = 'All' OR age IS NULL)".format(",".join(["%s"] * len(filters["age"])))
        params.extend(filters["age"])

    if filters["marital_status"]:
        query += " AND marital_status IN ({})".format(",".join(["%s"] * len(filters["marital_status"])))
        params.extend(filters["marital_status"])

    if filters["state"]:
        query += " AND state IN ({})".format(",".join(["%s"] * len(filters["state"])))
        params.extend(filters["state"])

    if filters["area"]:
        query += " AND area IN ({})".format(",".join(["%s"] * len(filters["area"])))
        params.extend(filters["area"])

    if filters["category"]:
        query += " AND category IN ({})".format(",".join(["%s"] * len(filters["category"])))
        params.extend(filters["category"])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    filtered_schemes = cursor.fetchall()
    conn.close()

    return jsonify(filtered_schemes)

@app.route("/get_scheme_details", methods=["GET"])
def get_scheme_details():
    scheme_id = request.args.get("id")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM schemes WHERE id = %s", (scheme_id,))
    scheme = cursor.fetchone()
    conn.close()
    return jsonify(scheme)


# Add a new scheme
@app.route('/add_scheme', methods=['POST'])
def add_scheme():
    data = request.json
    
    # Check if all required keys exist in the request data
    required_keys = ["name", "description", "age", "marital_status", "state", "residence", "category", "details","link"]
    for key in required_keys:
        if key not in data:
            return jsonify({"error": f"Missing field: {key}"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """INSERT INTO schemes 
            (name, description, age, marital_status, state, residence, category, details,link) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)"""

    values = (
        data["name"], data["description"], data["age"], 
        data["marital_status"], data["state"], data["residence"], 
        data["category"], data["details"],data["link"]   )

    cursor.execute(sql, values)
    conn.commit()
    scheme_id = cursor.lastrowid
    conn.close()

    send_email_notification(data["name"], data["description"])

    return jsonify({
        "id": scheme_id,
        "name": data["name"],
        "category": data["category"],
        "marital_status": data["marital_status"]
    })

# Delete a scheme
@app.route('/delete_scheme/<int:id>', methods=['DELETE'])
def delete_scheme(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schemes WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Scheme deleted successfully"}), 200


# Update scheme status
@app.route('/update_status', methods=['PUT'])
def update_status():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "UPDATE schemes SET status = %s WHERE id = %s"
    values = (data["status"], data["id"])
    cursor.execute(sql, values)
    conn.commit()
    conn.close()
    return jsonify({"message": "Status updated successfully"}), 200

@app.route('/get_users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name, email FROM users")
    users = cursor.fetchall()
    conn.close()
    return jsonify(users)

# Route to delete a user
@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT password FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Generate a temporary password
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    # Hash the temporary password before storing it in the database
    hashed_temp_password = generate_password_hash(temp_password)

    # Update database with the new hashed temporary password
    cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_temp_password, email))
    conn.commit()

    try:
        sender_email = "varshapanicker5@gmail.com"  # Use your email
                                               # Replace with your email
        sender_password = "wost xbou lqeo mdwv"  # Use an app password, not your main password
        subject = "Password Reset Request"

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = subject

        body = f"""
        Hello,

        A password reset was requested for your account.
        Your temporary password is: {temp_password}

        Please log in and change your password immediately.

        Regards,
        Your Team
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()

        return jsonify({"message": "Temporary password has been sent to your email"}), 200

    except Exception as e:
        return jsonify({"error": "Failed to send email", "details": str(e)}), 500

    finally:
        cursor.close()
        conn.close()



@app.route('/profile')
def profile():
    if "user_id" not in session:
        return redirect(url_for("login_page"))

    user_id = session["user_id"]
    
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        # Fetch user details
        cursor.execute("SELECT name, email FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()

        # Fetch the schemes added by the user
        cursor.execute("""
            SELECT schemes.id, schemes.name, schemes.description
            FROM UserScheme
            JOIN schemes ON UserScheme.scheme_id = schemes.id
            WHERE UserScheme.user_id = %s
        """, (user_id,))
        user_schemes = cursor.fetchall()

        cursor.close()
        db.close()
        
        if user_data:
            return render_template("profile.html", user=user_data, user_schemes=user_schemes)
        else:
            return redirect(url_for("login_page"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/g_scheme', methods=['GET'])
def g_scheme():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM schemes")
        schemes = cursor.fetchall()
        conn.close()
        return jsonify(schemes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/add_user_scheme', methods=['POST'])
def add_user_scheme():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401

    data = request.get_json()
    scheme_id = data.get('scheme_id')
    user_id = session['user_id']  # Get logged-in user ID

    if not scheme_id:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if the scheme is already added
        cursor.execute("SELECT * FROM UserScheme WHERE user_id = %s AND scheme_id = %s", (user_id, scheme_id))
        existing_entry = cursor.fetchone()

        if existing_entry:
            return jsonify({'success': False, 'message': 'Scheme already added'})

        # Insert new record
        cursor.execute("INSERT INTO UserScheme (user_id, scheme_id) VALUES (%s, %s)", (user_id, scheme_id))
        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/remove_user_scheme', methods=['POST'])
def remove_user_scheme():
    data = request.json
    user_id = session['user_id'] 
    scheme_id = data.get('scheme_id')
    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("DELETE FROM UserScheme WHERE user_id = %s AND scheme_id = %s", (user_id, scheme_id))
    conn.commit()
    return jsonify({"message": "Scheme removed successfully"})




if __name__ == '__main__':
    app.run(debug=True)