import os
import time
from EpiMap import app, db

# third-parties packages
from flask import render_template, request, redirect, url_for, flash, make_response, abort
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.utils import secure_filename
from bokeh.embed import components
from bokeh.resources import INLINE

# customized functions
from EpiMap.run_scripts import call_scripts, create_job_folder
from EpiMap.create_boken_figure import create_pca_figure
from EpiMap.models import User, Job, Model
from EpiMap.safe_check import is_safe_url, is_allowed_file


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/webserver', methods=['GET', 'POST'])
@login_required
def webserver():
    if request.method == 'POST':
        # get jobname adn description
        jobname = request.form['jobname']
        description = request.form['description']

        input_x = request.files['input-x']
        input_y = request.files['input-y']
        if input_x and input_y and is_allowed_file(input_x.filename) and is_allowed_file(input_y.filename):
            input_x_filename = secure_filename(input_x.filename)
            input_y_filename = secure_filename(input_y.filename)

            if input_x_filename == input_y_filename:
                flash("Training data have the same file name.")
                return redirect(request.url)

            # get checkbox value
            methods = request.form.getlist('methods')

            if len(methods) == 0:
                flash("You must choose at least one method!")
                return redirect(request.url)

            job = Job(jobname=jobname, description=description, status=0, user_id=current_user.id)
            db.session.add(job)
            db.session.commit()

            # get user ip and system time
            job_dir = create_job_folder(app.config['UPLOAD_FOLDER'], userid=current_user.id, jobid=job.id)

            input_x.save(os.path.join(job_dir, input_x_filename))
            input_y.save(os.path.join(job_dir, input_y_filename))
            # flash("File has been upload!")

            call_scripts(methods, job_dir, input_x_filename, input_y_filename)
            return redirect(url_for('result', userid=current_user.id))
        else:
            flash("Only .txt and .csv file types are valid!")
    return render_template('webserver.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/pca', methods=['GET', 'POST'])
def pca():
    # prepare some data
    x = [1, 2, 3, 4, 5]
    y = [6, 7, 2, 4, 5]

    boken_figure = create_pca_figure(x, y)

    script, div = components(boken_figure)

    return render_template('pca.html',
                           plot_script=script,
                           plot_div=div,
                           js_resources=INLINE.render_js(),
                           css_resources=INLINE.render_css())

    # return render_template('pca.html', userID=userID, mpld3=mpld3.fig_to_html(fig))


@app.route('/result/<userid>', methods=['GET', 'POST'])
def result(userid):
    if request.method == 'GET':
        user_dir = os.path.join(app.config['UPLOAD_FOLDER'], '_'.join([userid, current_user.username]))
        result_file = os.path.join(user_dir, 'EBEN_result.txt')
        if os.path.isfile(result_file):
            result_lines = []
            with open(result_file) as infile:
                result_lines = infile.readlines()
            return render_template('result.html', userID=userid, result_lines=result_lines)
    return render_template('processing.html', userID=userid)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user is not None:
            flash(message='This Email has been registered. Please log in or use another email address.',
                  category='error')
            return redirect(url_for('signup'))
        user = User(username=request.form['username'], email=request.form['email'])
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        login_user(user)
        # flash(message='Successful! You will be redirected to Home page.', category='message')
        time.sleep(5)
        return redirect(url_for('index'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user is None or not user.check_password(request.form['password']):
            flash(message='Login Failed! Invalid Username or Password.', category='error')
            return redirect(url_for('login'))
        else:
            # login_user(user, remember=request.form['remember_me'])
            login_user(user)
            next = request.args.get('next')
            if not is_safe_url(next):
                return abort(400)
            return redirect(next or url_for('index'))

    return render_template('login.html', title='Login')


@app.route('/user/profile')
@login_required
def profile():
    user = User.query.filter_by(id=current_user.id).first_or_404()
    return render_template('profile.html', user=user)


@app.route('/user/jobs')
@login_required
def jobs():
    user = User.query.filter_by(id=current_user.id).first_or_404()
    jobs = user.jobs.all()
    return render_template('jobs.html', user=user, jobs=jobs)


@app.route('/repository/')
def repository():
    # user = User.query.filter_by(id=userid).first_or_404()
    # jobs = user.jobs.all()
    return render_template('jobs.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(error):
    resp = make_response(render_template('page_not_found.html'), 404)
    resp.headers['X-Something'] = 'A value'
    return resp
