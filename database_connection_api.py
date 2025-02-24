from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)

# Database Connection
conn = mysql.connector.connect(
    host="safety-mysql-bd0690f-rpmshrivastav-dfb1.f.aivencloud.com",
    user="avnadmin",
    password="AVNS_6UIkNMMYTeP2qA8yFEX",
    database="defaultdb",
    port=23374
)
cursor = conn.cursor(dictionary=True)

# Create User
@app.route("/user", methods=["POST"])
def create_user():
    data = request.json

    # Check if the email already exists
    email_check_sql = "SELECT * FROM UserData WHERE Email = %s"
    cursor.execute(email_check_sql, (data["Email"],))
    existing_user = cursor.fetchone()

    if existing_user:
        return jsonify({"message": "Email already exists"}), 400

    # Check if the organization exists and get its OrganizationID
    org_check_sql = "SELECT OrganizationID FROM UserData WHERE Organization = %s LIMIT 1"
    cursor.execute(org_check_sql, (data["Organization"],))
    existing_org = cursor.fetchone()

    if existing_org:
        organization_id = existing_org[0]  # Use existing OrganizationID
    else:
        organization_id = data["OrganizationID"]  # Assign new OrganizationID

    # Insert the new user
    sql = """
        INSERT INTO UserData (Organization, OrganizationID, FullName, PersonID, Email, Password, PhoneNumber, TrustedContactName, TrustedContactID, TrustedContactNumber)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (
        data["Organization"], organization_id, data["FullName"], data["PersonID"],
        data["Email"], data["Password"], data["PhoneNumber"], data["TrustedContactName"],
        data["TrustedContactID"], data["TrustedContactNumber"]
    ))
    conn.commit()
    
    return jsonify({"message": "User created successfully"}), 201

# Read User
@app.route("/user/<int:person_id>", methods=["GET"])
def get_user(person_id):
    cursor.execute("SELECT * FROM UserData WHERE PersonID = %s", (person_id,))
    user = cursor.fetchone()
    return jsonify(user) if user else (jsonify({"error": "User not found"}), 404)

# Update User
@app.route("/user/<int:person_id>", methods=["PUT"])
def update_user(person_id):
    data = request.json
    sql = "UPDATE UserData SET FullName = %s, Email = %s, PhoneNumber = %s WHERE PersonID = %s"
    cursor.execute(sql, (data["FullName"], data["Email"], data["PhoneNumber"], person_id))
    conn.commit()
    return jsonify({"message": "User updated successfully"})

# Delete User
@app.route("/user/<int:person_id>", methods=["DELETE"])
def delete_user(person_id):
    cursor.execute("DELETE FROM UserData WHERE PersonID = %s", (person_id,))
    conn.commit()
    return jsonify({"message": "User deleted successfully"})

# Get all emails for an organization
@app.route("/organization/<org_name>/emails", methods=["GET"])
def get_emails_by_org(org_name):
    cursor.execute("SELECT Email FROM UserData WHERE Organization = %s", (org_name,))
    emails = cursor.fetchall()
    return jsonify(emails)

# Get all user data for an organization
@app.route("/organization/<org_name>/users", methods=["GET"])
def get_users_by_org(org_name):
    cursor.execute("SELECT * FROM UserData WHERE Organization = %s", (org_name,))
    users = cursor.fetchall()
    return jsonify(users)

# Get user data based on emails
@app.route("/users/by-email", methods=["POST"])
def get_users_by_emails():
    data = request.json
    emails = tuple(data["emails"])
    sql = f"SELECT * FROM UserData WHERE Email IN ({','.join(['%s'] * len(emails))})"
    cursor.execute(sql, emails)
    users = cursor.fetchall()
    return jsonify(users)

# get all users
@app.route("/allusers", methods=["GET"])
def get_all_users():
    cursor.execute("SELECT * FROM UserData ")
    users = cursor.fetchall()
    return jsonify(users)

@app.route("/users/verify-user", methods=["POST"]) 
def verify_user(): 
    data = request.json 
    email = data["email"] 
    password = data["password"] 
 
    cursor.execute("SELECT * FROM UserData WHERE Email = %s", (email,)) 
    user = cursor.fetchone() 
 
    if user: 
        if user["Password"] == password: 
            return jsonify({"status": "verified", "user_data": user}), 200 
        else: 
            return jsonify({"status": "password_wrong"}), 401 
    else: 
        return jsonify({"status": "user_not_found"}), 404

if __name__ == "__main__":
    app.run(debug=True)
