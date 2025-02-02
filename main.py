import datetime
import smtplib
import requests
from flask import Flask, render_template, redirect, url_for,request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField
from datetime import datetime
import os
from dotenv import load_dotenv

## email credentials
PASSWORD=os.environ.get("PASSWORD")
EMAIL=os.environ.get('EMAIL')
#create flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)
ckeditor = CKEditor(app)
# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class PostForm(FlaskForm):
    title = StringField('Blog Post Title',validators=[DataRequired()])
    subtitle=StringField('Subtitle',validators=[DataRequired()])
    author=StringField('Your Name',validators=[DataRequired()])
    img_url=StringField('Blog image URL',validators=[DataRequired(),URL()])
    body = CKEditorField('Body',validators=[DataRequired()])  # <--
    submit = SubmitField('Submit')
# CONFIGURE TABLE
class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


@app.route('/')
def get_all_posts():
    posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", all_posts=posts)

# TODO: Add a route so that you can click on individual posts.
@app.route('/post/<int:post_id>')
def show_post(post_id):
    # TODO: Retrieve a BlogPost from the database based on the post_id
    requested_post = db.get_or_404(BlogPost,post_id)
    #db.session.execute(db.select(BlogPost).where(BlogPost.id==post_id)).scalars().all())
    return render_template("post.html", post=requested_post)


# TODO: add_new_post() to create a new blog post
@app.route('/new-post',methods=['POST','GET'])
def add_new_post():
    form=PostForm()
    if form.validate_on_submit():
        post=BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=form.author.data,
            date=datetime.today().strftime("%B %d, %Y")
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template('make-post.html',form=form)


# TODO: edit_post() to change an existing blog post
@app.route('/edit-post/<post_id>',methods=['POST','GET'])
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
        post_tobe_edited.author=edit_form.author.data
        db.session.commit()
        return redirect(url_for('show_post',post_id=post_id))
    return render_template('make-post.html', form=edit_form,is_edit=True)

# TODO: delete_post() to remove a blog post from the database
@app.route('/delete/<int:post_id>',methods=['GET','DELETE'])
def delete_post(post_id):
    post_tobe_deleted=db.get_or_404(BlogPost,post_id)
    db.session.delete(post_tobe_deleted)
    db.session.commit()
    return redirect(url_for('get_all_posts'))
# Below is the code from previous lessons. No changes needed.
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

if __name__ == "__main__":
    app.run(debug=True, port=5003)
