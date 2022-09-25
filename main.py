import math
import sys
from db_location import SQLALCHEMY_DATABASE_URI
from flask import Flask, render_template, redirect, request, make_response, current_app
from flask_restful import abort
from github import Github
from loginform import LoginForm
from data import db_session
from data.users import User
from data.post import Post
from data.problem import Problem
from solutionaddform import SolutionAddForm
from data.comment import Comment
from data.solution import Solution
from data.category import Category
from registerform import RegisterForm
from postaddform import PostAddForm
from admin_message_form import AdminForm
from resetemailform import ResetEmailForm
from commentaddform import CommentAddForm
from problemaddform import ProblemAddForm
from problemeditform import ProblemEditForm
from profileeditform import ProfileEditForm
from data.users_file import UsersFile
from fileform import FileAddForm
from verifyform import VerifyForm
from navform import NavForm
from secret_code import generate_code
from data.codes import RegCode
from datetime import datetime, timedelta
import os
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import smtplib
from email.mime.text import MIMEText
import random
# from email_secret_data import EMAIL, PASSWORD, GITHUB_TOKEN
from email.mime.multipart import MIMEMultipart

EMAIL = os.environ["EMAIL"]
PASSWORD = os.environ["PASSWORD"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_EXTENSIONS'] = ['.txt', '.pdf', '.doc', '.docx', '.png', '.jpeg', '.jpg', '.gif']
login_manager = LoginManager()
login_manager.init_app(app)
basedir = os.path.abspath(os.curdir)


def push_file_to_GitHub(filename):
    github = Github(GITHUB_TOKEN)
    repository = github.get_user().get_repo('Ge0MathStoarge')
    # create with commit message
    file_path = os.path.join(os.path.join(basedir, 'static'),
                             filename)
    with open(file_path, 'rb') as file:
        our_bytes = file.read()
        bytes_count = len(our_bytes)
        content = ' '.join(str(byte) for byte in our_bytes)
    try:
        f = repository.get_contents(f"{filename.split('.')[0]}.txt")
    except Exception as e:
        f = repository.create_file(f"{filename.split('.')[0]}.txt", "some_file", content=f'{bytes_count}\n{content}')


def get_file_from_GitHub(filename):
    github = Github(GITHUB_TOKEN)
    repository = github.get_user().get_repo('Ge0MathStoarge')
    # path in the repository
    file_path = os.path.join(os.path.join(basedir, 'static'),
                             filename)
    try:
        f = repository.get_contents(f"{filename.split('.')[0]}.txt")
        with open(file_path, 'wb') as file:
            bytes_count_sts, *content = f.decoded_content.decode().split()
            our_bytes = bytearray(list(map(int, content)))
            file.write(our_bytes)
    except Exception as e:
        print(e)


def get_adminmessage():
    try:
        with open('/static/adminmessage.txt', 'r') as f:
            message = f.read()
    except Exception as e:
        message = ''
    return message


def set_adminmessage(text):
    with open('/static/adminmessage.txt', 'w') as f:
        f.write(text)
    push_file_to_GitHub('adminmessage.txt')


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
            res.append(f"<a href='/***/***/неделя/{''.join(teg)}'>#{''.join(teg)}</a>")
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
    print(publ.categories)
    db_sess.commit()


@app.route('/admin_message', methods=['POST', 'GET'])
def change_admin_message():
    global admin_message
    if not current_user.is_authenticated:
        return redirect('/login')
    if current_user.status != 'администратор':
        return redirect('/')
    form = AdminForm()
    if request.method == 'GET':
        form.content.data = get_adminmessage()
    if form.validate_on_submit():
        set_adminmessage(form.content.data)
        return redirect('/')
    return render_template('adminmessage.html', title='Сообщение администратора', form=form,
                           admin_message=get_adminmessage())


# Удаляем файлы, прикреплённые к чему-то и переходим по ссылке togo
@app.route('/delete_file/<int:file_id>/<togo>')
def delete_file(file_id, togo):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    users_file = db_sess.query(UsersFile).filter(UsersFile.id == file_id).first()
    if users_file:
        db_sess.delete(users_file)
        db_sess.commit()
        db_sess.close()
    else:
        db_sess.close()
        abort(404)
    return redirect(togo.replace('$', '/'))


# Помощь
@app.route('/help')
def help_():
    if not current_user.is_authenticated:
        return redirect('/login')
    return render_template('help.html', title="Помощь", with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Отправляем письмо по адресу to с кодом code
def send_email(to, code, message_type="register"):
    # Придумываем разный текст, чтобы Яндекс не заподозрил нас в рассылке
    if message_type == "register":
        text = random.choice([
            f'Вы только что зарегистрировались на нашем сайте, вот ваш код подтверждения:\n{code}. Введите его, а затем войдите.',
            f'Сообщаем об успешной регистрации на сайте ge0math, чтобы завершить её введите этот код и войдите на сайт с подтверждённой почтой:\n{code}',
            f'{code}\n Это код потверждения, который мы отправили вам на почту для подтверждения вашей электронной почты на сайте ge0math. Введите его и войдите на сайт.',
            f'Ваш код подтверждения:\n{code}\n Введите его, чтобы подтвердить вашу электронную почту на сайте ge0math. После этого вы сможете войти на сайт.',
            f'Ваш код подтверждения:\n{code}\n Введите его, чтобы завершить регистрацию на сайте ge0math и получить возможность войти.'
        ])
    elif message_type == 'email_change':
        text = random.choice([
            f'Вы свою электронную почту на нашем сайте и указали {to}, если это вы, введите ваш код подтверждения:\n{code}',
            f'Сообщаем о смене почты на сайте ge0math на {to}. Чтобы подтвердить смену электронной почты, введите этот код:\n{code}',
            f'{code}\n Это код потверждения, который мы отправили вам на почту для подтверждения смены вашей электронной почты на сайте ge0math.',
            f'Ваш код подтверждения:\n{code}\n Введите его, чтобы подтвердить смену электронной почты на сайте ge0math.',
        ])

    # Задаём параметры письма
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
    if not current_user.is_authenticated:
        return redirect('/login')
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
    return render_template("wrong.html", title='Неверные задачи и решения', Solution=Solution, Problem=Problem,
                           publications=publs[::-1], isinstance=isinstance, viewer=current_user,
                           with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Автор признал задачу(решение) неверной раньше, чем это сделали пользователи
@login_required
@app.route('/author_false/<name>/<int:publ_id>')
def author_false(name, publ_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    if name == "problem":
        publ = db_sess.query(Problem).filter(Problem.id == publ_id).first()
    else:
        publ = db_sess.query(Solution).filter(Solution.id == publ_id).first()
    if publ.user.id != current_user.id:
        db_sess.close()
        abort(404)
    publ.author_thinks_false = True
    arr = list(current_user.wrong)
    if f"{name} {publ_id}" in arr:
        arr.remove(f"{name} {publ_id}")
    current_user.wrong = arr
    db_sess.commit()
    db_sess.close()
    return redirect(f'/{name}/{publ_id}')


# Проверяем, верная задача или нет
def check_truth(publ, db_sess):
    rank = sum(
        [db_sess.query(User).filter(User.id == user_id).first().get_rank() for user_id in list(publ.think_is_true)]) - \
           sum([db_sess.query(User).filter(User.id == user_id).first().get_rank() for user_id in
                list(publ.think_is_false)])
    if rank < -400:
        if publ.is_true:
            publ.rank -= 100
        if not publ.is_false:
            publ.rank -= 100
        publ.is_false = True
        publ.is_true = False
    if -400 <= rank <= 400:
        if publ.is_false:
            publ.rank += 100
        if publ.is_true:
            publ.rank -= 100
        publ.is_true = False
        publ.is_false = False
    if rank > 400:
        if not publ.is_true:
            publ.rank += 100
        if publ.is_false:
            publ.rank += 100
        publ.is_false = False
        publ.is_true = True
    if isinstance(publ, Problem):
        line = f'problem {publ.id}'
    else:
        line = f'solution {publ.id}'
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
    if not current_user.is_authenticated:
        return redirect('/login')
    if user_id != current_user.id:
        abort(404)
    db_sess = db_session.create_session()
    if name == "problem":
        problem = db_sess.query(Problem).filter(Problem.id == publ_id).first()
        if not problem:
            abort(404)
        if user_id in problem.think_is_false:
            arr = list(problem.think_is_false)
            arr.remove(user_id)
            problem.think_is_false = arr
        else:
            if user_id in problem.think_is_true:
                arr = list(problem.think_is_true)
                arr.remove(user_id)
                problem.think_is_true = arr
            problem.think_is_false = list(problem.think_is_false) + [user_id]
        db_sess.commit()
        check_truth(problem, db_sess)
        db_sess.close()
        return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())
    else:
        solution = db_sess.query(Solution).filter(Solution.id == publ_id).first()
        if not solution:
            abort(404)
        if user_id in solution.think_is_false:
            arr = list(solution.think_is_false)
            arr.remove(user_id)
            solution.think_is_false = arr
        else:
            if user_id in solution.think_is_true:
                arr = list(solution.think_is_true)
                arr.remove(user_id)
                solution.think_is_true = arr
            solution.think_is_false = list(solution.think_is_false) + [user_id]
        db_sess.commit()
        check_truth(solution, db_sess)
        db_sess.close()
        return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Человек нажал на кнопку верно
@login_required
@app.route('/istrue/<name>/<int:publ_id>/<int:user_id>')
def make_true(name, publ_id, user_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    if user_id != current_user.id:
        abort(404)
    db_sess = db_session.create_session()
    if name == "problem":
        problem = db_sess.query(Problem).filter(Problem.id == publ_id).first()
        if not problem:
            abort(404)
        if user_id in problem.think_is_true:
            arr = list(problem.think_is_true)
            arr.remove(user_id)
            problem.think_is_true = arr
        else:
            if user_id in problem.think_is_false:
                arr = list(problem.think_is_false)
                arr.remove(user_id)
                problem.think_is_false = arr
            problem.think_is_true = list(problem.think_is_true) + [user_id]
        db_sess.commit()
        check_truth(problem, db_sess)
        db_sess.close()
        return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())
    else:
        solution = db_sess.query(Solution).filter(Solution.id == publ_id).first()
        if not solution:
            abort(404)
        if user_id in solution.think_is_true:
            arr = list(solution.think_is_true)
            arr.remove(user_id)
            solution.think_is_true = arr
        else:
            if user_id in solution.think_is_false:
                arr = list(solution.think_is_false)
                arr.remove(user_id)
                solution.think_is_false = arr
            solution.think_is_true = list(solution.think_is_true) + [user_id]
        solution.is_true = not solution.is_true
        db_sess.commit()
        check_truth(solution, db_sess)
        db_sess.close()
        return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Подписка на кого-то
@login_required
@app.route('/subscribe/<int:user_id>/<int:viewer_id>')
def subscribe(user_id, viewer_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    if viewer_id != current_user.id:
        abort(404)
    db_sess = db_session.create_session()
    viewer = db_sess.query(User).filter(User.id == viewer_id).first()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if viewer.subscribes:
        arr = list(viewer.subscribes)
        if user_id in arr:
            arr.remove(user_id)
            user.subscribers_count -= 1
        else:
            arr.append(user_id)
            user.subscribers_count += 1
        viewer.subscribes = arr
    else:
        viewer.subscribes = [user_id]
        user.subscribers_count += 1
    db_sess.commit()
    db_sess.close()
    return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Пользователь стал постоянным читателем(теперь нужно автоматически добавлять его публикации пользователю)
@login_required
@app.route('/reader/<int:user_id>/<int:viewer_id>')
def become_reader(user_id, viewer_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    if viewer_id != current_user.id:
        abort(404)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if user.readers:
        arr = list(user.readers)
        if viewer_id in arr:
            arr.remove(viewer_id)
        else:
            arr.append(viewer_id)
        user.readers = arr
    else:
        user.readers = [viewer_id]
    db_sess.commit()
    db_sess.close()
    return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Добавить к прочтению
@login_required
@app.route('/addtoread/<int:user_id>/<name>/<int:cont_id>')
def add_toread(user_id, name, cont_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    if user_id != current_user.id:
        abort(404)
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if user.toread:
        if f'{name} {cont_id}' in user.toread:
            arr = list(user.toread)
            arr.remove(f'{name} {cont_id}')
            user.toread = arr
        else:
            user.toread = list(user.toread) + [f'{name} {cont_id}']
    else:
        user.toread = [f'{name} {cont_id}']
    db_sess.commit()
    db_sess.close()
    return render_template("nowindow.html", with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Нравится
@login_required
@app.route('/liked/<int:user_id>/<name>/<int:cont_id>')
def like(user_id, name, cont_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    if user_id != current_user.id:
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
        abort(404)
    if publ.liked_by is None or user_id not in publ.liked_by:
        publ.rank += user.get_rank()
        if not publ.liked_by:
            arr = []
        else:
            arr = list(publ.liked_by)
        arr.append(user_id)
        publ.liked_by = arr
    else:
        publ.rank -= user.get_rank()
        arr = list(publ.liked_by)
        arr.remove(user_id)
        publ.liked_by = arr
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
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    problem = db_sess.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        db_sess.close()
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
            db_sess.commit()
            fix_cats(problem, db_sess)
            db_sess.close()
            return redirect(f'/problem/{problem_id}')
        if solform.validate_on_submit():  # Кто-то написал решение к задаче
            solution = Solution()
            solution.content = solform.content.data
            solution.theme = problem.theme
            current_user.solutions.append(solution)
            db_sess.merge(current_user)
            solution = db_sess.merge(solution)
            problem.solutions.append(solution)
            db_sess.commit()
            fix_cats(problem, db_sess)
            db_sess.close()
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
                db_sess.commit()
                fix_cats(problem, db_sess)
                db_sess.close()
                return redirect(f'/problem/{problem_id}')
    res = make_response(
        render_template("problemshow.html", title="Задача", problem=problem, form=form, comment_forms=comment_forms,
                        solform=solform,
                        viewer=current_user, with_cats_show=with_cats_show, admin_message=get_adminmessage()))

    return res


# Показываем пост
@login_required
@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post_show(post_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    post = db_sess.query(Post).filter(Post.id == post_id).first()
    if not post:
        db_sess.close()
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
        db_sess.commit()
        fix_cats(post, db_sess)
        db_sess.close()
        return redirect(f'/post/{post_id}')
    res = make_response(
        render_template("postshow.html", title="Запись", post=post, form=form, viewer=current_user,
                        with_cats_show=with_cats_show, admin_message=get_adminmessage()))

    return res


# Показываем отложенные
@login_required
@app.route('/my')
def toread():
    if not current_user.is_authenticated:
        return redirect('/login')
    publs = []
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
    return render_template("toread.html", title='Отложенные', Post=Post, Problem=Problem,
                           publications=publs[::-1], isinstance=isinstance, viewer=current_user,
                           with_cats_show=with_cats_show, admin_message=get_adminmessage())


@login_required
@app.route('/')
def main_page():
    return redirect('/***/***/1 день/NOTEGS')


# Главная страница
# (геома, алгебра, комба) (посты, задачи с решениями, задачи без решений) '30 минут', '5 часов', '1 день', 'неделя', 'месяц', 'год', 'всё время'
@login_required
@app.route('/<cathegories>/<post_types>/<time>/<tegs>', methods=["POST", "GET"])
def index(cathegories, post_types, time, tegs: str):
    if not current_user.is_authenticated:
        return redirect('/login')
    form = NavForm()
    if form.validate_on_submit():  # Если кто-то заполнил фарму и нажал искать, мы его переадресовываем
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
    # Подбираем подходящии публикации
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
        reit += random.randrange(10)
        k = 0
        if tegs != "NOTEGS":
            for teg_name in tegs.split(","):
                teg_name.replace(' ', '')
                print(teg_name)
                category = db_sess.query(Category).filter(Category.name == teg_name).first()
                if category and category in publ.categories:
                    k += 1
                    tegs_found += 1
        reit += k * 350
        print(publ.id, reit)
        return reit

    publications.sort(key=interest, reverse=True)
    print(publications)
    if tegs_found or tegs == "NOTEGS":
        res = make_response(
            render_template("index.html", title='Лента', form=form, Post=Post, Problem=Problem,
                            publications=publications, isinstance=isinstance, viewer=current_user,
                            with_cats_show=with_cats_show, admin_message=get_adminmessage()))
    else:
        res = make_response(
            render_template("index.html", title='Лента', form=form, Post=Post, Problem=Problem,
                            publications=publications, isinstance=isinstance, viewer=current_user,
                            with_cats_show=with_cats_show, message="Таких тегов не существует",
                            admin_message=get_adminmessage()))

    return res


# Профиль
@login_required
@app.route('/profile/<int:user_id>')
def profile(user_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if not user:
        db_sess.close()
        return redirect("/")
    publs = sorted(list(user.posts) + list(user.problems), key=lambda x: x.created_date)[
            ::-1]
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
                        publ_count=db_sess.query(Post).count() + db_sess.query(Problem).count()
                        ))

    return res


# Отмена смены электронной почты
@login_required
@app.route('/abord_email_reseting/<int:user_id>')
def abord_email_reseting(user_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    user.new_email_code = ''
    db_sess.commit()
    db_sess.close()
    return redirect(f'/profile/{user_id}')


# Новый код смены почты
@login_required
@app.route('/reset_new_email_code/<int:user_id>')
def reset_new_email_code(user_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    user.new_email_code = ''.join([str(random.randrange(10)) for _ in range(6)])
    db_sess.commit()
    db_sess.close()
    return redirect(f'/new_email_verify/{user_id}')


# Подтверждение электронной почты
@login_required
@app.route('/new_email_verify/<int:user_id>', methods=['GET', 'POST'])
def verify_new_email(user_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if user.new_email_code == "":
        return redirect('/login')
    form = VerifyForm()
    if form.validate_on_submit():
        if user.new_email_code == form.code.data:
            user.new_email_code = ""
            user.email = user.new_email
            db_sess.commit()
            db_sess.close()
            return redirect('/login')
        else:
            return render_template("verifynew.html", title='Проверка почты', form=form, message='Неправильный код',
                                   user_id=user_id, admin_message=get_adminmessage())
    send_email(user.new_email, user.new_email_code, message_type="email_change")
    return render_template("verifynew.html", title='Проверка почты', form=form, user_id=user_id,
                           with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Смена электронной почты
@login_required
@app.route('/reset_email/<int:user_id>', methods=['GET', 'POST'])
def reset_email(user_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if not user:
        db_sess.close()
        abort(404)
    form = ResetEmailForm()
    if form.validate_on_submit():
        if not user.check_password(form.password.data):
            res = make_response(render_template('resetemail.html', title='Смена электронной почты',
                                                form=form,
                                                message="Неверный пароль", with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))
            return res
        if form.email.data != form.email_again.data:
            res = make_response(render_template('resetemail.html', title='Смена электронной почты',
                                                form=form,
                                                message="Адреса электронной почты не совпадают",
                                                with_cats_show=with_cats_show, admin_message=get_adminmessage()))
            return res
        if db_sess.query(User).filter(User.email == form.email.data).first():
            db_sess.close()
            res = make_response(render_template('resetemail.html', title='Смена электронной почты',
                                                form=form,
                                                message="Такой пользователь уже есть", with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))
            return res
        user.new_email = form.email.data
        db_sess.commit()
        return redirect(f'/reset_new_email_code/{user_id}')
    res = make_response(render_template('resetemail.html', title='Смена электронной почты',
                                        form=form, with_cats_show=with_cats_show, admin_message=get_adminmessage()))
    return res


# Редактирование профиля
@login_required
@app.route('/edit_profile/<int:user_id>', methods=["POST", "GET"])
def edit_profile(user_id):
    if not current_user.is_authenticated:
        return redirect('login')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if not user:
        db_sess.close()
        abort(404)
    if user.email != current_user.email:
        db_sess.close()
        abort(404)
    form = ProfileEditForm()
    if form.validate_on_submit():
        if not user.check_password(form.old_password.data):
            res = make_response(render_template('profileedit.html', form=form, title='Редактирование профиля',
                                                message='Неверный пароль', with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))

            return res
        if form.change_status.data:
            db_sess = db_session.create_session()
            res, status = check_code(form.secret_code.data, db_sess)
            if not res:
                res = make_response(render_template('profileedit.html', title='Редактирование профиля',
                                                    form=form,
                                                    code_message=status, with_cats_show=with_cats_show,
                                                    admin_message=get_adminmessage()))

                return res
        else:
            status = user.status
        if form.password.data != form.password_again.data:
            res = make_response(render_template('profileedit.html', title='Редактирование профиля',
                                                form=form,
                                                message="Пароли не совпадают", with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))

            return res
        user.name = form.name.data
        user.about = form.about.data
        user.status = status
        user.set_password(form.password.data)
        db_sess.commit()
        return redirect(f'/profile/{user_id}')
    form.name.data = user.name
    form.about.data = user.about
    res = make_response(
        render_template("profileedit.html", title='Редактирование профиля', form=form, with_cats_show=with_cats_show,
                        admin_message=get_adminmessage()))

    return res


def check_code(code, db_sess):
    reg_code = db_sess.query(RegCode).filter(RegCode.code == code).first()
    if not reg_code:
        return False, "Код недействителен"
    if datetime.now() - reg_code.created_date > timedelta(days=1):
        db_sess.delete(reg_code)
        db_sess.commit()
        db_sess.close()
        return False, "Время действи кода истекло"
    result = reg_code.status
    db_sess.delete(reg_code)
    db_sess.commit()
    db_sess.close()
    return True, result


# Генерация кода регистрации
@login_required
@app.route('/generate_code/<status>')
def gen_code(status):
    if not current_user.is_authenticated:
        return redirect('/login')
    statuses = {'администратор': 3, 'жюри': 2, 'преподаватель': 1, 'участник': 0}
    if statuses.get(status, 1000) > statuses[current_user.status]:
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

        res = make_response(
            render_template('codegen.html', title='Код приглашения', status=status, code=code,
                            with_cats_show=with_cats_show, admin_message=get_adminmessage()))

        return res


# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if not user:
            return make_response(render_template('login.html', title='Авторизация',
                                                 message="Неправильный логин или пароль",
                                                 form=form, with_cats_show=with_cats_show,
                                                 admin_message=get_adminmessage()))
        user_id = user.id
        if user.email_code != "":
            db_sess.close()
            return redirect(f'/email_verify/{user_id}')
        if user.new_email_code != "":
            print(user.new_email_code)
            db_sess.close()
            return redirect(f'/reset_new_email_code/{user_id}')
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            db_sess.close()
            return redirect(f"/profile/{user.id}")
        db_sess.close()
        res = make_response(render_template('login.html', title='Авторизация',
                                            message="Неправильный логин или пароль",
                                            form=form, with_cats_show=with_cats_show, admin_message=get_adminmessage()))

        return res
    res = make_response(render_template('login.html', title='Авторизация', form=form, with_cats_show=with_cats_show,
                                        admin_message=get_adminmessage()))

    return res


# Смена кода подтверждения почты
@app.route('/reset_email_code/<int:user_id>')
def reset_email_code(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    user.email_code = ''.join([str(random.randrange(10)) for _ in range(6)])
    db_sess.commit()
    db_sess.close()
    return redirect(f'/email_verify/{user_id}')


# Подтверждение почты
@app.route('/email_verify/<int:user_id>', methods=['GET', 'POST'])
def verify_email(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if user.email_code == "":
        return redirect('/login')
    form = VerifyForm()
    if form.validate_on_submit():
        if user.email_code == form.code.data:
            user.email_code = ""
            db_sess.commit()
            db_sess.close()
            return redirect('/login')
        else:
            return render_template("verify.html", title="Проверка почты", form=form, message='Неправильный код',
                                   user_id=user_id,
                                   with_cats_show=with_cats_show, admin_message=get_adminmessage())
    send_email(user.email, user.email_code)
    return render_template("verify.html", title="Проверка почты", form=form, user_id=user_id,
                           with_cats_show=with_cats_show, admin_message=get_adminmessage())


# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        res, status = check_code(form.secret_code.data, db_sess)
        if not res:
            res = make_response(render_template('register.html', title='Регистрация',
                                                form=form,
                                                code_message=status, with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))

            return res
        if form.password.data != form.password_again.data:
            res = make_response(render_template('register.html', title='Регистрация',
                                                form=form,
                                                message="Пароли не совпадают", with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))

            return res
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
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
        user.set_password(form.password.data)
        user.email_code = ''.join([str(random.randrange(10)) for _ in range(6)])
        db_sess.add(user)
        user_id = user.id
        db_sess.commit()
        user_id = user.id
        db_sess.close()
        return redirect(f'/email_verify/{user_id}')
    res = make_response(render_template('register.html', title='Регистрация', form=form, with_cats_show=with_cats_show,
                                        admin_message=get_adminmessage()))

    return res


# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# Добавление поста
@app.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    if not current_user.is_authenticated:
        return redirect('/login')
    form = PostAddForm()
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == current_user.id).first()
    user.add_name = 'post'
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
        for reader_id in (user.readers if user.readers is not None else []):
            reader = db_sess.query(User).filter(User.id == reader_id).first()
            arr = (list(reader.toread) if reader.toread is not None else [])
            arr.append('post ' + str(post.id))
            reader.toread = arr
            db_sess.commit()
        post_id = post.id
        db_sess.commit()
        db_sess.close()
        return redirect(f'/post/{post_id}')
    res = make_response(render_template('postadd.html', title='Добавление информации для размышления',
                                        form=form, with_cats_show=with_cats_show, admin_message=get_adminmessage()))

    return res


# Добавление задачи
@app.route('/add_problem', methods=['GET', 'POST'])
@login_required
def add_problem():
    if not current_user.is_authenticated:
        return redirect('/login')
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
        for reader_id in (user.readers if user.readers is not None else []):
            reader = db_sess.query(User).filter(User.id == reader_id).first()
            arr = (list(reader.toread) if reader.toread is not None else [])
            arr.append('problem ' + str(problem.id))
            reader.toread = arr
            db_sess.commit()
        db_sess.commit()
        if form.original_solution.data:
            solution = Solution()
            solution.content = form.original_solution.data
            solution.theme = problem.theme
            user.solutions.append(solution)
            problem.solutions.append(solution)
        problem_id = problem.id
        db_sess.commit()
        fix_cats(problem, db_sess)
        db_sess.close()
        return redirect(f'/problem/{problem_id}')
    res = make_response(render_template('problemadd.html', title='Добавление информации для размышления',
                                        form=form, with_cats_show=with_cats_show, admin_message=get_adminmessage()))

    return res


# Редактирование поста
@app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    if not current_user.is_authenticated:
        return redirect('/login')
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
            abort(404)
    if request.method == 'POST':
        db_sess = db_session.create_session()
        post = db_sess.query(Post).filter(Post.id == id,
                                          Post.user == current_user
                                          ).first()
        if not post:
            db_sess.close()
            abort(404)
        if form.validate_on_submit():
            post.title = form.title.data
            post.content = form.content.data
            post.theme = form.theme.data
            db_sess.commit()
            fix_cats(post, db_sess)
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
                    db_sess.close()
                    abort(400)
                users_file = UsersFile()
                users_file.name = file.filename
                users_file.extension = file_ext
                post.files.append(users_file)

                filename = f'{users_file.id}{file_ext}'
                file_path = os.path.join(os.path.join(basedir, 'static'),
                                         filename)
                file.save(file_path)
                push_file_to_GitHub(filename)
            if file_form.geogebra_link.data != '':
                users_file = UsersFile()
                users_file.extension = '.ggb'
                users_file.name = file_form.geogebra_link.data
                post.files.append(users_file)
            db_sess.commit()
            res = make_response(render_template('postedit.html', title='Редактирование', form=form,
                                                href=f"$edit_post${id}", publ=post,
                                                file_form=file_form, with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))
            return res
    res = make_response(render_template('postedit.html', title='Редактирование', form=form,
                                        href=f"$edit_post${id}", publ=post,
                                        file_form=file_form, with_cats_show=with_cats_show,
                                        admin_message=get_adminmessage()))

    return res


# Редактирование задачи
@app.route('/edit_problem/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_problem(id):  # without solution
    if not current_user.is_authenticated:
        return redirect('/login')
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
            abort(404)
    if request.method == "POST":

        db_sess = db_session.create_session()
        problem = db_sess.query(Problem).filter(Problem.id == id,
                                                Problem.user == current_user
                                                ).first()
        if not problem:
            db_sess.close()
            abort(404)
        if form.validate_on_submit():
            problem.content = form.content.data
            problem.theme = form.theme.data
            problem.notauthor = form.notauthor.data
            db_sess.commit()
            fix_cats(problem, db_sess)
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
                    db_sess.close()
                    abort(400)
                users_file = UsersFile()
                users_file.name = file.filename
                users_file.extension = file_ext
                problem.files.append(users_file)

                filename = f'{users_file.id}{file_ext}'
                file_path = os.path.join(os.path.join(basedir, 'static'),
                                         filename)
                file.save(file_path)
                push_file_to_GitHub(filename)
            if file_form.geogebra_link.data != '':
                users_file = UsersFile()
                users_file.extension = '.ggb'
                users_file.name = file_form.geogebra_link.data
                problem.files.append(users_file)
            db_sess.commit()
            form.content.data = problem.content
            res = make_response(render_template('problemedit.html', title='Редактирование', form=form,
                                                href=f"$edit_problem${id}", publ=problem,
                                                file_form=file_form, with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))
            return res
    res = make_response(render_template('problemedit.html',
                                        title='Редактирование',
                                        form=form, href=f"$edit_problem${id}", publ=problem, file_form=file_form,
                                        with_cats_show=with_cats_show, admin_message=get_adminmessage()))

    return res


# Удаление поста
@app.route('/delete_post/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_post(id):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    post = db_sess.query(Post).filter(Post.id == id,
                                      Post.user == current_user
                                      ).first()
    if post and not post.comments:
        db_sess.delete(post)
        db_sess.commit()
        db_sess.close()
    else:
        db_sess.close()
        abort(404)
    return redirect(current_user.profile_href())


# Удаление задачи
@app.route('/delete_problem/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_problem(id):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    problem = db_sess.query(Problem).filter(Problem.id == id,
                                            Problem.user == current_user
                                            ).first()
    if problem and not problem.comments and not problem.solutions:
        db_sess.delete(problem)
        db_sess.commit()
        db_sess.close()
    else:
        db_sess.close()
        abort(404)
    return redirect(current_user.profile_href())


# Редактирование комментария
@app.route('/edit_comment/<int:comment_id>/<place_name>/<int:place_id>/<par_name>/<int:par_id>',
           methods=["POST", "GET"])
@login_required
def edit_comment(comment_id, place_name, place_id, par_name, par_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    comment = None
    db_sess = db_session.create_session()
    form = CommentAddForm()
    file_form = FileAddForm()
    if par_name == 'post':
        comment = db_sess.query(Comment).filter(Comment.id == comment_id,
                                                Comment.user == current_user,
                                                Comment.post_id == par_id).first()
    elif par_name == 'problem':
        comment = db_sess.query(Comment).filter(Comment.id == comment_id,
                                                Comment.user == current_user,
                                                Comment.problem_id == par_id).first()
    elif par_name == 'solution':
        comment = db_sess.query(Comment).filter(Comment.id == comment_id,
                                                Comment.user == current_user,
                                                Comment.solution_id == par_id).first()
    else:
        db_sess.close()
        abort(404)
    if comment:
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
            return redirect(f'/{place_name}/{place_id}')
        if file_form.validate_on_submit():
            form.content.data = comment.content
            file = file_form.file.data
            if file.filename != '':
                file_ext = os.path.splitext(file.filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                    db_sess.close()
                    abort(400)
                users_file = UsersFile()
                users_file.name = file.filename
                users_file.extension = file_ext
                comment.files.append(users_file)

                filename = f'{users_file.id}{file_ext}'
                file_path = os.path.join(os.path.join(basedir, 'static'),
                                         filename)
                file.save(file_path)
                push_file_to_GitHub(filename)
            if file_form.geogebra_link.data != '':
                users_file = UsersFile()
                users_file.extension = '.ggb'
                users_file.name = file_form.geogebra_link.data
                comment.files.append(users_file)
            db_sess.commit()
            form.content.data = comment.content
            res = make_response(render_template('solutionedit.html', title='Редактирование', form=form,
                                                href=f"$edit_comment${comment_id}${place_name}${place_id}${par_name}${par_id}",
                                                publ=comment,
                                                file_form=file_form, with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))

            return res
    else:
        db_sess.close()
        abort(404)
    res = make_response(render_template('commentedit.html', title='Редактирование', form=form,
                                        href=f"$edit_comment${comment_id}${place_name}${place_id}${par_name}${par_id}",
                                        publ=comment,
                                        file_form=file_form, with_cats_show=with_cats_show,
                                        admin_message=get_adminmessage()))

    return res


# Удаление комментария
@app.route('/delete_comment/<int:comment_id>/<place_name>/<int:place_id>/<par_name>/<int:par_id>',
           methods=["POST", "GET"])
@login_required
def delete_comment(comment_id, place_name, place_id, par_name, par_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    comment = None
    db_sess = db_session.create_session()
    if par_name == 'post':
        comment = db_sess.query(Comment).filter(Comment.id == comment_id,
                                                Comment.user == current_user,
                                                Comment.post_id == par_id).first()
    elif par_name == 'problem':
        comment = db_sess.query(Comment).filter(Comment.id == comment_id,
                                                Comment.user == current_user,
                                                Comment.problem_id == par_id).first()
    elif par_name == 'solution':
        comment = db_sess.query(Comment).filter(Comment.id == comment_id,
                                                Comment.user == current_user,
                                                Comment.solution_id == par_id).first()
    else:
        db_sess.close()
        abort(404)
    if comment:
        db_sess.delete(comment)
        db_sess.commit()
        db_sess.close()
        return redirect(f'/{place_name}/{place_id}')
    else:
        db_sess.close()
        abort(404)


# Редактирование решения
@app.route('/edit_solution/<int:solution_id>/<int:problem_id>',
           methods=["POST", "GET"])
@login_required
def edit_solution(solution_id, problem_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    solution = None
    db_sess = db_session.create_session()
    form = SolutionAddForm()
    file_form = FileAddForm()
    solution = db_sess.query(Solution).filter(Solution.id == solution_id,
                                              Solution.user == current_user,
                                              Solution.problem_id == problem_id).first()
    if solution:
        if request.method == "GET":
            if not form.content.data:
                form.content.data = solution.content
        if form.validate_on_submit():
            solution.content = form.content.data
            db_sess.commit()
            fix_cats(solution.problem, db_sess)
            db_sess.close()
            return redirect(f'/problem/{problem_id}')
        if file_form.validate_on_submit():
            form.content.data = solution.content
            file = file_form.file.data
            if file.filename != '':
                file_ext = os.path.splitext(file.filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                    db_sess.close()
                    abort(400)
                users_file = UsersFile()
                users_file.name = file.filename
                users_file.extension = file_ext
                solution.files.append(users_file)

                filename = f'{users_file.id}{file_ext}'
                file_path = os.path.join(os.path.join(basedir, 'static'),
                                         filename)
                file.save(file_path)
                push_file_to_GitHub(filename)
            if file_form.geogebra_link.data != '':
                users_file = UsersFile()
                users_file.extension = '.ggb'
                users_file.name = file_form.geogebra_link.data
                solution.files.append(users_file)
            db_sess.commit()
            form.content.data = solution.content
            res = make_response(render_template('solutionedit.html', title='Редактирование', form=form,
                                                href=f"$edit_solution${solution_id}${problem_id}", publ=solution,
                                                file_form=file_form, with_cats_show=with_cats_show,
                                                admin_message=get_adminmessage()))

            return res
    else:
        db_sess.close()
        abort(404)

    res = make_response(render_template('solutionedit.html', title='Редактирование', form=form,
                                        href=f"$edit_solution${solution_id}${problem_id}", publ=solution,
                                        file_form=file_form, with_cats_show=with_cats_show,
                                        admin_message=get_adminmessage()))

    return res


# Удаление решения
@app.route('/delete_solution/<int:solution_id>/<int:problem_id>',
           methods=["POST", "GET"])
@login_required
def delete_solution(solution_id, problem_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    solution = None
    db_sess = db_session.create_session()
    solution = db_sess.query(Solution).filter(Solution.id == solution_id,
                                              Solution.user == current_user,
                                              Solution.problem_id == problem_id).first()
    if solution and not solution.comments:
        db_sess.delete(solution)
        db_sess.commit()
        db_sess.close()
        return redirect(f'/problem/{problem_id}')
    else:
        db_sess.close()
        abort(404)


def main():
    db_session.global_init(SQLALCHEMY_DATABASE_URI)
    print(generate_code('администратор'))
    print(generate_code('жюри'))
    print(generate_code('преподаватель'))
    # socketio.init_app(app, debug=True)

    db_sess = db_session.create_session()

    for users_file in db_sess.query(UsersFile).all():
        get_file_from_GitHub(UsersFile.name)

    db_sess.close()

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    # app.run(port=8080, host='127.0.0.1')

    """db_sess = db_session.create_session()


    user = db_sess.query(User).filter(User.id==1).first()
    problem = Problem()
    problem.content = 'условие'
    user.problems.append(problem)
    db_sess.commit()


    user = db_sess.query(User).filter(User.id == 2).first()
    problem = db_sess.query(Problem).filter(Problem.id==1).first()
    comment = Comment()
    comment.content = 'tekst2'
    user.comments.append(comment)
    problem.comments.append(comment)

    user = db_sess.query(User).filter(User.id == 1).first()
    problem = db_sess.query(Problem).filter(Problem.id == 1).first()
    comment = Comment()
    comment.content = 'tekst1'
    user.comments.append(comment)
    problem.comments.append(comment)

    user1 = db_sess.query(User).filter(User.id==1).first()
    user2 = db_sess.query(User).filter(User.id==2).first()
    solution = Solution()
    solution.content = 'решение'
    user1.solutions.append(solution)
    problem.solutions.append(solution)
    comment = Comment()
    comment.content = 'tekst3'
    user2.comments.append(comment)
    solution.comments.append(comment)


    db_sess.commit()"""

    """db_sess = db_session.create_session()
    user1 = db_sess.query(User).filter(User.id == 1).first()
    user2 = db_sess.query(User).filter(User.id == 2).first()
    post = Post()
    post.title = "Геома"
    post.content = "Больше геомы"
    user1.posts.append(post)
    comment = Comment()
    comment.content = 'Да, согласен'
    user2.comments.append(comment)
    post.comments.append(comment)

    db_sess.commit()"""


if __name__ == '__main__':
    main()
