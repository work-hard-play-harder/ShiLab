import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'R\xb7\xff\xfc\x1a\x94\xd3\xfa\xce\x1e\x1az+J!\xdfW\xf7k\x9br\xd9?\xc5'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # for upload file
    UPLOAD_FOLDER = os.path.join(basedir, 'EpiMap','upload_data')
    ALLOWED_EXTENSIONS = set(['txt', 'csv'])

    # for run scripts
    EBEN_SCRIPT = os.path.join(basedir,'EpiMap','script','EBEN.R')
    LASSO_SCRIPT = os.path.join(basedir, 'EpiMap', 'script', 'lasso.R')
    MATRIX_EQTL_SCRIPT = os.path.join(basedir, 'EpiMap', 'script', 'Matrix_eQTL.R')
