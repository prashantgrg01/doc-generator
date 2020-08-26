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
  invoices = db.relationship("Invoice", backref="user", lazy=True)

  def __repr__(self):
    return f"User('{self.username}', '{self.email}', '{self.profile_image}')"

# Invoice Model
class Invoice(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  client_name = db.Column(db.String(100), nullable=False)
  client_business = db.Column(db.String(200), nullable=False)
  client_email = db.Column(db.String(100), nullable=False)
  client_address = db.Column(db.String(200), nullable=False)
  issue_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  due_date = db.Column(db.String(100), nullable=False, default="On Receipt")
  sub_total = db.Column(db.Integer, nullable=False, default=0)
  gst_total = db.Column(db.Integer, nullable=False, default=0)
  invoice_total = db.Column(db.Integer, nullable=False, default=0)
  invoice_items = db.relationship("InvoiceItem", backref="invoice", lazy=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

  def __repr__(self):
    return f"Invoice('{self.id}', '{self.client_name}', '{self.issue_date}')"

# Invoice Item Model
class InvoiceItem(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  description = db.Column(db.String(200), nullable=False)
  cost = db.Column(db.Integer, nullable=False)
  invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=True)

  def __repr__(self):
    return f"InvoiceItem('{self.id}', '{self.description}', '{self.cost}')"


