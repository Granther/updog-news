from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    submit = SubmitField('Sign Up', render_kw={"class": "bg-sky-500 hover:bg-sky-700 text-white py-2 px-5 rounded-full font-bold text-md transition duration-300"})

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login', render_kw={"class": "bg-sky-500 hover:bg-sky-700 text-white py-2 px-5 rounded-full font-bold text-md transition duration-300"})

class GenerateStoryForm(FlaskForm):
    """Takes the user's story proposal, gets added to execution queue after submission"""

    title = StringField('Title', validators=[DataRequired()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    guideline = StringField('Guideline', validators=[DataRequired()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    reporter_id = StringField('Reporter ID', validators=[DataRequired()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    submit = SubmitField('Login', render_kw={"class": "bg-sky-500 hover:bg-sky-700 text-white py-2 px-5 rounded-full font-bold text-md transition duration-300"})

class NewReporterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    personality = StringField('Personality', validators=[DataRequired()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    submit = SubmitField('Login', render_kw={"class": "bg-sky-500 hover:bg-sky-700 text-white py-2 px-5 rounded-full font-bold text-md transition duration-300"})

class CommentForm(FlaskForm):
    comment = StringField('Comment', validators=[DataRequired()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    submit = SubmitField('Post', render_kw={"class": "bg-sky-500 hover:bg-sky-700 text-white py-2 px-5 rounded-full font-bold text-md transition duration-300"})
