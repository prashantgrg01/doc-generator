from datetime import datetime
from app import db, login_manager
from flask_login.mixins import UserMixin

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

# User Model
class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(20), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password = db.Column(db.String(100), nullable=False)
  profile_image = db.Column(db.String(120), nullable=False, default="default.jpg")
  clients = db.relationship("Client", backref="user", lazy=True)
  invoices = db.relationship("Invoice", backref="user", lazy=True)
  receipts = db.relationship("Receipt", backref="user", lazy=True)

  def __repr__(self):
    return f"User('{self.username}', '{self.email}', '{self.profile_image}')"

# Client Model
class Client(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(120), unique=True, nullable=False)
  business = db.Column(db.String(120), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  address = db.Column(db.String(120), unique=True, nullable=False)
  created_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  invoices = db.relationship("Invoice", backref="client", lazy=True)
  receipts = db.relationship("Receipt", backref="client", lazy=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

  def __repr__(self):
    return f"Client('{self.name}', '{self.business}', '{self.email}')"

# Invoice Model
class Invoice(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  due_date = db.Column(db.String(100), nullable=False, default="On Receipt")
  sub_total = db.Column(db.Integer, nullable=False, default=0)
  gst_total = db.Column(db.Integer, nullable=False, default=0)
  invoice_total = db.Column(db.Integer, nullable=False, default=0)
  invoice_items = db.relationship("InvoiceItem", backref="invoice", lazy=True)
  receipt = db.relationship("Receipt", backref="invoice", uselist=False, lazy=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
  client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=True)

  def __repr__(self):
    return f"Invoice('{self.id}', '{self.invoice_total}', '{self.issue_date}')"

# Invoice Item Model 
class InvoiceItem(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  description = db.Column(db.String(200), nullable=False)
  cost = db.Column(db.Integer, nullable=False)
  invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=True)

  def __repr__(self):
    return f"InvoiceItem('{self.id}', '{self.description}', '{self.cost}')"

# Receipt Model
class Receipt(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=True)
  user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
  client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)

  def __repr__(self):
    return f"Invoice('{self.id}', '{self.payment_date}', '{self.issue_date}')"


