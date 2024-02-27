# PATIENT MANAGER
#### Video Demo:  https://youtu.be/4teIi1vi9lw
#### Description:
This web app provides management and monitoring of hospitalized patients, maintaining records of information about the patients and their stay. It allows hospital staff simple and quick access to the patient's profile, including their personal and contact information, allergies, restrictions, medications, condition, severity level, and admission dates. It also enables employees, according to their roles, to edit information, register a new admission, and discharge patients. Additionally, administrators can manage employee accounts and review requests for new account registration. It was created using the Flask framework, SQLite3 for database management, and HTML, CSS, and JavaScript for the user interface.

## How to use it:
- Navigate to the project folder in your terminal.
- Run `pip install -r requirements.txt` to install the required packages.
- Run the command `flask run`.
- Open the provided URL in your web browser.
- Log in using the default administrator username and password.
```
Username: admin
Password: Admin1234
```
- Alternatively, you can create a new account and approve it using the default administrator account, or edit the settings of the default administrator account as desired.

## Files:

### app.py: 
```python
def check_password(password):
```
- Checks if the entered password meets the requirements of a minimum of 8 characters, including at least one uppercase letter, one lowercase letter, and one number.

```python
def get_user_info():
```
- Retrieves the user ID from the session and returns their information from the database.

```python
def get_patient_info(patient_id):
```
- Returns the patient's information after retrieving it from the database using their ID.

```python
def get_latest_stay_info(patient_id):
```
- Returns information about the patient's current hospital stay, which is the stay with the most recent admission date. It assigns the text "Unavailable" to empty fields.

```python
def get_previous_stays_info(patient_id):
```
- Returns information about the patient's previous hospital stays, which are the records that include the discharge date, ordered by the most recent ones.

```python
def calculate_age(birth_date):
```
- Returns the patient's age calculated from their date of birth.

```python
def get_medical_history(patient_id):
```
- Returns the medical data of the patient, such as allergies and restrictions. Assigns the text "None" for empty fields.

```python
def check_access_level():
```
- Checks if the user in session has the minimum required position to edit patient information.

```python
@app.route("/register", methods=["GET", "POST"])
```
- Displays the new account registration form on the **register.html** page, receives the entered data, checks if they meet the requirements, and saves the data in the registration requests database for administrator evaluation.

```python
@app.route("/login", methods=["GET", "POST"])
```
- Displays the login form on the **login.html** page, receives the user-entered data, checks if they correspond to an existing account, and redirects to the **index.html** page, allowing access to the application.

```python
@app.route("/logout")
```
- Clears the session data and redirects to the login page.

```python
@app.route("/")
```
- Retrieves the patients currently hospitalized in the database and displays them on the homepage, **index.html**.

```python
@app.route("/register-patient", methods=["GET", "POST"])
```
- Displays the form for registering a new patient on the **register-patient.html** page, receives the entered data, and saves it in the database.

```python
@app.route("/patient/<int:patient_id>")
```
- Retrieves the patient's data from the database and displays it on their profile page, **patient-profile.html**.

```python
@app.route("/discharge-patient/<int:patient_id>", methods=["GET", "POST"])
```
- Displays a form to enter the discharge date and time of the patient on the dynamic block **discharge-patient.html**, receives the entered data, and saves it in the database.

```python
@app.route("/new-stay/<int:patient_id>", methods=["GET", "POST"])
```
- Displays a form to enter the admission date and time to start a new patient stay on the dynamic block **new-stay.html**, receives the entered data, and saves it in the database.

```python
@app.route("/edit-patient/<int:patient_id>", methods=["GET", "POST"])
```
- Displays the forms to update or edit patient information on the **edit-patient.html** page, receives the entered data, and saves it in the database.

```python
@app.route("/all-patients")
```
- Retrieves the list of all registered patients and displays them in a table on the **all-patients.html** page.

```python
@app.route("/your-profile")
```
- Displays the profile of the logged-in user on the **user-profile.html** page.

```python
@app.route("/account-settings", methods=["GET", "POST"])
```
- Displays the account settings on the **account-settings.html** page, receives the edited data, and saves it in the database.

```python
@app.route("/change-password", methods=["GET", "POST"])
```
- Displays the form for changing the password on the **change-password.html** page, receives and verifies the entered data, and saves it in the database.

```python
@app.route("/search-patient")
```
- Receives the entered data in the search bar, searches for matches in the database, and displays the results in a table on the **patient-search.html** page.

```python
@app.route("/control-panel")
```
- Displays the control panel to administrators on the **control-panel.html** page.

```python
@app.route("/registration-requests", methods=["GET", "POST"])
```
- Displays a table with registration requests to administrators on the **registration-requests.html** page, allowing approval and insertion of data into the staff table or rejection of the request and deletion of data from the registration requests table.

```python
@app.route("/manage-staff", methods=["GET", "POST"])
```
- Displays to administrators a table listing all registered employees and their roles on the **manage-staff.html** page. Also allows administrators to delete accounts, including their own after confirming the password on the **confirm-deletion.html** page.

```python
@app.route("/user/<int:user_id>")
```
- Retrieves the employee's data from the database and displays it to administrators on the **user-profile.html** page.


### helpers.py:

```python
def login_required(f):
```
- Decorate routes to require login.

```python
def format_date_and_time(date_str):
```
- Formats date and time data from the database into a user-readable format on the interface.


### hospital.db:

Stores all data of patients and staff.

``` sql
CREATE TABLE staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    job_title TEXT NOT NULL
);

CREATE TABLE stay(
    stay_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    patient_id INTEGER,
    current_condition TEXT,
    diagnosis_date TEXT,
    condition_severity TEXT,
    medication TEXT,
    admission_date TEXT,
    projected_discharge_date TEXT,
    discharge_date TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(id)
);

CREATE TABLE patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    fullname TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    birth_date TEXT,
    address TEXT, phone_numbers TEXT
);

CREATE TABLE medical_history (
    patient_id,
    allergies TEXT,
    restrictions TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(id)
);

CREATE TABLE registration_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    job_title TEXT NOT NULL
);
```

### Templates/ 

- **register.html**: Displays a form that allows the registration of new accounts by entering full name, username, job title, password, and password confirmation.

- **login.html**: Displays a form allowing users to enter their username and password to log in.

- **layout.html**: Defines the general structure and design of the HTML pages in the application.

- **index.html**: Displays a table with all currently hospitalized patients and their respective admission dates.

- **register-patient.html**:  Displays a form for registering a new patient. Requires full name, gender, date of birth, and admission date and time to start the hospitalization.

- **all-patients.html**: Displays a table with all registered patients.

- **patient-profile.html**: Displays the patient's profile, including full name, patient ID, gender, age, date of birth, allergies and restrictions. Information about hospitalization includes condition, diagnosis date, severity of the condition, medication, admission date and time, and projected discharge date. Contact information includes address and phone number. Also provides a history of previous hospitalizations.

- **patient-search.html**: Displays the results of the search for patients.

- **edit-patient.html**: Allows editing of the patient's personal and hospitalization information.

- **discharge-patient.html**: Displays a dynamic block that allows discharging the patient, including date and time for registration.

- **new-stay.html**: Displays a dynamic block that allows starting a new hospitalization, including date and time for registration.

- **user-profile.html**: Displays the user's profile with full name, username, and job title.

- **account-settings.html**: Allows the user to edit their username, full name, job title, and link to the change password page.

- **change-password.html**: Allows users to change their passwords.

- **control-panel.html**: Displays the control panel for administrators, providing access to new account registration requests and the staff list.

- **registration-requests.html**: Displays a table with new account registration requests, allowing administrators to approve or delete the requests.

- **manage-staff.html**: "Displays a table with all employees, allowing administrators to access their profiles and delete their accounts.

- **confirm-deletion.html**: Displays a form requesting a password confirmation when administrators try to delete their own accounts.








