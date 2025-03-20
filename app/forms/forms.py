from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class SelectReporterForm(FlaskForm):
    reporters = SelectField('Reporter', choices=[], validators=[DataRequired()], render_kw={"class": "bg-sky-500 hover:bg-sky-700 text-white py-2 px-5 rounded-full font-bold text-md transition duration-300"})
    submit = SubmitField('Set Profile', render_kw={"class": "bg-sky-500 hover:bg-sky-700 text-white py-2 px-5 rounded-full font-bold text-md transition duration-300"})

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    # email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    submit = SubmitField('Sign Up', render_kw={"class": "bg-sky-500 hover:bg-sky-700 text-white py-2 px-5 rounded-full font-bold text-md transition duration-300"})

class LoginForm(FlaskForm):
    # email = StringField('Email', validators=[DataRequired()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    username = StringField('Username', validators=[DataRequired()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"class": "border border-black rounded-lg text-black px-2 py-1 focus:outline-none w-full text-lg", "autocomplete":"off"})
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login', render_kw={"class": "bg-sky-500 hover:bg-sky-700 text-white py-2 px-5 rounded-full font-bold text-md transition duration-300"})

class GenerateStoryForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()], render_kw={"autocomplete":"off"})
    #guideline = TextAreaField('Guideline', render_kw={"autocomplete":"off", "rows": 5})
    #reporters = SelectField('Reporter', choices=[], validators=[DataRequired()], render_kw={"autocomplete":"off"})
    reporter_name = StringField('Reporter', validators=[DataRequired()], render_kw={"autocomplete":"off"})
    reporter_personality = TextAreaField('Personaility', validators=[DataRequired()], render_kw={"autocomplete":"off", "rows": 5})
    submit = SubmitField('Report!')

class NewReporterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()], render_kw={"autocomplete":"off"})
    personality = TextAreaField('Personality', validators=[DataRequired()], render_kw={"autocomplete":"off", "rows": 5})
    submit = SubmitField('Create')

class CommentForm(FlaskForm):
    comment = TextAreaField('Comment', validators=[DataRequired()], render_kw={"class": "px-0 w-full text-sm text-gray-900 border-0 focus:ring-0 focus:outline-none dark:text-white dark:placeholder-gray-400 dark:bg-gray-800", "autocomplete":"off", "placeholder": "Add Comment"})
    submit = SubmitField('Post', render_kw={"class": "bg-sky-500 hover:bg-sky-700 text-white py-2 px-5 font-bold text-md transition duration-300"})
