import json
from data import db_session
from data.users import User
from data.problem import Problem
from data.post import Post
from data.solution import Solution
from data.comment import Comment


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
#
# Содержимое файлов tg_msg.json и vk_msg.json в папке bots_files
# это список словарей вида
# {"vk":id/"tg":id (в зависимости от бота, у каждого свой файл), "text":"...", "files":[список пар строк - названий файлов в папке static]}
# необходимо отправить сообщение челу с id (это id уже в вк или в tg)
# с текстом о ключу text и файлами, из списка названий
# (они лежат в папке static, например, [("1.png", "геома.png", ("2.txt", "инверсия.txt")] -> отправить файлы
# по адресу static/1.png и static/2.txt и сделать, чтобы пользователь получил их с названиями геома.png и инверсия.txt)


def extend_messages(obj, messenger):
    try:
        with open(f"bots_files/{messenger}_msg.json", "r", encoding="utf-8") as f:
            msg_list = json.load(f)
    except Exception as e:
        # print(e)
        msg_list = []
    msg_list.extend(obj)
    # print(msg_list)
    with open(f"bots_files/{messenger}_msg.json", "w", encoding="utf-8") as f:
        json.dump(msg_list, f)


def cut(text, size):
    if len(text) <= size:
        return text
    return text[:size] + "..."


def get_interested_users(publ, user, db_sess):
    res = set()
    if publ.user_id != user.id:
        res.add(publ.user_id)
    for comment in publ.comments:
        if comment.user_id != user.id:
            res.add(comment.user_id)  # check automatic interest!!!
    for like_user_id in publ.liked_by:
        if like_user_id != user.id:
            res.add(like_user_id)  # check automatic interest!!!

    if isinstance(publ, Problem):
        for solution in publ.solutions:
            if solution.user_id != user.id:
                res.add(solution.user_id)
            for like_user_id in solution.liked_by:
                if like_user_id != user.id:
                    res.add(like_user_id)
            for comment in solution.comments:
                if comment.user_id != user.id:
                    res.add(comment.user_id)
                for like_user_id in comment.liked_by:
                    if like_user_id != user.id:
                        res.add(like_user_id)

    readers = set(user.readers)
    subscribers = set(user.subscribers)

    res = res.union(readers).union(subscribers)

    result = []
    for interested_user_id in res:
        if interested_user_id in subscribers:
            result.append((db_sess.query(User).filter(User.id == interested_user_id).first(), "subscriber"))
        elif interested_user_id in readers:
            result.append((db_sess.query(User).filter(User.id == interested_user_id).first(), "reader"))
        else:
            result.append((db_sess.query(User).filter(User.id == interested_user_id).first(), "interested"))

    print(result)

    return result


def query_by_types(users, action_type, theme):
    res = []
    for (user, reason) in users:
        if reason == "interested":
            if action_type != "like" or user.wants_like:
                res.append(("interested", user))
        elif reason == "subscriber":
            res.append(("subscriber", user))
        elif reason == "reader":
            if action_type == "prob" and user.wants_prob \
                    or action_type == "post" and user.wants_post \
                    or action_type == "solu" and user.wants_solu \
                    or action_type == "comm" and user.wants_comm \
                    or action_type == "like" and user.wants_like \
                    or action_type == "true" and user.wants_true \
                    or action_type == "false" and user.wants_fals \
                    or action_type == "authorfalse" and user.wants_athf:
                if theme == "geom" and user.wants_geom or theme == "algt" and user.wants_algt or theme == "comb" and user.wants_comb:
                    res.append(("reader", user))
    return res


def get_files_list(publ):
    return [(file.filename(), file.name) for file in publ.files]


def get_message_dict(messenger, id, text, files):
    return {messenger: id, "text": text, "files": files}


def problem_added(problem_id):
    db_sess = db_session.create_session()
    problem = db_sess.query(Problem).filter(Problem.id == problem_id).first()
    author: User
    author = problem.user
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(problem, author, db_sess), "prob", problem.theme):
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.vk_id,
                                                f"Пользователь {author.name} разместил задачу:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem_id}",
                                                get_files_list(problem)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.tg_id,
                                                f"Пользователь {author.name} разместил задачу:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem_id}",
                                                get_files_list(problem)))

    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()


def post_added(post_id):
    db_sess = db_session.create_session()
    post = db_sess.query(Post).filter(Post.id == post_id).first()
    author: User
    author = post.user
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(post, author, db_sess), "post", post.theme):
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.vk_id,
                                                f"Пользователь {author.name} добавил заметку:\n{cut(post.content, 25)}\nge0math.ru/post/{post_id}",
                                                get_files_list(post)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.tg_id,
                                                f"Пользователь {author.name} добавил заметку:\n{cut(post.content, 25)}\nge0math.ru/post/{post_id}",
                                                get_files_list(post)))
    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()


def solution_added(solution_id):
    db_sess = db_session.create_session()
    solution = db_sess.query(Solution).filter(Solution.id == solution_id).first()
    problem = solution.problem
    author: User
    author = solution.user
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(problem, author, db_sess), "solu", solution.theme):
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.tg_id,
                                                f"Пользователь {author.name} добавил решение к задаче:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem.id}",
                                                get_files_list(problem)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.vk_id,
                                                f"Пользователь {author.name} добавил решение к задаче:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem.id}",
                                                get_files_list(problem)))
    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()


def comment_added(comment_id):
    print(121424)
    db_sess = db_session.create_session()
    comment = db_sess.query(Comment).filter(Comment.id == comment_id).first()
    if comment.problem is not None:
        name = "problem"
        publ = comment.problem
    if comment.post is not None:
        name = "post"
        publ = comment.post
    if comment.solution is not None:
        name = "problem"
        publ = comment.solution.problem
    author: User
    author = comment.user
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(publ, author, db_sess), "comm", comment.theme):
        print(user)
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.vk_id,
                                                f"Пользователь {author.name} комментирует:\n{cut(publ.content, 25)}\nge0math.ru/{name}/{publ.id}",
                                                get_files_list(publ)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.tg_id,
                                                f"Пользователь {author.name} комментирует:\n{cut(publ.content, 25)}\nge0math.ru/{name}/{publ.id}",
                                                get_files_list(publ)))
    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()


def like_under_problem_added(problem_id, actor_id):
    db_sess = db_session.create_session()
    problem = db_sess.query(Problem).filter(Problem.id == problem_id).first()
    author: User
    author = problem.user
    actor = db_sess.query(User).filter(User.id == actor_id).first()
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(problem, actor, db_sess), "like", problem.theme):
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.vk_id,
                                                f"Пользователь {actor.name} оценил {'вашу ' if author.id == user.id else ''}задачу:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem_id}",
                                                get_files_list(problem)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.tg_id,
                                                f"Пользователь {actor.name} оценил {'вашу ' if author.id == user.id else ''}задачу:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem_id}",
                                                get_files_list(problem)))

    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()


def like_under_post_added(post_id, actor_id):
    db_sess = db_session.create_session()
    post = db_sess.query(Post).filter(Post.id == post_id).first()
    author: User
    author = post.user
    actor = db_sess.query(User).filter(User.id == actor_id).first()
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(post, actor, db_sess), "like", post.theme):
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.vk_id,
                                                f"Пользователь {actor.name} оценил {'вашу ' if author.id == user.id else ''}заметку:\n{cut(post.content, 25)}\nge0math.ru/post/{post_id}",
                                                get_files_list(post)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.tg_id,
                                                f"Пользователь {actor.name} оценил {'вашу ' if author.id == user.id else ''}заметку:\n{cut(post.content, 25)}\nge0math.ru/post/{post_id}",
                                                get_files_list(post)))
    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()


def like_under_solution_added(solution_id, actor_id):
    db_sess = db_session.create_session()
    solution = db_sess.query(Solution).filter(Solution.id == solution_id).first()
    problem = solution.problem
    author: User
    author = solution.user
    actor = db_sess.query(User).filter(User.id == actor_id).first()
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(problem, actor, db_sess), "like", solution.theme):
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.vk_id,
                                                f"Пользователь {actor.name} оценил {'ваше ' if author.id == user.id else ''}решение к {'вашей ' if solution.problem.user.id == user.id else ''}задаче:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem.id}",
                                                get_files_list(problem)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.tg_id,
                                                f"Пользователь {actor.name} оценил {'ваше ' if author.id == user.id else ''}решение к {'вашей ' if solution.problem.user.id == user.id else ''}задаче:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem.id}",
                                                get_files_list(problem)))
    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()


def like_under_comment_added(comment_id, actor_id):
    db_sess = db_session.create_session()
    comment = db_sess.query(Comment).filter(Comment.id == comment_id).first()
    if comment.problem is not None:
        under = "problem"
        name = "problem"
        publ = comment.problem
    if comment.post is not None:
        under = "post"
        name = "post"
        publ = comment.post
    if comment.solution is not None:
        under = "solution"
        name = "problem"
        publ = comment.solution.problem
    author: User
    author = comment.user
    actor = db_sess.query(User).filter(User.id == actor_id).first()
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(publ, actor, db_sess), "comm", comment.theme):
        if under == "problem":
            text = f"к {'вашей ' if publ.user.id == user.id else ''}задаче"
        if under == "post":
            text = f"к {'вашей ' if publ.user.id == user.id else ''}заметке"
        if under == "solution":
            text = f"к {'вашему ' if comment.solution.user.id == user.id else ''}решению {'вашей ' if publ.user.id == user.id else ''}задачи"
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.vk_id,
                                                f"Пользователь {actor.name} оценил {'ваш ' if author.id == user.id else ''}комментарий {text}:\n{cut(publ.content, 25)}\nge0math.ru/{name}/{publ.id}",
                                                get_files_list(publ)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.tg_id,
                                                f"Пользователь {actor.name} оценил {'ваш ' if author.id == user.id else ''}комментарий {text}:\n{cut(publ.content, 25)}\nge0math.ru/{name}/{publ.id}",
                                                get_files_list(publ)))
    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()


def problem_true(problem_id, actor_id):
    db_sess = db_session.create_session()
    problem = db_sess.query(Problem).filter(Problem.id == problem_id).first()
    author: User
    author = problem.user
    actor = db_sess.query(User).filter(User.id == actor_id).first()
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(problem, actor, db_sess), "true", problem.theme):
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.vk_id,
                                                f"Пользователь {actor.name} считает {'вашу ' if author.id == user.id else ''}задачу верной:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem_id}",
                                                get_files_list(problem)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.tg_id,
                                                f"Пользователь {actor.name} считает {'вашу ' if author.id == user.id else ''}задачу верной:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem_id}",
                                                get_files_list(problem)))

    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()


def solution_true(solution_id, actor_id):
    db_sess = db_session.create_session()
    solution = db_sess.query(Solution).filter(Solution.id == solution_id).first()
    problem = solution.problem
    author: User
    author = solution.user
    actor = db_sess.query(User).filter(User.id == actor_id).first()
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(problem, actor, db_sess), "true", solution.theme):
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.vk_id,
                                                f"Пользователь {actor.name} считает {'ваше' if author.id == user.id else ''}решение к {'вашей ' if solution.problem.user.id == user.id else ''}задаче верным:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem.id}",
                                                get_files_list(problem)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.tg_id,
                                                f"Пользователь {actor.name} считает {'ваше' if author.id == user.id else ''}решение к {'вашей ' if solution.problem.user.id == user.id else ''}задаче верным:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem.id}",
                                                get_files_list(problem)))
    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()


def problem_false(problem_id, actor_id):
    db_sess = db_session.create_session()
    problem = db_sess.query(Problem).filter(Problem.id == problem_id).first()
    author: User
    author = problem.user
    actor = db_sess.query(User).filter(User.id == actor_id).first()
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(problem, actor, db_sess), "false", problem.theme):
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.vk_id,
                                                f"Пользователь {actor.name} считает {'вашу ' if author.id == user.id else ''}задачу неверной:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem_id}",
                                                get_files_list(problem)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.tg_id,
                                                f"Пользователь {actor.name} считает {'вашу ' if author.id == user.id else ''}задачу неверной:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem_id}",
                                                get_files_list(problem)))

    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()


def solution_false(solution_id, actor_id):
    db_sess = db_session.create_session()
    solution = db_sess.query(Solution).filter(Solution.id == solution_id).first()
    problem = solution.problem
    author: User
    author = solution.user
    actor = db_sess.query(User).filter(User.id == actor_id).first()
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(problem, actor, db_sess), "false", solution.theme):
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.vk_id,
                                                f"Пользователь {actor.name} считает {'ваше ' if author.id == user.id else ''}решение к {'вашей ' if solution.problem.user.id == user.id else ''}задаче неверным:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem.id}",
                                                get_files_list(problem)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.tg_id,
                                                f"Пользователь {actor.name} считает {'ваше ' if author.id == user.id else ''}решение к {'вашей ' if solution.problem.user.id == user.id else ''}задаче неверным:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem.id}",
                                                get_files_list(problem)))
    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()


def problem_author_false(problem_id):
    db_sess = db_session.create_session()
    problem = db_sess.query(Problem).filter(Problem.id == problem_id).first()
    author: User
    author = problem.user
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(problem, author, db_sess), "authorfalse", problem.theme):
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.vk_id,
                                                f"Пользователь {author.name} признал свою задачу неверной:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem_id}",
                                                get_files_list(problem)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.tg_id,
                                                f"Пользователь {author.name} признал свою задачу неверной:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem_id}",
                                                get_files_list(problem)))

    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()


def solution_author_false(solution_id):
    db_sess = db_session.create_session()
    solution = db_sess.query(Solution).filter(Solution.id == solution_id).first()
    problem = solution.problem
    author: User
    author = solution.user
    vk_messages = []
    tg_messages = []
    for reason, user in query_by_types(get_interested_users(problem, author, db_sess), "authorfalse", solution.theme):
        if user.vk_id != "":
            vk_messages.append(get_message_dict("vk", user.vk_id,
                                                f"Пользователь {author.name} признал своё решение к {'вашей' if solution.user.id == user.id else ''}задаче неверным:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem.id}",
                                                get_files_list(problem)))
        if user.tg_id != "":
            tg_messages.append(get_message_dict("tg", user.tg_id,
                                                f"Пользователь {author.name} признал своё решение к {'вашей' if solution.user.id == user.id else ''}задаче неверным:\n{cut(problem.content, 25)}\nge0math.ru/problem/{problem.id}",
                                                get_files_list(problem)))
    extend_messages(vk_messages, "vk")
    extend_messages(tg_messages, "tg")
    db_sess.close()
