from flask import Flask, redirect, url_for, request, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
# For how long you want your session to last
from datetime import timedelta, datetime

app = Flask(__name__)
# Key for session
app.secret_key = "Key"
# Db for users
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_BINDS'] = {
    'todo': 'sqlite:///todo.db'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# For how long you want your session to last
app.permanent_session_lifetime = timedelta(minutes=5)


db = SQLAlchemy(app)


class users(db.Model):
    _id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    email = db.Column(db.String(200), unique=True)

    # Default constructor
    def __init__(self, name, password, email):
        # Sets them to the things when called
        self.name = name
        self.password = password
        self.email = email


class Todo(db.Model):
    __bind_keys__ = 'todo'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(10000), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    poster = db.Column(db.String(100))

    def __repr__(self):
        return '<Task %r>' % self.id


@app.route("/tasks", methods=['POST', 'GET'])
def task():
    if "user" in session and "pw" in session:
        # Checks if the call to the site was from POST
        if request.method == 'POST':
            # Logic for stuff
            task_content = request.form['content']
            # Creates a new task from input form
            new_task = Todo(content=task_content, poster=session["user"])
            # Tries to push data to database and redirects back into our index page
            db.session.add(new_task)
            db.session.commit()
            return redirect("/tasks")
        # Just displays all tasks on template
        else:
            tasks = Todo.query.order_by(Todo.date_created).all()
            return render_template("tasks.html", tasks=tasks)
    else:
        flash("Sign in to see your todo list")
        return redirect(url_for("login"))


@app.route('/delete/<int:id>')
def delete(id):
    # Gets the id or else it provides a 404 error
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect("/tasks")
    except:
        return "There was a problem deleting that task."


@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['content']

        try:
            db.session.commit()
            return redirect("/tasks")
        except:
            return 'There was an error updating your task.'
    else:
        return render_template("update.html", task=task)


@app.route('/login', methods=['POST', 'GET'])
def login():
    # Checks if submit was post
    if request.method == 'POST':
        # Sets it to permenant for as long the time you implemented at line 7
        session.permanent = True
        user = request.form['nm']
        pw = request.form['pw']

        # Keynotes:
        # users = name of our model (database)
        # query = performs the query
        # filter_by() = Finds all the things that meet the specific criteria
        # name=user = We want to find the thing where name is equal to user
        # first() = grabs the first entry
        found_user = users.query.filter_by(name=user, password=pw).first()
        if found_user:
            session["user"] = user
            session["pw"] = pw
            # Gets the email from users db
            session["email"] = found_user.email
        else:
            # Creates the user, then adds it to the database with the email blank
            #usr = users(user, pw, None)
            # db.session.add(usr)
            # Everytime you make a change in your db, you need to commit it.
            # db.session.commit()
            flash("Incorrect Name or Password")
            return redirect(url_for("login"))

        flash("Login Successful!")
        return redirect(url_for('user'))
    # Else, you didn't do anything yet, and it's just the normal page
    else:
        if "user" in session:
            flash("Already Logged in!")
            return redirect(url_for("user"))
        return render_template("login.html")


@app.route("/signup", methods=["POST", 'GET'])
def signup():
    if request.method == "POST":
        session.permanent = True
        user = request.form["nm"]
        # Checks if passwords match
        if request.form['pw'] != request.form['confirm_pw']:
            flash("The Passwords don't match")
            return redirect(url_for("signup"))
        else:
            password = request.form['pw']

        email = request.form['email']
        # Checks if account already exists with that username or email
        taken_email = users.query.filter_by(email=email).first()
        taken_user = users.query.filter_by(name=user).first()
        if taken_user:
            flash("The username has already been taken")
            return redirect(url_for("signup"))
        elif taken_email:
            flash("The email has already been taken.")
            return redirect(url_for("signup"))
        else:
            new_usr = users(user, password, email)
            db.session.add(new_usr)
            db.session.commit()
        session['user'] = user
        session['pw'] = password
        session['email'] = email
        flash("Account Created!")
        return redirect(("/user"))

    else:
        return render_template("signup.html")

# Displays all users


@app.route("/view")
def view():
    # gets all users and passes them as obj
    return render_template("view.html", values=users.query.all())


@app.route('/user', methods=["POST", 'GET'])
def user():
    email = None
    # Checks if User is in session
    if "user" in session and "pw" in session:
        user = session["user"]
        password = session["pw"]

        # Checks if /user was a POST connection (If email was added)
        if request.method == "POST":
            # Pulls the email from the form
            email = request.form["email"]
            # Stores email into a session
            session["email"] = email
            # Gets the query from db
            found_user = users.query.filter_by(
                name=user, password=password).first()
            # sets the found_user's email to email
            found_user.email = email
            # Commits the email
            db.session.commit()
            flash("Email was saved!")
        else:
            if "email" in session:
                email = session['email']
        # For {{}} tags in the HTML, you need to specify what user equals
        return render_template("user.html", email=email, user=user)
    # Else, just redirects to login
    else:
        flash("You are not logged in")
        return redirect(url_for('login'))


# Work in progress
@app.route("/updateMail", methods=["POST", "GET"])
def updateMail():
    if request.method == "POST":
        if 'pw' in session and 'user' in session:
            user = session["user"]
            password = session['pw']
            if request.method == 'POST':
                new_email = request.form["newemail"]
                session["email"] = new_email
                target_user = users.query.filter_by(
                    name=user, password=password).first()
                valid_email = users.query.filter_by(email=new_email).first()
                if valid_email:
                    flash("This email is already taken")
                    return redirect(url_for("updateMail"))
                target_user.email = new_email
                db.session.commit()
                flash("Email has been updated.")
                return redirect(url_for("user"))
    else:
        return render_template("updateemail.html")


@app.route("/logout")
def logout():
    # Checks if user is in session
    if "user" in session:
        user = session["user"]
        # Flashes message on logout
        flash(f"You have been logged out, {user}!", "info")
    # Removes user data from session
    session.pop("user", None)
    session.pop("email", None)
    session.pop("pw", None)
    # Redirects back to login
    return redirect(url_for("login"))


@app.route('/')
def index():
    return render_template("home.html")


if __name__ == '__main__':

    # Creates all databases, Make sure this is above app.run()
    db.create_all()
    app.run(debug=True)
