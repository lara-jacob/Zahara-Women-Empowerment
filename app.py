from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
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
    return render_template("login.html") 

@app.route("/profile")
def profile():
    return render_template("profile.html")

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
@app.route('/login', methods=['POST','GET'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Both email and password are required!"}), 400

    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT password FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()

        cursor.close()
        db.close()

        if result:
            stored_password = result[0]
            print(f"Stored Hash: {stored_password}")  # Debugging
            print(f"Entered Password: {password}")  # Debugging

            if check_password_hash(stored_password, password):
                return jsonify({"message": "Login successful! Redirecting..."}), 200
            else:
                return jsonify({"error": "Incorrect password!"}), 401
        else:
            return jsonify({"error": "User not found!"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)