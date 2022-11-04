import os
basedir = os.path.abspath(os.path.dirname(__file__))


print(os.environ.get('DATABASE_URL'))

if os.environ.get('DATABASE_URL') is None:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db/blogs.db') + "?check_same_thread=False"
    print(SQLALCHEMY_DATABASE_URI)
else:
    SQLALCHEMY_DATABASE_URI = f'postgresql{os.environ["DATABASE_URL"].strip()[8:]}' + "?check_same_thread=False"

# SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db')