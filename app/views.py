# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

# Python modules
import os, logging 

# Flask modules
from flask               import render_template, request, url_for, redirect, send_from_directory, flash
from flask_login         import login_user, logout_user, current_user, login_required
from werkzeug.exceptions import HTTPException, NotFound, abort
from werkzeug.utils      import secure_filename


# App modules
from app        import app, lm, db, bc
from app.models import User
from app.forms  import LoginForm, RegisterForm

# private imports
from .ml_logic.data_reading import data_handling
from .ml_logic.visualization import bokeh

# visualization
from bokeh.embed import components
from bokeh.plotting import figure


# File upload config
UPLOAD_FOLDER = 'user_data'
ALLOWED_EXTENSIONS = {'csv', 'CSV'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# provide login manager with load_user callback
@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Logout user
@app.route('/logout.html')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Register a new user
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    
    # declare the Registration Form
    form = RegisterForm(request.form)

    msg = None

    if request.method == 'GET': 

        return render_template( 'pages/register.html', form=form, msg=msg )

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 
        email    = request.form.get('email'   , '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        # filter User out of database through username
        user_by_email = User.query.filter_by(email=email).first()

        if user or user_by_email:
            msg = 'Error: User exists!'
        
        else:         

            pw_hash = password #bc.generate_password_hash(password)

            user = User(username, email, pw_hash)

            user.save()

            msg = 'User created, please <a href="' + url_for('login') + '">login</a>'     

    else:
        msg = 'Input error'     

    return render_template( 'pages/register.html', form=form, msg=msg )

# Authenticate user
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    
    # Declare the login form
    form = LoginForm(request.form)

    # Flask message injected into the page, in case of any errors
    msg = None

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        if user:
            #if bc.check_password_hash(user.password, password):
            if user.password == password:
                login_user(user)
                return redirect(url_for('index'))
            else:
                msg = "Wrong password. Please try again."
        else:
            msg = "Unknown user"

    return render_template( 'pages/login.html', form=form, msg=msg )

# Authenticate user
@app.route('/visualization.html', methods=[ 'GET','POST'])
def visualize_data():
    
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    file_url = None
    msg = None
    feature_names = ["SepalLengthCm","SepalWidthCm","PetalLengthCm","PetalWidthCm"]
    # print(request.files)
    if 'input_data_file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    input_file_path = request.files['input_data_file']#form.get('input_data_file', '', type=str)
        # password = request.form.get('password', '', type=str) 
    if input_file_path.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if input_file_path and allowed_file(input_file_path.filename):
        filename = secure_filename(input_file_path.filename)
        file_url = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        input_file_path.save(file_url)
        msg = "loaded input file"
    else:
        msg = "unable to load input file"


    data_handle = data_handling.LoadData()
    input_df = data_handle.get_df(file_url)

    current_feature_name = request.args.get("feature_name")

    if current_feature_name == None:
        current_feature_name = "SepalLengthCm"

    # bokeh_obj = bokeh.Bokeh()
    # fig1 = bokeh_obj.create_figure(input_df, current_feature_name, 10)
    # script1, div1 = components(fig1)
    plot = figure()
    plot.circle([1,2], [3,4])
    script1, div1 = components(plot)

   
    return render_template( 'ml_pages/visualization.html', script=script1, div=div1, feature_names=feature_names,  current_feature_name=current_feature_name)



# App main route + generic routing
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path>')
def index(path):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    content = None

    try:

        # try to match the pages defined in -> pages/<input file>
        return render_template( 'pages/'+path )
    
    except:
        
        return render_template( 'ml_pages/'+path )

        return render_template( 'pages/error-404.html' )

# Return sitemap 
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sitemap.xml')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS