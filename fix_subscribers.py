from data import db_session
from data.users import User

db_sess = db_session.create_session()

for user in db_sess.query(User).all():
    for other_user_id in user.subscribes:
        other_user = db_sess.query(User).filter(User.id == other_user_id).first()
        other_user.subscribers = list(other_user.subscribers) + [user.id]

db_sess.commit()
db_sess.close()

# TODO run this when push to server !!!!!
