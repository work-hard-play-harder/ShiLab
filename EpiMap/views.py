import os
import time
from EpiMap import app, db

# third-parties packages
from flask import render_template, request, redirect, url_for, flash, make_response, abort, send_file
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.utils import secure_filename
from bokeh.embed import components
from bokeh.resources import INLINE

# customized functions
from EpiMap.run_scripts import call_scripts, create_job_folder, check_job_status
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
        jobname = request.form['jobname']
        description = request.form['description']
        methods = request.form.getlist('methods')

        input_x = request.files['input-x']
        input_y = request.files['input-y']
        if input_x and input_y and is_allowed_file(input_x.filename) and is_allowed_file(input_y.filename):
            x_filename = secure_filename(input_x.filename)
            y_filename = secure_filename(input_y.filename)

            if x_filename == y_filename:
                flash("Training data have the same file name.")
                return redirect(request.url)

            if len(methods) == 0:
                flash("You must choose at least one method!")
                return redirect(request.url)

            job = Job(jobname=jobname, description=description, status=0, user_id=current_user.id)
            db.session.add(job)
            db.session.commit()
            job_dir = create_job_folder(app.config['UPLOAD_FOLDER'], userid=current_user.id, jobid=job.id)

            input_x.save(os.path.join(job_dir, x_filename))
            input_y.save(os.path.join(job_dir, y_filename))
            # flash("File has been upload!")
            params = {'alpha': '1'}
            call_scripts(methods, params, job_dir, x_filename, y_filename)
            return redirect(url_for('processing', jobid=job.id, methods=methods))
        else:
            flash("Only .txt and .csv file types are valid!")
    return render_template('webserver.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/processing/<jobid>/<methods>')
@login_required
def processing(jobid, methods):
    job = Job.query.filter_by(id=jobid).first_or_404()
    print('job.status',job.status)
    if job.status == 2:
        return redirect(url_for('result', jobid=job.id, methods=methods))
    else:
        check_job_status(jobid, methods)
        return render_template('processing.html', jobid=job.id, methods=methods)


@app.route('/result/<jobid>/<methods>')
@login_required
def result(jobid, methods):
    job_dir = os.path.join(app.config['UPLOAD_FOLDER'],
                           '_'.join(['userid', str(current_user.id)]),
                           '_'.join(['jobid', str(jobid)]))

    if not os.path.exists(job_dir):
        flash("Job doesn't exist!", category='error')
        return redirect(request.url)
    return render_template('result.html', jobid=jobid, job_dir=job_dir, methods=methods)


@app.route('/show_pic/<jobid>/<filename>')
@login_required
def show_pic(jobid, filename):
    job_dir = os.path.join(app.config['UPLOAD_FOLDER'],
                           '_'.join(['userid', str(current_user.id)]),
                           '_'.join(['jobid', str(jobid)]))
    if not os.path.exists(job_dir):
        flash("Job doesn't exist!", category='error')
        return redirect(request.url)

    try:
        return send_file(os.path.join(job_dir, filename), attachment_filename=filename)
    except Exception as e:
        return str(e)


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
        # time.sleep(5)
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
    print(jobs[0].timestamp)
    return render_template('jobs.html', jobs=jobs)


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
