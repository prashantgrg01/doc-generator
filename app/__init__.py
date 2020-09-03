import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config["SECRET_KEY"] = "secretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///../site.db"
app.config["INVOICE_FOLDER"] = os.path.dirname(os.path.abspath(__file__)) + "/generated_docs/invoices/"
app.config["RECEIPT_FOLDER"] = os.path.dirname(os.path.abspath(__file__)) + "/generated_docs/receipts/"
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "warning"

from app import routes