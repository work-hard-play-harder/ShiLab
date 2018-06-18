import os
import shlex
import subprocess

from EpiMap import app


def create_job_folder(upload_folder='', userid=None, jobid=None):
    # create user dir
    user_dir = os.path.join(upload_folder, '_'.join(['userid', str(userid)]))
    if not os.path.exists(user_dir):
        cmd_args = shlex.split('mkdir ' + user_dir)
        subprocess.Popen(cmd_args).wait()

    # create job dir
    job_dir = os.path.join(user_dir, '_'.join(['jobid', str(jobid)]))
    if not os.path.exists(job_dir):
        cmd_args = shlex.split('mkdir ' + job_dir)
        subprocess.Popen(cmd_args).wait()

    return job_dir


def call_scripts(methods, params=None, job_dir='', x_filename='', y_filename=''):
    print(methods)
    for method in methods:
        print(method)
        if method == 'EBEN':
            with open(os.path.join(job_dir, 'EBEN.stdout'), 'w') as EBEN_stdout, \
                    open(os.path.join(job_dir, 'EBEN.stderr'), 'w') as EBEN_stderr:
                subprocess.Popen(['Rscript', app.config['EBEN_SCRIPT'], job_dir, x_filename, y_filename],
                                 stdout=EBEN_stdout,
                                 stderr=EBEN_stderr)

        if method == 'LASSO':
            with open(os.path.join(job_dir, 'LASSO.stdout'), 'w') as LASSO_stdout, \
                    open(os.path.join(job_dir, 'LASSO.stderr'), 'w') as LASSO_stderr:
                subprocess.Popen(
                    ['Rscript', app.config['LASSO_SCRIPT'], params['alpha'], job_dir, x_filename, y_filename],
                    stdout=LASSO_stdout,
                    stderr=LASSO_stderr)

        if method == 'Matrix_eQTL':
            with open(os.path.join(job_dir, 'Matrix_eQTL.R.stdout'), 'w') as Matrix_eQTL_stdout, \
                    open(os.path.join(job_dir, 'Matrix_eQTL.R.stderr'), 'w') as Matrix_eQTL_stderr:
                subprocess.Popen(['Rscript', app.config['MATRIX_EQTL_SCRIPT'], job_dir, x_filename, y_filename],
                                 stdout=Matrix_eQTL_stdout,
                                 stderr=Matrix_eQTL_stderr)
