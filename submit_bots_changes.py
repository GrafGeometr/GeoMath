import json
from data import db_session
from data.users import User


# Мы отправляем пользователю уведомление, если
#   действие совершил тот, читателем кого он является
#   или тот, подписчиком кого он является,
#   или действие совершено над публикацией пользователя
#   или над публикацией, в которой он заинтересован
# При этом действие может быть одного из видов:
#   добавление задачи, поста, решения, комментария, лайка, отметка верно, отметка неверно, признание неверным (признание - это когда это делает автор) - тип
#   геома, комба, алгебра и тч - тема
# Эти вещи пользователь может кастомизировать, т.е. выбирать,
# какие типы действий ему интересны и какие темы (если он заинтересован, то игнорим это)
# все эти настройки мы делаем в боте (типы и темы)
# можно в бота добавить автоматическую заинтересованность
# по желанию пользователя к задаче, которую он решил ...
#
# Поэтому изменения, которые боты отправляют сайту - это:
# {"user": {"vk":id, "tg":id - одно из них не указано в зависимости от бота, которому он это сказал},
# "type": <"type"/"theme">, "param": <"prob"/"post"/"solu"/"comm"/"like"/"true"/"false"/"authorfalse" - если это изменение типа,
# "geom"/"comb"/"algt" - если это изменение темы>} - означает,
# что пользователь из vk/tg с id=id
# изменил своё желание видеть уведомления темы/типа (который указан)
# Как именно будет реализован диалог с пользователем - на усмотрение того, кто пишет бота
# Файл bots_files/changes_in_db.json - это json со списком таких словарей.
# То, что сайт делает с бд, я сделаю сам


def submit_changes():
    try:
        with open("bots_files/changes_in_bd.json", "r") as file:
            list_of_changes = json.load(file)
            for change in list_of_changes:
                db_sess = db_session.create_session()
                user: User
                if change["user"].get("tg", None) is not None:  # tg user
                    user = db_sess.query(User).filter(User.tg_id == change["tg"]).first()
                if change["user"].get("vk", None) is not None:  # vk user
                    user = db_sess.query(User).filter(User.vk_id == change["vk"]).first()
                if user is not None:
                    if change["type"] == "type":
                        if change["param"] == "prob":
                            user.wants_prob = not user.wants_prob
                        if change["param"] == "post":
                            user.wants_post = not user.wants_post
                        if change["param"] == "solu":
                            user.wants_solu = not user.wants_solu
                        if change["param"] == "comm":
                            user.wants_comm = not user.wants_comm
                        if change["param"] == "like":
                            user.wants_like = not user.wants_like
                        if change["param"] == "false":
                            user.wants_fals = not user.wants_fals
                        if change["param"] == "true":
                            user.wants_true = not user.wants_true
                        if change["param"] == "authorfalse":
                            user.wants_athf = not user.wants_athf
                    if change["type"] == "theme":
                        if change["param"] == "geom":
                            user.wants_geom = not user.wants_geom
                        if change["param"] == "algt":
                            user.wants_algt = not user.wants_algt
                        if change["param"] == "comb":
                            user.wants_comb = not user.wants_comb
                db_sess.commit()
                db_sess.close()
    except Exception as e:
        with open("bots_files/changes_in_bd.json", "w") as file:
            file.write("[]")
