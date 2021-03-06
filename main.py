from flask import Flask, render_template, redirect, request, url_for, make_response
from flask_socketio import SocketIO
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

async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = '/user_images'
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
login_manager = LoginManager()
login_manager.init_app(app)
basedir = os.path.abspath(os.curdir)
socketio = SocketIO(app, async_mode=async_mode, logger=True)


def docookies():
    user_actions = request.cookies.get("user_actions", '')
    db_sess = db_session.create_session()
    for line in user_actions.split(';'):
        text = line.split()
        if text[0] == 'like':
            if text[2] == 'post':
                post = db_sess.query(Post).filter(Post.id == int(text[3])).first()
                post.rank += float(text[4])
            if text[2] == 'problem':
                problem = db_sess.query(Problem).filter(Problem.id == int(text[3])).first()
                problem.rank += float(text[4])
            if text[2] == 'solution':
                solution = db_sess.query(Solution).filter(Solution.id == int(text[3])).first()
                solution.rank += float(text[4])
            if text[2] == 'comment':
                comment = db_sess.query(Comment).filter(Comment.id == int(text[3])).first()
                comment.rank += float(text[4])
        if text[0] == 'dislike':
            if text[2] == 'post':
                post = db_sess.query(Post).filter(Post.id == int(text[3])).first()
                post.rank -= float(text[4])
            if text[2] == 'problem':
                problem = db_sess.query(Problem).filter(Problem.id == int(text[3])).first()
                problem.rank -= float(text[4])
            if text[2] == 'solution':
                solution = db_sess.query(Solution).filter(Solution.id == int(text[3])).first()
                solution.rank -= float(text[4])
            if text[2] == 'comment':
                comment = db_sess.query(Comment).filter(Comment.id == int(text[3])).first()
                comment.rank -= float(text[4])
        if text[0] == 'toread':
            if text[2] == 'post':
                post = db_sess.query(Post).filter(Post.id == int(text[3])).first()
                post.rank += float(text[4]) / 2
            if text[2] == 'problem':
                problem = db_sess.query(Problem).filter(Problem.id == int(text[3])).first()
                problem.rank += float(text[4]) / 2
            user = db_sess.query(User).filter(User.id == int(text[1]))
            user.toread = list(user.toread) + [text[2] + ' ' + text[3]]
    db_sess.commit()
    db_sess.close()


@socketio.on('client_disconnecting')
def disconnect_details(data):
    print(123)


@socketio.on('disconnect_request')
def disconnect():
    print(123)


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
        res = make_response("?? ?????????????????? ?????????? ???????????? ??????")
        res.set_cookie('user_actions', '')
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
                solution.comments.append(comment)
                db_sess.commit()
                db_sess.close()
                return redirect(f'/problem/{problem_id}')
    res = make_response(
        render_template("problemshow.html", problem=problem, form=form, comment_forms=comment_forms, solform=solform,
                        viewer=current_user,
                        sync_mode=socketio.async_mode))
    res.set_cookie('user_actions', '')
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
        res = make_response("?? ?????????????????? ?????????? ???????????? ??????")
        res.set_cookie('user_actions', '')
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
        current_user.comments.append(comment)
        db_sess.merge(current_user)
        comment = db_sess.merge(comment)
        post.comments.append(comment)
        db_sess.commit()
        db_sess.close()
        return redirect(f'/post/{post_id}')
    res = make_response(render_template("postshow.html", post=post, form=form, viewer=current_user,
                                        sync_mode=socketio.async_mode))
    res.set_cookie('user_actions', '')
    return res


@login_required
@app.route('/my')
def toread():
    if not current_user.is_authenticated:
        return redirect('/login')
    pass


@app.route('/')
def main_page():
    return redirect('/***/***/30 ??????????')


# (??????????, ??????????????, ??????????) (??????????, ???????????? ?? ??????????????????, ???????????? ?????? ??????????????) '30 ??????????', '5 ??????????', '1 ????????', '????????????', '??????????', '??????', '?????? ??????????'
@app.route('/<cathegories>/<post_types>/<time>', methods=["POST", "GET"])
def index(cathegories, post_types, time):
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
    timedist = {'30 ??????????': timedelta(minutes=30), '5 ??????????': timedelta(hours=5), '1 ????????': timedelta(days=1),
                '????????????': timedelta(weeks=1), '??????????': timedelta(days=30), '??????': timedelta(days=365),
                '?????? ??????????': timedelta(days=365 * (now.year - 1))}[time]
    oldest = now - timedist
    db_sess = db_session.create_session()
    good_themes = [i for i in range(3) if cats[i] == '*']
    if form.posts.data:
        posts = list(db_sess.query(Post).filter(Post.created_date > oldest,
                                                Post.theme.in_(good_themes)).all())  # TODO ???????????????? ???????? ????????????
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
    res = make_response(render_template("index.html", title='???????????????? ????????????????', form=form, Post=Post, Problem=Problem,
                                        publications=publications, isinstance=isinstance,
                                        sync_mode=socketio.async_mode))
    res.set_cookie('user_actions', '')
    return res


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
    res = make_response(
        render_template("profile.html", user=user, viewer=current_user, friends=1, subscribers=2, readers=3,
                        geom1=60, alg1=30, comb1=95,
                        geom2=0, alg2=100, comb2=35,
                        sync_mode=socketio.async_mode))
    res.set_cookie('user_actions', '')
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
            res = make_response(render_template('profileedit.html', form=form, title='???????????????????????????? ??????????????',
                                                message='???????????????? ????????????',
                                                sync_mode=socketio.async_mode))
            res.set_cookie('user_actions', '')
            return res
        if form.change_status.data:
            res, status = check_code(form.secret_code.data)
            if not res:
                res = make_response(render_template('profileedit.html', title='???????????????????????????? ??????????????',
                                                    form=form,
                                                    code_message=status,
                                                    sync_mode=socketio.async_mode))
                res.set_cookie('user_actions', '')
                return res
        else:
            status = user.status
        if form.password.data != form.password_again.data:
            res = make_response(render_template('profileedit.html', title='???????????????????????????? ??????????????',
                                                form=form,
                                                message="???????????? ???? ??????????????????",
                                                sync_mode=socketio.async_mode))
            res.set_cookie('user_actions', '')
            return res
        if user.email != form.email.data:
            if db_sess.query(User).filter(User.email == form.email.data).first():
                db_sess.close()
                res = make_response(render_template('profileedit.html', title='???????????????????????????? ??????????????',
                                                    form=form,
                                                    message="?????????? ???????????????????????? ?????? ????????",
                                                    sync_mode=socketio.async_mode))
                res.set_cookie('user_actions', '')
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
    res = make_response(render_template("profileedit.html", title='???????????????????????????? ??????????????', form=form,
                                        sync_mode=socketio.async_mode))
    res.set_cookie('user_actions', '')
    return res


@login_required
@app.route('/generate_code/<status>')
def gen_code(status):
    if not current_user.is_authenticated:
        return redirect('/login')
    statuses = {'??????????': 3, '????????': 2, '??????????????????????????': 1, '????????????????': 0}
    if statuses.get(status, 1000) > statuses[current_user.status]:
        return redirect('/')
    else:
        res = make_response(render_template('codegen.html', status=status, code=generate_code(status),
                                            sync_mode=socketio.async_mode))
        res.set_cookie('user_actions', '')
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
                                            message="???????????????????????? ?????????? ?????? ????????????",
                                            form=form,
                                            sync_mode=socketio.async_mode))
        res.set_cookie('user_actions', '')
        return res
    res = make_response(render_template('login.html', title='??????????????????????', form=form,
                                        sync_mode=socketio.async_mode))
    res.set_cookie('user_actions', '')
    return res


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        res, status = check_code(form.secret_code.data)
        if not res:
            res = make_response(render_template('register.html', title='??????????????????????',
                                                form=form,
                                                code_message=status,
                                                sync_mode=socketio.async_mode))
            res.set_cookie('user_actions', '')
            return res
        if form.password.data != form.password_again.data:
            res = make_response(render_template('register.html', title='??????????????????????',
                                                form=form,
                                                message="???????????? ???? ??????????????????",
                                                sync_mode=socketio.async_mode))
            res.set_cookie('user_actions', '')
            return res
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            db_sess.close()
            res = make_response(render_template('register.html', title='??????????????????????',
                                                form=form,
                                                message="?????????? ???????????????????????? ?????? ????????",
                                                sync_mode=socketio.async_mode))
            res.set_cookie('user_actions', '')
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
    res = make_response(render_template('register.html', title='??????????????????????', form=form,
                                        sync_mode=socketio.async_mode))
    res.set_cookie('user_actions', '')
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
        db_sess.close()
        return redirect(f'/post/{post.id}')
    res = make_response(render_template('postadd.html', title='???????????????????? ???????????????????? ?????? ??????????????????????',
                                        form=form,
                                        sync_mode=socketio.async_mode))
    res.set_cookie('user_actions', '')
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
        db_sess.commit()
        problem = user.problems[-1]
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
            user.solutions.append(solution)
            problem.solutions.append(solution)
        db_sess.commit()
        problem_id = problem.id
        db_sess.close()
        return redirect(f'/problem/{problem_id}')
    res = make_response(render_template('problemadd.html', title='???????????????????? ???????????????????? ?????? ??????????????????????',
                                        form=form,
                                        sync_mode=socketio.async_mode))
    res.set_cookie('user_actions', '')
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
                                        title='????????????????????????????',
                                        form=form,
                                        sync_mode=socketio.async_mode
                                        ))
    res.set_cookie('user_actions', '')
    return res


@app.route('/edit_problem/<int:id>', methods=['GET', 'POST'])
@login_required  # TODO fix problem original solution
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
                                        title='????????????????????????????',
                                        form=form,
                                        sync_mode=socketio.async_mode
                                        ))
    res.set_cookie('user_actions', '')
    return res


@app.route('/delete_post/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_post(id):
    db_sess = db_session.create_session()
    post = db_sess.query(Post).filter(Post.id == id,
                                      Post.user == current_user
                                      ).first()
    if post and not post.comments:  # TODO check likes
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
    if problem and not problem.comments and not problem.solutions:  # TODO check likes
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
    res = make_response(render_template('comsoledit.html', title='????????????????????????????', form=form,
                                        sync_mode=socketio.async_mode))
    res.set_cookie('user_actions', '')
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
    res = make_response(render_template('comsoledit.html', title='????????????????????????????', form=form,
                                        sync_mode=socketio.async_mode))
    res.set_cookie('user_actions', '')
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
    if solution and not solution.comments:  # TODO check likes
        db_sess.delete(solution)
        db_sess.commit()
        db_sess.close()
        return redirect(f'/problem/{problem_id}')
    else:
        db_sess.close()
        abort(404)


def main():
    db_session.global_init("db/blogs.db")
    print(generate_code('??????????'))
    print(generate_code('????????'))
    print(generate_code('??????????????????????????'))
    # socketio.init_app(app, debug=True)
    app.run(port=8080, host='127.0.0.1')
    # app.run(port=8080, host='127.0.0.1')
    """db_sess = db_session.create_session()


    user = db_sess.query(User).filter(User.id==1).first()
    problem = Problem()
    problem.content = '??????????????'
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
    solution.content = '??????????????'
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
    post.title = "??????????"
    post.content = "???????????? ??????????"
    user1.posts.append(post)
    comment = Comment()
    comment.content = '????, ????????????????'
    user2.comments.append(comment)
    post.comments.append(comment)

    db_sess.commit()"""


if __name__ == '__main__':
    main()
