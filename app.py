from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

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

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login_page"))
    
    email = session["user"]
    
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT name, email FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()
        
        if user_data:
            return render_template("profile.html", user=user_data)
        else:
            return redirect(url_for("login_page"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            return jsonify({"message": "Login successful! Redirecting..."}), 200
        else:
            return jsonify({"error": "Invalid email or password!"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Logout Route
@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route('/get_sche', methods=['GET'])
def get_sche():
    try:
        db = get_db_connection()  # Establish a database connection
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id, name, description, category,age FROM schemes")
        schemes = cursor.fetchall()
        cursor.close()
        db.close()  # Close the connection
        return jsonify(schemes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# API to fetch detailed information about a specific scheme
@app.route('/get_scheme_details', methods=['GET'])
def get_scheme_details():
    db = get_db_connection() 
    scheme_id = request.args.get('id')
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT name, details FROM schemes WHERE id = %s", (scheme_id,))
    scheme = cursor.fetchone()
    cursor.close()
    return jsonify(scheme)


# Fetch all schemes
@app.route('/get_schemes', methods=['GET'])
def get_schemes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM schemes")
    schemes = cursor.fetchall()
    conn.close()
    return jsonify(schemes)

# Add a new scheme
@app.route('/add_scheme', methods=['POST'])
def add_scheme():
    data = request.json
    
    # Check if all required keys exist in the request data
    required_keys = ["name", "description", "age", "marital_status", "state", "residence", "category", "details"]
    for key in required_keys:
        if key not in data:
            return jsonify({"error": f"Missing field: {key}"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """INSERT INTO schemes 
            (name, description, age, marital_status, state, residence, category, details) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

    values = (
        data["name"], data["description"], data["age"], 
        data["marital_status"], data["state"], data["residence"], 
        data["category"], data["details"]
    )

    cursor.execute(sql, values)
    conn.commit()
    scheme_id = cursor.lastrowid
    conn.close()

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

if __name__ == '__main__':
    app.run(debug=True)