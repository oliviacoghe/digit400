from flask import Flask, render_template, url_for, flash, redirect, request, session, make_response, send_file
from datetime import datetime, timedelta 
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from passlib.hash import sha256_crypt
from pymysql import escape_string as thwart
import gc
from functools import wraps 
from werkzeug.utils import secure_filename 
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from google_images_download import google_images_download
from google_img_lib import image_fetcher
import random
import pickle

from db_connect import connection 
from database import database 

#sys.executable("/var/www/FlaskApp/FlaskApp/google_img_lib.py")
UPLOADS_FOLDER = '/var/www/FlaskApp/FlaskApp/uploads'
ALLOWED_EXTENSIONS = set(["txt", "pdf", "png", "jpeg", "jpg", "gif"])
app = Flask(__name__)
app.config["UPLOADS_FOLDER"] = UPLOADS_FOLDER

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("Please login.")
            return redirect(url_for('login'))
    return wrap

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS 
    
# CMS Structure title, path, message
APP_CONTENT = {
    "Home":[["My Home","/","Welcome back! see what new stories are available for you."],["Gallery","/googleimg/","Explore the gallery and discover what you want to learn next."],["Forum","/forum/","Interact with other members of Approachable Art!"]], 
    
    "Profile":[["User Profile","/userprofile/","Edit your profile here!"],["Photo Upload", "/uploads/", "Upload your user profile photo here."],["Contact Us", "/contact/","Reach out and let us know whats up!"],],
    
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
        return(str(e)) 
    
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
                
                flash("You are now logged in " + session['username'])
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
    session.clear()
    flash("You have been logged out!")
    gc.collect()
    return redirect(url_for("login"))



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
    
@app.route("/uploads/", methods =["GET", "POST"])
@login_required
def upload_file():
    try:
        if request.method == "POST":
            if 'file' not in request.files: 
                flash('Incomplete filename. Please add valid file type suffix.')
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                flash("incomplete filename. Please add valid filename.")
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename) 
                file.save(os.path.join(app.config["UPLOADS_FOLDER"], filename))
                database(session['username'], filename)
                flash("File upload successful.")
                return render_template("uploads.html", filename = filename)
            else:
                flash("Invalid file type. Please add valid filename.")
                return redirect(request.url)
        return render_template("uploads.html")
    except Exception as e:
        return(str(e))
@app.route("/download/")
@login_required
def download():
    try:
        return send_file('/var/www/FlaskApp/FlaskApp/uploads/screencap.png', attachment_filename="screencap.png")
    except Exception as e:
        return(str(e)) 
    
@app.route("/downloader/", methods=["GET","POST"])
@login_required
def downloader():
    error = ''
    try:
        if request.method == "POST":
            filename = request.form['filename']
            return send_file('/var/www/FlaskApp/FlaskApp/uploads/'+filename, attachment_filename='download')
        return render_template('downloader.html', error = error)
    
    except Exception as e:
        return(str(e)) 


@app.route("/googleimg/", methods =["GET", "POST"])
def img_fetch():
    error = ''
    artist_name = ''
    file_list = []
    try:
        if request.method == "POST":
            artist_name = request.form['arguments']
            file_names = image_fetcher(artist_name) #need to add permissions for google library here
            
            vis_path = '/var/www/FlaskApp/FlaskApp/static/downloads/'+artist_name
        
            for paths, subdirs, files in os.walk(vis_path):
                for file in files:
                    a = os.path.join(file)
                    file_list.append(a)
            return render_template('googleimg.html', error=error, file_list=file_list, artist_name=artist_name)
        
        return render_template('googleimg.html', error=error,file_list=file_list, artist_name=artist_name)
            
    except Exception as e:
        return(str(e)) 
    
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
    
@app.route("/Baroque/")
def Baroque():
    try:
        return render_template("Baroque.html")
    except Exception as e:
        return render_template("500.html", error = e)
    
@app.route("/VincentVanGogh/")
def VincentVanGogh():
    try:
        return render_template("VincentVanGogh.html")
    except Exception as e:
        return render_template("500.html", error = e)

@app.route("/random/")
def random():
    import random
    pages = ['cubism','Baroque', 'VincentVanGogh']
    choice_page = random.choice(pages)
    return redirect(url_for(choice_page))

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
