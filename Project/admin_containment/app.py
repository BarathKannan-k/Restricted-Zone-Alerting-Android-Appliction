# import statements
from __future__ import print_function

import json

# from jinja2.utils import select_auto escape
import bcrypt
from flask import *
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flaskext.mysql import MySQL

# initialization
app = Flask(__name__)

# config
app.secret_key = "\x19Ts\xbe\xe7\x8c_\r\x12Q\x14\x13>q\xb7'WTH0\x9f\xe4\xec\xb1"
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'zone2'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'

mysql = MySQL(app)


def init_db():
    signup_connection = mysql.connect()
    signup_cursor = signup_connection.cursor()
    try:
        signup_cursor.execute("CREATE DATABASE zone2")
    except:
        print("skipping db creation")
    user = """
    CREATE TABLE users(
    id integer AUTO_INCREMENT primary key,
    user_name TEXT,
    user_email TEXT,
    user_password TEXT,
    user_type TEXT
    )
    """
    try:
        signup_cursor.execute(user)
    except:
        print("skipping user table creation")
    user_loc = """
    CREATE TABLE user_location(
    id integer AUTO_INCREMENT primary key,
    location_lat TEXT,
    location_long TEXT,
    user_id INTEGER,
    timestamp TEXT)
    """
    try:
        signup_cursor.execute(user_loc)
    except:
        print("skipping user_location table creation")


    loc = """
    CREATE TABLE location(
    id integer AUTO_INCREMENT primary key,
    location_lat TEXT,
    location_long TEXT,
    location_visited INTEGER)
    """
    try:
        signup_cursor.execute(loc)
    except:
        print("skipping location table creation")


init_db()


# functions
def send_mail(email):
    # Email details
    sender_email = "19p208@kce.ac.in"
    receiver_email = email
    password = "tajzibejpjerrblz"
    subject = "caution"

    # Creating message object
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Name"] = "Please Stay Safe"
    message["Subject"] = subject

    # Create the HTML content
    html = """<h2>You are entering into a containment Zone</h2>"""

    # Attach the HTML content to the email message
    part = MIMEText(html, "html")
    message.attach(part)

    # Creating SMTP session
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(sender_email, password)

    # Sending email
    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)

    # Closing SMTP session
    server.quit()


def create_bcrypt_hash(password):
    # convert the string to bytes
    password_bytes = password.encode()
    # generate a salt
    salt = bcrypt.gensalt(14)
    # calculate a hash as bytes
    password_hash_bytes = bcrypt.hashpw(password_bytes, salt)
    # decode bytes to a string
    password_hash_str = password_hash_bytes.decode()
    return password_hash_str


def verify_password(password, hash_from_database):
    password_bytes = password.encode()
    hash_bytes = hash_from_database.encode()

    # this will automatically retrieve the salt from the hash,
    # then combine it with the password (parameter 1)
    # and then hash that, and compare it to the user's hash
    does_match = bcrypt.checkpw(password_bytes, hash_bytes)

    return does_match


# Api's


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        # get the data from the form
        password = request.form['password']
        email = request.form['email']

        # initialize the cursor
        signup_connection = mysql.connect()
        signup_cursor = signup_connection.cursor()

        # check whether user already exists
        user_result = signup_cursor.execute(
            "SELECT * FROM USERS WHERE user_email=%s", [email]
        )

        if (user_result > 0):
            data = signup_cursor.fetchone()
            data_password = data[3]
            if (verify_password(password, data_password)):
                signup_cursor.close()
                session['id'] = data[0]
                session['name'] = data[1]
                session['email'] = data[2]
                return redirect(url_for("home"))
            else:
                return render_template('login.html', error=1)
        else:
            return render_template('login.html', error=2)
    return render_template('login.html', error=3)


@app.route("/signup", methods=["POST", "GET"])
def signup():
    if (request.method == "POST"):

        # get the data from the form
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # hash the password
        pw_hash = create_bcrypt_hash(password)

        # initialize the cursor
        signup_connection = mysql.connect()
        signup_cursor = signup_connection.cursor()

        # check whether user already exists
        user_result = signup_cursor.execute(
            "SELECT * FROM USERS WHERE user_email=%s", [email]
        )
        if user_result > 0:
            signup_cursor.close()
            return render_template('signup.html', error=True)
        else:
            # execute the query
            signup_cursor.execute(
                'INSERT INTO USERS(user_name,user_email,user_password,user_type) VALUES(%s,%s,%s,%s)', (
                    name, email, str(pw_hash), "2"
                )
            )

            signup_connection.commit()
            signup_cursor.close()
            return redirect(url_for('login'))

    return render_template('signup.html', error=False)


@app.route("/home", methods=["POST", "GET"])
def home():
    if (session['id'] == None):
        return redirect(url_for('login'))

    if (request.method == "POST"):
        # get data
        lat = request.form["lat"]
        lon = request.form["lon"]
        vis = 0
        if (lat == "" or lon == ""):
            return render_template('home.html', name=session['name'], email=session['email'], id=session['id'],
                                   success=0)

        # create a location cursor
        location_connection = mysql.connect()
        location_cursor = location_connection.cursor()

        # Execute the query
        location_cursor.execute(
            'INSERT INTO LOCATION(location_lat,location_long,location_visited) VALUES(%s,%s,%s)', (
                lat, lon, vis
            )
        )
        location_connection.commit()
        location_cursor.close()
        return render_template('home.html', name=session['name'], email=session['email'], id=session['id'],
                               success=True)
    return render_template('home.html', name=session['name'], email=session['email'], id=session['id'])


@app.route("/logout")
def logout():
    # remove the username from the session if it is there
    session['id'] = None
    session['name'] = None
    session['email'] = None
    return redirect(url_for('login'))


@app.route("/data")
def data():
    if (session['id'] == None):
        return redirect(url_for('login'))

    location_connection = mysql.connect()
    location_cursor = location_connection.cursor()

    # check whether user already exists
    user_result = location_cursor.execute(
        "SELECT * FROM LOCATION"
    )
    if (user_result == 0):
        return render_template("data.html", responses=0)
    else:
        res = location_cursor.fetchall()
        print(res)
        return render_template("data.html", responses=res)


@app.route("/android_sign_up", methods=["POST"])
def upload():
    if (request.method == "POST"):

        # get the data from the form
        name = request.json['name']
        email = request.json['email']
        password = request.json['password']

        # hash the password
        pw_hash = create_bcrypt_hash(password)

        # initialize the cursor
        signup_connection = mysql.connect()
        signup_cursor = signup_connection.cursor()

        # check whether user already exists
        user_result = signup_cursor.execute(
            "SELECT * FROM USERS WHERE user_email=%s", [email]
        )
        if user_result > 0:
            signup_cursor.close()
            return {'status': 'failure'}
        else:
            # execute the query
            signup_cursor.execute(
                'INSERT INTO USERS(user_name,user_email,user_password,user_type) VALUES(%s,%s,%s,%s)', (
                    name, email, str(pw_hash), "1"
                )
            )

            signup_connection.commit()
            id_result = signup_cursor.execute(
                'SELECT id FROM USERS WHERE user_email = %s', [email]
            )
            if id_result > 0:
                id = signup_cursor.fetchone()
                signup_cursor.close()
                return {"id": id[0]}
            else:
                return {"status": "failure"}


@app.route("/get_all_users")
def getusers():
    signup_cursor = mysql.connect().cursor()

    # check whether user already exists
    user_result = signup_cursor.execute(
        "SELECT * FROM USERS"
    )
    if user_result > 0:
        rv = signup_cursor.fetchall()
        row_headers = [x[0] for x in signup_cursor.description]
        json_data = []
        for result in rv:
            json_data.append(dict(zip(row_headers, result)))
        return json.dumps(json_data)


@app.route("/post_user_location_data", methods=["POST"])
def post_user_location():
    if request.method == "POST":
        # get the data from the form
        lat = round(float(request.json['lat']), 2)
        lon = round(float(request.json['long']), 2)
        id = request.json['id']
        ts = request.json['timestamp']

        # initialize the cursor
        user_location_connection = mysql.connect()
        user_location_cursor = user_location_connection.cursor()

        # execute the query
        user_location_cursor.execute(
            'INSERT INTO USER_LOCATION(location_lat,location_long,user_id,timestamp) VALUES(%s,%s,%s,%s)', (
                lat, lon, id, ts
            )
        )

        user_location_connection.commit()

        return {"response": "success"}


@app.route("/location_data")
def location_data():
    location_connection = mysql.connect()
    location_cursor = location_connection.cursor()

    # check whether user already exists
    user_result = location_cursor.execute(
        "SELECT * FROM LOCATION"
    )
    if (user_result != 0):
        res = location_cursor.fetchall()
        print(res)
        row_headers = [x[0] for x in location_cursor.description]
        json_data = []
        for result in res:
            json_data.append(dict(zip(row_headers, result)))
        return json.dumps(json_data)
    else:
        return {"response": "failure"}


@app.route("/send_trigger", methods=["POST"])
def send_trigger():
    if (request.method == "POST"):
        # get the data from the form
        email = request.json['email']
        location_id = request.json['id']
        location_connection = mysql.connect()
        location_cursor = location_connection.cursor()

        # check whether user already exists
        user_result = location_cursor.execute(
            "SELECT location_visited FROM LOCATION WHERE id=%s", [
                location_id]
        )
        if (user_result == 0):
            return {"response": "failure"}
        else:
            res = location_cursor.fetchone()
            print(res[0])
            visited = res[0]
            visited = visited + 1
            location_cursor.execute(
                "UPDATE LOCATION SET location_visited = %s WHERE id=%s",
                (visited, location_id)
            )
            location_connection.commit()

        send_mail(email)
        return {"response": "success"}


# main
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
