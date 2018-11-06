from flask import Flask, render_template, url_for, flash, redirect, request, session, make_response
from datetime import datetime, timedelta 
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
import gc
from functools import wraps 


from .db_connect import connection 
app = Flask(__name__)

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Please login.")
            return redirect(url_for('login'))
    return wrap
    
# CMS Structure title, path, message
APP_CONTENT = {
    "Home":[["Welcome","/welcome/","Welcome to my App, you can do many things here."],["Background","/about/","We had a lot of fun building this app. Learn more about our story"],["Messages","/messages/","Get your messages from the community!"]], 
    
    "Profile":[["User Profile","/userprofile/","Edit your profile here!"],["Terms of Service", "/tos/","The legal stuff!"],["Photo Upload", "/upload", "Upload your user profile photo here."],],
    
    "Contact":[["Conact us","/contact/","Get in touch, we would love to hear from you."],],
}

@app.route("/", methods = ["GET", "POST"])
def hello():
    try:
        c, conn = connection()
        if request.method == "POST":
            
            data = c.execute("SELECT * FROM users WHERE username = ('{0}')".format(thwart(request.form['username'])))
            
            data = c.fetchone()[2]
            
            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']
                
                flash("You are now logged in" + session['username'])
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid Credentials. Please Try Again."
                return render_template("login.html", error = error)
        else:
            return render_template("main.html")
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route("/welcome/")
@login_required
def templating():
    try:
        output =["DIGIT is good", "python, Java, php, SQL, C++","<p><strong>hello!</strong><P>",42, "42"]
        return render_template("templating_demo.html", output = output)
        
    except Exception as e:
        return(str(e)) #remove for production
    
@app.route("/login/", methods = ["GET", "POST"])
def login():    
    error = ""
    try:
        c, conn = connection()
        if request.method == "POST":
            
            data = c.execute("SELECT * FROM users WHERE username = ('{0}')".format(thwart(request.form['username'])))
            
            data = c.fetchone()[2]
            
            if sha256_crypt.verify(request.form['password'], data):
                session['logged_in'] = True
                session['username'] = request.form['username']
                
                flash("You are now logged in" + session['username'])
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid credentials. Try again!"
                return render_template("login.html", error = error)
        else:
            return render_template('login.html')
    
    except:
        return render_template("login.html", error = error)
    
@app.route("/logout/")
@login_required
def logout():
    sessoin.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for('main'))

class RegistrationForm(Form):
    username = TextField("Username", [validators.Length(min=4, max=20)])
    email = TextField("Email Address", [validators.Length(min=6, max=50)])
    password = PasswordField("New Password", [validators.Required(),
                                             validators.EqualTo("confirm", message="Password must match")])
    confirm = PasswordField("Repeat Password")
    accept_tos = BooleanField("I accept the Terms of Service and Privacy Notice", [validators.Required()])

    
@app.route("/register/", methods=["GET","POST"])
def register_page():
    try:
        form = RegistrationForm(request.form)
        if request.method == "POST" and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt((str(form.password.data)))

            c, conn = connection()

            x = c.execute("SELECT * FROM users WHERE username= ('{0}')".format((thwart(username))))

            if int(x) > 0:
                flash("That username is already taken, please choose another")
                return render_template("register.html", form = form)
            else:
                c.execute("INSERT INTO users(username, password, email, tracking) VALUES ('{0}','{1}','{2}','{3}')".format(thwart(username),thwart(password),thwart(email),thwart("/dashboard/")))

            conn.commit()
            flash("Thanks for registering!")
            c.close()
            conn.close()
            gc.collect()

            session['logged_in'] = True
            session['username'] = username

            return redirect(url_for("dashboard"))

        return render_template("register.html", form = form)
    except Exception as e:
        return(str(e))

@app.route("/dashboard/")
@login_required
def dashboard():
    try:
        return render_template("dashboard.html", APP_CONTENT = APP_CONTENT)
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route("/about/")
def about():
    try:
        return render_template("about.html")
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route("/cubism/")
def cubism():
    try:
        return render_template("cubism.html")
    except Exception as e:
        return render_template("500.html", error = e)

@app.route('/sitemap.xml/', methods=['GET'])
def sitemap():
    try:
        pages = []
        week = (datetime.now()- timedelta(days = 7)).date().isoformat()
        for rule in app.url_map.iter_rules():
            if "GET" in rule.methods and len(rule.arguments)==0:
                pages.append(["http://142.93.253.142" +str(rule.rule),week])
        sitemap_xml = render_template('sitemap_template.xml', pages = pages)
        response = make_response(sitemap_xml)
        response.headers["Content-Type"] = "application/xml"
        return response 
    
    except Exception as e:
        return(str(e))
    



@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

@app.errorhandler(405)
def method_not_allowed(e):
    return render_template("405.html")


@app.errorhandler(500)
def internal_server(e):
    return render_template("500.html", error = e)

if __name__ == "__main__":
	app.run()
