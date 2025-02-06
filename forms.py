from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,EmailField,PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField


class RegisterForm(FlaskForm):
    email=EmailField('Enter Your Email',validators=[DataRequired()])
    name=StringField('Enter Your Name',validators=[DataRequired()])
    password=PasswordField('Enter Your Password',validators=[DataRequired()])
    register=SubmitField('Sign me up!')

class LoginForm(FlaskForm):
    email=EmailField('Enter Your Email',validators=[DataRequired()])
    password=PasswordField('Enter Your Password',validators=[DataRequired()])
    login=SubmitField('Log in')

class PostForm(FlaskForm):
    title = StringField('Blog Post Title',validators=[DataRequired()])
    subtitle=StringField('Subtitle',validators=[DataRequired()])
    author=StringField('Your Name',validators=[DataRequired()])
    img_url=StringField('Blog image URL',validators=[DataRequired(),URL()])
    body = CKEditorField('Body',validators=[DataRequired()])  # <--
    submit = SubmitField('Submit')
class CommentsForm(FlaskForm):
    text=CKEditorField('Comment')
    submit=SubmitField('Submit Comment')