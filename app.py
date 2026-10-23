import os
import secrets
from datetime import datetime, date
from pathlib import Path
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, DateField, SelectField, EmailField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = Path(os.environ.get("INSTANCE_DIR", BASE_DIR / "instance")).resolve()
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", INSTANCE_DIR / "uploads")).resolve()
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, instance_path=str(INSTANCE_DIR), instance_relative_config=True)
app.jinja_env.globals["getattr"] = getattr
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or "dev-only-change-me-before-deployment",
    SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL") or f"sqlite:///{(INSTANCE_DIR / 'catering.db').as_posix()}",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
    UPLOAD_FOLDER=str(UPLOAD_DIR),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
)
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "admin_login"
login_manager.login_message = "Please log in to access the admin dashboard."
limiter = Limiter(get_remote_address, app=app, default_limits=["300 per day", "80 per hour"], storage_uri="memory://")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False, default="")

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    published = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    address = db.Column(db.Text, nullable=False, default="Address to be confirmed")
    city = db.Column(db.String(100), nullable=False, default="City to be confirmed")
    phone = db.Column(db.String(50), default="Contact details to be confirmed")
    hours = db.Column(db.String(160), default="Hours to be confirmed")
    map_url = db.Column(db.String(500), default="")
    published = db.Column(db.Boolean, default=True, nullable=False)

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    designation = db.Column(db.String(140), nullable=False)
    bio = db.Column(db.Text, default="")
    image = db.Column(db.String(255))
    published = db.Column(db.Boolean, default=True, nullable=False)

class Certification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    issuer = db.Column(db.String(160), default="Issuer to be confirmed")
    certificate_number = db.Column(db.String(100), default="To be provided")
    validity = db.Column(db.String(100), default="To be confirmed")
    document = db.Column(db.String(255))
    published = db.Column(db.Boolean, default=False, nullable=False)

class GalleryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    published = db.Column(db.Boolean, default=True, nullable=False)

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(140), nullable=False)
    quote = db.Column(db.Text, nullable=False)
    published = db.Column(db.Boolean, default=False, nullable=False)

class Enquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(24), unique=True, nullable=False, index=True)
    name = db.Column(db.String(140), nullable=False)
    phone = db.Column(db.String(40), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    event_date = db.Column(db.Date, nullable=True)
    guests = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(255), nullable=False, default="To be confirmed")
    branch_id = db.Column(db.Integer, db.ForeignKey("branch.id"), nullable=True)
    budget = db.Column(db.String(80), default="")
    message = db.Column(db.Text, default="")
    status = db.Column(db.String(40), default="New", nullable=False, index=True)
    internal_notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    branch = db.relationship("Branch", backref="enquiries")

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=256)])

class EnquiryForm(FlaskForm):
    name = StringField("Your name", validators=[DataRequired(), Length(min=2, max=140)])
    phone = StringField("Phone number", validators=[DataRequired(), Length(min=7, max=40)])
    email = EmailField("Email address", validators=[DataRequired(), Email(), Length(max=160)])
    event_type = SelectField("Event type", choices=[
        ("Wedding Catering", "Wedding Catering"), ("Corporate Catering", "Corporate Catering"),
        ("Birthday / Anniversary", "Birthday / Anniversary"), ("Private Party", "Private Party"),
        ("Institutional / Bulk Catering", "Institutional / Bulk Catering"), ("Other", "Other")
    ], validators=[DataRequired()])
    event_date = DateField("Event date", validators=[Optional()], format="%Y-%m-%d")
    guests = IntegerField("Approximate number of guests", validators=[Optional(), NumberRange(min=1, max=100000)])
    location = StringField("Event location", validators=[Optional(), Length(max=255)])
    branch_id = SelectField("Preferred branch", coerce=int, validators=[Optional()])
    budget = StringField("Estimated budget (optional)", validators=[Optional(), Length(max=80)])
    message = TextAreaField("Food preferences or special requests", validators=[Optional(), Length(max=3000)])

def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        return view(*args, **kwargs)
    return wrapped

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload(file):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        raise ValueError("Unsupported file type. Upload JPG, PNG, WEBP, or PDF.")
    filename = secure_filename(file.filename)
    suffix = Path(filename).suffix.lower()
    unique_name = f"{secrets.token_hex(12)}{suffix}"
    file.save(UPLOAD_DIR / unique_name)
    return unique_name

@app.context_processor
def inject_site_settings():
    settings = {s.key: s.value for s in SiteSetting.query.all()} if app.config.get("SQLALCHEMY_DATABASE_URI") else {}
    return {"site_settings": settings, "current_year": datetime.now().year}

@app.route("/")
def home():
    services = Service.query.filter_by(published=True).order_by(Service.id.desc()).limit(6).all()
    branches = Branch.query.filter_by(published=True).order_by(Branch.id.asc()).limit(3).all()
    testimonials = Testimonial.query.filter_by(published=True).limit(3).all()
    return render_template("index.html", services=services, branches=branches, testimonials=testimonials)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    items = Service.query.filter_by(published=True).order_by(Service.title.asc()).all()
    return render_template("services.html", services=items)

@app.route("/certifications")
def certifications():
    items = Certification.query.filter_by(published=True).order_by(Certification.id.desc()).all()
    return render_template("certifications.html", certifications=items)

@app.route("/branches")
def branches():
    items = Branch.query.filter_by(published=True).order_by(Branch.name.asc()).all()
    return render_template("branches.html", branches=items)

@app.route("/team")
def team():
    items = TeamMember.query.filter_by(published=True).order_by(TeamMember.id.asc()).all()
    return render_template("team.html", team=items)

@app.route("/contact", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def contact():
    form = EnquiryForm()
    branches_list = Branch.query.filter_by(published=True).order_by(Branch.name.asc()).all()
    form.branch_id.choices = [(0, "No preference")] + [(b.id, b.name) for b in branches_list]
    if form.validate_on_submit():
        reference = "APC-" + secrets.token_hex(4).upper()
        enquiry = Enquiry(
            reference=reference, name=form.name.data.strip(), phone=form.phone.data.strip(),
            email=form.email.data.strip(), event_type=form.event_type.data,
            event_date=form.event_date.data, guests=form.guests.data,
            location=(form.location.data or "").strip() or "To be confirmed",
            branch_id=form.branch_id.data or None, budget=(form.budget.data or "").strip(),
            message=(form.message.data or "").strip()
        )
        db.session.add(enquiry)
        db.session.commit()
        return render_template("enquiry_success.html", reference=reference)
    return render_template("contact.html", form=form, branches=branches_list)

@app.route("/uploads/<path:filename>")
def public_upload(filename):
    # Only general published image assets should be linked publicly. Certification PDFs should be linked by an authenticated route.
    item = GalleryImage.query.filter_by(filename=filename, published=True).first()
    if not item:
        abort(404)
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=False)

@app.route("/admin/login", methods=["GET", "POST"])
@limiter.limit("8 per hour", methods=["POST"])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = Admin.query.filter_by(username=form.username.data.strip()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(request.args.get("next") if request.args.get("next", "").startswith("/admin") else url_for("admin_dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("admin/login.html", form=form)

@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    counts = {
        "enquiries": Enquiry.query.count(),
        "new_enquiries": Enquiry.query.filter_by(status="New").count(),
        "services": Service.query.count(),
        "branches": Branch.query.count(),
        "team": TeamMember.query.count(),
        "certifications": Certification.query.count(),
    }
    recent = Enquiry.query.order_by(Enquiry.created_at.desc()).limit(8).all()
    return render_template("admin/dashboard.html", counts=counts, recent=recent)

@app.route("/admin/enquiries")
@admin_required
def admin_enquiries():
    status = request.args.get("status", "").strip()
    query = Enquiry.query
    if status:
        query = query.filter_by(status=status)
    items = query.order_by(Enquiry.created_at.desc()).limit(250).all()
    return render_template("admin/enquiries.html", enquiries=items, selected_status=status)

@app.route("/admin/enquiries/<int:enquiry_id>", methods=["GET", "POST"])
@admin_required
def admin_enquiry_detail(enquiry_id):
    item = db.get_or_404(Enquiry, enquiry_id)
    if request.method == "POST":
        item.status = request.form.get("status", "New")
        if item.status not in {"New", "Contacted", "Quotation Sent", "Confirmed", "Completed", "Cancelled"}:
            abort(400)
        item.internal_notes = request.form.get("internal_notes", "")[:5000]
        db.session.commit()
        flash("Enquiry updated.", "success")
        return redirect(url_for("admin_enquiry_detail", enquiry_id=item.id))
    return render_template("admin/enquiry_detail.html", enquiry=item)

# Generic CRUD routes for manageable catalogue tables.
CATALOGS = {
    "services": {"model": Service, "fields": [("title", "Title"), ("description", "Description"), ("image", "Image filename")], "bool": "published"},
    "branches": {"model": Branch, "fields": [("name", "Branch name"), ("address", "Address"), ("city", "City"), ("phone", "Phone"), ("hours", "Business hours"), ("map_url", "Google Maps URL")], "bool": "published"},
    "team": {"model": TeamMember, "fields": [("name", "Name"), ("designation", "Designation"), ("bio", "Biography"), ("image", "Image filename")], "bool": "published"},
    "certifications": {"model": Certification, "fields": [("title", "Certificate title"), ("issuer", "Issuing authority"), ("certificate_number", "Certificate number"), ("validity", "Validity"), ("document", "Document filename")], "bool": "published"},
    "testimonials": {"model": Testimonial, "fields": [("customer_name", "Customer name"), ("quote", "Testimonial")], "bool": "published"},
}

@app.route("/admin/manage/<catalog>")
@admin_required
def manage_catalog(catalog):
    if catalog not in CATALOGS:
        abort(404)
    config = CATALOGS[catalog]
    items = config["model"].query.order_by(config["model"].id.desc()).limit(300).all()
    return render_template("admin/catalog_list.html", catalog=catalog, config=config, items=items)

@app.route("/admin/manage/<catalog>/new", methods=["GET", "POST"])
@app.route("/admin/manage/<catalog>/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_catalog(catalog, item_id=None):
    if catalog not in CATALOGS:
        abort(404)
    config = CATALOGS[catalog]
    model = config["model"]
    item = db.session.get(model, item_id) if item_id else model()
    if item_id and not item:
        abort(404)
    if request.method == "POST":
        for field, label in config["fields"]:
            value = request.form.get(field, "").strip()
            setattr(item, field, value or None if field in {"image", "document", "map_url"} else value)
        setattr(item, config["bool"], request.form.get("published") == "on")
        db.session.add(item)
        db.session.commit()
        flash("Record saved.", "success")
        return redirect(url_for("manage_catalog", catalog=catalog))
    return render_template("admin/catalog_edit.html", catalog=catalog, config=config, item=item)

@app.route("/admin/manage/<catalog>/<int:item_id>/delete", methods=["POST"])
@admin_required
def delete_catalog(catalog, item_id):
    if catalog not in CATALOGS:
        abort(404)
    item = db.get_or_404(CATALOGS[catalog]["model"], item_id)
    db.session.delete(item)
    db.session.commit()
    flash("Record deleted.", "success")
    return redirect(url_for("manage_catalog", catalog=catalog))

@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    keys = ["business_phone", "business_email", "business_address", "whatsapp_number", "instagram_url", "facebook_url"]
    if request.method == "POST":
        for key in keys:
            value = request.form.get(key, "").strip()[:500]
            setting = SiteSetting.query.filter_by(key=key).first()
            if setting:
                setting.value = value
            else:
                db.session.add(SiteSetting(key=key, value=value))
        db.session.commit()
        flash("Website settings saved.", "success")
        return redirect(url_for("admin_settings"))
    settings = {s.key: s.value for s in SiteSetting.query.filter(SiteSetting.key.in_(keys)).all()}
    return render_template("admin/settings.html", settings=settings)

@app.route("/admin/password", methods=["GET", "POST"])
@admin_required
def admin_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        if not current_user.check_password(current_password):
            flash("Current password is incorrect.", "error")
        elif len(new_password) < 12:
            flash("New password must be at least 12 characters.", "error")
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash("Password updated.", "success")
            return redirect(url_for("admin_dashboard"))
    return render_template("admin/password.html")

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

@app.errorhandler(413)
def file_too_large(error):
    flash("Upload too large. Maximum request size is 8 MB.", "error")
    return redirect(request.referrer or url_for("home"))

def init_db():
    with app.app_context():
        db.create_all()
        # Seed neutral editable examples only when the database is empty.
        if Service.query.count() == 0:
            db.session.add_all([
                Service(title="Wedding Catering", description="Custom wedding menus and service plans. Contact us for a quotation."),
                Service(title="Corporate Catering", description="Catering options for meetings, office events, and corporate gatherings."),
                Service(title="Private Events", description="Flexible catering for birthdays, anniversaries, and family celebrations."),
            ])
        if Branch.query.count() == 0:
            db.session.add(Branch(name="Main Branch — Details Pending", address="Address to be confirmed", city="City to be confirmed", phone="Contact details to be confirmed"))
        db.session.commit()

if __name__ == "__main__":
    init_db()
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
