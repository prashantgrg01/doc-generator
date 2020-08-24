from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, PasswordField, SubmitField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from app.models import User

# Registration Form
class RegistrationForm(FlaskForm):
  username = StringField("Username", validators=[DataRequired(), Length(min=2, max=20)])
  email = EmailField("Email", validators=[DataRequired(), Email()])
  password = PasswordField("Password", validators=[DataRequired()])
  confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
  submit = SubmitField("Add User")

  # Username validator
  def validate_username(self, username):
    user = User.query.filter_by(username=username.data).first()
    if user:
      raise ValidationError("Username is already taken! Please choose a different one.")

  # Email validator
  def validate_email(self, email):
    user = User.query.filter_by(email=email.data).first()
    if user:
      raise ValidationError("Email already exists! Please choose a different one.")

# Login Form
class LoginForm(FlaskForm):
  email = EmailField("Email", validators=[DataRequired(), Email()])
  password = PasswordField("Password", validators=[DataRequired()])
  remember = BooleanField("Remember Me")
  submit = SubmitField("Login")

# Registration Form
class InvoiceForm(FlaskForm):
  client_name = StringField("Client Name", validators=[DataRequired()])
  client_email = EmailField("Email", validators=[DataRequired(), Email()])
  client_address = StringField("Client Address", validators=[DataRequired()])
  item_description = StringField("Item Description", validators=[DataRequired()])
  item_cost = IntegerField("Item Cost", validators=[DataRequired()])
  submit = SubmitField("Add Invoice")