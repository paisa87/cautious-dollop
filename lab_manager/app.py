from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, send_from_directory, abort)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vgcc-lab-manager-2024-change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lab_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

db = SQLAlchemy(app)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'fasta'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'results'), exist_ok=True)

ALLOWED_FASTA = {'fa', 'fasta', 'txt'}
ALLOWED_RESULTS = {'xlsx', 'csv', 'txt', 'pdf'}

# ── Models ────────────────────────────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    initials = db.Column(db.String(10), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')  # instructor, staff, student

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(300))
    contact = db.Column(db.String(100))
    account_number = db.Column(db.String(50))
    notes = db.Column(db.Text)


class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), default='chemical')
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'))
    catalog_number = db.Column(db.String(100))
    unit_size = db.Column(db.String(50))
    cas_number = db.Column(db.String(50))
    location_room = db.Column(db.String(50))
    location_unit = db.Column(db.String(100))
    location_details = db.Column(db.String(200))
    amount_in_stock = db.Column(db.String(50))
    min_stock = db.Column(db.String(50))
    price = db.Column(db.Float)
    expiration_date = db.Column(db.Date)
    lot_number = db.Column(db.String(100))
    date_received = db.Column(db.Date)
    date_opened = db.Column(db.Date)
    formula = db.Column(db.String(100))
    molecular_weight = db.Column(db.Float)
    physical_state = db.Column(db.String(50))
    purity = db.Column(db.String(50))
    sds_link = db.Column(db.String(500))
    url = db.Column(db.String(500))
    notes = db.Column(db.Text)
    # Primer/probe-specific fields
    sequence_5to3 = db.Column(db.Text)
    target_gene = db.Column(db.String(100))
    organism_target = db.Column(db.String(100))
    primer_application = db.Column(db.String(100))
    reference = db.Column(db.String(300))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    added_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    vendor = db.relationship('Vendor', backref='items')
    added_by = db.relationship('User', foreign_keys=[added_by_id])


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    accession_number = db.Column(db.String(50), unique=True)
    batch_id = db.Column(db.String(50))
    sample_name = db.Column(db.String(200), nullable=False)
    organism_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date_collected = db.Column(db.Date)
    storage_location = db.Column(db.String(200))
    notes = db.Column(db.Text)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    submitted_by = db.relationship('User', foreign_keys=[submitted_by_id])


class QCMeasurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    method = db.Column(db.String(20))           # Qubit, Nanodrop
    sop = db.Column(db.String(20))              # VG001, VG005
    nucleic_acid_type = db.Column(db.String(20))
    concentration_ng_ul = db.Column(db.Float)
    ratio_260_280 = db.Column(db.Float)
    ratio_260_230 = db.Column(db.Float)
    notes = db.Column(db.Text)

    sample = db.relationship('Sample', backref='qc_measurements')
    operator = db.relationship('User', foreign_keys=[operator_id])


class Extraction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(50))
    date = db.Column(db.Date)
    sop = db.Column(db.String(20))
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    instrument = db.Column(db.String(100))
    checklist_complete = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

    operator = db.relationship('User', foreign_keys=[operator_id])
    extraction_samples = db.relationship('ExtractionSample', backref='extraction',
                                         lazy=True, cascade='all, delete-orphan')


class ExtractionSample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    extraction_id = db.Column(db.Integer, db.ForeignKey('extraction.id'))
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'))
    tube_id = db.Column(db.String(50))
    well_position = db.Column(db.String(10))
    tissue_amount_mg = db.Column(db.Float)
    final_volume_ul = db.Column(db.Float)

    sample = db.relationship('Sample')


class PCRRun(db.Model):
    __tablename__ = 'pcr_run'
    id = db.Column(db.Integer, primary_key=True)
    run_date = db.Column(db.Date)
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    thermocycler_program = db.Column(db.String(100))
    gel_run = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

    operator = db.relationship('User', foreign_keys=[operator_id])
    pcr_samples = db.relationship('PCRSample', backref='pcr_run',
                                  lazy=True, cascade='all, delete-orphan')


class PCRSample(db.Model):
    __tablename__ = 'pcr_sample'
    id = db.Column(db.Integer, primary_key=True)
    pcr_run_id = db.Column(db.Integer, db.ForeignKey('pcr_run.id'))
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'))
    tube_label = db.Column(db.String(50))
    primer_f_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'))
    primer_r_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'))
    template_volume_ul = db.Column(db.Float)
    expected_size_bp = db.Column(db.Integer)
    result = db.Column(db.String(100))

    sample = db.relationship('Sample')
    primer_f = db.relationship('InventoryItem', foreign_keys=[primer_f_id])
    primer_r = db.relationship('InventoryItem', foreign_keys=[primer_r_id])


class SequencingRun(db.Model):
    __tablename__ = 'sequencing_run'
    id = db.Column(db.Integer, primary_key=True)
    run_date = db.Column(db.Date)
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    instrument = db.Column(db.String(100), default='SeqStudio')
    notes = db.Column(db.Text)

    operator = db.relationship('User', foreign_keys=[operator_id])
    seq_samples = db.relationship('SequencingSample', backref='run',
                                  lazy=True, cascade='all, delete-orphan')


class SequencingSample(db.Model):
    __tablename__ = 'sequencing_sample'
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('sequencing_run.id'))
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'))
    tube_number = db.Column(db.Integer)
    sample_label = db.Column(db.String(100))
    primer_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'))
    bigdye_volume_ul = db.Column(db.Float)
    template_volume_ul = db.Column(db.Float)
    concentration_ng_ul = db.Column(db.Float)
    fasta_filename = db.Column(db.String(500))
    result_notes = db.Column(db.Text)

    sample = db.relationship('Sample')
    primer = db.relationship('InventoryItem', foreign_keys=[primer_id])


class QPCRRun(db.Model):
    __tablename__ = 'qpcr_run'
    id = db.Column(db.Integer, primary_key=True)
    run_date = db.Column(db.Date)
    operator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assay_type = db.Column(db.String(100))
    instrument = db.Column(db.String(100), default='QuantStudio 3')
    plate_filename = db.Column(db.String(500))
    notes = db.Column(db.Text)

    operator = db.relationship('User', foreign_keys=[operator_id])
    qpcr_samples = db.relationship('QPCRSample', backref='qpcr_run',
                                   lazy=True, cascade='all, delete-orphan')


class QPCRSample(db.Model):
    __tablename__ = 'qpcr_sample'
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.Integer, db.ForeignKey('qpcr_run.id'))
    sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'))
    well_position = db.Column(db.String(10))
    ct_value = db.Column(db.Float)
    replicate_group = db.Column(db.String(50))
    result = db.Column(db.String(100))

    sample = db.relationship('Sample')


# ── Auth helpers ──────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def instructor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        u = db.session.get(User, session['user_id'])
        if u.role not in ('instructor', 'staff'):
            flash('You do not have permission for that action.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


def current_user():
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None


app.jinja_env.globals['current_user'] = current_user
app.jinja_env.globals['today'] = date.today


def allowed_file(filename, allowed):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def save_upload(file, subfolder, allowed):
    if file and file.filename and allowed_file(file.filename, allowed):
        filename = secure_filename(file.filename)
        dest = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)
        file.save(dest)
        return filename
    return None


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form['username']).first()
        if u and u.check_password(request.form['password']):
            session['user_id'] = u.id
            flash(f'Welcome back, {u.name}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def dashboard():
    from sqlalchemy import func
    stats = {
        'inventory': InventoryItem.query.count(),
        'samples': Sample.query.count(),
        'seq_runs': SequencingRun.query.count(),
        'qpcr_runs': QPCRRun.query.count(),
    }
    # Items expiring within 60 days or already expired
    today = date.today()
    from datetime import timedelta
    soon = today + timedelta(days=60)
    expiring = (InventoryItem.query
                .filter(InventoryItem.expiration_date != None)
                .filter(InventoryItem.expiration_date <= soon)
                .order_by(InventoryItem.expiration_date)
                .limit(10).all())
    recent_samples = Sample.query.order_by(Sample.date_added.desc()).limit(5).all()
    recent_seq = SequencingRun.query.order_by(SequencingRun.run_date.desc()).limit(5).all()
    return render_template('index.html', stats=stats, expiring=expiring,
                           recent_samples=recent_samples, recent_seq=recent_seq,
                           today=today)


# ── Inventory ─────────────────────────────────────────────────────────────────

@app.route('/inventory')
@login_required
def inventory_list():
    q = request.args.get('q', '').strip()
    cat = request.args.get('cat', '')
    room = request.args.get('room', '')
    query = InventoryItem.query
    if q:
        query = query.filter(InventoryItem.item_name.ilike(f'%{q}%'))
    if cat:
        query = query.filter_by(category=cat)
    if room:
        query = query.filter_by(location_room=room)
    items = query.order_by(InventoryItem.item_name).all()
    categories = db.session.query(InventoryItem.category).distinct().order_by(InventoryItem.category).all()
    rooms = db.session.query(InventoryItem.location_room).distinct().order_by(InventoryItem.location_room).all()
    return render_template('inventory/list.html', items=items, q=q, cat=cat, room=room,
                           categories=[c[0] for c in categories if c[0]],
                           rooms=[r[0] for r in rooms if r[0]])


@app.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def inventory_add():
    vendors = Vendor.query.order_by(Vendor.name).all()
    if request.method == 'POST':
        f = request.form
        item = InventoryItem(
            item_name=f['item_name'],
            category=f.get('category', 'chemical'),
            vendor_id=f.get('vendor_id') or None,
            catalog_number=f.get('catalog_number'),
            unit_size=f.get('unit_size'),
            cas_number=f.get('cas_number'),
            location_room=f.get('location_room'),
            location_unit=f.get('location_unit'),
            location_details=f.get('location_details'),
            amount_in_stock=f.get('amount_in_stock'),
            min_stock=f.get('min_stock'),
            price=float(f['price']) if f.get('price') else None,
            expiration_date=_parse_date(f.get('expiration_date')),
            lot_number=f.get('lot_number'),
            date_received=_parse_date(f.get('date_received')),
            date_opened=_parse_date(f.get('date_opened')),
            formula=f.get('formula'),
            molecular_weight=float(f['molecular_weight']) if f.get('molecular_weight') else None,
            physical_state=f.get('physical_state'),
            purity=f.get('purity'),
            sds_link=f.get('sds_link'),
            url=f.get('url'),
            notes=f.get('notes'),
            sequence_5to3=f.get('sequence_5to3'),
            target_gene=f.get('target_gene'),
            organism_target=f.get('organism_target'),
            primer_application=f.get('primer_application'),
            reference=f.get('reference'),
            added_by_id=session['user_id'],
        )
        db.session.add(item)
        db.session.commit()
        flash(f'"{item.item_name}" added to inventory.', 'success')
        return redirect(url_for('inventory_list'))
    return render_template('inventory/form.html', item=None, vendors=vendors,
                           categories=_inventory_categories())


@app.route('/inventory/<int:id>')
@login_required
def inventory_view(id):
    item = db.get_or_404(InventoryItem, id)
    return render_template('inventory/view.html', item=item)


@app.route('/inventory/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def inventory_edit(id):
    item = db.get_or_404(InventoryItem, id)
    vendors = Vendor.query.order_by(Vendor.name).all()
    if request.method == 'POST':
        f = request.form
        item.item_name = f['item_name']
        item.category = f.get('category', item.category)
        item.vendor_id = f.get('vendor_id') or None
        item.catalog_number = f.get('catalog_number')
        item.unit_size = f.get('unit_size')
        item.cas_number = f.get('cas_number')
        item.location_room = f.get('location_room')
        item.location_unit = f.get('location_unit')
        item.location_details = f.get('location_details')
        item.amount_in_stock = f.get('amount_in_stock')
        item.min_stock = f.get('min_stock')
        item.price = float(f['price']) if f.get('price') else None
        item.expiration_date = _parse_date(f.get('expiration_date'))
        item.lot_number = f.get('lot_number')
        item.date_received = _parse_date(f.get('date_received'))
        item.date_opened = _parse_date(f.get('date_opened'))
        item.formula = f.get('formula')
        item.molecular_weight = float(f['molecular_weight']) if f.get('molecular_weight') else None
        item.physical_state = f.get('physical_state')
        item.purity = f.get('purity')
        item.sds_link = f.get('sds_link')
        item.url = f.get('url')
        item.notes = f.get('notes')
        item.sequence_5to3 = f.get('sequence_5to3')
        item.target_gene = f.get('target_gene')
        item.organism_target = f.get('organism_target')
        item.primer_application = f.get('primer_application')
        item.reference = f.get('reference')
        db.session.commit()
        flash(f'"{item.item_name}" updated.', 'success')
        return redirect(url_for('inventory_view', id=item.id))
    return render_template('inventory/form.html', item=item, vendors=vendors,
                           categories=_inventory_categories())


@app.route('/inventory/<int:id>/delete', methods=['POST'])
@instructor_required
def inventory_delete(id):
    item = db.get_or_404(InventoryItem, id)
    name = item.item_name
    db.session.delete(item)
    db.session.commit()
    flash(f'"{name}" removed from inventory.', 'info')
    return redirect(url_for('inventory_list'))


# ── Samples ───────────────────────────────────────────────────────────────────

@app.route('/samples')
@login_required
def samples_list():
    q = request.args.get('q', '').strip()
    samples = Sample.query
    if q:
        samples = samples.filter(
            Sample.sample_name.ilike(f'%{q}%') |
            Sample.accession_number.ilike(f'%{q}%') |
            Sample.organism_type.ilike(f'%{q}%')
        )
    samples = samples.order_by(Sample.date_added.desc()).all()
    return render_template('samples/list.html', samples=samples, q=q)


@app.route('/samples/add', methods=['GET', 'POST'])
@login_required
def samples_add():
    users = User.query.order_by(User.name).all()
    if request.method == 'POST':
        f = request.form
        # Auto-generate accession number if blank
        acc = f.get('accession_number') or _next_accession()
        s = Sample(
            accession_number=acc,
            batch_id=f.get('batch_id'),
            sample_name=f['sample_name'],
            organism_type=f.get('organism_type'),
            description=f.get('description'),
            submitted_by_id=f.get('submitted_by_id') or session['user_id'],
            date_collected=_parse_date(f.get('date_collected')),
            storage_location=f.get('storage_location'),
            notes=f.get('notes'),
        )
        db.session.add(s)
        db.session.commit()
        flash(f'Sample "{s.sample_name}" ({s.accession_number}) added.', 'success')
        return redirect(url_for('samples_view', id=s.id))
    return render_template('samples/form.html', sample=None, users=users)


@app.route('/samples/<int:id>')
@login_required
def samples_view(id):
    s = db.get_or_404(Sample, id)
    return render_template('samples/view.html', sample=s)


@app.route('/samples/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def samples_edit(id):
    s = db.get_or_404(Sample, id)
    users = User.query.order_by(User.name).all()
    if request.method == 'POST':
        f = request.form
        s.accession_number = f.get('accession_number') or s.accession_number
        s.batch_id = f.get('batch_id')
        s.sample_name = f['sample_name']
        s.organism_type = f.get('organism_type')
        s.description = f.get('description')
        s.submitted_by_id = f.get('submitted_by_id') or s.submitted_by_id
        s.date_collected = _parse_date(f.get('date_collected'))
        s.storage_location = f.get('storage_location')
        s.notes = f.get('notes')
        db.session.commit()
        flash('Sample updated.', 'success')
        return redirect(url_for('samples_view', id=s.id))
    return render_template('samples/form.html', sample=s, users=users)


@app.route('/samples/<int:id>/delete', methods=['POST'])
@instructor_required
def samples_delete(id):
    s = db.get_or_404(Sample, id)
    name = s.sample_name
    db.session.delete(s)
    db.session.commit()
    flash(f'Sample "{name}" deleted.', 'info')
    return redirect(url_for('samples_list'))


# ── QC Measurements ───────────────────────────────────────────────────────────

@app.route('/qc')
@login_required
def qc_list():
    records = QCMeasurement.query.order_by(QCMeasurement.date.desc()).all()
    return render_template('qc/list.html', records=records)


@app.route('/qc/add', methods=['GET', 'POST'])
@login_required
def qc_add():
    samples = Sample.query.order_by(Sample.sample_name).all()
    users = User.query.order_by(User.name).all()
    if request.method == 'POST':
        f = request.form
        qc = QCMeasurement(
            sample_id=f['sample_id'],
            operator_id=f.get('operator_id') or session['user_id'],
            method=f.get('method'),
            sop=f.get('sop'),
            nucleic_acid_type=f.get('nucleic_acid_type'),
            concentration_ng_ul=float(f['concentration_ng_ul']) if f.get('concentration_ng_ul') else None,
            ratio_260_280=float(f['ratio_260_280']) if f.get('ratio_260_280') else None,
            ratio_260_230=float(f['ratio_260_230']) if f.get('ratio_260_230') else None,
            notes=f.get('notes'),
        )
        db.session.add(qc)
        db.session.commit()
        flash('QC measurement recorded.', 'success')
        return redirect(url_for('qc_list'))
    preselect = request.args.get('sample_id')
    return render_template('qc/form.html', samples=samples, users=users,
                           preselect=preselect)


@app.route('/qc/<int:id>/delete', methods=['POST'])
@instructor_required
def qc_delete(id):
    qc = db.get_or_404(QCMeasurement, id)
    db.session.delete(qc)
    db.session.commit()
    flash('QC record deleted.', 'info')
    return redirect(url_for('qc_list'))


# ── Extractions ───────────────────────────────────────────────────────────────

@app.route('/extractions')
@login_required
def extractions_list():
    exts = Extraction.query.order_by(Extraction.date.desc()).all()
    return render_template('extractions/list.html', extractions=exts)


@app.route('/extractions/add', methods=['GET', 'POST'])
@login_required
def extractions_add():
    users = User.query.order_by(User.name).all()
    samples = Sample.query.order_by(Sample.sample_name).all()
    if request.method == 'POST':
        f = request.form
        ext = Extraction(
            batch_id=f.get('batch_id') or _today_batch_id(),
            date=_parse_date(f.get('date')) or date.today(),
            sop=f.get('sop'),
            operator_id=f.get('operator_id') or session['user_id'],
            instrument=f.get('instrument'),
            checklist_complete='checklist_complete' in f,
            notes=f.get('notes'),
        )
        db.session.add(ext)
        db.session.flush()  # get ext.id before adding children
        # Handle multiple samples submitted as lists
        s_ids = request.form.getlist('sample_id[]')
        tube_ids = request.form.getlist('tube_id[]')
        wells = request.form.getlist('well_position[]')
        tissues = request.form.getlist('tissue_amount_mg[]')
        vols = request.form.getlist('final_volume_ul[]')
        for i, sid in enumerate(s_ids):
            if sid:
                es = ExtractionSample(
                    extraction_id=ext.id,
                    sample_id=int(sid),
                    tube_id=tube_ids[i] if i < len(tube_ids) else None,
                    well_position=wells[i] if i < len(wells) else None,
                    tissue_amount_mg=float(tissues[i]) if i < len(tissues) and tissues[i] else None,
                    final_volume_ul=float(vols[i]) if i < len(vols) and vols[i] else None,
                )
                db.session.add(es)
        db.session.commit()
        flash(f'Extraction batch {ext.batch_id} saved.', 'success')
        return redirect(url_for('extractions_view', id=ext.id))
    return render_template('extractions/form.html', users=users, samples=samples)


@app.route('/extractions/<int:id>')
@login_required
def extractions_view(id):
    ext = db.get_or_404(Extraction, id)
    return render_template('extractions/view.html', extraction=ext)


# ── PCR ───────────────────────────────────────────────────────────────────────

@app.route('/pcr')
@login_required
def pcr_list():
    runs = PCRRun.query.order_by(PCRRun.run_date.desc()).all()
    return render_template('pcr/list.html', runs=runs)


@app.route('/pcr/add', methods=['GET', 'POST'])
@login_required
def pcr_add():
    users = User.query.order_by(User.name).all()
    samples = Sample.query.order_by(Sample.sample_name).all()
    primers = InventoryItem.query.filter(
        InventoryItem.category.in_(['primer', 'probe'])
    ).order_by(InventoryItem.item_name).all()
    if request.method == 'POST':
        f = request.form
        run = PCRRun(
            run_date=_parse_date(f.get('run_date')) or date.today(),
            operator_id=f.get('operator_id') or session['user_id'],
            thermocycler_program=f.get('thermocycler_program'),
            gel_run='gel_run' in f,
            notes=f.get('notes'),
        )
        db.session.add(run)
        db.session.flush()
        s_ids = request.form.getlist('sample_id[]')
        labels = request.form.getlist('tube_label[]')
        pf_ids = request.form.getlist('primer_f_id[]')
        pr_ids = request.form.getlist('primer_r_id[]')
        tvols = request.form.getlist('template_volume_ul[]')
        sizes = request.form.getlist('expected_size_bp[]')
        results = request.form.getlist('result[]')
        for i, sid in enumerate(s_ids):
            if sid:
                ps = PCRSample(
                    pcr_run_id=run.id,
                    sample_id=int(sid),
                    tube_label=labels[i] if i < len(labels) else None,
                    primer_f_id=int(pf_ids[i]) if i < len(pf_ids) and pf_ids[i] else None,
                    primer_r_id=int(pr_ids[i]) if i < len(pr_ids) and pr_ids[i] else None,
                    template_volume_ul=float(tvols[i]) if i < len(tvols) and tvols[i] else None,
                    expected_size_bp=int(sizes[i]) if i < len(sizes) and sizes[i] else None,
                    result=results[i] if i < len(results) else None,
                )
                db.session.add(ps)
        db.session.commit()
        flash('PCR run recorded.', 'success')
        return redirect(url_for('pcr_view', id=run.id))
    return render_template('pcr/form.html', users=users, samples=samples, primers=primers)


@app.route('/pcr/<int:id>')
@login_required
def pcr_view(id):
    run = db.get_or_404(PCRRun, id)
    return render_template('pcr/view.html', run=run)


# ── Sequencing ────────────────────────────────────────────────────────────────

@app.route('/sequencing')
@login_required
def sequencing_list():
    runs = SequencingRun.query.order_by(SequencingRun.run_date.desc()).all()
    return render_template('sequencing/list.html', runs=runs)


@app.route('/sequencing/add', methods=['GET', 'POST'])
@login_required
def sequencing_add():
    users = User.query.order_by(User.name).all()
    samples = Sample.query.order_by(Sample.sample_name).all()
    primers = InventoryItem.query.filter(
        InventoryItem.category.in_(['primer', 'probe'])
    ).order_by(InventoryItem.item_name).all()
    if request.method == 'POST':
        f = request.form
        run = SequencingRun(
            run_date=_parse_date(f.get('run_date')) or date.today(),
            operator_id=f.get('operator_id') or session['user_id'],
            instrument=f.get('instrument', 'SeqStudio'),
            notes=f.get('notes'),
        )
        db.session.add(run)
        db.session.flush()
        s_ids = request.form.getlist('sample_id[]')
        tube_nums = request.form.getlist('tube_number[]')
        labels = request.form.getlist('sample_label[]')
        primer_ids = request.form.getlist('primer_id[]')
        bigdye_vols = request.form.getlist('bigdye_volume_ul[]')
        tmpl_vols = request.form.getlist('template_volume_ul[]')
        concs = request.form.getlist('concentration_ng_ul[]')
        result_notes = request.form.getlist('result_notes[]')
        fasta_files = request.files.getlist('fasta_file[]')
        for i, sid in enumerate(s_ids):
            if sid:
                fasta_name = None
                if i < len(fasta_files):
                    fasta_name = save_upload(fasta_files[i], 'fasta', ALLOWED_FASTA)
                ss = SequencingSample(
                    run_id=run.id,
                    sample_id=int(sid),
                    tube_number=int(tube_nums[i]) if i < len(tube_nums) and tube_nums[i] else i + 1,
                    sample_label=labels[i] if i < len(labels) else None,
                    primer_id=int(primer_ids[i]) if i < len(primer_ids) and primer_ids[i] else None,
                    bigdye_volume_ul=float(bigdye_vols[i]) if i < len(bigdye_vols) and bigdye_vols[i] else None,
                    template_volume_ul=float(tmpl_vols[i]) if i < len(tmpl_vols) and tmpl_vols[i] else None,
                    concentration_ng_ul=float(concs[i]) if i < len(concs) and concs[i] else None,
                    fasta_filename=fasta_name,
                    result_notes=result_notes[i] if i < len(result_notes) else None,
                )
                db.session.add(ss)
        db.session.commit()
        flash('Sequencing run recorded.', 'success')
        return redirect(url_for('sequencing_view', id=run.id))
    return render_template('sequencing/form.html', users=users, samples=samples,
                           primers=primers)


@app.route('/sequencing/<int:id>')
@login_required
def sequencing_view(id):
    run = db.get_or_404(SequencingRun, id)
    return render_template('sequencing/view.html', run=run)


@app.route('/sequencing/fasta/<path:filename>')
@login_required
def fasta_download(filename):
    return send_from_directory(
        os.path.join(app.config['UPLOAD_FOLDER'], 'fasta'), filename
    )


# ── qPCR ──────────────────────────────────────────────────────────────────────

@app.route('/qpcr')
@login_required
def qpcr_list():
    runs = QPCRRun.query.order_by(QPCRRun.run_date.desc()).all()
    return render_template('qpcr/list.html', runs=runs)


@app.route('/qpcr/add', methods=['GET', 'POST'])
@login_required
def qpcr_add():
    users = User.query.order_by(User.name).all()
    samples = Sample.query.order_by(Sample.sample_name).all()
    if request.method == 'POST':
        f = request.form
        plate_file = request.files.get('plate_file')
        plate_name = save_upload(plate_file, 'results', ALLOWED_RESULTS)
        run = QPCRRun(
            run_date=_parse_date(f.get('run_date')) or date.today(),
            operator_id=f.get('operator_id') or session['user_id'],
            assay_type=f.get('assay_type'),
            instrument=f.get('instrument', 'QuantStudio 3'),
            plate_filename=plate_name,
            notes=f.get('notes'),
        )
        db.session.add(run)
        db.session.flush()
        s_ids = request.form.getlist('sample_id[]')
        wells = request.form.getlist('well_position[]')
        cts = request.form.getlist('ct_value[]')
        reps = request.form.getlist('replicate_group[]')
        results = request.form.getlist('result[]')
        for i, sid in enumerate(s_ids):
            if sid:
                qs = QPCRSample(
                    run_id=run.id,
                    sample_id=int(sid),
                    well_position=wells[i] if i < len(wells) else None,
                    ct_value=float(cts[i]) if i < len(cts) and cts[i] else None,
                    replicate_group=reps[i] if i < len(reps) else None,
                    result=results[i] if i < len(results) else None,
                )
                db.session.add(qs)
        db.session.commit()
        flash('qPCR run recorded.', 'success')
        return redirect(url_for('qpcr_view', id=run.id))
    return render_template('qpcr/form.html', users=users, samples=samples,
                           assay_types=_qpcr_assay_types())


@app.route('/qpcr/<int:id>')
@login_required
def qpcr_view(id):
    run = db.get_or_404(QPCRRun, id)
    return render_template('qpcr/view.html', run=run)


@app.route('/qpcr/results/<path:filename>')
@login_required
def qpcr_download(filename):
    return send_from_directory(
        os.path.join(app.config['UPLOAD_FOLDER'], 'results'), filename
    )


# ── Vendors ───────────────────────────────────────────────────────────────────

@app.route('/vendors')
@login_required
def vendors_list():
    vendors = Vendor.query.order_by(Vendor.name).all()
    return render_template('vendors/list.html', vendors=vendors)


@app.route('/vendors/add', methods=['GET', 'POST'])
@instructor_required
def vendors_add():
    if request.method == 'POST':
        f = request.form
        v = Vendor(name=f['name'], website=f.get('website'),
                   contact=f.get('contact'), account_number=f.get('account_number'),
                   notes=f.get('notes'))
        db.session.add(v)
        db.session.commit()
        flash(f'Vendor "{v.name}" added.', 'success')
        return redirect(url_for('vendors_list'))
    return render_template('vendors/form.html', vendor=None)


@app.route('/vendors/<int:id>/edit', methods=['GET', 'POST'])
@instructor_required
def vendors_edit(id):
    v = db.get_or_404(Vendor, id)
    if request.method == 'POST':
        f = request.form
        v.name = f['name']
        v.website = f.get('website')
        v.contact = f.get('contact')
        v.account_number = f.get('account_number')
        v.notes = f.get('notes')
        db.session.commit()
        flash(f'Vendor "{v.name}" updated.', 'success')
        return redirect(url_for('vendors_list'))
    return render_template('vendors/form.html', vendor=v)


# ── Users ─────────────────────────────────────────────────────────────────────

@app.route('/users')
@instructor_required
def users_list():
    users = User.query.order_by(User.name).all()
    return render_template('users/list.html', users=users)


@app.route('/users/add', methods=['GET', 'POST'])
@instructor_required
def users_add():
    if request.method == 'POST':
        f = request.form
        if User.query.filter_by(username=f['username']).first():
            flash('That username is already taken.', 'danger')
            return render_template('users/form.html', user=None)
        u = User(name=f['name'], initials=f['initials'],
                 username=f['username'], role=f.get('role', 'student'))
        u.set_password(f['password'])
        db.session.add(u)
        db.session.commit()
        flash(f'User "{u.name}" created.', 'success')
        return redirect(url_for('users_list'))
    return render_template('users/form.html', user=None)


@app.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@instructor_required
def users_edit(id):
    u = db.get_or_404(User, id)
    if request.method == 'POST':
        f = request.form
        u.name = f['name']
        u.initials = f['initials']
        u.role = f.get('role', u.role)
        if f.get('password'):
            u.set_password(f['password'])
        db.session.commit()
        flash(f'User "{u.name}" updated.', 'success')
        return redirect(url_for('users_list'))
    return render_template('users/form.html', user=u)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_date(s):
    if not s:
        return None
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y'):
        try:
            return datetime.strptime(s, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _next_accession():
    today_str = date.today().strftime('%Y%m%d')
    count = Sample.query.filter(
        Sample.accession_number.like(f'{today_str}%')
    ).count()
    return f'{today_str}-{count + 1:03d}'


def _today_batch_id():
    return date.today().strftime('%Y%m%d') + '-001'


def _inventory_categories():
    return ['chemical', 'reagent', 'primer', 'probe', 'standard',
            'consumable', 'equipment', 'solution', 'media', 'other']


def _qpcr_assay_types():
    return [
        'BactiQuant (bacterial load)',
        'FungiQuant (fungal load)',
        'Black Spot of Rose (Dc_09)',
        'Grey Mold (Bc3)',
        'Other',
    ]


# ── Init ──────────────────────────────────────────────────────────────────────

def init_db():
    db.create_all()
    # Seed default admin if no users exist
    if User.query.count() == 0:
        admin = User(name='Lab Instructor', initials='ALP',
                     username='admin', role='instructor')
        admin.set_password('labadmin')
        db.session.add(admin)
        # Seed approved vendors from the inventory
        vendors = [
            Vendor(name='ThermoFisher Scientific', website='https://www.thermofisher.com'),
            Vendor(name='Sigma-Aldrich / MilliporeSigma', website='https://www.sigmaaldrich.com'),
            Vendor(name='New England Biolabs (NEB)', website='https://www.neb.com'),
            Vendor(name='Promega', website='https://www.promega.com'),
            Vendor(name='Zymo Research', website='https://www.zymoresearch.com'),
            Vendor(name='Qiagen', website='https://www.qiagen.com'),
            Vendor(name='Bio-Rad', website='https://www.bio-rad.com'),
            Vendor(name='VWR International', website='https://www.vwr.com'),
            Vendor(name='Fisher Scientific', website='https://www.fishersci.com'),
            Vendor(name='Oxoid', website='https://www.oxoid.com'),
        ]
        for v in vendors:
            db.session.add(v)
        db.session.commit()
        print('Database initialized with default admin user (username: admin, password: labadmin)')
        print('IMPORTANT: Change the default password after first login!')


if __name__ == '__main__':
    with app.app_context():
        init_db()
    print('\n  Lab Manager is running.')
    print('  Open your browser to: http://localhost:5000\n')
    app.run(debug=False, host='0.0.0.0', port=5000)
