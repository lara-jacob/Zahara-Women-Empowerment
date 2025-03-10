from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(_name_)
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

@app.route('/login')
def login_page():
    return render_template('login.html')

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
    return redirect(url_for("login_page"))

if _name_ == '_main_':
    app.run(debug=True)