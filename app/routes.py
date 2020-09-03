import os
from flask import render_template, url_for, redirect, flash, request, abort, send_from_directory, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from docxtpl import DocxTemplate
from datetime import datetime
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, NewClientForm, EditClientForm, InvoiceForm, ReceiptForm
from app.models import User, Client, Invoice, InvoiceItem, Receipt

# Homepage Route
@app.route("/")
def home():
  return redirect(url_for("login"))

# About Page Route
@app.route("/about")
def about():
  return render_template("about.html")

# New User Registration Route
@app.route("/user/new", methods=["GET", "POST"])
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
@app.route("/logout")
@login_required
def logout():
  logout_user()
  return redirect(url_for("home"))

# Dashboard Route
@app.route("/dashboard")
@login_required
def dashboard():
  clients = Client.query.all()
  invoices = Invoice.query.all()
  receipts = Receipt.query.all()
  return render_template("dashboard.html", data={ "clients": clients, "invoices": invoices, "receipts": receipts })

# Client Dashboard Route
@app.route("/client/")
@login_required
def client_dashboard():
  clients = Client.query.order_by(Client.created_on.desc()).all()
  # Amend the client id for display
  for client in clients:
    client.id = client.id + 10000
  return render_template("client_dashboard.html", data={ "clients": clients })

# New Client Registration Route
@app.route("/client/new", methods=["GET", "POST"])
def new_client():
  form = NewClientForm()
  if form.validate_on_submit():
    # Create new client
    new_client = Client(name=form.name.data, business=form.business.data, email=form.email.data, address=form.address.data)
    # Save the new client to the database
    db.session.add(new_client)
    db.session.commit()
    # Show the new client created success message and redirect them to the client dashboard
    flash(f"New client {form.name.data} added!", "success")
    return redirect(url_for("client_dashboard"))
  return render_template("new_client.html", data={ "form": form })

# Edit Client Route
@app.route("/client/edit/<int:client_id>", methods=["GET", "POST"])
def edit_client(client_id):
  # Calculate the client id
  client_id = client_id - 10000
  # Retrive the associated client from the database
  client = Client.query.get_or_404(client_id)

  form = EditClientForm()
  if form.validate_on_submit():
    # Update the client with new field values
    client.name = form.name.data
    client.business = form.business.data
    client.email = form.email.data
    client.address = form.address.data
    # Save the updated client to the database
    db.session.commit()
    # Show the new client created success message and redirect them to the client dashboard
    flash(f"Client details updated successfully!", "success")
  elif request.method == "GET":
    form.name.data = client.name
    form.business.data = client.business
    form.email.data = client.email
    form.address.data = client.address
  return render_template("edit_client.html", data={ "form": form })

# Invoices Dashboard Route
@app.route("/invoice/")
@login_required
def invoice_dashboard():
  invoices = Invoice.query.order_by(Invoice.issue_date.desc()).all()
  # Amend the invoice id for display
  for invoice in invoices:
    invoice.id = invoice.id + 10000
  return render_template("invoice_dashboard.html", data={ "invoices": invoices })

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
    "client_name": invoice.client.name,
    "client_email": invoice.client.email,
    "client_address": invoice.client.address,
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
  document.save("app/generated_docs/invoices/invoice_" + str(invoice.id + 10000) + ".docx")

# New Invoice Route
@app.route("/invoice/new", methods=["GET", "POST"])
@login_required
def new_invoice():
  # Initialize the invoice form
  form = InvoiceForm()
  # Get the list of all the clients from the database
  clients = Client.query.order_by(Client.created_on.desc()).all()
  # Dynamically assign the choices for the client field of the invoice
  form.client_id.choices = [(c.id, c.name) for c in clients]

  if form.validate_on_submit():
    # Get the client id from the form fields
    client_id = form.client_id.data
    client = Client.query.get(client_id)

    # Create new invoice
    invoice = Invoice(client=client, user=current_user)
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

    # Update sub_total, 10% gst_total and invoice_total for the current invoice
    invoice.sub_total = sub_total
    invoice.gst_total = int(0.1 * sub_total)
    invoice.invoice_total = sub_total
    db.session.commit()

    # Generate and save the invoice to a temporary folder
    generate_and_save_invoice(invoice)

    # Show the invoice created message
    flash(f"New invoice generated!", "success")
    return redirect(url_for("invoice_dashboard"))
  return render_template("new_invoice.html", data={ "form": form, "clients": clients })

# Download Generated Invoice Route
@app.route("/invoice/download/<int:invoice_id>")
def download_invoice(invoice_id):
  # Create the invoice filename
  filename = "invoice_" + str(invoice_id) + ".docx"
  try:
    # Check if the invoice already exists
    if not os.path.exists(app.config["INVOICE_FOLDER"] + filename):
      # Retrieve the invoice details from the database based on the invoice id
      invoice = Invoice.query.get(int(invoice_id) - 10000)
      # Generate and save the invoice to a temporary folder
      generate_and_save_invoice(invoice)
    # Send the file to the user
    return send_from_directory(app.config["INVOICE_FOLDER"], filename=filename, as_attachment=True)
  except FileNotFoundError:
    abort(404)

# Receipts Dashboard Route
@app.route("/receipt/")
@login_required
def receipt_dashboard():
  receipts = Receipt.query.order_by(Receipt.issue_date.desc()).all()
  # Amend the receipt id for display
  for receipt in receipts:
    receipt.id = receipt.id + 10000
  return render_template("receipt_dashboard.html", data={ "receipts": receipts })

# New Receipt Route
@app.route("/receipt/new", methods=["GET", "POST"])
@login_required
def new_receipt():
  # Initialize the receipt form
  form = ReceiptForm()

  # Get the list of all the clients from the database
  clients = Client.query.order_by(Client.created_on.desc()).all()
  # Dynamically assign the choices for the client field of the receipt
  form.client_id.choices = [(c.id, c.name) for c in clients]

  # Used form.submit.data instead of form.validate_on_submit() due to a weird validation issue with the invoice field selection 
  if form.submit.data:
    # Get the client id and invoice id from the form fields
    client_id = form.client_id.data
    client = Client.query.get(client_id)
    invoice_id = form.invoice_id.data
    invoice = Invoice.query.get(invoice_id)

    # Create new receipt
    receipt = Receipt(payment_date=form.payment_date.data, invoice=invoice, client=client, user=current_user)
    db.session.add(receipt)
    db.session.commit()

    # Generate and save the receipt to a temporary folder
    generate_and_save_receipt(receipt)

    # Show the receipt created message
    flash(f"New receipt generated!", "success")
    return redirect(url_for("receipt_dashboard"))
  return render_template("new_receipt.html", data={ "form": form, "clients": clients })

# API for Receipt Invoice Options
@app.route("/api/client/<int:client_id>/invoices", methods=["GET"])
@login_required
def receipt_options(client_id):
  # Get the list of all the invoices for the given client
  client = Client.query.get_or_404(client_id)
  # Create a list of invoice options for the given client
  invoice_options = []
  for invoice in client.invoices:
    label = "#" + str(invoice.id + 10000) + " - "
    for invoice_item in invoice.invoice_items:
      label += invoice_item.description + ", "
    invoice_options.append({ "id": invoice.id, "label": label[:-2] })
  return jsonify({ "options": invoice_options })

# Function to generate and save receipt
def generate_and_save_receipt(receipt):
  # Create invoice items for our document context
  invoice_items = []
  for item in receipt.invoice.invoice_items:
    invoice_item = {
      "id": str(receipt.invoice.id + 10000),
      "description": item.description,
      "total_cost": "$" + str(format(item.cost, ".2f"))
    }
    invoice_items.append(invoice_item)

  # Create our document context
  context = { 
    "receipt_id": str(receipt.id + 10000),
    "client_name": receipt.client.name,
    "client_email": receipt.client.email,
    "client_address": receipt.client.address,
    "issue_date": receipt.issue_date.strftime("%B %d, %Y"),
    "payment_date": receipt.payment_date.strftime("%B %d, %Y"),
    "row_contents": invoice_items,
    "sub_total": "$" + str(format(receipt.invoice.sub_total, ".2f")),
    "gst_total": "$" + str(format(receipt.invoice.gst_total, ".2f")),
    "invoice_total": "$" + str(format(receipt.invoice.invoice_total, ".2f"))
  }

  # Open the document template
  document = DocxTemplate("app/doc_templates/receipt_template.docx")
  # Render the document template by integrating it with our document context 
  document.render(context)
  # Save the document
  document.save("app/generated_docs/receipts/receipt_" + str(receipt.id + 10000) + ".docx")

# Download Generated Receipt Route
@app.route("/receipt/download/<int:receipt_id>")
def download_receipt(receipt_id):
  # Create the receipt filename
  filename = "receipt_" + str(receipt_id) + ".docx"
  try:
    # Check if the receipt already exists
    if not os.path.exists(app.config["RECEIPT_FOLDER"] + filename):
      # Retrieve the receipt details from the database based on the receipt id
      receipt = Receipt.query.get(int(receipt_id) - 10000)
      # Generate and save the receipt to a temporary folder
      generate_and_save_receipt(receipt)
    # Send the file to the user
    return send_from_directory(app.config["RECEIPT_FOLDER"], filename=filename, as_attachment=True)
  except FileNotFoundError:
    abort(404)
