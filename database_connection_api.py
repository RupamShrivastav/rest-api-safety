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

# 1️⃣ Create a new user
@app.route("/user", methods=["POST"])
def create_user():
    data = request.json
    try:
        if not "@" in data.get("Email", ""):
            return jsonify({"message": "Invalid email format"}), 400

        # Check if email exists
        cursor.execute("SELECT Email FROM Users WHERE Email = %s", (data["Email"],))
        if cursor.fetchone():
            return jsonify({"message": "Email already exists"}), 409

        # Insert user
        cursor.execute("""
            INSERT INTO Users (FullName, Email, Password, PhoneNumber) 
            VALUES (%s, %s, %s, %s)
        """, (data["FullName"], data["Email"], data["Password"], data["PhoneNumber"]))
        user_id = cursor.lastrowid

        # Handle Organization
        cursor.execute("SELECT OrganizationID FROM Organizations WHERE Organization = %s", (data["Organization"],))
        org_result = cursor.fetchone()
        
        if org_result:
            organization_id = org_result["OrganizationID"]
        else:
            cursor.execute("INSERT INTO Organizations (Organization) VALUES (%s)", (data["Organization"],))
            organization_id = cursor.lastrowid
        
        # Insert User-Organization relationship
        cursor.execute("INSERT INTO User_Organizations (UserID, OrganizationID) VALUES (%s, %s)", (user_id, organization_id))

        # Handle Trusted Contact
        if "TrustedContactName" in data and "TrustedContactNumber" in data:
            cursor.execute("""
                INSERT INTO TrustedContacts (UserID, TrustedContactName, TrustedContactNumber)
                VALUES (%s, %s, %s)
            """, (user_id, data["TrustedContactName"], data["TrustedContactNumber"]))

        conn.commit()

        # Fetch created user data from UserData view
        cursor.execute("SELECT * FROM UserData WHERE UserID = %s", (user_id,))
        created_user = cursor.fetchone()

        return jsonify({
            "message": "User created successfully",
            "user_data": created_user
        }), 201

    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    finally:
        while cursor.nextset():  # Clear any unread results
            pass
        
@app.route("/updateTrustedContactNumber/<email>", methods=["PUT"])
def update_trusted_contact_number(email):
    data = request.json
    try:
        check_sql = """
            SELECT TC.TrustedContactID 
            FROM TrustedContacts TC
            JOIN Users U ON TC.UserID = U.UserID
            WHERE U.Email = %s
        """
        cursor.execute(check_sql, (email,))
        existing_contact = cursor.fetchone()

        if existing_contact:
            sql = """
                UPDATE TrustedContacts 
                SET TrustedContactName = %s, TrustedContactNumber = %s 
                WHERE UserID = (SELECT UserID FROM Users WHERE Email = %s)
            """
            cursor.execute(sql, (data["TrustedContactName"], data["TrustedContactNumber"], email))
        else:
            sql = """
                INSERT INTO TrustedContacts (UserID, TrustedContactName, TrustedContactNumber)
                SELECT UserID, %s, %s FROM Users WHERE Email = %s
            """
            cursor.execute(sql, (data["TrustedContactName"], data["TrustedContactNumber"], email))

        conn.commit()
        return jsonify({"message": "Trusted Contact updated successfully"})

    except Exception as e:
        conn.rollback()
        return jsonify({"message": str(e)}), 500

@app.route("/user/<int:user_id>", methods=["GET"])
def get_user(user_id):
    cursor.execute("SELECT * FROM UserData WHERE UserID = %s", (user_id,))
    user = cursor.fetchone()
    return jsonify(user) if user else (jsonify({"message": "User not found"}), 404)

@app.route("/user/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.json
    try:
        sql = """
            UPDATE Users 
            SET FullName = %s, Email = %s, PhoneNumber = %s 
            WHERE UserID = %s
        """
        cursor.execute(sql, (data["FullName"], data["Email"], data["PhoneNumber"], user_id))
        conn.commit()
        return jsonify({"message": "User updated successfully"})

    except Exception as e:
        conn.rollback()
        return jsonify({"message": str(e)}), 500

@app.route("/user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        cursor.execute("DELETE FROM Users WHERE UserID = %s", (user_id,))
        conn.commit()
        return jsonify({"message": "User deleted successfully"})

    except Exception as e:
        conn.rollback()
        return jsonify({"message": str(e)}), 500

@app.route("/organization/<org_name>/emails", methods=["GET"])
def get_emails_by_org(org_name):
    cursor.execute("SELECT Email FROM UserData WHERE Organization = %s", (org_name,))
    emails = cursor.fetchall()
    return jsonify(emails)

@app.route("/organization/<org_name>/users", methods=["GET"])
def get_users_by_org(org_name):
    cursor.execute("SELECT * FROM UserData WHERE Organization = %s", (org_name,))
    users = cursor.fetchall()
    return jsonify(users)

@app.route("/users/by-email", methods=["POST"])
def get_users_by_emails():
    data = request.json
    emails = tuple(data["emails"])
    if not emails:
        return jsonify({"message": "No emails provided"}), 400

    sql = f"SELECT * FROM UserData WHERE Email IN ({','.join(['%s'] * len(emails))})"
    cursor.execute(sql, emails)
    users = cursor.fetchall()
    return jsonify(users)

@app.route("/allusers", methods=["GET"])
def get_all_users():
    cursor.execute("SELECT * FROM UserData")
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