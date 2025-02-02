from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)


# Database Connection
conn = mysql.connector.connect(
    host="mysql-4a991a1-abarakadabara698-7bd8.c.aivencloud.com",
    user="avnadmin",
    password="AVNS_Rfu9thyCzg-r-9CcyXE",
    database="defaultdb",
    port=10038
)
cursor = conn.cursor(dictionary=True)

# Create User
@app.route("/user", methods=["POST"])
def create_user():
    data = request.json
    sql = """
        INSERT INTO UserData (Organization, OrganizationID, FullName, PersonID, Email, Password, PhoneNumber, TrustedContactName, TrustedContactID, TrustedContactNumber)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (
        data["Organization"], data["OrganizationID"], data["FullName"], data["PersonID"],
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


if __name__ == "__main__":
    app.run(debug=True)
