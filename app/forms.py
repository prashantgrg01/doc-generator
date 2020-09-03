from flask_wtf import FlaskForm
from wtforms import Form, FieldList, FormField, IntegerField, StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.fields.html5 import EmailField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from app.models import User

# User Registration Form
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

# User Login Form
class LoginForm(FlaskForm):
  email = EmailField("Email", validators=[DataRequired(), Email()])
  password = PasswordField("Password", validators=[DataRequired()])
  remember = BooleanField("Remember Me")
  submit = SubmitField("Login")

# Client Registration Form
class NewClientForm(FlaskForm):
  name = StringField("Client Name", validators=[DataRequired()])
  business = StringField("Client Business", validators=[DataRequired()])
  email = EmailField("Client Email", validators=[DataRequired(), Email()])
  address = StringField("Client Address", validators=[DataRequired()])
  submit = SubmitField("Add Client")

# Edit Client Form
class EditClientForm(FlaskForm):
  name = StringField("Client Name", validators=[DataRequired()])
  business = StringField("Client Business", validators=[DataRequired()])
  email = EmailField("Client Email", validators=[DataRequired(), Email()])
  address = StringField("Client Address", validators=[DataRequired()])
  submit = SubmitField("Edit Client")

# Invoice Item Form
class InvoiceItemForm(Form):
  item_description = StringField("Item Description", validators=[DataRequired()])
  item_cost = IntegerField("Item Cost", validators=[DataRequired()])

# Invoice Form
class InvoiceForm(FlaskForm):
  client_id = SelectField("Select Client", coerce=int)
  invoice_items = FieldList(
    FormField(InvoiceItemForm),
    min_entries=1,
    max_entries=5
  )
  submit = SubmitField("Generate Invoice")

# Receipt Form
class ReceiptForm(FlaskForm):
  client_id = SelectField("Select Client", coerce=int)
  invoice_id = SelectField("Select Invoice", coerce=int)
  payment_date = DateField("Payment Date", validators=[DataRequired()])
  submit = SubmitField("Generate Receipt")
