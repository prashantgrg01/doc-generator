import os
from flask import render_template, url_for, redirect, flash, request, abort, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from docxtpl import DocxTemplate
from datetime import datetime
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, InvoiceForm
from app.models import User, Invoice, InvoiceItem

# Homepage Route
@app.route("/")
def home():
  return redirect(url_for("login"))

# About Page Route
@app.route("/about")
def about():
  return render_template("about.html")

# New User Registration Route
@app.route("/users/new", methods=["GET", "POST"])
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
    return redirect(url_for("login"))
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
  invoices = Invoice.query.all()
  return render_template("dashboard.html", data={ "invoices": invoices })

# Invoices Dashboard Route
@app.route("/invoices/")
@login_required
def invoice_dashboard():
  invoices = Invoice.query.order_by(Invoice.issue_date.desc()).all()
  # Amend the invoice id for display
  for invoice in invoices:
    invoice.id = invoice.id + 10000
  return render_template("invoice_dashboard.html", data={ "invoices": invoices })

# New Invoice Route
@app.route("/invoices/new", methods=["GET", "POST"])
@login_required
def new_invoice():
  form = InvoiceForm()
  if form.validate_on_submit():
    # Get all the values from the form fields
    client_name = form.client_name.data
    client_business = form.client_business.data
    client_email = form.client_email.data
    client_address = form.client_address.data

    # Create new invoice
    invoice = Invoice(client_name=client_name, client_business=client_business, client_email=client_email, client_address=client_address, user=current_user)
    db.session.add(invoice)
    db.session.commit()

    # Initialize sub_total
    sub_total = 0
    # Loop through all the invoice_items in the form
    for invoice_item in form.invoice_items.data:
      # Create new invoice item
      new_invoice_item = InvoiceItem(description=invoice_item["item_description"], cost=invoice_item["item_cost"], invoice=invoice)
      db.session.add(new_invoice_item)
      db.session.commit()
      # Add item to our sub_total
      sub_total += int(invoice_item["item_cost"])

    # Update sub_total, gst_total and invoice_total for the current invoice
    invoice.sub_total = sub_total
    invoice.gst_total = int(0.1 * sub_total)
    invoice.invoice_total = sub_total
    db.session.commit()

    # Generate and save the invoice to a temporary folder
    generate_and_save_invoice(invoice)

    # Show the invoice created message
    flash(f"New invoice generated!", "success")
    return redirect(url_for("invoice_dashboard"))
  return render_template("new_invoice.html", data={ "form": form })

# Function to generate and save invoice
def generate_and_save_invoice(invoice):
  # Create invoice items for our document context
  invoice_items = []
  for item in invoice.invoice_items:
    invoice_item = {
      "description": item.description,
      "total_cost": "$" + str(format(item.cost, ".2f"))
    }
    invoice_items.append(invoice_item)

  # Create our document context
  context = { 
    "invoice_id": str(invoice.id + 10000),
    "client_name": invoice.client_name,
    "client_email": invoice.client_email,
    "client_address": invoice.client_address,
    "issue_date": invoice.issue_date.strftime("%B %d, %Y"),
    "due_date": "On Receipt",
    "row_contents": invoice_items,
    "sub_total": "$" + str(format(invoice.sub_total, ".2f")),
    "gst_total": "$" + str(format(invoice.gst_total, ".2f")),
    "invoice_total": "$" + str(format(invoice.invoice_total, ".2f"))
  }

  # Open the document template
  document = DocxTemplate("app/doc_templates/invoice_template.docx")
  # Render the document template by integrating it with our document context 
  document.render(context)
  # Save the document
  document.save("app/generated_docs/invoice_" + str(invoice.id + 10000) + ".docx")

# Download Generated Invoice Route
@app.route("/invoices/generated/<int:invoice_id>")
def download_invoice(invoice_id):
  # Create the invoice filename
  filename = "invoice_" + str(invoice_id) + ".docx"
  try:
    # Check if the invoice already exists
    if not os.path.exists(app.config["INVOICE_FOLDER"] + filename):
      # Retreve the invoice details from the database based on the invoice id
      invoice = Invoice.query.get(int(invoice_id) - 10000)
      # Generate and save the invoice to a temporary folder
      generate_and_save_invoice(invoice)
    # Send the file to the user
    return send_from_directory(app.config["INVOICE_FOLDER"], filename=filename, as_attachment=True)
  except FileNotFoundError:
    abort(404)
