from flask import Flask, render_template, redirect, request, url_for, make_response
from flask_restful import abort
from loginform import LoginForm
from data import db_session
from data.users import User
from data.post import Post
from data.problem import Problem
from solutionaddform import SolutionAddForm
from data.comment import Comment
from data.solution import Solution
from registerform import RegisterForm
from postaddform import PostAddForm
from commentaddform import CommentAddForm
from problemaddform import ProblemAddForm
from problemeditform import ProblemEditForm
from profileeditform import ProfileEditForm
from navform import NavForm
from secret_code import generate_code, check_code
from datetime import datetime, timedelta
import os
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = '/user_images'
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
login_manager = LoginManager()
login_manager.init_app(app)
basedir = os.path.abspath(os.curdir)


@app.route('/jstest')
def jstest():
    return render_template("jstest.html")

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
                           publications=publs[::-1], isinstance=isinstance, viewer=current_user)


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
    print(arr)
    if publ.is_false or publ.is_true or (not publ.think_is_false):
        if line in arr:
            arr.remove(line)
    elif publ.think_is_false:
        if line in arr:
            arr.remove(line)
        arr.append(line)
    print(arr)
    publ.user.wrong = arr
    db_sess.commit()

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
        return render_template("nowindow.html")
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
        return render_template("nowindow.html")

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
        return render_template("nowindow.html")
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
        return render_template("nowindow.html")

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
    return render_template("nowindow.html")

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
    return render_template("nowindow.html")

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
    return render_template("nowindow.html")

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
    return render_template("nowindow.html")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


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
        if form.validate_on_submit():
            comment = Comment()
            comment.content = form.content.data
            files_filenames = []
            k = 0
            for file in form.images.data:
                if file.filename != '':
                    k += 1
                    try:
                        f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'r')
                        n = int(f.read())
                        f.close()
                    except Exception as e:
                        n = 0

                    file_ext = os.path.splitext(file.filename)[1]
                    if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                        abort(400)
                    filename = f'img{n}.png'
                    file_path = os.path.join(os.path.join(basedir, 'static', 'user_images'), filename)
                    file.save(file_path)
                    files_filenames.append(filename)
                    n += 1
                    f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'w')
                    f.write(str(n))
                    f.close()
            if k > 0:
                comment.image_ids = files_filenames
            else:
                comment.image_ids = []
            current_user.comments.append(comment)
            db_sess.merge(current_user)
            comment = db_sess.merge(comment)
            problem.comments.append(comment)
            db_sess.commit()
            db_sess.close()
            return redirect(f'/problem/{problem_id}')
        if solform.validate_on_submit():
            solution = Solution()
            solution.content = solform.content.data
            files_filenames = []
            k = 0
            for file in solform.images.data:
                if file.filename != '':
                    k += 1
                    try:
                        f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'r')
                        n = int(f.read())
                        f.close()
                    except Exception as e:
                        n = 0

                    file_ext = os.path.splitext(file.filename)[1]
                    if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                        abort(400)
                    filename = f'img{n}.png'
                    file_path = os.path.join(os.path.join(basedir, 'static', 'user_images'), filename)
                    file.save(file_path)
                    files_filenames.append(filename)
                    n += 1
                    f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'w')
                    f.write(str(n))
                    f.close()
            if k > 0:
                solution.image_ids = files_filenames
            else:
                solution.image_ids = []
            solution.theme = problem.theme
            current_user.solutions.append(solution)
            db_sess.merge(current_user)
            solution = db_sess.merge(solution)
            problem.solutions.append(solution)
            db_sess.commit()
            db_sess.close()
            return redirect(f'/problem/{problem_id}')
        for i in range(len(comment_forms)):
            if comment_forms[i].validate_on_submit():
                comment = Comment()
                comment.content = comment_forms[i].content.data
                files_filenames = []
                k = 0
                for file in comment_forms[i].images.data:
                    if file.filename != '':
                        k += 1
                        try:
                            f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'r')
                            n = int(f.read())
                            f.close()
                        except Exception as e:
                            n = 0

                        file_ext = os.path.splitext(file.filename)[1]
                        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                            abort(400)
                        filename = f'img{n}.png'
                        file_path = os.path.join(os.path.join(basedir, 'static', 'user_images'), filename)
                        file.save(file_path)
                        files_filenames.append(filename)
                        n += 1
                        f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'w')
                        f.write(str(n))
                        f.close()
                if k > 0:
                    comment.image_ids = files_filenames
                else:
                    comment.image_ids = []
                current_user.comments.append(comment)
                db_sess.merge(current_user)
                comment = db_sess.merge(comment)
                solution = problem.solutions[i]
                comment.theme = solution.theme
                solution.comments.append(comment)
                db_sess.commit()
                db_sess.close()
                return redirect(f'/problem/{problem_id}')
    res = make_response(
        render_template("problemshow.html", problem=problem, form=form, comment_forms=comment_forms, solform=solform,
                        viewer=current_user))

    return res


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
    if form.validate_on_submit():
        comment = Comment()
        comment.content = form.content.data
        files_filenames = []
        k = 0
        for file in form.images.data:
            if file.filename != '':
                k += 1
                try:
                    f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'r')
                    n = int(f.read())
                    f.close()
                except Exception as e:
                    n = 0

                file_ext = os.path.splitext(file.filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                    abort(400)
                filename = f'img{n}.png'
                file_path = os.path.join(os.path.join(basedir, 'static', 'user_images'), filename)
                file.save(file_path)
                files_filenames.append(filename)
                n += 1
                f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'w')
                f.write(str(n))
                f.close()
        if k > 0:
            comment.image_ids = files_filenames
        else:
            comment.image_ids = []
        comment.theme = post.theme
        current_user.comments.append(comment)
        db_sess.merge(current_user)
        comment = db_sess.merge(comment)
        post.comments.append(comment)
        db_sess.commit()
        db_sess.close()
        return redirect(f'/post/{post_id}')
    res = make_response(render_template("postshow.html", post=post, form=form, viewer=current_user))

    return res


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
                           publications=publs[::-1], isinstance=isinstance, viewer=current_user)

@login_required
@app.route('/')
def main_page():
    return redirect('/***/***/30 минут')


# (геома, алгебра, комба) (посты, задачи с решениями, задачи без решений) '30 минут', '5 часов', '1 день', 'неделя', 'месяц', 'год', 'всё время'
@login_required
@app.route('/<cathegories>/<post_types>/<time>', methods=["POST", "GET"])
def index(cathegories, post_types, time):  # TODO добавить функцию упорядочивания по рейтингу, времени и т п
    if not current_user.is_authenticated:
        return redirect('/login')
    form = NavForm()
    if form.validate_on_submit():
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
        s = f'/{cats}/{typs}/{form.time.data}'
        return redirect(s)
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
    form.time.data = time
    now = datetime.now()
    timedist = {'30 минут': timedelta(minutes=30), '5 часов': timedelta(hours=5), '1 день': timedelta(days=1),
                'неделя': timedelta(weeks=1), 'месяц': timedelta(days=30), 'год': timedelta(days=365),
                'всё время': timedelta(days=365 * (now.year - 1))}[time]
    oldest = now - timedist
    db_sess = db_session.create_session()
    good_themes = [i for i in range(3) if cats[i] == '*']
    if form.posts.data:
        posts = list(db_sess.query(Post).filter(Post.created_date > oldest,
                                                Post.theme.in_(good_themes)).all())
    else:
        posts = []
    solprobs = []
    nosolprobs = []
    for problem in db_sess.query(Problem).filter(Problem.created_date > oldest, Problem.theme.in_(good_themes)).all():
        if problem.solutions and form.solprob.data:
            solprobs.append(problem)
        elif not problem.solutions and form.nosolprob.data:
            nosolprobs.append(problem)
    publications = posts + solprobs + nosolprobs

    def interest(publ):
        reit = 0
        if publ.user.id in current_user.subscribes:
            reit += 100 + random.randrange(100)
        reit += publ.rank
        if (datetime.now() - publ.created_date).seconds < 60 * 15:
            reit += 100
        reit+=random.randrange(50)
        return reit

    publications.sort(key=interest, reverse=True)
    res = make_response(render_template("index.html", title='Домашняя страница', form=form, Post=Post, Problem=Problem,
                                        publications=publications, isinstance=isinstance, viewer=current_user))

    return res


@login_required
@app.route('/profile/<int:user_id>')
def profile(user_id):  # TODO check time order
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if not user:
        db_sess.close()
        return redirect("/")
    publs = sorted(list(user.posts) + list(user.problems), key=lambda x: x.created_date)[
            ::-1]  # TODO check how reiting works
    res = make_response(
        render_template("profile.html", user=user, viewer=current_user, publications=publs, isinstance=isinstance,
                        Post=Post, Problem=Problem,
                        subscribers=user.subscribers_count, readers=(0 if not user.readers else len(user.readers)),
                        geom1=user.get_rank('0', creating_only=True),
                        alg1=user.get_rank('1', creating_only=True), comb1=user.get_rank('2', creating_only=True),
                        geom2=user.get_rank('0'),
                        alg2=user.get_rank('1'), comb2=user.get_rank('2'),
                        ))

    return res


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
                                                message='Неверный пароль'))

            return res
        if form.change_status.data:
            res, status = check_code(form.secret_code.data)
            if not res:
                res = make_response(render_template('profileedit.html', title='Редактирование профиля',
                                                    form=form,
                                                    code_message=status))

                return res
        else:
            status = user.status
        if form.password.data != form.password_again.data:
            res = make_response(render_template('profileedit.html', title='Редактирование профиля',
                                                form=form,
                                                message="Пароли не совпадают"))

            return res
        if user.email != form.email.data:
            if db_sess.query(User).filter(User.email == form.email.data).first():
                db_sess.close()
                res = make_response(render_template('profileedit.html', title='Редактирование профиля',
                                                    form=form,
                                                    message="Такой пользователь уже есть"))

                return res
        user.email = form.email.data
        user.name = form.name.data
        user.about = form.about.data
        user.status = status
        user.set_password(form.password.data)
        db_sess.commit()
        return redirect(f'/profile/{user_id}')
    form.email.data = user.email
    form.name.data = user.name
    form.about.data = user.about
    res = make_response(render_template("profileedit.html", title='Редактирование профиля', form=form))

    return res


@login_required
@app.route('/generate_code/<status>')
def gen_code(status):
    if not current_user.is_authenticated:
        return redirect('/login')
    statuses = {'админ': 3, 'жюри': 2, 'преподаватель': 1, 'участник': 0}
    if statuses.get(status, 1000) > statuses[current_user.status]:
        return redirect('/')
    else:
        res = make_response(render_template('codegen.html', status=status, code=generate_code(status)))

        return res


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            db_sess.close()
            return redirect(f"/profile/{user.id}")
        db_sess.close()
        res = make_response(render_template('login.html',
                                            message="Неправильный логин или пароль",
                                            form=form))

        return res
    res = make_response(render_template('login.html', title='Авторизация', form=form))

    return res


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        res, status = check_code(form.secret_code.data)
        if not res:
            res = make_response(render_template('register.html', title='Регистрация',
                                                form=form,
                                                code_message=status))

            return res
        if form.password.data != form.password_again.data:
            res = make_response(render_template('register.html', title='Регистрация',
                                                form=form,
                                                message="Пароли не совпадают"))

            return res
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            db_sess.close()
            res = make_response(render_template('register.html', title='Регистрация',
                                                form=form,
                                                message="Такой пользователь уже есть"))

            return res
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data,
            status=status
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        db_sess.close()
        return redirect('/login')
    res = make_response(render_template('register.html', title='Регистрация', form=form))

    return res


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    form = PostAddForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        post = Post()
        post.title = form.title.data
        post.content = form.content.data
        post.theme = form.theme.data
        files_filenames = []
        k = 0
        for file in form.images.data:
            if file.filename != '':
                k += 1
                try:
                    f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'r')
                    n = int(f.read())
                    f.close()
                except Exception as e:
                    n = 0

                file_ext = os.path.splitext(file.filename)[1]
                if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                    abort(400)
                filename = f'img{n}.png'
                file_path = os.path.join(os.path.join(basedir, 'static', 'user_images'), filename)
                file.save(file_path)
                files_filenames.append(filename)
                n += 1
                f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'w')
                f.write(str(n))
                f.close()
        if k > 0:
            post.image_ids = files_filenames
        else:
            post.image_ids = []
        current_user.posts.append(post)
        user = db_sess.merge(current_user)
        db_sess.commit()
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
                                        form=form))

    return res


@app.route('/add_problem', methods=['GET', 'POST'])
@login_required
def add_problem():
    form = ProblemAddForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        problem = Problem()
        problem.content = form.content.data
        problem.theme = form.theme.data
        problem.notauthor = form.notauthor.data
        files_filenames = []
        k = 0
        for file in form.images.data:
            if file.filename != '':
                k += 1
                try:
                    f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'r')
                    n = int(f.read())
                    f.close()
                except Exception as e:
                    n = 0

                    file_ext = os.path.splitext(file.filename)[1]
                    if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                        abort(400)
                filename = f'img{n}.png'
                file_path = os.path.join(os.path.join(basedir, 'static', 'user_images'), filename)
                file.save(file_path)
                files_filenames.append(filename)
                n += 1
                f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'w')
                f.write(str(n))
                f.close()
        if k > 0:
            problem.image_ids = files_filenames
        else:
            problem.image_ids = []
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
        if not form.nosolution.data and form.original_solution.data:
            solution = Solution()
            solution.content = form.original_solution.data
            sol_files_filenames = []
            k = 0
            for file in form.solution_images.data:
                k += 1
                if file.filename != '':
                    try:
                        f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'r')
                        n = int(f.read())
                        f.close()
                    except Exception as e:
                        n = 0

                    file_ext = os.path.splitext(file.filename)[1]
                    if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                        abort(400)
                    filename = f'img{n}.png'
                    file_path = os.path.join(os.path.join(basedir, 'static', 'user_images'), filename)
                    file.save(file_path)
                    sol_files_filenames.append(filename)
                    n += 1
                    f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'w')
                    f.write(str(n))
                    f.close()
            if k > 0:
                solution.image_ids = sol_files_filenames
            else:
                solution.image_ids = []
            solution.theme = problem.theme
            user.solutions.append(solution)
            problem.solutions.append(solution)
        problem_id = problem.id
        db_sess.commit()
        db_sess.close()
        return redirect(f'/problem/{problem_id}')
    res = make_response(render_template('problemadd.html', title='Добавление информации для размышления',
                                        form=form))

    return res


@app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    form = PostAddForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        post = db_sess.query(Post).filter(Post.id == id,
                                          Post.user == current_user
                                          ).first()
        if post:
            form.title.data = post.title
            form.content.data = post.content
            # form.images.data = [FileStorage(open(os.path.join(basedir,'static','user_images',filename))) for filename in post.image_ids]
        else:
            db_sess.close()
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        post = db_sess.query(Post).filter(Post.id == id,
                                          Post.user == current_user
                                          ).first()
        if post:
            post.title = form.title.data
            post.content = form.content.data
            post.theme = form.theme.data
            k = 0
            files_filenames = []
            if form.images.data:
                for file in form.images.data:
                    if file.filename != '':
                        k += 1
                        try:
                            f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'r')
                            n = int(f.read())
                            f.close()
                        except Exception as e:
                            n = 0

                            file_ext = os.path.splitext(file.filename)[1]
                            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                                db_sess.close()
                                abort(400)
                        filename = f'img{n}.png'
                        file_path = os.path.join(os.path.join(basedir, 'static', 'user_images'),
                                                 filename)
                        file.save(file_path)
                        files_filenames.append(filename)
                        n += 1
                        f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'w')
                        f.write(str(n))
                        f.close()
            if form.delete_old_images.data:
                if k != 0:
                    post.image_ids = files_filenames
                else:
                    post.image_ids = []
            else:
                if k != 0:
                    new_files_filenames = list(post.image_ids) + files_filenames
                    post.image_ids = new_files_filenames
                    db_sess.commit()
            db_sess.commit()
            db_sess.close()
            return redirect(f'/post/{id}')
        else:
            db_sess.close()
            abort(404)
    res = make_response(render_template('postedit.html',
                                        title='Редактирование',
                                        form=form))

    return res


@app.route('/edit_problem/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_problem(id):  # without solution
    form = ProblemEditForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        problem = db_sess.query(Problem).filter(Problem.id == id,
                                                Problem.user == current_user
                                                ).first()
        if problem:
            form.content.data = problem.content
        else:
            db_sess.close()
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        problem = db_sess.query(Problem).filter(Problem.id == id,
                                                Problem.user == current_user
                                                ).first()
        if problem:
            problem.content = form.content.data
            problem.theme = form.theme.data
            problem.notauthor = form.notauthor.data
            k = 0
            files_filenames = []
            if form.images.data:
                for file in form.images.data:
                    if file.filename != '':
                        k += 1
                        try:
                            f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'r')
                            n = int(f.read())
                            f.close()
                        except Exception as e:
                            n = 0

                            file_ext = os.path.splitext(file.filename)[1]
                            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                                db_sess.close()
                                abort(400)
                        filename = f'img{n}.png'
                        file_path = os.path.join(os.path.join(basedir, 'static', 'user_images'),
                                                 filename)
                        file.save(file_path)
                        files_filenames.append(filename)
                        n += 1
                        f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'w')
                        f.write(str(n))
                        f.close()
            if form.delete_old_images.data:
                if k != 0:
                    problem.image_ids = files_filenames
                else:
                    problem.image_ids = []
            else:
                if k != 0:
                    new_files_filenames = list(problem.image_ids) + files_filenames
                    problem.image_ids = new_files_filenames
                    db_sess.commit()
            db_sess.commit()
            db_sess.close()
            return redirect(f'/problem/{id}')
        else:
            db_sess.close()
            abort(404)
    res = make_response(render_template('problemedit.html',
                                        title='Редактирование',
                                        form=form))

    return res


@app.route('/delete_post/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_post(id):
    db_sess = db_session.create_session()
    post = db_sess.query(Post).filter(Post.id == id,
                                      Post.user == current_user
                                      ).first()
    if post and not post.comments:  # TODO добавить неверные задачи,решения...
        db_sess.delete(post)
        db_sess.commit()
        db_sess.close()
    else:
        db_sess.close()
        abort(404)
    return redirect(current_user.profile_href())


@app.route('/delete_problem/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_problem(id):
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


@app.route('/edit_comment/<int:comment_id>/<place_name>/<int:place_id>/<par_name>/<int:par_id>',
           methods=["POST", "GET"])
@login_required
def edit_comment(comment_id, place_name, place_id, par_name, par_id):
    comment = None
    db_sess = db_session.create_session()
    form = CommentAddForm()
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
            form.content.data = comment.content
        if form.validate_on_submit():
            comment.content = form.content.data
            k = 0
            files_filenames = []
            if form.images.data:
                for file in form.images.data:
                    if file.filename != '':
                        k += 1
                        try:
                            f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'r')
                            n = int(f.read())
                            f.close()
                        except Exception as e:
                            n = 0

                            file_ext = os.path.splitext(file.filename)[1]
                            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                                db_sess.close()
                                abort(400)
                        filename = f'img{n}.png'
                        file_path = os.path.join(os.path.join(basedir, 'static', 'user_images'),
                                                 filename)
                        file.save(file_path)
                        files_filenames.append(filename)
                        n += 1
                        f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'w')
                        f.write(str(n))
                        f.close()
            if form.delete_old_images.data:
                if k != 0:
                    comment.image_ids = files_filenames
                else:
                    comment.image_ids = []
            else:
                if k != 0:
                    new_files_filenames = list(comment.image_ids) + files_filenames
                    comment.image_ids = new_files_filenames
                    db_sess.commit()
            db_sess.commit()
            db_sess.close()
            return redirect(f'/{place_name}/{place_id}')
    else:
        db_sess.close()
        abort(404)
    res = make_response(render_template('comsoledit.html', title='Редактирование', form=form))

    return res


@app.route('/delete_comment/<int:comment_id>/<place_name>/<int:place_id>/<par_name>/<int:par_id>',
           methods=["POST", "GET"])
@login_required
def delete_comment(comment_id, place_name, place_id, par_name, par_id):
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


@app.route('/edit_solution/<int:solution_id>/<int:problem_id>',
           methods=["POST", "GET"])
@login_required
def edit_solution(solution_id, problem_id):
    solution = None
    db_sess = db_session.create_session()
    form = SolutionAddForm()
    solution = db_sess.query(Solution).filter(Solution.id == solution_id,
                                              Solution.user == current_user,
                                              Solution.problem_id == problem_id).first()
    if solution:
        if request.method == "GET":
            form.content.data = solution.content
        if form.validate_on_submit():
            solution.content = form.content.data
            k = 0
            files_filenames = []
            if form.images.data:
                for file in form.images.data:
                    if file.filename != '':
                        k += 1
                        try:
                            f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'r')
                            n = int(f.read())
                            f.close()
                        except Exception as e:
                            n = 0

                            file_ext = os.path.splitext(file.filename)[1]
                            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                                db_sess.close()
                                abort(400)
                        filename = f'img{n}.png'
                        file_path = os.path.join(os.path.join(basedir, 'static', 'user_images'),
                                                 filename)
                        file.save(file_path)
                        files_filenames.append(filename)
                        n += 1
                        f = open(os.path.join(basedir, 'static', 'imgcount.txt'), 'w')
                        f.write(str(n))
                        f.close()
            if form.delete_old_images.data:
                if k != 0:
                    solution.image_ids = files_filenames
                else:
                    solution.image_ids = []
            else:
                if k != 0:
                    new_files_filenames = list(solution.image_ids) + files_filenames
                    solution.image_ids = new_files_filenames
                    db_sess.commit()
            db_sess.commit()
            db_sess.close()
            return redirect(f'/problem/{problem_id}')
    else:
        db_sess.close()
        abort(404)
    res = make_response(render_template('comsoledit.html', title='Редактирование', form=form))

    return res


@app.route('/delete_solution/<int:solution_id>/<int:problem_id>',
           methods=["POST", "GET"])
@login_required
def delete_solution(solution_id, problem_id):
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
    db_session.global_init("db/blogs.db")
    print(generate_code('админ'))
    print(generate_code('жюри'))
    print(generate_code('преподаватель'))
    # socketio.init_app(app, debug=True)

    db_sess = db_session.create_session()
    db_sess.close()

    app.run(port=8080, host='127.0.0.1')
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
