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
@app.route("/user", methods=["POST"])
def create_user():
    data = request.json
    try:
        if not "@" in data.get("Email", ""):
            return jsonify({"message": "Invalid email format"}), 400

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

        cursor.execute("INSERT INTO User_Organizations (UserID, OrganizationID) VALUES (%s, %s)", (user_id, organization_id))

        # Handle Trusted Contact
        if "TrustedContactName" in data and "TrustedContactNumber" in data:
            cursor.execute("""
                INSERT INTO TrustedContacts (UserID, TrustedContactName, TrustedContactNumber)
                VALUES (%s, %s, %s)
            """, (user_id, data["TrustedContactName"], data["TrustedContactNumber"]))

        # Store Security PIN
        if "PIN" in data:
            cursor.execute("""
                INSERT INTO SecurityPIN (UserID, PIN)
                VALUES (%s, %s)
            """, (user_id, data["PIN"]))

        conn.commit()

        return jsonify({"message": "User created successfully"}), 201

    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"message": f"Database error: {str(e)}"}), 500

@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    user_input = data.get("email_or_phone")
    security_pin = data.get("PIN")
    new_password = data.get("new_password")

    if not user_input or not security_pin or not new_password:
        return jsonify({"message": "Missing required fields"}), 400

    try:
        cursor.execute("""
            SELECT U.UserID 
            FROM Users U 
            JOIN SecurityPIN S ON U.UserID = S.UserID
            WHERE (U.Email = %s OR U.PhoneNumber = %s) AND S.PIN = %s
        """, (user_input, user_input, security_pin))

        user = cursor.fetchone()

        if user:
            cursor.execute("UPDATE Users SET Password = %s WHERE UserID = %s", (new_password, user["UserID"]))
            conn.commit()
            return jsonify({"message": "Password reset successful"}), 200
        elif not user:
            return jsonify({"message": "User not found"}), 404
        else:
            return jsonify({"message": "Invalid credentials"}), 401

    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"message": f"Database error: {str(e)}"}), 500

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

@app.route("/updateUserPhNoName/<email>", methods=["PUT"])
def update_user_ph_no_name(email):
    data = request.json
    try:
        sql = """
            UPDATE Users 
            SET FullName = %s, PhoneNumber = %s 
            WHERE Email = %s
        """
        cursor.execute(sql, (data["FullName"], data["PhoneNumber"], email))
        conn.commit()
        return jsonify({"message": "User details updated successfully"})

    except Exception as e:
        conn.rollback()
        return jsonify({"message": str(e)}), 500

@app.route("/updateUserPassword/<email>", methods=["PUT"])
def update_password(email):
    data = request.json
    try:
        # Step 1: Retrieve the current password from the database
        cursor.execute("SELECT Password FROM Users WHERE Email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"message": "User not found"}), 404

        stored_password = user["Password"]

        # Compare OldPassword with stored password
        if stored_password != data["OldPassword"]:
            return jsonify({"message": "Old password is incorrect"}), 400

        # Step 3: Update password only if old password is correct
        cursor.execute("UPDATE Users SET Password = %s WHERE Email = %s", (data["NewPassword"], email))
        conn.commit()

        return jsonify({"message": "Password updated successfully"})

    except Exception as e:
        conn.rollback()
        return jsonify({"message": str(e)}), 500

@app.route("/user/update-pin", methods=["PUT"])
def update_security_pin():
    data = request.json
    try:
        # Check if the user exists
        cursor.execute("SELECT UserID FROM Users WHERE Email = %s", (data["Email"],))
        user = cursor.fetchone()

        if not user:
            return jsonify({"message": "User not found"}), 404

        # Update Security PIN
        sql = "UPDATE SecurityPIN SET PIN = %s WHERE UserID = %s"
        cursor.execute(sql, (data["NewPIN"], user["Email"]))
        conn.commit()
        return jsonify({"message": "Security PIN updated successfully"})

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
    