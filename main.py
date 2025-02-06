import datetime
import smtplib
from functools import wraps
from flask_bootstrap import Bootstrap5
from flask import Flask, render_template, redirect, url_for, request, flash, g, abort
from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey
from datetime import datetime
import os
from  flask_gravatar import Gravatar
from flask_login import LoginManager, login_user, UserMixin, logout_user, login_required, current_user
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm,PostForm,LoginForm,CommentsForm

## email credentials
load_dotenv()
PASSWORD=os.environ.get("PASSWORD")
EMAIL=os.environ.get('EMAIL')
#create flask app

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
ckeditor = CKEditor(app)

gravatar = Gravatar(app,
                    size=50,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)
# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)
#create login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User,user_id)

# CONFIGURE TABLE
class BlogPost(db.Model):
    __tablename__='blog_post'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("user.id"))
    author = relationship("User", back_populates="posts")
    comment=relationship('Comments',back_populates='parent_post',cascade='all, delete-orphan')

class User(db.Model,UserMixin):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email:Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(250),nullable=False)
    password:Mapped[str] = mapped_column(String(250),nullable=False)
    posts = relationship("BlogPost", back_populates="author")
    comment=relationship('Comments',back_populates="user")

class Comments(db.Model):
    __tablename__='comments'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=True)

    user_id:Mapped[int] = mapped_column(Integer, db.ForeignKey("user.id"))
    user=relationship('User',back_populates='comment')
    parent_post=relationship('BlogPost',back_populates='comment')
    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_post.id"))

with app.app_context():
    db.create_all()


@app.route('/')
def get_all_posts():
    posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", all_posts=posts)

@app.route('/post/<int:post_id>',methods=['POST','GET'])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost,post_id)
    comment_form=CommentsForm()
    if comment_form.validate_on_submit():
        if current_user.is_authenticated:
            new_comment=Comments(
                text=comment_form.text.data,
                user=current_user,
                parent_post=requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
            date=datetime.today().strftime("%B %d, %Y")
            return  render_template("post.html", post=requested_post,comment_form=comment_form,date=date)
        else:
            flash('You need to log in or register to comment')
            return redirect(url_for('login'))
    return render_template("post.html", post=requested_post,comment_form=comment_form)

def admin_only(func):
    @wraps(func)
    @login_required
    def wrapper_func(*args,**kwargs):
        if  current_user.id==1:
            return func(*args, **kwargs)
        else:
            return abort(403)
    return wrapper_func

@app.route('/new-post',methods=['POST','GET'])
@admin_only
def add_new_post():
    form=PostForm()
    if form.validate_on_submit():
        post=BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=datetime.today().strftime("%B %d, %Y"),


        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template('make-post.html',form=form,current_user=current_user)


@app.route('/edit-post/<post_id>',methods=['POST','GET'])
@admin_only
def edit_post(post_id):
    post_tobe_edited = db.get_or_404(BlogPost, post_id)

    edit_form=PostForm(    title=post_tobe_edited.title,
    subtitle=post_tobe_edited.subtitle,
    img_url=post_tobe_edited.img_url,
    author=post_tobe_edited.author,
    body=post_tobe_edited.body)
    if edit_form.validate_on_submit():
        post_tobe_edited.title=edit_form.title.data
        post_tobe_edited.subtitle=edit_form.subtitle.data
        post_tobe_edited.img_url=edit_form.img_url.data
        post_tobe_edited.body=edit_form.body.data
        post_tobe_edited.author=current_user
        db.session.commit()
        return redirect(url_for('show_post',post_id=post_id))
    return render_template('make-post.html', form=edit_form,is_edit=True)

@app.route('/delete/<int:post_id>',methods=['GET','DELETE','POST'])
@admin_only
def delete_post(post_id):
    post_tobe_deleted=db.get_or_404(BlogPost,post_id)
    db.session.delete(post_tobe_deleted)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

@app.route('/delete-comment/<int:comment_id>',methods=['GET','DELETE'])
@admin_only
def delete_comment(comment_id):
    comment_tobe_del=db.get_or_404(Comments,comment_id)
    db.session.delete(comment_tobe_del)
    db.session.commit()
    return redirect(url_for('show_post',post_id=comment_tobe_del.post_id))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact",methods=['POST','GET'])
def contact():
    if request.method == "POST":
        data = request.form
        send_email(data["name"],data["email"],data["phone"],request.form.get('message'))
        return render_template("contact.html", msg_sent=True)
    return render_template("contact.html", msg_sent=False)


def send_email(name,email,phone,message):
    with smtplib.SMTP('smtp.gmail.com') as connection:
        connection.starttls()
        connection.login(user=EMAIL,password=PASSWORD)
        connection.sendmail(from_addr=email,to_addrs='nazanhaciyeva43@gmail.com',
                            msg=f'Subject:Message from your Blog\n\n Name: {name}\n'
                                f' Email: {email}\n Phone:{phone}\n Message:{message}')


@app.route("/register",methods=['POST','GET'])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        email=form.email.data
        name=form.name.data
        password= generate_password_hash(form.password.data, method='pbkdf2:sha256',
                                         salt_length=8 )
        new_user=User(name=name, password=password,email=email)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('get_all_posts'))
    return render_template('register.html',form=form)

@app.route('/login',methods=['POST','GET'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        email=form.email.data
        password=form.password.data
        user=db.session.execute(db.select(User).where(User.email==email)).scalar()
        if  user is None:
            flash('Email is not exits in database, please register first')
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))

    return render_template('login.html', form=form)

@app.route('/logout',methods=['POST','GET'])
def logout():
    logout_user()
    return  redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True, port=5003)
