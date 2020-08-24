from flask import render_template, url_for, redirect, flash, request, abort
from flask_login import login_user, logout_user, current_user, login_required
from docxtpl import DocxTemplate
from datetime import datetime
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, InvoiceForm
from app.models import User, Invoice, InvoiceRowContent

# Homepage Route
@app.route("/")
def home():
  return redirect(url_for("login"))

# About Page Route
@app.route("/about")
def about():
  return render_template("about.html")

# New User Registration Route
@app.route("/users/add", methods=["GET", "POST"])
def register_user():
  form = RegistrationForm()
  if form.validate_on_submit():
    # Hash the new user's password
    hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
    # Create new user
    new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
    # Save the new user to the database
    db.session.add(new_user)
    db.session.commit()
    # Show the new user created success message and redirect them to the login page
    flash(f"Account created successfully for {form.username.data}!", "success")
    return redirect(url_for("dashboard"))
  return render_template("register.html", data={ "form": form })

# Login Route
@app.route("/login", methods=["GET", "POST"])
def login():
  # If a user is already logged in, redirect them to the dashboard
  if current_user.is_authenticated:
    return redirect(url_for("dashboard"))

  form = LoginForm()
  if form.validate_on_submit():
    # Check if the user exists and if they provided the correct password or not
    user = User.query.filter_by(email=form.email.data).first()
    if user and bcrypt.check_password_hash(user.password, form.password.data):
      # Login the user
      login_user(user, remember=form.remember.data)
      # Show the login success 
      flash(f"Welcome {user.username}!", "success")
      # Check if the user is trying to access a different authenticated page
      next_page = request.args.get("next")
      # Redirect them to their dashboard or the respective page they are trying to access
      return redirect(next_page) if next_page else redirect(url_for("dashboard"))
    else:
      flash(f"Invalid email or password! Please try again.", "danger")
  return render_template("login.html", data={ "form": form })

# Logout Route
@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
  logout_user()
  return redirect(url_for("home"))

# Dashboard Route
@app.route("/dashboard")
@login_required
def dashboard():
  users = User.query.all()
  return render_template("dashboard.html", data={ "users": users })

# Invoices Dashboard Route
@app.route("/invoices")
@login_required
def invoice_dashboard():
  return render_template("invoice_dashboard.html", data={ })

# New Invoice Route
@app.route("/invoices/new", methods=["GET", "POST"])
@login_required
def new_invoice():
  form = InvoiceForm()
  if form.validate_on_submit():
    # Get all the values from the form fields
    client_name = form.client_name.data
    client_email = form.client_email.data
    client_address = form.client_address.data
    item_description = form.item_description.data
    item_cost = form.item_cost.data
    
    # Create new row content
    # row_content = InvoiceRowContent(description=item_description, total_cost=item_cost)
    # db.session.add(row_content)

    # Calculate subtotal, gst and total
    sub_total = item_cost
    gst_total = int(0.1 * sub_total)
    invoice_total = item_cost

    # Create new invoice
    # invoice = Invoice(client_name=client_name, client_email=client_email, client_address=client_address, sub_total=sub_total, gst_total=gst_total, invoice_total=invoice_total, row_contents=list(row_content))
    # db.session.add(invoice)

    # db.session.commit()

    # Create row contents for our document context
    row_contents = [
      {
        "description": item_description,
        "total_cost": "$" + str(format(item_cost, ".2f"))
      }
    ]

    # Create our document context
    context = { 
      "invoice_id": str(1 + 10000),
      "client_name": client_name,
      "client_email": client_email,
      "client_address": client_address,
      "issue_date": datetime.utcnow().strftime("%B %d, %Y"),
      "due_date": "On Receipt",
      "row_contents": row_contents,
      "sub_total": "$" + str(format(sub_total, ".2f")),
      "gst_total": "$" + str(format(gst_total, ".2f")),
      "invoice_total": "$" + str(format(invoice_total, ".2f"))
    }

    # Open the document template
    document = DocxTemplate("app/doc_templates/invoice_template.docx")
    # Render the context by integrating it with the document template
    document.render(context)
    # Save the document
    document.save("app/generated_docs/new_invoice.docx")
    # Show the invoice created message
    flash(f"New invoice generated!", "success")
    return redirect(url_for("invoice_dashboard"))
  return render_template("new_invoice.html", data={ "form": form })

