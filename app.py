from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import login_required, format_date_and_time

# Configure application
app = Flask(__name__)

# Custom Jinja filter to format date and time
app.jinja_env.filters["format_date_and_time"] = format_date_and_time

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///hospital.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Staff positions and access levels
JOB_TITLES = [
    {"title": "Nurse"},
    {"title": "Nursing Technician"},
    {"title": "Doctor"},
    {"title": "Administrator"},
] 

# Check if password is valid
def check_password(password):
    # Check if inserted password is at least eight characters long 
        if len(password) < 8:
            flash("Password must be at least eight characters long!", "error")
            return False
        
        # Check if inserted password contain at least one uppercase letter
        if not any(char.isupper() for char in password):
            flash("Password must contain at least one uppercase letter!", "error")
            return False
        
        # Check if inserted password contain at least one lowercase letter
        if not any(char.islower() for char in password):
            flash("Password must contain at least one lowercase letter!", "error")
            return False
        
        # Check if inserted password contain at least one digit
        if not any(char.isdigit() for char in password):
            flash("Password must contain at least one digit!", "error")
            return False
        
        else:
            return True

# Fetch user information from database
def get_user_info():
    user_id = session["user_id"]

    return db.execute("SELECT id, username, full_name, job_title FROM staff WHERE id = ?", user_id)[0]

# Fetch patient information from database
def get_patient_info(patient_id):
    return db.execute("SELECT * FROM patients WHERE id = ?", patient_id)[0]

# Fetch data from patient's latest or current hospitalization from database
def get_latest_stay_info(patient_id):
    stay_info = db.execute("SELECT * FROM stay WHERE patient_id = ? ORDER BY admission_date DESC LIMIT 1", patient_id)
    if stay_info:
        stay_info = stay_info[0]
        # Change the value from empty fields to "Unavailable" to avoid errors
        for key, value in stay_info.items():
            if value is None:
                stay_info[key] = "Unavailable"
    return stay_info

# Fetch data from patient's previous hospitalizations
def get_previous_stays_info(patient_id):
    # Select everything except the stay row where there's no discharge date
    return db.execute("SELECT * FROM stay WHERE patient_id = ? AND discharge_date IS NOT NULL ORDER BY admission_date DESC", patient_id)

# Calculate age based on patient's birth date
def calculate_age(birth_date):
    # Format value from database into a datetime object and extract the date from it
    birth_object = datetime.strptime(birth_date, "%Y-%m-%d").date()
    # Get current time and extract date
    current_date = datetime.now().date()
    # Calculate patient's age and adjust it by 1 if patient's birthday has already happened in current year
    return current_date.year - birth_object.year - (current_date < birth_object.replace(year=current_date.year))

# Fetch data about patient's allergies and restrictions
def get_medical_history(patient_id):
    medical_history = db.execute("SELECT * FROM medical_history WHERE patient_id = ?", patient_id)
    if medical_history:
        medical_history = medical_history[0]
        for key, value in medical_history.items():
            if value is None:
                medical_history[key] = "None"
            return medical_history
    else:
        return {'allergies': 'None', 'restrictions': 'None'}

# Check if the user has the required access level to edit information
def check_access_level():
    user_id = session["user_id"]
    user_position = db.execute("SELECT job_title FROM staff WHERE id = ?", user_id)[0]
    print("User position is: ", user_position)

    if user_position["job_title"] not in ["Nursing Technician", "Doctor", "Administrator"]:
        return False
    else:
        return True

# Register a new account
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Receive data from registration form
        fullname = request.form.get("fullname")
        username = request.form.get("username")
        job_title = request.form.get("job-title")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Return message if any fields are empty
        if not (fullname and username and job_title and password and confirmation):
            flash("Field must not be empty!", "error")
            return redirect("/register")

        # Check if inserted username is taken
        check_duplicate = db.execute("SELECT * FROM staff WHERE username = ?", username)

        # Return message is username is taken
        if check_duplicate:
            flash("Username already exists!", "error")
            return redirect("/register")

        # Check if inserted job position is valid 
        if job_title not in [job["title"] for job in JOB_TITLES]:
            flash("Invalid job title!", "error")
            return redirect("/register")

        # Check if inserted password meet the requirements
        is_valid = check_password(password)
        if not is_valid:
            return redirect("/register")

        # Check if password and password confimation match
        if password != confirmation:
            flash("Passwords do not match!", "error")
            return redirect("/register")

        # Proceed to hash password and insert data into the registration requests databse
        else:
            hash = generate_password_hash(password, method="pbkdf2", salt_length=16)
            db.execute(
                "INSERT INTO registration_requests (full_name, username, hash, job_title) VALUES(?, ?, ?, ?)", fullname, username, hash, job_title
            )
            flash("You have successfully registered! Your request will be reviewed soon.", "success")
            return redirect("/register")
            
    else:
        return render_template("register.html", titles=JOB_TITLES)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must provide username!", "error")
            return redirect("/login")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password!", "error")
            return redirect("/login")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM staff WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            flash("Invalid username and/or password!", "error")
            return redirect("/login")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Store user job title in session
        session["job_title"] = rows[0]["job_title"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# Display all currently hospitalized patients in index
@app.route("/")
@login_required
def index():
    patients = db.execute(
        "SELECT patients.id, patients.fullname, stay.admission_date FROM patients JOIN stay ON stay.patient_id = patients.id WHERE stay.discharge_date IS NULL ORDER BY patients.fullname"
        )

    return render_template("index.html", patients=patients)

# Register new patient
@app.route("/register-patient", methods=["GET", "POST"])
@login_required
def register_patient():
    if request.method == "POST":
        # Retrieve submitted data
        fullname = request.form.get("fullname")
        gender = request.form.get("gender")
        birth_date = request.form.get("birth-date")
        admission_date = request.form.get("admission-date")
        # Check if any field was left empty
        if not (fullname and gender and birth_date and admission_date):
            flash("Field must not be empty!", "error")
            return redirect("/register-patient")
        
        # If no fields were left empty, proceed to insert data into the database
        else:
            db.execute(
                "INSERT INTO patients (fullname, gender, birth_date) VALUES(?, ?, ?)", fullname, gender, birth_date
            )
            # Get the ID from the inserted row into the patient's table
            patient_id = db.execute("SELECT last_insert_rowid() AS id")[0]["id"]
            # Create a new stay record 
            db.execute(
                "INSERT INTO stay (patient_id, admission_date) VALUES (?, ?)",
                patient_id, admission_date
            )
            flash("New patient successfully registered!", "success")
            return redirect("/")
    else:
        return render_template("register-patient.html")

# Display patient profile    
@app.route("/patient/<int:patient_id>")
@login_required
def patient_profile(patient_id):
    patient_info = get_patient_info(patient_id)
    stay_info = get_latest_stay_info(patient_id)
    previous_stays_info = get_previous_stays_info(patient_id)
    age = calculate_age(patient_info.get('birth_date'))
    medical_history = get_medical_history(patient_id)
    can_edit = check_access_level()

    return render_template("patient-profile.html", patient=patient_info, stay=stay_info, age=age, previous_stays = previous_stays_info, medical_history=medical_history, can_edit=can_edit)

# Display form to submit discharge data
@app.route("/discharge-patient/<int:patient_id>", methods=["GET", "POST"])
@login_required
def discharge_patient(patient_id):
    patient_info = get_patient_info(patient_id)
    stay_info = get_latest_stay_info(patient_id)
    previous_stays_info = get_previous_stays_info(patient_id)
    age = calculate_age(patient_info.get('birth_date'))
    medical_history = get_medical_history(patient_id)
    can_edit = check_access_level()

    if request.method == "POST":
        stay_id = request.form.get("stay-id")
        discharge_date = request.form.get("discharge-date")
        db.execute(
                    "UPDATE stay SET discharge_date = ? WHERE stay_id = ? AND patient_id = ?", discharge_date, stay_id, patient_id
                    )
        flash("Patient successfully discharged!", "success")
        return redirect("/patient/{}".format(patient_id))
    else:
        return render_template("discharge-patient.html", patient=patient_info, stay=stay_info, age=age, previous_stays_info = previous_stays_info, medical_history=medical_history, can_edit=can_edit)

# Display form to submit new hospitalization
@app.route("/new-stay/<int:patient_id>", methods=["GET", "POST"])
@login_required
def new_stay(patient_id):
    patient_info = get_patient_info(patient_id)
    stay_info = get_latest_stay_info(patient_id)
    previous_stays_info = get_previous_stays_info(patient_id)
    age = calculate_age(patient_info.get('birth_date'))
    medical_history = get_medical_history(patient_id)
    can_edit = check_access_level()

    if request.method == "POST":
        admission_date = request.form.get("admission-date")
        db.execute(
            "INSERT INTO stay (patient_id, admission_date) VALUES (?, ?)", patient_id, admission_date
            )
        flash("New stay record successfully added!", "success")
        return redirect("/patient/{}".format(patient_id))
    else:
        return render_template("new-stay.html", patient=patient_info, stay=stay_info, age=age, previous_stays_info=previous_stays_info, medical_history=medical_history, can_edit=can_edit)

# Edit patient info
@app.route("/edit-patient/<int:patient_id>", methods=["GET", "POST"])
@login_required
def edit_patient(patient_id):
    patient_info = get_patient_info(patient_id)
    stay_info = get_latest_stay_info(patient_id)
    previous_stays_info = get_previous_stays_info(patient_id)
    age = calculate_age(patient_info.get('birth_date'))
    medical_history = get_medical_history(patient_id)
    can_edit = check_access_level()

    stay_id = stay_info['stay_id']
    
    if request.method == "POST":
        patient_fields = ["fullname", "gender", "birth-date", "address", "phone-numbers"]
        stay_fields = ["current-condition", "diagnosis-date", "condition-severity", "medication", "projected-discharge-date"]
        medical_fields = ["allergies", "restrictions"]

        for field in patient_fields + stay_fields + medical_fields:
            form_value = request.form.get(field)
            # Format the submited fields to match the fields in database
            db_field = field.replace("-", "_")
            # Get current values from database
            if field in patient_fields:
                current_value = patient_info.get(db_field)
            elif field in stay_fields:
                current_value = stay_info.get(db_field)
            elif field in medical_fields:
                current_value = medical_history.get(db_field)
                # If medical fields were left empty, set value to "None"
                if not form_value:
                    form_value = "None"

            print(f"Updating {field}: {current_value} -> {form_value}")
            # If submited value is different from the value from database, prepare to update database
            if form_value and form_value != current_value:
                if field in patient_fields:
                    sql = f"UPDATE patients SET {db_field} = ? WHERE id = ?"
                elif field in stay_fields:
                    sql = f"UPDATE stay SET {db_field} = ? WHERE stay_id = {stay_id} AND patient_id = ?"
                elif field in medical_fields:
                    # If fields were left empty, check if patient already has a medical history record
                    if current_value == "None":
                        check_patient = db.execute("SELECT * FROM medical_history WHERE patient_id = ?", patient_id)
                        # Prepare to insert a new row if there's none associated with the patient yet
                        if not check_patient:
                            sql = f"INSERT INTO medical_history ({db_field}, patient_id) VALUES (?, ?)"
                        # Prepare to update if patient already has a record
                        else:
                            sql = f"UPDATE medical_history SET {db_field} = ? WHERE patient_id = ?"
                    # If a value was submited, prepare to update database
                    else:
                        sql = f"UPDATE medical_history SET {db_field} = ? WHERE patient_id = ?"

                print(f"Executing SQL: {sql}")
                # Try to update values in database
                try:
                    db.execute(sql, form_value, patient_id)
                # If update wasn't successful, print error message to the console
                except Exception as e:
                    print(f"Error updating {db_field}: {e}")

        return redirect("/patient/{}".format(patient_id))
    
    else:
        return render_template("edit-patient.html", patient=patient_info, stay=stay_info, age=age, previous_stays_info=previous_stays_info, medical_history=medical_history, can_edit=can_edit)

# Display all patients
@app.route("/all-patients")
@login_required
def all_patients():
    patients = db.execute("SELECT * FROM patients")
    return render_template("all-patients.html", patients=patients)

# Display user profile
@app.route("/your-profile")
@login_required
def your_profile():
    user_info = get_user_info()
    return render_template("user-profile.html", user_info = user_info)

# Edit account settings
@app.route("/account-settings", methods=["GET", "POST"])
@login_required
def profile_settings():
    user_info = get_user_info()
    user_id = user_info["id"]

    if request.method == "POST":
        user_fields = ["username", "full-name", "job-title"]

        for field in user_fields:
            form_value = request.form.get(field)
            # Format the submited fields to match the fields in database
            db_field = field.replace("-", "_")
            # Get current values from database
            current_value = user_info.get(db_field)

            # Check if inserted username is taken
            if field == "username" and form_value != user_info["username"]:
                check_duplicate = db.execute("SELECT * FROM staff WHERE username = ?", form_value)
                if check_duplicate:
                    flash("Username is already taken!", "error")
                    return redirect("/account-settings")
                
            print(f"Updating {field}: {current_value} -> {form_value}")

            # If a value is submitted and it's different from the value in database
            if form_value and form_value != current_value:
                # Prepare to update database
                sql = f"UPDATE staff SET {db_field} = ? WHERE id = ?"
                print(f"Executing SQL: {sql}")
                # Try to update values in database
                try:
                    db.execute(sql, form_value, user_id)
                # If update wasn't successful, print error message to the console
                except Exception as e:
                    print(f"Error updating {db_field}: {e}")
    
        return redirect("/your-profile")

    else:
        return render_template("account-settings.html", user_info = user_info, titles=JOB_TITLES)

# Display form to change password
@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    user_info = get_user_info()
    user_id = get_user_info()["id"]

    if request.method == "POST":
        current_password = request.form.get("current-password")
        new_password = request.form.get("new-password")
        confirm_new_password = request.form.get("confirm-new-password")

        # Check if fields were not left empty
        if not (current_password and new_password and confirm_new_password):
            flash("Fields must not be empty!", "error")
            return redirect("/account-settings")
        
        # Check if new password meet the requirements
        is_valid = check_password(new_password)
        if not is_valid:
            return redirect("/change-password")

        # Check if new password and confirmation match
        if new_password != confirm_new_password:
            flash("Passwords do not match!", "error")
            return redirect("/account-settings")
        
        # Check if current password is correct
        old_password = db.execute("SELECT hash FROM staff WHERE id = ?", user_id)

        if not check_password_hash(old_password[0]["hash"], current_password):
            flash("Current password incorrect!", "error")
            return redirect("/account-settings")
        
        # Hash new password
        new_hash = generate_password_hash(new_password, method="pbkdf2", salt_length=16)

        # Ensure new password is different from old password
        if old_password[0]["hash"] == new_hash:
            flash("New password cannot be the same as your old password!", "error")
            return redirect("/account-settings")
        
        # Proceed to update password
        else:
            db.execute("UPDATE staff SET hash = ? WHERE id = ?", new_hash, user_id)
            flash("Password changed successfully!", "success")
        return redirect("/account-settings")

    else:
        return render_template("change-password.html", user_info=user_info, titles=JOB_TITLES)

# Display results for patient search
@app.route("/search-patient")
@login_required
def search_patient():
    query = request.args.get("query")

    if query:
        # If query is a number, search for patient id
        if query.isnumeric():
            results = db.execute("SELECT * FROM patients WHERE id = ?", query)
        # If query is composed by letters, search for patients names
        else:
            results = db.execute("SELECT * FROM patients WHERE fullname like ?", ('%' + query + '%',))
    # If no results were found, set it to None
    else:
        results = None
        
    return render_template("patient-search.html", results=results)

# Display control panel to administrators
@app.route("/control-panel")
@login_required
def control_panel():
    return render_template("control-panel.html")

# Manage registration requests
@app.route("/registration-requests", methods=["GET", "POST"])
@login_required
def registration_requests():
    # Fetch data from the requests database
    requests = db.execute("SELECT * FROM registration_requests")

    if request.method == "POST":
        # Receive action that will be performed
        action = request.form.get("action")
        request_id = request.form.get("request-id")
        
        # Approve registration request
        if action == "approve":
            # Copy data from the registration requests table to the staff table  
            db.execute(
                "INSERT INTO staff (username, hash, full_name, job_title) SELECT username, hash, full_name, job_title FROM registration_requests"
                )
            
            # Delete copied data from registration requests         
            db.execute("DELETE FROM registration_requests WHERE id = ?", request_id)
            flash("Request was successfully approved", "success")
            return redirect("/registration-requests")

        # Delete registration request
        elif action == "delete":
            db.execute("DELETE FROM registration_requests WHERE id = ?", request_id)
            flash("Request was successfully deleted!", "success")
            return redirect("/registration-requests")

    # Display requests
    else:    
        return render_template("registration-requests.html", requests=requests)

# Manage staff members
@app.route("/manage-staff", methods=["GET", "POST"])
@login_required
def manage_staff():
    staff = db.execute("SELECT id, username, full_name, job_title FROM staff")

    if request.method == "POST":
        staff_member_id = request.form.get('user-id')
        action = request.form.get('action')

        # Display password form to confirm deletion of own account
        if action == 'delete-own':
            return render_template("confirm-deletion.html", staff_member_id=staff_member_id)
        
        # Check if confirmation is valid
        elif action == 'confirm-deletion':
            inserted_password = request.form.get('password')
            password = db.execute("SELECT hash FROM staff WHERE id = ?", staff_member_id)

            # Display error if inserted password was incorrect
            if not check_password_hash(password[0]["hash"], inserted_password):
                flash("Incorrect password!", "error")
                return redirect("/manage-staff")
            
            # If the inserted passoword was correct, delete account from database
            else:
                db.execute("DELETE FROM staff WHERE id = ?", staff_member_id)
                # Clear session data and redirect to login page
                session.clear()
                return redirect("/login")

        # Delete another user profile
        else:
            db.execute("DELETE FROM staff WHERE id = ?", staff_member_id)
            flash("Staff member profile was successfully deleted!", "success")
            return redirect("/manage-staff")

    else:
        return render_template("manage-staff.html", staff=staff)

# Display staff member profile
@app.route("/user/<int:user_id>")
@login_required
def user_profile(user_id):
    staff_member_info = db.execute("SELECT id, username, full_name, job_title FROM staff WHERE id = ?", user_id)[0]

    # Show delete profile button only through staff member profile route
    showButton = True

    return render_template("user-profile.html", user_info=staff_member_info, showButton=showButton)
