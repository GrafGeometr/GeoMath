# -*- coding: utf-8 -*-
import json
import math
import os
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from set_bot_message import *
from submit_bots_changes import submit_changes

from flask import Flask, render_template, redirect, request, make_response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import abort

from data import db_session
from data.category import Category
from data.codes import RegCode
from data.comment import Comment
from data.logmessage import Log
from data.post import Post
from data.problem import Problem
from data.solution import Solution
from data.users import User
from data.users_file import UsersFile
from db_location import SQLALCHEMY_DATABASE_URI
from forms.admin_message_form import AdminForm
from forms.commentaddform import CommentAddForm
from forms.fileform import FileAddForm
from forms.loginform import LoginForm
from forms.navform import NavForm
from forms.postaddform import PostAddForm
from forms.problemaddform import ProblemAddForm
from forms.problemeditform import ProblemEditForm
from forms.profileeditform import ProfileEditForm
from forms.registerform import RegisterForm
from forms.resetemailform import ResetEmailForm
from forms.solutionaddform import SolutionAddForm
from forms.verifyform import VerifyForm
from forms.simpleform import SimpleForm
from secret_code import generate_code

try:
    from email_secret_data import EMAIL, PASSWORD
except Exception:
    EMAIL = os.environ["EMAIL"]
    PASSWORD = os.environ["PASSWORD"]
    GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_EXTENSIONS'] = ['.txt', '.pdf', '.doc', '.docx', '.png', '.jpeg', '.jpg', '.gif']
login_manager = LoginManager()
login_manager.init_app(app)
basedir = os.path.abspath(os.curdir)


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


# ненужный гитхаб
"""def push_file_to_GitHub(filename):
    github = Github(GITHUB_TOKEN)
    repository = github.get_user().get_repo('Ge0MathStoarge')
    # create with commit message
    file_path = os.path.join(os.path.join(basedir, 'static'),
                             filename)  # FIX THIS WTF!!!
    with open(file_path, 'rb') as file:
        our_bytes = file.read()
        bytes_count = len(our_bytes)
        content = ' '.join(str(byte) for byte in our_bytes)
    try:
        f = repository.get_contents(f"{filename.split('.')[0]}.txt")
        repository.update_file(f"{filename.split('.')[0]}.txt", "some_file", f'{bytes_count}\n{content}', file.sha)
        # TODO проверить, что это работает
        add_log(f"Файл {filename} изменён в GitHub")
    except Exception as e:
        f = repository.create_file(f"{filename.split('.')[0]}.txt", "some_file", content=f'{bytes_count}\n{content}')
        add_log(f"Файл {filename} создан в GitHub")
def get_file_from_GitHub(filename):
    github = Github(GITHUB_TOKEN)
    repository = github.get_user().get_repo('Ge0MathStoarge')
    # path in the repository
    file_path = os.path.join(os.path.join(basedir, 'static'),
                             filename)
    try:
        name = f"{filename.split('.')[0]}.txt"
        f = repository.get_contents(name)
        with open(file_path, 'wb') as file:
            bytes_count_sts, *content = f.decoded_content.decode().split()
            our_bytes = bytearray(list(map(int, content)))
            file.write(our_bytes)
            add_log(f"Файл {filename} скачан с GitHub и сохранён в {file_path}")
    except Exception as e:
        add_log(f"Файл {filename} должен был быть скачан с GitHub, но что-то пошло не так: {e}")
        print(e)"""


def get_adminmessage():
    file_path = os.path.join(os.path.join(basedir, 'static'),
                             "adminmessage.txt")
    try:
        with open(file_path, 'r', encoding="utf-8") as f:
            message = f.read()
    except Exception as e:
        message = ''
    return message


def set_adminmessage(text):
    file_path = os.path.join(os.path.join(basedir, 'static'),
                             "adminmessage.txt")
    with open(file_path, 'w', encoding="utf-8") as f:
        f.write(text)
    add_log(f"Админское сообщение: \n{text}")
    # push_file_to_GitHub('adminmessage.txt')
    # add_log(f"Изменения в файле {file_path} сохранены в GitHub")


# @app.route('/jstest')
# def jstest():
#    return render_template("jstest.html")

# Выделяем теги из текста и преобразуем их в ссылки
def with_cats_show(text):
    res = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '#':
            j = 1
            teg = []
            while i + j < n:
                if text[i + j] in '#\n \t,;':
                    break
                teg.append(text[i + j])
                j += 1
            res.append(f"<a href='/***/***/год/{''.join(teg)}'>#{''.join(teg)}</a>")
            if i + j < n:
                res.append(text[i + j])
            i += j
        else:
            res.append(text[i])
            i += 1
    return ''.join(res)


# Проверяем, что у публикации категории в базе данных совпадают с теми, что в её тексте(заголовке, тексте, комментариях...)
def fix_cats(publ, db_sess):
    names = publ.get_needed_cats()
    publ_name = str(type(publ)) + str(publ.id)
    add_log(f"У публикации {publ_name} были теги {[teg.name for teg in publ.categories]}", db_sess=db_sess)
    for name in names:
        if not db_sess.query(Category).filter(Category.name == name).first():
            category = Category()
            category.name = name
            publ.categories.append(category)
        else:
            category = db_sess.query(Category).filter(Category.name == name).first()
            if category not in publ.categories:
                publ.categories.append(category)
    for category in publ.categories:
        if category.name not in names:
            publ.categories.remove(category)
    add_log(f"Теперь у публикации {publ_name} теги {[teg.name for teg in publ.categories]}", db_sess=db_sess)
    db_sess.commit()


@app.route('/show_last_logs')
def show_last_logs():
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел проникнуть в /show_last_logs")
        return redirect('/login/$show_last_logs')
    if current_user.status != 'администратор':
        add_log(f"Не администратор с id={current_user.id} пытался проникнуть в /show_last_logs")
        return redirect('/')
    # print(124)
    add_log(f"Администратор с id={current_user.id} решил посмотреть логи")
    # print(1356)
    db_sess = db_session.create_session()
    actions = db_sess.query(Log).all()[::-1]
    # print(actions)
    return render_template("showlogs.html", actions=actions)


@app.route('/admin_debug', methods=['POST', 'GET'])
def admin_debug():
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел проникнуть в /admin_debug")
        return redirect('/login/$admin_debug')
    if current_user.status != 'администратор':
        add_log(f"Не администратор с id={current_user.id} пытался проникнуть в /admin_debug")
        return redirect('/')
    form = AdminForm()
    if form.validate_on_submit():
        add_log(f"Администратор с id={current_user.id} в /admin_debug запустил код:\n{form.content.data}")
        exec(form.content.data)
        form.content.data = form.content.data
        return render_template('admindebug.html', title='Админская дичь', form=form,
                               admin_message=get_adminmessage())
    add_log(f"Администратор с id={current_user.id} зашёл в /admin_debug")
    return render_template('admindebug.html', title='Админская дичь', form=form,
                           admin_message=get_adminmessage())


@app.route('/admin_message', methods=['POST', 'GET'])
def change_admin_message():
    submit_changes()
    global admin_message
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел проникнуть в /admin_message")
        return redirect('/login/$admin_message')
    if current_user.status != 'администратор':
        add_log(f"Не администратор с id={current_user.id} хотел проникнуть в /admin_message")
        return redirect('/')
    form = AdminForm()
    if request.method == 'GET':
        add_log(f"Администратор с id={current_user.id} зашёл в /admin_message")
        form.content.data = get_adminmessage()
    if form.validate_on_submit():
        add_log(f"Администратор с id={current_user.id} изменяет сообщение на {form.content.data}")
        set_adminmessage(form.content.data)
        return redirect('/')
    return render_template('adminmessage.html', title='Сообщение администратора', form=form,
                           admin_message=get_adminmessage())


# Удаляем файлы, прикреплённые к чему-то и переходим по ссылке togo
@app.route('/delete_file/<int:file_id>/<togo>')
def delete_file(file_id, togo):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел удалить файл с id={file_id} и перейти по ссылке {togo}")
        return redirect(f'/login/delete_file${file_id}${togo}')
    db_sess = db_session.create_session()
    users_file = db_sess.query(UsersFile).filter(UsersFile.id == file_id).first()
    if users_file.user_id != current_user.id:
        add_log(f"Пользователь с id={current_user.id} пытался удалить чужой файл с id={users_file.id}")
        db_sess.commit()
        db_sess.close()
        return redirect(togo.replace('$', '/'))
    if users_file:
        add_log(
            f"Пользователь с id={current_user.id} удалил файл {users_file.name} с id={users_file.id} и перешёл по ссылке {togo}",
            db_sess=db_sess)
        db_sess.delete(users_file)
        db_sess.commit()
        db_sess.close()
    else:

        db_sess.close()
        add_log(f"Пользователь с id={current_user.id} хотел удалить файл с id={file_id}, но файл не нашёлся")
        abort(404)
    return redirect(togo.replace('$', '/'))


# Помощь
@app.route('/help')
def help_():
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел попасть в /help")
        return redirect('/login/$help')
    add_log(f"Пользователь с id={current_user.id} перешёл в помощь")
    return render_template('help.html', title="Помощь", with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Отправляем письмо по адресу to с кодом code
def send_email(to, code, message_type="register"):
    # Придумываем разный текст, чтобы Яндекс не заподозрил нас в рассылке
    if message_type == "register":
        text = random.choice([
            f'Вы только что зарегистрировались на нашем сайте, вот ваш код подтверждения:\n{code}. Введите его, а затем войдите.',
            f'Сообщаем об успешной регистрации на сайте ge0math, чтобы завершить её введите этот код и войдите на сайт с подтверждённой почтой:\n{code}',
            f'{code}\n Это код подтверждения, который мы отправили вам на почту для подтверждения вашей электронной почты на сайте ge0math. Введите его и войдите на сайт.',
            f'Ваш код подтверждения:\n{code}\n Введите его, чтобы подтвердить вашу электронную почту на сайте ge0math. После этого вы сможете войти на сайт.',
            f'Ваш код подтверждения:\n{code}\n Введите его, чтобы завершить регистрацию на сайте ge0math и получить возможность войти.'
        ])
    elif message_type == 'email_change':
        text = random.choice([
            f'Вы свою электронную почту на нашем сайте и указали {to}, если это вы, введите ваш код подтверждения:\n{code}',
            f'Сообщаем о смене почты на сайте ge0math на {to}. Чтобы подтвердить смену электронной почты, введите этот код:\n{code}',
            f'{code}\n Это код подтверждения, который мы отправили вам на почту для подтверждения смены вашей электронной почты на сайте ge0math.',
            f'Ваш код подтверждения:\n{code}\n Введите его, чтобы подтвердить смену электронной почты на сайте ge0math.',
        ])
    # Задаём параметры письма
    add_log(f"Отправляем письмо с темой '{message_type}' и содержанием: \n{text} \n на почту {to}")

    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = to
    if message_type == 'register':
        msg['Subject'] = 'Регистрация на сайте'
    elif message_type == 'email_change':
        msg['Subject'] = 'Смена электронной почты'
    message = text
    msg.attach(MIMEText(message))

    mailserver = smtplib.SMTP('smtp.yandex.ru', 587)
    mailserver.ehlo()
    mailserver.starttls()
    mailserver.ehlo()
    mailserver.login(EMAIL, PASSWORD)
    mailserver.sendmail(EMAIL, to, msg.as_string())
    mailserver.quit()


# Показываем задачи и решения пользователя, которые часть людей считают неверными
@login_required
@app.route('/wrong')
def wrong():
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел попасть в /wrong")
        return redirect('/login/$wrong')
    publs = []
    used = set()
    if current_user.wrong:
        db_sess = db_session.create_session()
        for name in current_user.wrong:
            if name not in used:
                used.add(name)
                publ_type, publ_id = name.split()
                if publ_type == 'solution':
                    solution = db_sess.query(Solution).filter(Solution.id == int(publ_id)).first()
                    publs.append(solution)
                else:
                    problem = db_sess.query(Problem).filter(Problem.id == int(publ_id)).first()
                    publs.append(problem)
    add_log(f"Пользователь с id={current_user.id} посмотрел неверные решения и задачи")
    return render_template("wrong.html", title='Неверные задачи и решения', Solution=Solution, Problem=Problem,
                           publications=publs[::-1], isinstance=isinstance, viewer=current_user,
                           with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Автор признал задачу(решение) неверной раньше, чем это сделали пользователи
@login_required
@app.route('/author_false/<name>/<int:publ_id>')
def author_false(name, publ_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(
            f"Неавторизованный пользователь хотел попасть в /author_false и сказать, что автор считает {name} {publ_id} неверным")
        return redirect(f'/login/$author_false${name}${publ_id}')
    db_sess = db_session.create_session()
    if name == "problem":
        publ = db_sess.query(Problem).filter(Problem.id == publ_id).first()
    else:
        publ = db_sess.query(Solution).filter(Solution.id == publ_id).first()
    if publ.user.id != current_user.id:
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id} хотел притвориться пользователем с id={publ.user.id} и сказать, что автор считает {name} {publ_id} неверным")
        abort(404)
    publ.author_thinks_false = True
    arr = list(current_user.wrong)
    print(f"{name} {publ_id}", arr)
    if f"{name} {publ_id}" in arr:
        arr.remove(f"{name} {publ_id}")
    current_user.wrong = arr
    db_sess.merge(current_user)
    if name == "post" or name == "problem":
        href = f"/{name}/{publ_id}"
    elif name == "solution":
        href = f"/problem/{publ.problem_id}"
    else:
        if publ.solution_id is not None:
            href = f"/problem/{publ.solution.problem_id}"
        elif publ.problem_id is not None:
            href = f"/problem/{publ.problem_id}"
        else:
            href = f"/post/{publ.post_id}"
    db_sess.commit()
    db_sess.close()
    add_log(f"Автор считает {name} {publ_id} неверным")
    if name == "problem":
        problem_author_false(publ_id)
    if name == "solution":
        solution_author_false(publ_id)
    return redirect(href)


# Проверяем, верная задача или нет
def check_truth(publ, db_sess):
    rank = sum(
        [db_sess.query(User).filter(User.id == user_id).first().get_rank() for user_id in list(publ.think_is_true)]) - \
           sum([db_sess.query(User).filter(User.id == user_id).first().get_rank() for user_id in
                list(publ.think_is_false)])
    if isinstance(publ, Problem):
        line = f'problem {publ.id}'
    else:
        line = f'solution {publ.id}'
    add_log(
        f"Разница в рейтинге {line} людей({list(publ.think_is_true)} и {list(publ.think_is_false)}), считающих, что это верно и что это неверно, равна {rank}",
        db_sess=db_sess)
    if rank < -400:
        publ.is_false = True
        publ.is_true = False
        add_log(f"{line} признано неверным",
                db_sess=db_sess)
    if -400 <= rank <= 400:
        publ.is_true = False
        publ.is_false = False
        add_log(f"{line} находится в зоне равновесия голосов",
                db_sess=db_sess)
    if rank > 400:
        publ.is_false = False
        publ.is_true = True
        add_log(f"{line} признано верным",
                db_sess=db_sess)
    arr = list(publ.user.wrong)
    if publ.is_false or publ.is_true or (not publ.think_is_false):
        if line in arr:
            arr.remove(line)
    elif publ.think_is_false:
        if line in arr:
            arr.remove(line)
        arr.append(line)
    publ.user.wrong = arr
    db_sess.commit()


# Человек нажал на кнопку неверно
@login_required
@app.route('/isfalse/<name>/<int:publ_id>/<int:user_id>')
def make_false(name, publ_id, user_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел попасть в /isfalse и сказать, что {name} {publ_id} неверно")
        return redirect(f'/login/$isfalse${name}${publ_id}$user_id')
    if user_id != current_user.id:
        add_log(
            f"Пользователь с id={current_user.id}!={user_id} хотел попасть в /isfalse и сказать, что {name} {publ_id} неверно")
        abort(404)
    flag = False
    db_sess = db_session.create_session()
    if name == "problem":
        problem = db_sess.query(Problem).filter(Problem.id == publ_id).first()
        if not problem:
            add_log(
                f"Пользователь с id={current_user.id} хотел сказать, что {name} {publ_id} неверно, но такой публикации не существует",
                db_sess=db_sess)
            abort(404)
        if user_id in problem.think_is_false:
            arr = list(problem.think_is_false)
            arr.remove(user_id)
            problem.think_is_false = arr
            add_log(f"Пользователь с id={current_user.id} передумал, что {name} {publ_id} неверно", db_sess=db_sess)
        else:
            if user_id in problem.think_is_true:
                add_log(
                    f"Пользователь с id={current_user.id} думал, что {name} {publ_id} верно и решил, что это неверно",
                    db_sess=db_sess)
                arr = list(problem.think_is_true)
                arr.remove(user_id)
                problem.think_is_true = arr
            problem.think_is_false = list(problem.think_is_false) + [user_id]
            add_log(f"Пользователь с id={current_user.id} считает {name} {publ_id} неверным", db_sess=db_sess)
            flag = True
        db_sess.commit()
        check_truth(problem, db_sess)
        db_sess.close()
        problem_false(publ_id, user_id)
        return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())
    else:
        solution = db_sess.query(Solution).filter(Solution.id == publ_id).first()
        if not solution:
            add_log(
                f"Пользователь с id={current_user.id} хотел сказать, что {name} {publ_id} неверно, но такой публикации не существует",
                db_sess=db_sess)
            abort(404)
        if user_id in solution.think_is_false:
            arr = list(solution.think_is_false)
            arr.remove(user_id)
            solution.think_is_false = arr
            add_log(f"Пользователь с id={current_user.id} передумал, что {name} {publ_id} неверно", db_sess=db_sess)
        else:
            if user_id in solution.think_is_true:
                add_log(
                    f"Пользователь с id={current_user.id} думал, что {name} {publ_id} верно и решил, что это неверно",
                    db_sess=db_sess)
                arr = list(solution.think_is_true)
                arr.remove(user_id)
                solution.think_is_true = arr
            solution.think_is_false = list(solution.think_is_false) + [user_id]
            add_log(f"Пользователь с id={current_user.id} считает {name} {publ_id} неверным", db_sess=db_sess)
            flag = True
        db_sess.commit()
        check_truth(solution, db_sess)
        db_sess.close()
        solution_false(publ_id, user_id)
        return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Человек нажал на кнопку верно
@login_required
@app.route('/istrue/<name>/<int:publ_id>/<int:user_id>')
def make_true(name, publ_id, user_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел попасть в /istrue и сказать, что {name} {publ_id} верно")
        return redirect(f'/login/$istrue${name}${publ_id}${user_id}')
    if user_id != current_user.id:
        add_log(
            f"Пользователь с id={current_user.id}!={user_id} хотел попасть в /istrue и сказать, что {name} {publ_id} верно")
        abort(404)
    flag = False
    db_sess = db_session.create_session()
    if name == "problem":
        problem = db_sess.query(Problem).filter(Problem.id == publ_id).first()
        if not problem:
            add_log(
                f"Пользователь с id={current_user.id} хотел сказать, что {name} {publ_id} верно, но такой публикации не существует",
                db_sess=db_sess)
            abort(404)
        if user_id in problem.think_is_true:
            arr = list(problem.think_is_true)
            arr.remove(user_id)
            problem.think_is_true = arr
            add_log(f"Пользователь с id={current_user.id} передумал, что {name} {publ_id} верно", db_sess=db_sess)
        else:
            if user_id in problem.think_is_false:
                arr = list(problem.think_is_false)
                arr.remove(user_id)
                problem.think_is_false = arr
                add_log(
                    f"Пользователь с id={current_user.id} думал, что {name} {publ_id} неверно и решил, что это верно",
                    db_sess=db_sess)
            problem.think_is_true = list(problem.think_is_true) + [user_id]
            add_log(f"Пользователь с id={current_user.id} считает {name} {publ_id} верным", db_sess=db_sess)
            flag = True
        db_sess.commit()
        check_truth(problem, db_sess)
        db_sess.close()
        if flag:
            problem_true(publ_id, user_id)
        return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())
    else:
        solution = db_sess.query(Solution).filter(Solution.id == publ_id).first()
        if not solution:
            add_log(
                f"Пользователь с id={current_user.id} хотел сказать, что {name} {publ_id} верно, но такой публикации не существует",
                db_sess=db_sess)
            abort(404)
        if user_id in solution.think_is_true:
            arr = list(solution.think_is_true)
            arr.remove(user_id)
            solution.think_is_true = arr
            add_log(f"Пользователь с id={current_user.id} передумал, что {name} {publ_id} верно", db_sess=db_sess)
        else:
            if user_id in solution.think_is_false:
                arr = list(solution.think_is_false)
                arr.remove(user_id)
                solution.think_is_false = arr
                add_log(
                    f"Пользователь с id={current_user.id} думал, что {name} {publ_id} неверно и решил, что это верно",
                    db_sess=db_sess)
            solution.think_is_true = list(solution.think_is_true) + [user_id]
            add_log(f"Пользователь с id={current_user.id} считает {name} {publ_id} верным", db_sess=db_sess)
        solution.is_true = not solution.is_true
        db_sess.commit()
        check_truth(solution, db_sess)
        db_sess.close()
        if flag:
            solution_true(publ_id, user_id)
        return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Подписка на кого-то
@login_required
@app.route('/subscribe/<int:user_id>/<int:viewer_id>')
def subscribe(user_id, viewer_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел стать подписчиком пользователя с id={user_id}")
        return redirect(f'/login/$subscribe${user_id}${viewer_id}')
    if viewer_id != current_user.id:
        add_log(f"Пользователь с id={current_user.id}!={viewer_id} хотел стать подписчиком пользователя с id={user_id}")
        abort(404)
    db_sess = db_session.create_session()
    viewer = db_sess.query(User).filter(User.id == viewer_id).first()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if viewer.subscribes:
        arr = list(viewer.subscribes)
        arr1 = list(user.subscribers)
        if user_id in arr:
            arr.remove(user_id)
            user.subscribers_count -= 1
            arr1.remove(viewer_id)
            add_log(
                f"Пользователь с id={current_user.id} перестал быть подписчиком пользователя с id={user_id}",
                db_sess=db_sess)
        else:
            arr.append(user_id)
            arr1.append(viewer_id)
            user.subscribers_count += 1
            add_log(
                f"Пользователь с id={current_user.id} стал подписчиком пользователя с id={user_id}",
                db_sess=db_sess)
        viewer.subscribes = arr
        user.subscribers = arr1
    else:
        viewer.subscribes = [user_id]
        user.subscribers_count += 1
        user.subscribers = [viewer_id]
        add_log(
            f"Пользователь с id={current_user.id} стал подписчиком пользователя с id={user_id}",
            db_sess=db_sess)
    db_sess.commit()
    db_sess.close()
    return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Пользователь стал постоянным читателем(теперь нужно автоматически добавлять его публикации пользователю)
@login_required
@app.route('/reader/<int:user_id>/<int:viewer_id>')
def become_reader(user_id, viewer_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел стать читателем пользователя с id={user_id}")
        return redirect(f'/login/$reader${user_id}${viewer_id}')
    if viewer_id != current_user.id:
        add_log(f"Пользователь с id={current_user.id}!={viewer_id} хотел стать читателем пользователя с id={user_id}")
        abort(404)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if user.readers:
        arr = list(user.readers)
        if viewer_id in arr:
            arr.remove(viewer_id)
            add_log(
                f"Пользователь с id={current_user.id} перестал быть читателем пользователя с id={user_id}",
                db_sess=db_sess)
        else:
            arr.append(viewer_id)
            add_log(
                f"Пользователь с id={current_user.id} стал читателем пользователя с id={user_id}",
                db_sess=db_sess)
        user.readers = arr
    else:
        user.readers = [viewer_id]
        add_log(
            f"Пользователь с id={current_user.id} стал читателем пользователя с id={user_id}",
            db_sess=db_sess)
    db_sess.commit()
    db_sess.close()
    return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Добавить к прочтению
@login_required
@app.route('/addtoread/<int:user_id>/<name>/<int:cont_id>')
def add_toread(user_id, name, cont_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел почитать {name} {cont_id} попозже")
        return redirect(f'/login/$addtoread${user_id}${name}${cont_id}')
    if user_id != current_user.id:
        add_log(f"Пользователь с id={current_user.id}!={user_id} хотел почитать {name} {cont_id} попозже")
        abort(404)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if user.toread:
        if f'{name} {cont_id}' in user.toread:
            arr = list(user.toread)
            arr.remove(f'{name} {cont_id}')
            user.toread = arr
            add_log(
                f"Пользователь с id={current_user.id} убрал из отложенных {name} {cont_id}",
                db_sess=db_sess)
        else:
            user.toread = list(user.toread) + [f'{name} {cont_id}']
            add_log(
                f"Пользователь с id={current_user.id} добавил в отложенные {name} {cont_id}",
                db_sess=db_sess)
    else:
        user.toread = [f'{name} {cont_id}']
        add_log(
            f"Пользователь с id={current_user.id} добавил в отложенные {name} {cont_id}",
            db_sess=db_sess)
    db_sess.commit()
    db_sess.close()
    return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Нравится
@login_required
@app.route('/liked/<int:user_id>/<name>/<int:cont_id>')
def like(user_id, name, cont_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел лайкнуть {name} {cont_id}")
        return redirect(f'/login/$liked${user_id}${name}${cont_id}')
    if user_id != current_user.id:
        add_log(f"Пользователь с id={current_user.id}!={user_id} хотел лайкнуть {name} {cont_id}")
        abort(404)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    publ = None
    if name == "post":
        publ = db_sess.query(Post).filter(Post.id == cont_id).first()
    if name == "problem":
        publ = db_sess.query(Problem).filter(Problem.id == cont_id).first()
    if name == "comment":
        publ = db_sess.query(Comment).filter(Comment.id == cont_id).first()
    if name == "solution":
        publ = db_sess.query(Solution).filter(Solution.id == cont_id).first()
    if not publ:
        db_sess.close()
        add_log(f"Пользователь с id={current_user.id} хотел лайкнуть {name} {cont_id}, но оно не существует")
        abort(404)
    add_log(
        f"Пользователь с id={current_user.id} и рейтингом {user.get_rank()} лайкнул {name} {cont_id}. Рейтинг публикации был {publ.rank}, её лайкнули {publ.liked_by}",
        db_sess=db_sess)
    # print(publ.rank, publ.liked_by, user_id)
    # print(user.get_rank())
    if publ.liked_by is None or user_id not in publ.liked_by:
        # print(123)
        publ.rank += user.get_rank()
        if not publ.liked_by:
            arr = []
        else:
            arr = list(publ.liked_by)
        arr.append(user_id)
        publ.liked_by = arr
        add_log(
            f"Пользователь с id={current_user.id} и рейтингом {user.get_rank()} лайкнул {name} {cont_id}. Рейтинг публикации стал {publ.rank}, её лайкнули {publ.liked_by}",
            db_sess=db_sess)
        if name == "post":
            like_under_post_added(cont_id, user_id)
        if name == "problem":
            like_under_problem_added(cont_id, user_id)
        if name == "solution":
            like_under_solution_added(cont_id, user_id)
        if name == "comment":
            like_under_comment_added(cont_id, user_id)
    else:
        # print(456)
        publ.rank -= user.get_rank()
        arr = list(publ.liked_by)
        arr.remove(user_id)
        publ.liked_by = arr
        add_log(
            f"Пользователь с id={current_user.id} и рейтингом {user.get_rank()} убрал лайк {name} {cont_id}. Рейтинг публикации стал {publ.rank}, её лайкнули {publ.liked_by}",
            db_sess=db_sess)
    # print(publ.liked_by, publ.rank)
    db_sess.commit()
    db_sess.close()
    return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# Показываем задачу
@login_required
@app.route('/problem/<int:problem_id>', methods=['GET', 'POST'])
def problem_show(problem_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел посмотреть задачу {problem_id}")
        return redirect(f'/login/$problem${problem_id}')
    db_sess = db_session.create_session()
    problem = db_sess.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        db_sess.close()
        add_log(f"Пользователь с id={current_user.id} хотел посмотреть задачу {problem_id}, но она не нашлась")
        res = make_response("К сожалению такой задачи нет")
        return res
    form = CommentAddForm(prefix='problem_comment_form')
    comment_forms = [CommentAddForm(prefix=f'solution_comment_form{i}') for i in range(len(problem.solutions))]
    solform = SolutionAddForm(prefix='problem_solution_form')
    if request.method == 'POST':
        if form.validate_on_submit():  # Кто-то написал комментарий к задаче
            comment = Comment()
            comment.content = form.content.data
            current_user.comments.append(comment)
            db_sess.merge(current_user)
            comment = db_sess.merge(comment)
            problem.comments.append(comment)
            user_id = current_user.id
            comment_id = comment.id
            fix_cats(problem, db_sess)
            db_sess.commit()
            db_sess.close()
            add_log(
                f"Пользователь с id={user_id} добавил комментарий с содержанием:\n {form.content.data}\n к задаче {problem_id}.")
            comment_added(comment_id)
            return redirect(f'/problem/{problem_id}')
        if solform.validate_on_submit():  # Кто-то написал решение к задаче
            solution = Solution()
            solution.content = solform.content.data
            solution.theme = problem.theme
            fake_user = db_sess.merge(current_user)
            fake_user.solutions.append(solution)
            solution = db_sess.merge(solution)
            problem.solutions.append(solution)
            fix_cats(problem, db_sess)
            user_id = current_user.id
            solution_id = solution.id
            db_sess.commit()
            db_sess.close()
            add_log(
                f"Пользователь с id={user_id} добавил решение с содержанием:\n {solform.content.data}\n к задаче {problem_id}.")
            solution_added(solution_id)
            return redirect(f'/problem/{problem_id}')
        for i in range(len(comment_forms)):
            if comment_forms[i].validate_on_submit():  # Кто-то написал комментарий к решению
                comment = Comment()
                comment.content = comment_forms[i].content.data
                current_user.comments.append(comment)
                db_sess.merge(current_user)
                comment = db_sess.merge(comment)
                solution = problem.solutions[i]
                comment.theme = solution.theme
                solution.comments.append(comment)
                sol_id = solution.id
                comment_id = comment.id
                fix_cats(problem, db_sess)
                db_sess.commit()
                db_sess.close()
                add_log(
                    f"Пользователь с id={current_user.id} добавил комментарий с содержанием:\n {comment_forms[i].content.data}\n к {i} решению с id={sol_id} задачи {problem_id}.")
                comment_added(comment_id)
                return redirect(f'/problem/{problem_id}')
    add_log(
        f"Пользователь с id={current_user.id} смотрит задачу {problem_id}.")
    res = make_response(
        render_template("problem.html", title="Задача", problem=problem, form=form, comment_forms=comment_forms,
                        solform=solform,
                        viewer=current_user, with_cats_show=with_cats_show, admin_message=get_adminmessage()))

    return res


# Показываем пост
@login_required
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_show(post_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел посмотреть пост {post_id}")
        return redirect(f'/login/$post${post_id}')
    db_sess = db_session.create_session()
    post = db_sess.query(Post).filter(Post.id == post_id).first()
    if not post:
        db_sess.close()
        add_log(f"Пользователь с id={current_user.id} хотел посмотреть пост {post_id}, но он не нашёлся")
        res = make_response("К сожалению такой записи нет")

        return res
    form = CommentAddForm()
    if form.validate_on_submit():  # Кто-то написал комментарий к посту
        comment = Comment()
        comment.content = form.content.data
        comment.theme = post.theme
        current_user.comments.append(comment)
        db_sess.merge(current_user)
        comment = db_sess.merge(comment)
        post.comments.append(comment)
        comment_id = comment.id
        fix_cats(post, db_sess)
        db_sess.commit()
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id} добавил комментарий с содержанием:\n {form.content.data}\n к посту {post_id}.")
        comment_added(comment_id)
        return redirect(f'/post/{post_id}')
    add_log(
        f"Пользователь с id={current_user.id} смотрит пост {post_id}.")
    res = make_response(
        render_template("post.html", title="Запись", post=post, form=form, viewer=current_user,
                        with_cats_show=with_cats_show, admin_message=get_adminmessage()))

    return res


# Показываем отложенные
@login_required
@app.route('/my')
def toread():
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел попасть в /my")
        return redirect('/login/$my')
    publs = []
    db_sess = None
    used = set()
    if current_user.toread:
        db_sess = db_session.create_session()
        for name in current_user.toread:
            if name not in used:
                used.add(name)
                publ_type, publ_id = name.split()
                if publ_type == 'post':
                    post = db_sess.query(Post).filter(Post.id == int(publ_id)).first()
                    publs.append(post)
                else:
                    problem = db_sess.query(Problem).filter(Problem.id == int(publ_id)).first()
                    publs.append(problem)
    add_log(f"Пользователь с id={current_user.id} посмотрел отложенные задачи и посты", db_sess=db_sess)
    return render_template("toread.html", title='Отложенные', Post=Post, Problem=Problem,
                           publications=publs[::-1], isinstance=isinstance, viewer=current_user,
                           with_cats_show=with_cats_show, admin_message=get_adminmessage())


@login_required
@app.route('/')
def main_page():
    submit_changes()
    add_log(f"Чувака отправили на главную страницу")
    return redirect('/***/***/месяц/NOTEGS')


# Главная страница
# (геома, алгебра, комба) (посты, задачи с решениями, задачи без решений) '30 минут', '5 часов', '1 день', 'неделя', 'месяц', 'год', 'всё время'
@login_required
@app.route('/<cathegories>/<post_types>/<time>/<tegs>', methods=["POST", "GET"])
def index(cathegories, post_types, time, tegs: str):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел попасть на главную")
        return redirect(f'/login/${cathegories}${post_types}${time}${tegs}')
    form = NavForm()
    if form.validate_on_submit():  # Если кто-то заполнил форму и нажал искать, мы его переадресовываем
        cats = ''
        if form.geom.data:
            cats += '*'
        else:
            cats += '.'
        if form.algb.data:
            cats += '*'
        else:
            cats += '.'
        if form.comb.data:
            cats += '*'
        else:
            cats += '.'
        typs = ''
        if form.posts.data:
            typs += '*'
        else:
            typs += '.'
        if form.solprob.data:
            typs += '*'
        else:
            typs += '.'
        if form.nosolprob.data:
            typs += '*'
        else:
            typs += '.'
        if cats == '...':
            cats = '***'
        if typs == '...':
            typs = '***'
        tegs_from_form = ','.join([teg.replace(' ', '').replace("#", "") for teg in form.tegs.data.split(',')])
        if not tegs_from_form:
            tegs_from_form = "NOTEGS"
        s = f'/{cats}/{typs}/{form.time.data}/{tegs_from_form}'
        add_log(f"Пользователь с id={current_user.id} на главной странице сделал запрос: {s}")
        return redirect(s)
    # Заполняем форму в соответствии с адресной строкой
    if tegs != "NOTEGS":
        form.tegs.data = ','.join(['#' + teg.replace(' ', '') for teg in tegs.split(',')])
    else:
        form.tegs.data = ''
    cats = cathegories
    if cats == '...':
        cats = '***'
    typs = post_types
    if typs == '...':
        typs = '***'
    if cats[0] == '*':
        form.geom.data = True
    else:
        form.geom.data = False
    if cats[1] == '*':
        form.algb.data = True
    else:
        form.algb.data = False
    if cats[2] == '*':
        form.comb.data = True
    else:
        form.comb.data = False
    if typs[0] == '*':
        form.posts.data = True
    else:
        form.posts.data = False
    if typs[1] == '*':
        form.solprob.data = True
    else:
        form.solprob.data = False
    if typs[2] == '*':
        form.nosolprob.data = True
    else:
        form.nosolprob.data = False
    # Находим самую раннюю дату возможной публикации
    form.time.data = time
    now = datetime.now()
    timedist = {'30 минут': timedelta(minutes=30), '5 часов': timedelta(hours=5), '1 день': timedelta(days=1),
                'неделя': timedelta(weeks=1), 'месяц': timedelta(days=30), 'год': timedelta(days=365),
                'всё время': timedelta(days=365 * (now.year - 1))}[time]
    oldest = now - timedist
    db_sess = db_session.create_session()
    # Подбираем подходящие публикации
    good_themes = [str(i) for i in range(3) if cats[i] == '*']
    if form.posts.data:
        posts = []
        for post in list(db_sess.query(Post).filter(Post.created_date > oldest).all()):
            if post.theme in good_themes:
                posts.append(post)
    else:
        posts = []
    solprobs = []
    nosolprobs = []
    for problem in db_sess.query(Problem).filter(Problem.created_date > oldest).all():
        if problem.theme in good_themes and (problem.solutions and form.solprob.data):
            solprobs.append(problem)
        elif problem.theme in good_themes and (not problem.solutions and form.nosolprob.data):
            nosolprobs.append(problem)
    publications = posts + solprobs + nosolprobs
    tegs_found = 0

    def interest(publ):  # Формируем рейтинг публикации
        nonlocal tegs_found
        reit = 0
        if publ.user.id in current_user.subscribes:
            reit += 100 + random.randrange(100)
        reit += max(0, math.atan(publ.rank / 2000) / math.pi * 200)
        if (datetime.now() - publ.created_date).seconds < 60 * 15:
            reit += max(24 * 60 * 60 - (datetime.now() - publ.created_date).seconds, 0) / (24 * 6 * 6)
        reit += publ.user.get_rank()
        # reit += random.randrange(10)
        k = 0
        if tegs != "NOTEGS":
            for teg_name in tegs.split(","):
                teg_name.replace(' ', '')
                category = db_sess.query(Category).filter(Category.name == teg_name).first()
                if category and category in publ.categories:
                    k += 1
                    tegs_found += 1
        reit += k * 350
        return reit

    publications.sort(key=interest, reverse=True)
    if tegs_found or tegs == "NOTEGS":
        add_log(f"Пользователь с id={current_user.id} на главной странице", db_sess=db_sess)
        res = make_response(
            render_template("index.html", title='Лента', form=form, Post=Post, Problem=Problem,
                            publications=publications, isinstance=isinstance, viewer=current_user,
                            with_cats_show=with_cats_show, admin_message=get_adminmessage()))
    else:
        add_log(f"Пользователь с id={current_user.id} на главной странице искал теги {tegs} и они не нашлись",
                db_sess=db_sess)
        res = make_response(
            render_template("index.html", title='Лента', form=form, Post=Post, Problem=Problem,
                            publications=publications, isinstance=isinstance, viewer=current_user,
                            with_cats_show=with_cats_show, message="Таких тегов не существует",
                            admin_message=get_adminmessage()))

    return res


# Профиль
@login_required
@app.route('/profile/<int:user_id>', methods=['POST', 'GET'])
def profile(user_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел посмотреть профиль пользователя с id={user_id}")
        return redirect(f'/login/$profile${user_id}')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if not user:
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id} хотел посмотреть профиль пользователя с id={user_id}, но такого нет")
        return redirect("/")
    publs = sorted(list(user.posts) + list(user.problems), key=lambda x: x.created_date)[
            ::-1]

    vk_form = SimpleForm(prefix="vkform")
    tg_form = SimpleForm(prefix="tgform")
    if vk_form.validate_on_submit():
        user.vk_id = vk_form.text.data

        extend_messages([{'vk': vk_form.text.data,
                          'text': 'Кто-то привязал ваш аккаунт в Вконтакте к сайту ge0math.ru. Если это не вы, напишите /stop и бот не будет вам писать.'}],
                        "vk")

        db_sess.commit()

    if tg_form.validate_on_submit():
        user.tg_id = tg_form.text.data
        extend_messages([{'tg': tg_form.text.data,
                          'text': 'Кто-то привязал ваш аккаунт в telegram к сайту ge0math.ru. Если это не вы, напишите /stop и бот не будет вам писать.'}],
                        "tg")
        db_sess.commit()

    add_log(f"Пользователь с id={current_user.id} посмотрел профиль пользователя с id={user_id}", db_sess=db_sess)
    res = make_response(
        render_template("profile.html", title=user.name, user=user, viewer=current_user, publications=publs,
                        isinstance=isinstance,
                        Post=Post, Problem=Problem,
                        subscribers=user.subscribers_count, readers=(0 if not user.readers else len(user.readers)),
                        geom1=user.get_rank('0', creating_only=True),
                        alg1=user.get_rank('1', creating_only=True), comb1=user.get_rank('2', creating_only=True),
                        geom2=user.get_rank('0'),
                        alg2=user.get_rank('1'), comb2=user.get_rank('2'), with_cats_show=with_cats_show,
                        admin_message=get_adminmessage(), users_count=db_sess.query(User).count(),
                        publ_count=db_sess.query(Post).count() + db_sess.query(Problem).count(),
                        vk_form=vk_form, tg_form=tg_form
                        ))

    return res


# Отмена смены электронной почты
@login_required
@app.route('/abord_email_reseting/<int:user_id>')
def abord_email_reseting(user_id):
    submit_changes()
    db_sess = db_session.create_session()
    if current_user.id != User.id:
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id}!={user_id} хотел отменить смену электронной почты пользователя с id={user_id}")
        abort(404)
    user = db_sess.query(User).filter(User.id == user_id).first()
    user.new_email_code = ''
    db_sess.commit()
    db_sess.close()
    add_log(
        f"Пользователь с id={current_user.id}отменил смену электронной почты")
    return redirect(f'/profile/{user_id}')


# Новый код смены почты
@login_required
@app.route('/reset_new_email_code/<int:user_id>')
def reset_new_email_code(user_id):
    submit_changes()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    user.new_email_code = ''.join([str(random.randrange(10)) for _ in range(6)])
    db_sess.commit()
    db_sess.close()
    add_log(
        f"Пользователь с id={current_user.id} запросил новый код для смены электронной почты")
    return redirect(f'/new_email_verify/{user_id}')


# Подтверждение новой электронной почты
@login_required
@app.route('/new_email_verify/<int:user_id>', methods=['GET', 'POST'])
def verify_new_email(user_id):
    submit_changes()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if user.new_email_code == "":
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id} хотел подтвердить новую электронную почту, но это кто-то уже сделал")
        return redirect('/login')
    form = VerifyForm()
    if form.validate_on_submit():
        if user.new_email_code == form.code.data:
            user.new_email_code = ""
            user.email = user.new_email
            db_sess.commit()
            db_sess.close()
            add_log(
                f"Пользователь с id={current_user.id} подтвердил новую электронную почту и отправлен в /login")
            return redirect('/login')
        else:
            add_log(
                f"Пользователь с id={current_user.id} хотел подтвердить новую электронную почту, но ввёл неправильный код")
            return render_template("verifynew.html", title='Проверка почты', form=form, message='Неправильный код',
                                   user_id=user_id, admin_message=get_adminmessage())
    add_log(
        f"Пользователь с id={current_user.id} пришёл, чтобы подтвердить новую электронную почту")
    send_email(user.new_email, user.new_email_code, message_type="email_change")
    return render_template("verifynew.html", title='Проверка почты', form=form, user_id=user_id,
                           with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Смена электронной почты
@login_required
@app.route('/reset_email/<int:user_id>', methods=['GET', 'POST'])
def reset_email(user_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(
            f"Неавторизованный пользователь хотел изменить электронную почту пользователя с id={user_id}")
        return redirect('/login')
    db_sess = db_session.create_session()
    if current_user.id != user_id:
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id}!={user_id} хотел изменить электронную почту пользователя с id={user_id}")
        abort(404)
    user = db_sess.query(User).filter(User.id == user_id).first()
    if not user:
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id} хотел изменить электронную почту пользователя с id={user_id}, но его не существует")
        abort(404)
    form = ResetEmailForm()
    if form.validate_on_submit():
        if not user.check_password(form.password.data):
            add_log(
                f"Пользователь с id={current_user.id} хотел изменить электронную почту на {form.email.data}, но ввёл неправильный пароль",
                db_sess=db_sess)
            res = make_response(render_template('resetemail.html', title='Смена электронной почты',
                                                form=form,
                                                message="Неверный пароль", with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))
            return res
        if form.email.data != form.email_again.data:
            add_log(
                f"Пользователь с id={current_user.id} хотел изменить электронную почту на {form.email.data}!={form.email_again.data}",
                db_sess=db_sess)
            res = make_response(render_template('resetemail.html', title='Смена электронной почты',
                                                form=form,
                                                message="Адреса электронной почты не совпадают",
                                                with_cats_show=with_cats_show, admin_message=get_adminmessage()))
            return res
        if db_sess.query(User).filter(User.email == form.email.data).first():
            db_sess.close()
            add_log(
                f"Пользователь с id={current_user.id} хотел изменить электронную почту на {form.email.data}, но такая почта уже есть")
            res = make_response(render_template('resetemail.html', title='Смена электронной почты',
                                                form=form,
                                                message="Такой пользователь уже есть", with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))
            return res
        user.new_email = form.email.data
        db_sess.commit()
        add_log(
            f"Пользователь с id={current_user.id} хотел изменить электронную почту на {form.email.data} и отправлен на проверку")
        return redirect(f'/reset_new_email_code/{user_id}')
    add_log(
        f"Пользователь с id={current_user.id} решил изменить электронную почту", db_sess=db_sess)
    res = make_response(render_template('resetemail.html', title='Смена электронной почты',
                                        form=form, with_cats_show=with_cats_show, admin_message=get_adminmessage()))
    return res


# Редактирование профиля
@login_required
@app.route('/edit_profile/<int:user_id>', methods=["POST", "GET"])
def edit_profile(user_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(
            f"Неавторизованный пользователь хотел изменить профиль пользователя с id={user_id}")
        return redirect('login')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if not user:
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id} хотел изменить электронную почту пользователя с id={user_id}, но его не существует")
        abort(404)
    if user.email != current_user.email:
        db_sess.close()
        add_log(
            f"Пользователь с email={current_user.email}!={user.email} хотел изменить изменить профиль пользователя с id={user_id}")
        abort(404)
    form = ProfileEditForm()
    if form.validate_on_submit():
        if not user.check_password(form.old_password.data):
            add_log(
                f"Пользователь с id={current_user.id} хотел изменить профиль, но ввёл неправильный пароль",
                db_sess=db_sess)
            res = make_response(render_template('profileedit.html', form=form, title='Редактирование профиля',
                                                message='Неверный пароль', with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))

            return res
        if form.change_status.data:
            res, status, reg_code = check_code(form.secret_code.data, db_sess)
            if not res:
                add_log(
                    f"Пользователь с id={current_user.id} хотел изменить профиль и статус, но ввёл неправильный код",
                    db_sess=db_sess)
                res = make_response(render_template('profileedit.html', title='Редактирование профиля',
                                                    form=form,
                                                    code_message=status, with_cats_show=with_cats_show,
                                                    admin_message=get_adminmessage()))

                return res
            else:
                add_log(
                    f"Пользователь с id={current_user.id} изменил статус на {status}",
                    db_sess=db_sess)
            if reg_code is not None:
                db_sess.delete(reg_code)
        else:
            status = user.status
        if form.password.data != form.password_again.data:
            add_log(
                f"Пользователь с id={current_user.id} хотел изменить профиль и пароль, но пароли не совпадают",
                db_sess=db_sess)
            res = make_response(render_template('profileedit.html', title='Редактирование профиля',
                                                form=form,
                                                message="Пароли не совпадают", with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))

            return res
        user.name = form.name.data
        user.about = form.about.data
        user.status = status
        user_name = user.name
        user_about = user.about
        user_status = user.status # TODO why user can't change to admin!!!!!!!!!!!!!!!
        if form.password.data:
            user.set_password(form.password.data)
        db_sess.commit()
        db_sess.close()
        add_log(
            f"Пользователь с id={user_id} изменил профиль: name='{user_name}', about='{user_about}', status='{user_status}'")
        return redirect(f'/profile/{user_id}')
    form.name.data = user.name
    form.about.data = user.about
    add_log(
        f"Пользователь с id={current_user.id} изменяет профиль")
    res = make_response(
        render_template("profileedit.html", title='Редактирование профиля', form=form, with_cats_show=with_cats_show,
                        admin_message=get_adminmessage()))

    return res


def check_code(code, db_sess):
    reg_code = db_sess.query(RegCode).filter(RegCode.code == code).first()
    if not reg_code:
        add_log(
            f"Код {reg_code} не существует", db_sess=db_sess)
        return False, "Код недействителен", None
    if datetime.now() - reg_code.created_date > timedelta(days=2):
        db_sess.delete(reg_code)
        db_sess.commit()
        add_log(
            f"Код {reg_code} существует, но создан давно", db_sess=db_sess)
        db_sess.close()
        return False, "Время действия кода истекло", None
    result = reg_code.status
    add_log(
        f"Код {reg_code} существует, его статус: {result}", db_sess=db_sess)
    db_sess.close()
    return True, result, reg_code


# Генерация кода регистрации
@login_required
@app.route('/generate_code/<status>')
def gen_code(status):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(
            f"Неавторизованный пользователь хотел сгенерировать код регистрации")
        return redirect('/login/$generate_code')
    statuses = {'администратор': 3, 'жюри': 2, 'преподаватель': 1, 'участник': 0}
    if statuses.get(status, 1000) > statuses[current_user.status]:
        add_log(
            f"Пользователь с id={current_user.id} и статусом {current_user.status} хотел сгенерировать код со статусом {status}")
        return redirect('/')
    else:
        code = None
        db_sess = db_session.create_session()
        while True:
            code = generate_code(status)
            reg_code = db_sess.query(RegCode).filter(RegCode.code == code).first()
            if not reg_code:
                break
            if datetime.now() - reg_code.created_date <= timedelta(days=1):
                db_sess.delete(reg_code)
                break
        reg_code = RegCode(code=code, status=status)
        db_sess.add(reg_code)
        db_sess.commit()
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id} и статусом {current_user.status} сгенерировал код со статусом {status}")
        res = make_response(
            render_template('codegen.html', title='Код приглашения', status=status, code=code,
                            with_cats_show=with_cats_show, admin_message=get_adminmessage()))

        return res


@app.route('/login/<togo>', methods=['GET', 'POST'])
def login_with_link(togo):
    submit_changes()
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if not user:
            add_log(
                f"Чувак хотел войти, но пользователя с email={form.email.data} не существует", db_sess=db_sess)
            return make_response(render_template('login.html', title='Авторизация',
                                                 message="Неправильный логин или пароль",
                                                 form=form, with_cats_show=with_cats_show,
                                                 admin_message=get_adminmessage()))
        user_id = user.id
        if user.email_code != "":
            add_log(
                f"Чувак хотел войти, но он не подтвердил email={form.email.data}", db_sess=db_sess)
            db_sess.close()
            return redirect(f'/email_verify/{user_id}')
        if user.new_email_code != "":
            add_log(
                f"Чувак хотел войти, но он изменил email с {user.email} на {user.new_email} и не подтвердил второй",
                db_sess=db_sess)
            db_sess.close()
            return redirect(f'/reset_new_email_code/{user_id}')
        if user and user.check_password(form.password.data):
            add_log(
                f"Чувак с email={user.email} вошёл",
                db_sess=db_sess)
            login_user(user, remember=form.remember_me.data)
            db_sess.close()
            return redirect(togo.replace('$', '/'))
        db_sess.close()
        add_log(
            f"Чувак с email={user.email} ввёл неправильный пароль",
            db_sess=db_sess)
        res = make_response(render_template('login.html', title='Авторизация',
                                            message="Неправильный логин или пароль",
                                            form=form, with_cats_show=with_cats_show, admin_message=get_adminmessage()))

        return res
    add_log(
        f"Чувак с попал в /login")
    res = make_response(render_template('login.html', title='Авторизация', form=form, with_cats_show=with_cats_show,
                                        admin_message=get_adminmessage()))

    return res


# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    submit_changes()
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if not user:
            add_log(
                f"Чувак хотел войти, но пользователя с email={form.email.data} не существует", db_sess=db_sess)
            return make_response(render_template('login.html', title='Авторизация',
                                                 message="Неправильный логин или пароль",
                                                 form=form, with_cats_show=with_cats_show,
                                                 admin_message=get_adminmessage()))
        user_id = user.id
        if user.email_code != "":
            add_log(
                f"Чувак хотел войти, но он не подтвердил email={form.email.data}", db_sess=db_sess)
            db_sess.close()
            return redirect(f'/email_verify/{user_id}')
        if user.new_email_code != "":
            add_log(
                f"Чувак хотел войти, но он изменил email с {user.email} на {user.new_email} и не подтвердил второй",
                db_sess=db_sess)
            db_sess.close()
            return redirect(f'/reset_new_email_code/{user_id}')
        if user and user.check_password(form.password.data):
            add_log(
                f"Чувак с email={user.email} вошёл",
                db_sess=db_sess)
            login_user(user, remember=form.remember_me.data)
            db_sess.close()
            return redirect(f"/profile/{user.id}")
        db_sess.close()
        add_log(
            f"Чувак с email={user.email} ввёл неправильный пароль",
            db_sess=db_sess)
        res = make_response(render_template('login.html', title='Авторизация',
                                            message="Неправильный логин или пароль",
                                            form=form, with_cats_show=with_cats_show, admin_message=get_adminmessage()))

        return res
    add_log(
        f"Чувак с попал в /login")
    res = make_response(render_template('login.html', title='Авторизация', form=form, with_cats_show=with_cats_show,
                                        admin_message=get_adminmessage()))

    return res


# Смена кода подтверждения почты
@app.route('/reset_email_code/<int:user_id>')
def reset_email_code(user_id):
    submit_changes()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    user.email_code = ''.join([str(random.randrange(10)) for _ in range(6)])
    db_sess.commit()
    add_log(
        f"Пользователь изменил код подтверждения почты для пользователя с id={user_id}")
    db_sess.close()
    return redirect(f'/email_verify/{user_id}')


# Подтверждение почты
@app.route('/email_verify/<int:user_id>', methods=['GET', 'POST'])
def verify_email(user_id):
    submit_changes()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if user.email_code == "":
        db_sess.close()
        add_log(
            f"Пользователь с id={user_id} хотел подтвердить электронную почту, но это кто-то уже сделал")
        return redirect('/login')
    form = VerifyForm()
    if form.validate_on_submit():
        if user.email_code == form.code.data:
            user.email_code = ""
            db_sess.commit()
            db_sess.close()
            add_log(
                f"Пользователь с id={user_id} подтвердил электронную почту")
            return redirect('/login')
        else:
            add_log(
                f"Пользователь с id={user_id} хотел подтвердить электронную почту и ввёл неправильный код")
            return render_template("verify.html", title="Проверка почты", form=form, message='Неправильный код',
                                   user_id=user_id,
                                   with_cats_show=with_cats_show, admin_message=get_adminmessage())
    add_log(
        f"Пользователь с id={user_id} пришёл подтвердить электронную почту", db_sess=db_sess)
    send_email(user.email, user.email_code)
    return render_template("verify.html", title="Проверка почты", form=form, user_id=user_id,
                           with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    submit_changes()
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        users_count = db_sess.query(User).count()
        res, status, reg_code = check_code(form.secret_code.data, db_sess)
        if not users_count:
            res, status = True, "администратор"
            add_log(f"Чувак пришёл зарегистрироваться. Это первый пользователь => это админ", db_sess=db_sess)
        if not res:
            add_log(f"Чувак пришёл зарегистрироваться и ввёл неправильный код регистрации", db_sess=db_sess)
            res = make_response(render_template('register.html', title='Регистрация',
                                                form=form,
                                                code_message=status, with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))

            return res
        if form.password.data != form.password_again.data:
            add_log(f"Чувак пришёл зарегистрироваться и ввёл разные пароли", db_sess=db_sess)
            res = make_response(render_template('register.html', title='Регистрация',
                                                form=form,
                                                message="Пароли не совпадают", with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))

            return res
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            add_log(f"Чувак пришёл зарегистрироваться, но чувак с такой почтой уже есть", db_sess=db_sess)
            db_sess.close()
            res = make_response(render_template('register.html', title='Регистрация',
                                                form=form,
                                                message="Такой пользователь уже есть", with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))

            return res
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data,
            status=status
        )
        print(form.password.data)
        user.set_password(form.password.data)
        if users_count:
            user.email_code = ''.join([str(random.randrange(10)) for _ in range(6)])
        else:
            user.email_code = ''
        db_sess.add(user)
        if reg_code is not None:
            db_sess.delete(reg_code)
        db_sess.commit()
        user_id = user.id
        add_log(
            f"Чувак с почтой {form.email.data}, логином {form.name.data}, about={form.about.data} зарегистрировался и получил статус {status}",
            db_sess=db_sess)
        db_sess.close()
        if users_count:
            return redirect(f'/email_verify/{user_id}')
        else:
            return redirect('/login')
    add_log(f"Чувак пришёл зарегистрироваться")
    res = make_response(render_template('register.html', title='Регистрация', form=form, with_cats_show=with_cats_show,
                                        admin_message=get_adminmessage()))

    return res


# Выход
@app.route('/logout')
@login_required
def logout():
    submit_changes()
    add_log(f"Чувак с id={current_user.id} выходит(")
    logout_user()
    return redirect("/")


# Добавление поста
@app.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел добавить пост")
        return redirect('/login/$add_post')
    form = PostAddForm()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    db_sess.commit()
    if form.validate_on_submit():
        post = Post()
        post.title = form.title.data
        post.content = form.content.data
        post.theme = form.theme.data
        user.posts.append(post)

        db_sess.commit()
        fix_cats(post, db_sess)
        post = user.posts[-1]
        readers = []
        for reader_id in (user.readers if user.readers is not None else []):
            reader = db_sess.query(User).filter(User.id == reader_id).first()
            arr = (list(reader.toread) if reader.toread is not None else [])
            arr.append('post ' + str(post.id))
            reader.toread = arr
            db_sess.commit()
            readers.append((reader.name, reader.id))
        post_id = post.id
        db_sess.commit()
        add_log(
            f"Пользователь с id={current_user.id} добавил пост '{post.title}'({post.theme}) с содержанием:\n{post.content}\nОн автоматически добавлен к прочтению пользователям {readers}",
            db_sess=db_sess)
        db_sess.close()
        post_added(post_id)
        return redirect(f'/post/{post_id}')
    add_log(
        f"Пользователь с id={current_user.id} пришёл добавить пост", db_sess=db_sess)
    res = make_response(render_template('postadd.html', title='Добавление информации для размышления',
                                        form=form, with_cats_show=with_cats_show, admin_message=get_adminmessage()))

    return res


# Добавление задачи
@app.route('/add_problem', methods=['GET', 'POST'])
@login_required
def add_problem():
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел добавить задачу")
        return redirect('/login/$add_problem')
    form = ProblemAddForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        problem = Problem()
        problem.content = form.content.data
        problem.theme = form.theme.data
        problem.notauthor = form.notauthor.data
        current_user.problems.append(problem)
        user = db_sess.merge(current_user)
        problem = user.problems[-1]
        problem_id = problem.id
        readers = []
        for reader_id in (user.readers if user.readers is not None else []):
            reader = db_sess.query(User).filter(User.id == reader_id).first()
            arr = (list(reader.toread) if reader.toread is not None else [])
            arr.append('problem ' + str(problem.id))
            reader.toread = arr
            readers.append((reader.id, reader.name))
        db_sess.commit()
        if form.original_solution.data:
            solution = Solution()
            solution.content = form.original_solution.data
            solution.theme = problem.theme
            user.solutions.append(solution)
            problem.solutions.append(solution)
        problem_id = problem.id
        if form.original_solution.data:
            add_log(
                f"Пользователь с id={current_user.id} добавил задачу({problem.theme}) с содержанием:\n{problem.content}\nИ даже прикрепил к ней своё решение:\n{form.original_solution.data}\nОна автоматически добавлена к прочтению пользователям {readers}",
                db_sess=db_sess)
        else:
            add_log(
                f"Пользователь{'(не автор)' if form.notauthor.data else ''} с id={current_user.id} добавил задачу({problem.theme}) с содержанием:\n{problem.content}\nИ не прикрепил к ней решение. Она автоматически добавлена к прочтению пользователям {readers}",
                db_sess=db_sess)
        fix_cats(problem, db_sess)
        db_sess.commit()
        db_sess.close()
        problem_added(problem_id)
        return redirect(f'/problem/{problem_id}')
    add_log(
        f"Пользователь с id={current_user.id} пришёл добавить задачу")
    res = make_response(render_template('problemadd.html', title='Добавление задачи',
                                        form=form, with_cats_show=with_cats_show, admin_message=get_adminmessage()))

    return res


# Редактирование поста
@app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел отредактировать пост с id={id}")
        return redirect(f'/login/$edit_post${id}')
    form = PostAddForm()
    file_form = FileAddForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        post = db_sess.query(Post).filter(Post.id == id,
                                          Post.user == current_user
                                          ).first()
        if post:
            if not form.title.data:
                form.title.data = post.title
            if not form.content.data:
                form.content.data = post.content
            form.theme.data = post.theme
            # form.images.data = [FileStorage(open(os.path.join(basedir,'static','user_files',filename))) for filename in post.image_ids]
        else:
            db_sess.close()
            add_log(f"Пользователь с id={current_user.id} хотел отредактировать пост с id={id}, но он не существует")
            abort(404)
    if request.method == 'POST':
        db_sess = db_session.create_session()
        post = db_sess.query(Post).filter(Post.id == id,
                                          Post.user == current_user
                                          ).first()
        if not post:
            add_log(f"Пользователь с id={current_user.id} хотел отредактировать пост с id={id}, но он не существует",
                    db_sess=db_sess)
            db_sess.close()
            abort(404)
        if form.validate_on_submit():
            post.title = form.title.data
            post.content = form.content.data
            post.theme = form.theme.data
            db_sess.commit()
            fix_cats(post, db_sess)
            add_log(
                f"Пользователь с id={current_user.id} отредактировал пост '{post.title}'({post.theme})с id={id}. Содержание:\n{post.content}\n",
                db_sess=db_sess)
            db_sess.close()
            return redirect(f'/post/{id}')
        if file_form.validate_on_submit():
            form.title.data = post.title
            form.content.data = post.content
            form.theme.data = post.theme
            file = file_form.file.data
            if file.filename != '':
                file_ext = os.path.splitext(file.filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                    add_log(
                        f"Пользователь с id={current_user.id} хотел добавить файл с плохим расширением({file.filename}) к посту с id={id}",
                        db_sess=db_sess)
                    db_sess.close()
                    abort(400)
                users_file = UsersFile()
                users_file.name = file.filename
                users_file.extension = file_ext
                fake_user = db_sess.merge(current_user)
                fake_user.files.append(users_file)
                post.files.append(users_file)
                users_file = db_sess.merge(users_file)
                filename = f'{users_file.id}{file_ext}'
                file_path = os.path.join(os.path.join(basedir, 'static'),
                                         filename)
                file.save(file_path)
                add_log(
                    f"Пользователь с id={current_user.id} добавил файл с именем {file.filename} к посту с id={id}",
                    db_sess=db_sess)
                # push_file_to_GitHub(filename)
            if file_form.geogebra_link.data != '':
                users_file = UsersFile()
                users_file.extension = '.ggb'
                users_file.name = file_form.geogebra_link.data
                post.files.append(users_file)
                add_log(
                    f"Пользователь с id={current_user.id} добавил геогебровский чертёж с ссылкой {file_form.geogebra_link.data} к посту с id={id}",
                    db_sess=db_sess)
            db_sess.commit()
            res = make_response(render_template('postedit.html', title='Редактирование', form=form,
                                                href=f"$edit_post${id}", publ=post,
                                                file_form=file_form, with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))
            return res
    add_log(
        f"Пользователь с id={current_user.id} пришёл отредактировать пост с id={id}", db_sess=db_sess)
    res = make_response(render_template('postedit.html', title='Редактирование', form=form,
                                        href=f"$edit_post${id}", publ=post,
                                        file_form=file_form, with_cats_show=with_cats_show,
                                        admin_message=get_adminmessage()))

    return res


# Редактирование задачи
@app.route('/edit_problem/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_problem(id):  # without solution
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел отредактировать задачу с id={id}")
        return redirect(f'/login/$edit_problem/{id}')
    form = ProblemEditForm()
    file_form = FileAddForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        problem = db_sess.query(Problem).filter(Problem.id == id,
                                                Problem.user == current_user
                                                ).first()
        if problem:
            if not form.content.data:
                form.content.data = problem.content
            form.theme.data = problem.theme
            form.notauthor.data = problem.notauthor
        else:
            db_sess.close()
            add_log(f"Пользователь с id={current_user.id} хотел отредактировать задачу с id={id}, но она не существует")
            abort(404)
    if request.method == "POST":

        db_sess = db_session.create_session()
        problem = db_sess.query(Problem).filter(Problem.id == id,
                                                Problem.user == current_user
                                                ).first()
        if not problem:
            add_log(f"Пользователь с id={current_user.id} хотел отредактировать пост с id={id}, но он не существует",
                    db_sess=db_sess)
            db_sess.close()
            abort(404)
        if form.validate_on_submit():
            problem.content = form.content.data
            problem.theme = form.theme.data
            problem.notauthor = form.notauthor.data
            db_sess.commit()
            fix_cats(problem, db_sess)
            add_log(
                f"Пользователь{'(не автор)' if form.notauthor.data else ''} с id={current_user.id} отредактировал задачу ({problem.theme}) с id={id}. Содержание:\n{problem.content}\n",
                db_sess=db_sess)
            db_sess.close()
            return redirect(f'/problem/{id}')
        if file_form.validate_on_submit():
            form.content.data = problem.content
            form.notauthor.data = problem.notauthor
            form.theme.data = problem.theme
            file = file_form.file.data
            if file.filename != '':
                file_ext = os.path.splitext(file.filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                    add_log(
                        f"Пользователь с id={current_user.id} хотел добавить файл с плохим расширением({file.filename}) к задаче с id={id}",
                        db_sess=db_sess)
                    db_sess.close()
                    abort(400)
                users_file = UsersFile()
                users_file.name = file.filename
                users_file.extension = file_ext
                fake_user = db_sess.merge(current_user)
                fake_user.files.append(users_file)
                problem.files.append(users_file)
                users_file = db_sess.merge(users_file)
                filename = f'{users_file.id}{file_ext}'
                file_path = os.path.join(os.path.join(basedir, 'static'),
                                         filename)
                file.save(file_path)
                add_log(
                    f"Пользователь с id={current_user.id} добавил файл с именем {file.filename} к задаче с id={id}",
                    db_sess=db_sess)
                # push_file_to_GitHub(filename)
            if file_form.geogebra_link.data != '':
                users_file = UsersFile()
                users_file.extension = '.ggb'
                users_file.name = file_form.geogebra_link.data
                problem.files.append(users_file)
            db_sess.commit()
            form.content.data = problem.content
            add_log(
                f"Пользователь с id={current_user.id} добавил геогебровский чертёж с ссылкой {file_form.geogebra_link.data} к задаче с id={id}",
                db_sess=db_sess)
            res = make_response(render_template('problemedit.html', title='Редактирование', form=form,
                                                href=f"$edit_problem${id}", publ=problem,
                                                file_form=file_form, with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))
            return res
    add_log(
        f"Пользователь с id={current_user.id} пришёл отредактировать задачу с id={id}", db_sess=db_sess)
    res = make_response(render_template('problemedit.html',
                                        title='Редактирование',
                                        form=form, href=f"$edit_problem${id}", publ=problem, file_form=file_form,
                                        with_cats_show=with_cats_show, admin_message=get_adminmessage()))

    return res


# Удаление поста
@app.route('/delete_post/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_post(id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел удалить пост с id={id}")
        return redirect(f'/login/$delete_post${id}')
    db_sess = db_session.create_session()
    post = db_sess.query(Post).filter(Post.id == id,
                                      Post.user == current_user
                                      ).first()
    if post and not post.comments:
        for i in range(len(post.user.posts)):
            if post.user.posts[i].id == post.id:
                post.user.posts.pop(i)
                break
        db_sess.delete(post)
        db_sess.commit()
        db_sess.close()
        add_log(f"Пользователь с id={current_user.id} удалил пост с id={id}")
    else:
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id} хотел удалить пост с id={id}, но он не существует, или у неё есть комментарии")
        abort(404)
    return redirect(current_user.profile_href())


# Удаление задачи
@app.route('/delete_problem/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_problem(id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел удалить задачу с id={id}")
        return redirect(f'/login/$delete_problem${id}')
    db_sess = db_session.create_session()
    problem = db_sess.query(Problem).filter(Problem.id == id,
                                            Problem.user == current_user
                                            ).first()
    if problem and not problem.comments and not problem.solutions:
        for i in range(len(problem.user.problems)):
            if problem.user.problems[i].id == problem.id:
                problem.user.problems.pop(i)
                break
        arr = list(current_user.wrong)
        print(f"problem {id}", arr)
        if f"problem {id}" in arr:
            arr.remove(f"problem {id}")
        current_user.wrong = arr
        db_sess.merge(current_user)
        db_sess.delete(problem)
        db_sess.commit()
        db_sess.close()
        add_log(f"Пользователь с id={current_user.id} удалил задачу с id={id}")
    else:
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id} хотел удалить задачу с id={id}, но она не существует, или у неё есть комментарии или решения")
        abort(404)
    return redirect(current_user.profile_href())


# Редактирование комментария
@app.route('/edit_comment/<int:comment_id>',
           methods=["POST", "GET"])
@login_required
def edit_comment(comment_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(
            f"Неавторизованный пользователь хотел отредактировать комментарий по ссылке /edit_comment/comment_id:{comment_id}")
        return redirect(f'/login/$edit_comment${comment_id}')
    comment = None
    db_sess = db_session.create_session()
    form = CommentAddForm()
    file_form = FileAddForm()
    comment = db_sess.query(Comment).filter(Comment.id == comment_id,
                                            Comment.user == current_user).first()
    if comment:
        place_name, place_id = comment.get_great_parent()
        if request.method == "GET":
            if not form.content.data:
                form.content.data = comment.content
        if form.validate_on_submit():
            comment.content = form.content.data
            db_sess.commit()
            if comment.post:
                fix_cats(comment.post, db_sess)
            elif comment.problem:
                fix_cats(comment.problem, db_sess)
            elif comment.solution:
                fix_cats(comment.solution, db_sess)
            db_sess.close()
            add_log(
                f"Пользователь с id={current_user.id} отредактировал комментарий по ссылке /edit_comment/comment_id:{comment_id} и изменил content={form.content.data}")
            return redirect(f'/{place_name}/{place_id}')
        if file_form.validate_on_submit():
            form.content.data = comment.content
            file = file_form.file.data
            if file.filename != '':
                file_ext = os.path.splitext(file.filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                    add_log(
                        f"Пользователь с id={current_user.id} хотел добавить файл с плохим расширением({file.filename}) к комментарию по ссылке /edit_comment/comment_id:{comment_id}",
                        db_sess=db_sess)
                    db_sess.close()
                    abort(400)
                users_file = UsersFile()
                users_file.name = file.filename
                users_file.extension = file_ext
                fake_user = db_sess.merge(current_user)
                fake_user.files.append(users_file)
                comment.files.append(users_file)
                users_file = db_sess.merge(users_file)
                filename = f'{users_file.id}{file_ext}'
                file_path = os.path.join(os.path.join(basedir, 'static'),
                                         filename)
                file.save(file_path)
                add_log(
                    f"Пользователь с id={current_user.id} добавил файл с именем {file.filename} к комментарию по ссылке /edit_comment/comment_id:{comment_id}",
                    db_sess=db_sess)
                # push_file_to_GitHub(filename)
            if file_form.geogebra_link.data != '':
                users_file = UsersFile()
                users_file.extension = '.ggb'
                users_file.name = file_form.geogebra_link.data
                comment.files.append(users_file)
                add_log(
                    f"Пользователь с id={current_user.id} добавил геогебровский чертёж с ссылкой {file_form.geogebra_link.data} к комментарию по ссылке /edit_comment/comment_id:{comment_id}",
                    db_sess=db_sess)
            db_sess.commit()
            form.content.data = comment.content
            res = make_response(render_template('solutionedit.html', title='Редактирование', form=form,
                                                href=f"$edit_comment${comment_id}",
                                                publ=comment,
                                                file_form=file_form, with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))

            return res
    else:
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id} хотел отредактировать комментарий по ссылке /edit_comment/comment_id:{comment_id}, но он не существует")
        abort(404)
    add_log(
        f"Пользователь с id={current_user.id} пришёл отредактировать комментарий по ссылке /edit_comment/comment_id:{comment_id}",
        db_sess=db_sess)
    res = make_response(render_template('commentedit.html', title='Редактирование', form=form,
                                        href=f"$edit_comment${comment_id}",
                                        publ=comment,
                                        file_form=file_form, with_cats_show=with_cats_show,
                                        admin_message=get_adminmessage()))

    return res


# Удаление комментария
@app.route('/delete_comment/<int:comment_id>/<place_name>/<int:place_id>/<par_name>/<int:par_id>',
           methods=["POST", "GET"])
@login_required
def delete_comment(comment_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(
            f"Неавторизованный пользователь хотел удалить комментарий по ссылке /edit_comment/comment_id:{comment_id}")
        return redirect(f'/login/$delete_comment${comment_id}')
    comment = None
    db_sess = db_session.create_session()
    comment = db_sess.query(Comment).filter(Comment.id == comment_id,
                                            Comment.user == current_user).first()
    if comment:
        place_name, place_id = comment.get_great_parent()
        if comment.post:
            for i in range(len(comment.post.comments)):
                if comment.post.comments[i].id == comment.id:
                    comment.post.comments.pop(i)
                    break
        if comment.solution:
            for i in range(len(comment.solution.comments)):
                if comment.solution.comments[i].id == comment.id:
                    comment.solution.comments.pop(i)
                    break
        if comment.problem:
            for i in range(len(comment.problem.comments)):
                if comment.problem.comments[i].id == comment.id:
                    comment.problem.comments.pop(i)
                    break
        for i in range(len(comment.user.comments)):
            if comment.user.comments[i].id == comment.id:
                comment.user.comments.pop(i)
                break
        db_sess.delete(comment)
        db_sess.commit()
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id} удалил комментарий по ссылке /edit_comment/comment_id:{comment_id}")
        return redirect(f'/{place_name}/{place_id}')
    else:
        add_log(
            f"Пользователь с id={current_user.id} хотел удалить комментарий по ссылке /edit_comment/comment_id:{comment_id}, но он не существует")
        db_sess.close()
        abort(404)


# Редактирование решения
@app.route('/edit_solution/<int:solution_id>',
           methods=["POST", "GET"])
@login_required
def edit_solution(solution_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(
            f"Неавторизованный пользователь хотел отредактировать решение с id={solution_id}")
        return redirect(f'/login/$edit_solution${solution_id}')
    solution = None
    db_sess = db_session.create_session()
    form = SolutionAddForm()
    file_form = FileAddForm()
    solution = db_sess.query(Solution).filter(Solution.id == solution_id,
                                              Solution.user == current_user).first()
    if solution:
        problem_id = solution.problem_id
        if request.method == "GET":
            if not form.content.data:
                form.content.data = solution.content
        if form.validate_on_submit():
            solution.content = form.content.data
            db_sess.commit()
            fix_cats(solution.problem, db_sess)
            db_sess.close()
            add_log(
                f"Пользователь с id={current_user.id} отредактировал решение с id={solution_id} у задачи с id={problem_id}. Содержание:\n{form.content.data}")
            return redirect(f'/problem/{problem_id}')
        if file_form.validate_on_submit():
            form.content.data = solution.content
            file = file_form.file.data
            if file.filename != '':
                file_ext = os.path.splitext(file.filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                    add_log(
                        f"Пользователь с id={current_user.id} хотел добавить файл с плохим расширением({file.filename}) к решению с id={solution_id} у задачи с id={problem_id}",
                        db_sess=db_sess)
                    db_sess.close()
                    abort(400)
                users_file = UsersFile()
                users_file.name = file.filename
                users_file.extension = file_ext
                fake_user = db_sess.merge(current_user)
                fake_user.files.append(users_file)
                solution.files.append(users_file)
                users_file = db_sess.merge(users_file)
                filename = f'{users_file.id}{file_ext}'
                file_path = os.path.join(os.path.join(basedir, 'static'),
                                         filename)
                file.save(file_path)
                add_log(
                    f"Пользователь с id={current_user.id} добавил файл с именем {file.filename} к решению с id={solution_id} у задачи с id={problem_id}",
                    db_sess=db_sess)
                # push_file_to_GitHub(filename)
            if file_form.geogebra_link.data != '':
                users_file = UsersFile()
                users_file.extension = '.ggb'
                users_file.name = file_form.geogebra_link.data
                solution.files.append(users_file)
                add_log(
                    f"Пользователь с id={current_user.id} добавил геогебровский чертёж с ссылкой {file_form.geogebra_link.data} к решению с id={solution_id} у задачи с id={problem_id}",
                    db_sess=db_sess)
            db_sess.commit()
            form.content.data = solution.content
            res = make_response(render_template('solutionedit.html', title='Редактирование', form=form,
                                                href=f"$edit_solution${solution_id}${problem_id}", publ=solution,
                                                file_form=file_form, with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))

            return res
    else:
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id} хотел отредактировать решение с id={solution_id}, но оно не существует")
        abort(404)
    add_log(
        f"Пользователь с id={current_user.id} пришёл отредактировать решение с id={solution_id}",
        db_sess=db_sess)
    res = make_response(render_template('solutionedit.html', title='Редактирование', form=form,
                                        href=f"$edit_solution${solution_id}", publ=solution,
                                        file_form=file_form, with_cats_show=with_cats_show,
                                        admin_message=get_adminmessage()))

    return res


# Удаление решения
@app.route('/delete_solution/<int:solution_id>/<int:problem_id>',
           methods=["POST", "GET"])
@login_required
def delete_solution(solution_id):
    submit_changes()
    if not current_user.is_authenticated:
        add_log(f"Неавторизованный пользователь хотел удалить решение с id={solution_id}")
        return redirect(f'/login/$delete_solution${solution_id}')
    solution = None
    db_sess = db_session.create_session()
    solution = db_sess.query(Solution).filter(Solution.id == solution_id,
                                              Solution.user == current_user).first()
    if solution and not solution.comments:
        problem_id = solution.problem_id
        for i in range(len(solution.user.solutions)):
            if solution.user.solutions[i].id == solution.id:
                solution.user.solutions.pop(i)
                break
        for i in range(len(solution.problem.solutions)):
            if solution.problem.solutions[i].id == solution.id:
                solution.problem.solutions.pop(i)
                break
        arr = list(current_user.wrong)
        print(f"solution {solution_id}", arr)
        if f"solution {solution_id}" in arr:
            arr.remove(f"solution {solution_id}")
        current_user.wrong = arr
        db_sess.merge(current_user)
        db_sess.delete(solution)
        db_sess.commit()
        db_sess.close()
        add_log(f"Пользователь с id={current_user.id} удалил решение с id={solution_id} у задачи с id={problem_id}")
        return redirect(f'/problem/{problem_id}')
    else:
        db_sess.close()
        add_log(
            f"Пользователь с id={current_user.id} хотел удалить решение с id={solution_id}, но он не существует, или у него есть комментарии")
        abort(404)


def main():
    db_session.global_init(SQLALCHEMY_DATABASE_URI)
    # print(generate_code('администратор'))
    # print(generate_code('жюри'))
    # print(generate_code('преподаватель'))
    # socketio.init_app(app, debug=True)
    # get_file_from_GitHub("adminmessage.txt")

    # db_sess = db_session.create_session()

    # for users_file in db_sess.query(UsersFile).all():
    #    get_file_from_GitHub(users_file.filename())

    # db_sess.close()

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    # app.run(port=8080, host='127.0.0.1')

    """
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id==1).first()
    print(user.comments, user.solutions)


    db_sess = db_session.create_session()
    solution = db_sess.query(Solution).filter(Solution.id==14).first()
    solution.rank = 0
    solution.liked_by = []
    db_sess.commit()
    db_sess.close()
    """


if __name__ == '__main__':
    main()
