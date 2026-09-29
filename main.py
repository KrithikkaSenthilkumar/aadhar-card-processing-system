import os
import mysql.connector

# Connect to MySQL
db = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "AADHAR_CARD_PROCESSING_SYSTEM")
)

print("========================================")
print("     AADHAR CARD PROCESSING SYSTEM")
print("========================================")

while True:
    print("\n1. Register Citizen")
    print("2. Apply for Aadhaar")
    print("3. Verify Documents")
    print("4. Check Application Status")
    print("5. Search Citizen")
    print("6. Update Aadhaar Details")
    print("7. View Reports")
    print("8. Exit")

    choice = input("\nEnter your choice: ")
    
    if choice == "1":
        name = input("Enter name: ")
        date_of_birth = input("Enter date of birth (YYYY-MM-DD): ")
        gender = input("Enter gender: ")
        phone = input("Enter phone number: ")
        address = input("Enter address: ")
        city = input("Enter city: ")
        state = input("Enter state: ")

        query = """
        INSERT INTO Citizen
        (name, date_of_birth, gender, phone, address, city, state)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        values = (name, date_of_birth, gender, phone, address, city, state)

        cursor = db.cursor()
        cursor.execute(query, values)
        db.commit()

        print("Citizen registered successfully!")
        cursor.close()

    elif choice == "2":
        citizen_id = input("Enter citizen ID: ")
        application_type = input("Enter application type: ")
        application_date = input("Enter application date (YYYY-MM-DD): ")

        query = """
        INSERT INTO Application
        (citizen_id, application_type, application_date)
        VALUES (%s, %s, %s)
        """

        values = (citizen_id, application_type, application_date)

        cursor = db.cursor()
        cursor.execute(query, values)
        db.commit()

        print("Aadhaar application submitted successfully!")
        cursor.close()

    elif choice == "3":
        application_id = input("Enter application ID: ")
        result = input("Enter verification result (Approved/Rejected): ")
        remarks = input("Enter remarks: ")

        cursor = db.cursor()

        check_query = """
        SELECT application_id
        FROM Verification
        WHERE application_id = %s
        """

        cursor.execute(check_query, (application_id,))
        existing = cursor.fetchone()

        if existing:
            query = """
            UPDATE Verification
            SET verification_date = CURDATE(),
                verified_by = 'Officer',
                verification_result = %s,
                remarks = %s
            WHERE application_id = %s
            """

            values = (result, remarks, application_id)
            cursor.execute(query, values)

        else:
            query = """
            INSERT INTO Verification
            (application_id, verification_date, verified_by,
             verification_result, remarks)
            VALUES (%s, CURDATE(), 'Officer', %s, %s)
            """

            values = (application_id, result, remarks)
            cursor.execute(query, values)

        db.commit()

        print("Document verification updated successfully!")

        cursor.close()

    elif choice == "4":
        application_id = input("Enter application ID: ")

        query = """
        SELECT a.application_id,
               c.name,
               a.application_type,
               a.application_date,
               a.status,
               v.verification_result
        FROM Application a
        JOIN Citizen c ON a.citizen_id = c.citizen_id
        LEFT JOIN Verification v ON a.application_id = v.application_id
        WHERE a.application_id = %s
        """

        cursor = db.cursor()
        cursor.execute(query, (application_id,))
        result = cursor.fetchone()

        if result:
            print("\n--- Application Details ---")
            print("Application ID:", result[0])
            print("Citizen Name:", result[1])
            print("Application Type:", result[2])
            print("Application Date:", result[3])
            print("Application Status:", result[4])
            print("Verification Result:", result[5])
        else:
            print("Application ID not found.")

        cursor.close()

    elif choice == "5":
        citizen_id = input("Enter citizen ID: ")

        query = """
        SELECT citizen_id, name, date_of_birth, gender,
               phone, address, city, state
        FROM Citizen
        WHERE citizen_id = %s
        """

        cursor = db.cursor()
        cursor.execute(query, (citizen_id,))
        result = cursor.fetchone()

        if result:
            print("\n--- Citizen Details ---")
            print("Citizen ID:", result[0])
            print("Name:", result[1])
            print("Date of Birth:", result[2])
            print("Gender:", result[3])
            print("Phone:", result[4])
            print("Address:", result[5])
            print("City:", result[6])
            print("State:", result[7])
        else:
            print("Citizen not found.")

        cursor.close()

    elif choice == "6":
        citizen_id = input("Enter citizen ID: ")
        update_type = input("Enter update type (Address/Phone Number): ")
        new_value = input("Enter new value: ")

        if update_type == "Address":
            query = "SELECT address FROM Citizen WHERE citizen_id = %s"
        elif update_type == "Phone Number":
            query = "SELECT phone FROM Citizen WHERE citizen_id = %s"
        else:
            print("Invalid update type.")
            continue

        cursor = db.cursor()
        cursor.execute(query, (citizen_id,))
        result = cursor.fetchone()

        if result:
            old_value = result[0]

            insert_query = """
            INSERT INTO Update_Request
            (citizen_id, update_type, old_value, new_value, request_date, status)
            VALUES (%s, %s, %s, %s, CURDATE(), 'Pending')
            """

            cursor.execute(
                insert_query,
                (citizen_id, update_type, old_value, new_value)
            )
            db.commit()

            print("Update request submitted successfully!")
        else:
            print("Citizen not found.")

        cursor.close()
    elif choice == "7":
        cursor = db.cursor()

        query = """
        SELECT
            a.application_id,
            c.name,
            a.application_type,
            a.application_date,
            a.status,
            v.verification_result,
            ac.aadhaar_number,
            ac.issue_date,
            ac.card_status
        FROM Application a
        JOIN Citizen c
            ON a.citizen_id = c.citizen_id
        LEFT JOIN Verification v
            ON a.application_id = v.application_id
        LEFT JOIN Aadhaar_Card ac
            ON a.application_id = ac.application_id
        """

        cursor.execute(query)
        results = cursor.fetchall()

        print("\n--- AADHAAR APPLICATION REPORT ---")

        if results:
            for row in results:
                print("----------------------------------------")
                print("Application ID:", row[0])
                print("Name:", row[1])
                print("Application Type:", row[2])
                print("Application Date:", row[3])
                print("Status:", row[4])
                print("Verification:", row[5])
                print("Aadhaar Number:", row[6])
                print("Issue Date:", row[7])
                print("Card Status:", row[8])
        else:
            print("No application records found.")

        cursor.close()

    elif choice == "8":
        print("Thank you!")
        break

    else:
        print("Invalid choice. Please try again.")

db.close()