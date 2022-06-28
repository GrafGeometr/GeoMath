from flask import Flask, render_template, redirect, request, url_for
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
from postform import PostForm
from commentaddform import CommentAddForm
from secret_code import generate_code, check_code
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@login_required
@app.route('/problem/<problem_id>', methods=['GET', 'POST'])
def problem_show(problem_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    problem = db_sess.query(Problem).filter(Problem.id == problem_id).first()
    if not problem:
        return "К сожалению такой задачи нет"
    form = CommentAddForm(prefix='problem_comment_form')
    comment_forms = [CommentAddForm(prefix=f'solution_comment_form{i}') for i in range(len(problem.comments))]
    solform = SolutionAddForm(prefix='problem_solution_form')
    if request.method == 'POST':
        if form.validate_on_submit():
            comment = Comment()
            comment.content = form.content.data
            current_user.comments.append(comment)
            db_sess.merge(current_user)
            comment = db_sess.merge(comment)
            problem.comments.append(comment)
            db_sess.commit()
            return redirect(f'/problem/{problem_id}')
        if solform.validate_on_submit():
            solution = Solution()
            solution.content = solform.content.data
            current_user.solutions.append(solution)
            db_sess.merge(current_user)
            solution = db_sess.merge(solution)
            problem.solutions.append(solution)
            db_sess.commit()
            return redirect(f'/problem/{problem_id}')
        for i in range(len(comment_forms)):
            if comment_forms[i].validate_on_submit():
                comment = Comment()
                comment.content = comment_forms[i].content.data
                current_user.comments.append(comment)
                db_sess.merge(current_user)
                comment = db_sess.merge(comment)
                solution = problem.solutions[i]
                solution.comments.append(comment)
                db_sess.commit()
                return redirect(f'/problem/{problem_id}')
    return render_template("problemshow.html", problem=problem, form=form, comment_forms=comment_forms, solform=solform)


@login_required
@app.route('/post/<post_id>', methods=['GET', 'POST'])
def post_show(post_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    post = db_sess.query(Post).filter(Post.id == post_id).first()
    if not post:
        return "К сожалению такой записи нет"
    form = CommentAddForm()
    if form.validate_on_submit():
        comment = Comment()
        comment.content = form.content.data
        current_user.comments.append(comment)
        db_sess.merge(current_user)
        comment = db_sess.merge(comment)
        post.comments.append(comment)
        db_sess.commit()
        return redirect(f'/post/{post_id}')
    return render_template("postshow.html", post=post, form=form)


@login_required
@app.route('/my')
def toread():
    if not current_user.is_authenticated:
        return redirect('/login')
    pass


# (геома, алгебра, комба, всё) (посты, задачи, задачи без решений, всё) (друзья, подписки, популярные) (час, день, неделя, месяц, все)
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        posts = db_sess.query(Post).filter(
            (Post.user == current_user) | (Post.is_private != True))
    else:
        posts = db_sess.query(Post).filter(Post.is_private != True)
    return render_template("index.html", title='Домашняя страница', posts=posts)


@login_required
@app.route('/profile/<user_id>')
def profile(user_id):
    if not current_user.is_authenticated:
        return redirect('/login')
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    if not user:
        return redirect("/")
    return render_template("profile.html", user=user, viewer=current_user, friends=1, subscribers=2, readers=3,
                           geom1=60, alg1=30, comb1=95,
                           geom2=0, alg2=100, comb2=35)


@login_required
@app.route('/generate_code/<status>')
def gen_code(status):
    if not current_user.is_authenticated:
        return redirect('/login')
    statuses = {'админ': 3, 'жюри': 2, 'преподаватель': 1, 'участник': 0}
    if statuses.get(status, 1000) > statuses[current_user.status]:
        return redirect('/')
    else:
        return render_template('codegen.html', status=status, code=generate_code(status))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(f"/profile/{user.id}")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        res, status = check_code(form.secret_code.data)
        if not res:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   code_message=status)
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data,
            status=status
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


"""@app.route('/post', methods=['GET', 'POST'])
@login_required
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        post = Post()
        post.title = form.title.data
        post.content = form.content.data
        post.is_private = form.is_private.data
        current_user.posts.append(post)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('post.html', title='Добавление новости',
                           form=form)


@app.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    form = PostForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        post = db_sess.query(Post).filter(Post.id == id,
                                          Post.user == current_user
                                          ).first()
        if post:
            form.title.data = post.title
            form.content.data = post.content
            form.is_private.data = post.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        post = db_sess.query(Post).filter(Post.id == id,
                                          Post.user == current_user
                                          ).first()
        if post:
            post.title = form.title.data
            post.content = form.content.data
            post.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('post.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/post_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def post_delete(id):
    db_sess = db_session.create_session()
    post = db_sess.query(Post).filter(Post.id == id,
                                      Post.user == current_user
                                      ).first()
    if post:
        db_sess.delete(post)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')
"""


def main():
    db_session.global_init("db/blogs.db")
    print(generate_code('админ'))
    print(generate_code('жюри'))
    print(generate_code('преподаватель'))
    app.run(port=8080, host='127.0.0.1')
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
