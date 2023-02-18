from data import db_session
from data.logmessage import Log


def add_log(text, db_sess=None):
    if db_sess is None:
        new_session = True
        db_sess = db_session.create_session()
    else:
        new_session = False
    log = Log()
    log.message = text
    db_sess.add(log)
    while db_sess.query(Log).count() > 10000:
        first_log = db_sess.query(Log).first()
        db_sess.delete(first_log)
    db_sess.commit()
    # print(db_sess.query(Log).all())
    if new_session:
        db_sess.close()