from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date, UTC
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func, extract
from sqlalchemy import or_
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

app = Flask(__name__)
UPLOAD_FOLDER = 'static'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = "crm_secret_key"

app.config['SQLALCHEMY_DATABASE_URI'] = \
'mysql+pymysql://root:RIYA1234@localhost/crm_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def has_access(*allowed_roles):

    return session.get(
        'role'
    ) in allowed_roles

class User(db.Model):

    __tablename__ = 'users'

    user_id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True
    )

    password = db.Column(
        db.String(255)
    )

    role = db.Column(
        db.String(50)
    )
    full_name = db.Column(
        db.String(100)
    )

    email = db.Column(
        db.String(100)
    )

    is_active = db.Column(
        db.String(10)
    )

class Lead(db.Model):

    __tablename__ = 'leads'

    lead_id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))

    reference = db.Column(db.String(200))

    location = db.Column(db.String(200))

    phone = db.Column(db.String(20))

    responses = db.Column(db.Text)

    date_of_1st_followup = db.Column(db.Date)

    next_to_call = db.Column(db.Date)

    recent = db.Column(db.Text)


class Meeting(db.Model):

    __tablename__ = 'meetings'

    meeting_id = db.Column(db.Integer, primary_key=True)

    meeting_fixed_by = db.Column(db.String(100))

    source = db.Column(db.String(100))

    name = db.Column(db.String(100))

    reference = db.Column(db.String(200))

    firm_name = db.Column(db.String(200))

    designation = db.Column(db.String(100))

    address = db.Column(db.Text)

    state = db.Column(db.String(100))

    contact_no = db.Column(db.String(20))

    email = db.Column(db.String(100))

    company_info_shared = db.Column(db.String(10))

    meeting_fixed = db.Column(db.String(10))

    date_of_meeting = db.Column(db.Date)

    mode_of_meeting = db.Column(db.String(50))

    meeting_status = db.Column(db.String(50))

    meeting_conducted_by = db.Column(db.String(100))

    floor_plan_shared = db.Column(db.String(10))

    site_visit = db.Column(db.String(10))

    post_meeting_mail = db.Column(db.String(10))

    date_of_last_followup = db.Column(db.Date)

    date_to_call_next = db.Column(db.Date)

    final_remarks = db.Column(db.Text)

    reschedule_date = db.Column(db.Date)
    
    reason_for_reschedule = db.Column(db.Text)

    remarks = db.Column(db.Text)

    lead_id = db.Column(
        db.Integer,
        db.ForeignKey('leads.lead_id')
    )

class Visit(db.Model):

    __tablename__ = 'visits'

    visit_id = db.Column(
        db.Integer,
        primary_key=True
    )

    meeting_id = db.Column(
        db.Integer,
        db.ForeignKey('meetings.meeting_id')
    )

    state = db.Column(
        db.String(100)
    )

    region = db.Column(
        db.String(100)
    )

    abc = db.Column(
        db.String(100)
    )

    company_name = db.Column(
        db.String(200)
    )

    person_name = db.Column(
        db.String(100)
    )

    designation = db.Column(
        db.String(100)
    )

    contact_no = db.Column(
        db.String(20)
    )

    address = db.Column(
        db.Text
    )

    brief = db.Column(
        db.Text
    )

    visit_date = db.Column(
        db.Date
    )

    leads_generated = db.Column(
        db.Integer
    )

    m2 = db.Column(
        db.Text
    )

    m3 = db.Column(
        db.Text
    )

class Drawing(db.Model):

    __tablename__ = 'drawings'

    drawing_id = db.Column(
        db.Integer,
        primary_key=True
    )

    visit_id = db.Column(
        db.Integer,
        db.ForeignKey('visits.visit_id')
    )

    name = db.Column(
        db.String(100)
    )

    address = db.Column(
        db.Text
    )

    iterations = db.Column(
        db.Integer
    )

    moca = db.Column(
        db.String(100)
    )

    drawing_pdf = db.Column(
        db.String(255)
    )

class Proposal(db.Model):

    __tablename__ = 'proposals'

    proposal_id = db.Column(db.Integer, primary_key=True)

    reference_no = db.Column(db.String(50))

    name = db.Column(db.String(100))

    phone_no_client = db.Column(db.String(20))

    source = db.Column(db.String(100))

    type = db.Column(db.String(100))

    reference_source_details = db.Column(db.Text)

    phone_no_source = db.Column(db.String(20))

    contact_person = db.Column(db.String(100))

    phone_no_contact_person = db.Column(db.String(20))

    email = db.Column(db.String(100))

    site_address = db.Column(db.Text)

    state = db.Column(db.String(100))

    total_area_sqft = db.Column(db.Numeric(10,2))

    type_of_units = db.Column(db.String(100))

    no_of_mvd_units = db.Column(db.Integer)

    no_of_mvd_max_units = db.Column(db.Integer)

    total_no_of_units = db.Column(db.Integer)

    product = db.Column(db.String(200))

    cost_total_per_unit = db.Column(db.Numeric(10,2))

    no_of_monitors = db.Column(db.Integer)

    cmc = db.Column(db.String(10))

    per_unit_cost = db.Column(db.Numeric(10,2))

    per_unit_cost_max_unit = db.Column(db.Numeric(10,2))

    cmc_cost = db.Column(db.Numeric(10,2))

    monitor_cost = db.Column(db.Numeric(10,2))

    installation_cost = db.Column(db.Numeric(10,2))

    total_amount = db.Column(db.Numeric(12,2))

    cmc_starting_period = db.Column(db.String(100))

    discount = db.Column(db.Numeric(10,2))

    final_amount = db.Column(db.Numeric(12,2))

    date_of_proposal_sent = db.Column(db.Date)

    proposal_prepared_by = db.Column(db.String(100))

    proposal_shared_by = db.Column(db.String(100))

    status = db.Column(db.String(50))

    date_of_last_followup = db.Column(db.Date)

    next_to_call = db.Column(db.Date)

    remarks = db.Column(db.Text)

    proposal_pdf = db.Column(db.String(255))

    meeting_id = db.Column(
        db.Integer,
        db.ForeignKey('meetings.meeting_id')
    )
    drawing_id = db.Column(
        db.Integer,
        db.ForeignKey('drawings.drawing_id')
    )

class SalesPipeline(db.Model):

    __tablename__ = 'sales_pipeline'

    sales_id = db.Column(
        db.Integer,
        primary_key=True
    )

    proposal_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'proposals.proposal_id'
        )
    )

    name = db.Column(
        db.String(100)
    )

    reference_no = db.Column(
        db.String(50)
    )

    project_stage = db.Column(
        db.String(100)
    )

    moc = db.Column(
        db.String(100)
    )

    source = db.Column(
        db.String(100)
    )

    next_action = db.Column(
        db.Text
    )

    address = db.Column(
        db.Text
    )

    contact_no = db.Column(
        db.String(20)
    )

    project_type = db.Column(
        db.String(100)
    )

    category = db.Column(
        db.String(100)
    )

    email_id = db.Column(
        db.String(100)
    )

    site_incharge = db.Column(
        db.String(100)
    )

    site_incharge_contact = db.Column(
        db.String(20)
    )

    first_contact = db.Column(
        db.Date
    )

    last_contact = db.Column(
        db.Date
    )

    followup_date = db.Column(
        db.Date
    )

    no_of_site_visits = db.Column(
        db.Integer
    )

    area_covered = db.Column(
        db.Numeric(12,2)
    )

    total_units = db.Column(
        db.Integer
    )

    price_of_units = db.Column(
        db.Numeric(12,2)
    )

    first_year_cmc = db.Column(
        db.Numeric(12,2)
    )

    installation = db.Column(
        db.Numeric(12,2)
    )

    total_sensor = db.Column(
        db.Integer
    )

    sensor_cost = db.Column(
        db.Numeric(12,2)
    )

    discount = db.Column(
        db.Numeric(12,2)
    )

    revenue = db.Column(
        db.Numeric(12,2)
    )

    amount_received = db.Column(
        db.Numeric(12,2)
    )

    amount_due = db.Column(
        db.Numeric(12,2)
    )

    total_revenue = db.Column(
        db.Numeric(12,2)
    )

    gst_no = db.Column(
        db.String(50)
    )

    cmc_onwards = db.Column(
        db.Numeric(12,2)
    )

    total_cmc = db.Column(
        db.Numeric(12,2)
    )

    sales_person = db.Column(
        db.String(100)
    )

class Invoice(db.Model):

    __tablename__ = 'invoices'

    invoice_id = db.Column(
        db.Integer,
        primary_key=True
    )

    sales_id = db.Column(
        db.Integer,
        db.ForeignKey('sales_pipeline.sales_id')
    )

    name = db.Column(
        db.String(100)
    )

    doi = db.Column(
        db.Date
    )

    invoice_no = db.Column(
        db.String(100)
    )

    gst_no = db.Column(
        db.String(50)
    )

    product_sold = db.Column(
        db.String(200)
    )

    total_units = db.Column(
        db.Integer
    )

    price_of_units = db.Column(
        db.Numeric(12,2)
    )

    first_year_cmc = db.Column(
        db.Numeric(12,2)
    )

    installation = db.Column(
        db.Numeric(12,2)
    )

    total_sensor = db.Column(
        db.Integer
    )

    sensor_cost = db.Column(
        db.Numeric(12,2)
    )

    revenue = db.Column(
        db.Numeric(12,2)
    )

    total_revenue = db.Column(
        db.Numeric(12,2)
    )

    invoice_pdf = db.Column(
        db.String(255)
    )

class Client(db.Model):

    __tablename__ = 'client'

    client_id = db.Column(db.Integer, primary_key=True)

    client_name = db.Column(db.String(100))

    monitor_present = db.Column(db.String(20))

    property_type = db.Column(db.String(200))

    address = db.Column(db.Text)

    location_link = db.Column(db.Text)

    nearest_metrostation = db.Column(db.String(100))

    mail_id = db.Column(db.String(100))

    state = db.Column(db.String(100))

    mobile_no = db.Column(db.String(20))

    product = db.Column(db.String(200))

    installation_date = db.Column(db.Date)

    activation_date = db.Column(db.Date)

    filter_colour = db.Column(db.String(50))

    no_of_units_installed = db.Column(db.Integer)

    solution_working = db.Column(db.String(20))

    cmc_applicable = db.Column(db.String(10))

    cmc_due_days = db.Column(db.Integer)

    cmc_due = db.Column(db.String(10))

    next_cmc_renewal_date = db.Column(db.Date)

    cmc_amount = db.Column(db.Numeric(10,2))

    last_service_days = db.Column(db.Integer)

    last_service_date = db.Column(db.Date)

    service_interval_days = db.Column(db.Integer)

    service_due = db.Column(db.String(10))

    filter_clean = db.Column(db.String(20))

    service_for = db.Column(db.String(200))

    no_of_filters_replaced = db.Column(db.Integer)

    pre_service_msg = db.Column(db.String(10))

    post_service_msg = db.Column(db.String(10))

    remark = db.Column(db.Text)

    proposal_id = db.Column(
        db.Integer,
        db.ForeignKey('proposals.proposal_id')
    )

    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey('invoices.invoice_id')
   )



class CustomerCareCard(db.Model):

    __tablename__ = 'customer_care_card'

    card_id = db.Column(db.Integer, primary_key=True)

    client_id = db.Column(
        db.Integer,
        db.ForeignKey('client.client_id')
    )
    client = db.relationship(
        'Client',
        backref='services'
    )
    
    service_date = db.Column(db.Date)

    service_of = db.Column(db.String(100))

    no_of_filters = db.Column(db.Integer)

    controller_changed = db.Column(db.String(10))

    fan_changed = db.Column(db.String(10))

    serviced_by = db.Column(db.String(100))

    pre_service_msgd = db.Column(db.String(10))

    post_service_report_sent = db.Column(db.String(10))

    miscellaneous_messages = db.Column(db.Text)

    tips_and_tricks = db.Column(db.Text)

    referrals_program = db.Column(db.String(100))

    news_sent = db.Column(db.String(10))

    communication_date = db.Column(db.Date)

    remark = db.Column(db.Text)

class CompletedTask(db.Model):

    __tablename__ = 'completed_tasks'

    completed_task_id = db.Column(
        db.Integer,
        primary_key=True
    )

    module_type = db.Column(
        db.String(20),
        nullable=False
    )

    record_id = db.Column(
        db.Integer,
        nullable=False
    )

    task_name = db.Column(
        db.String(255)
    )

    completed_by = db.Column(
        db.String(100)
    )

    completed_on = db.Column(
        db.DateTime,
        default=datetime.now
    )

class DeleteRequest(db.Model):

    __tablename__ = 'delete_requests'

    request_id = db.Column(
        db.Integer,
        primary_key=True
    )

    module_type = db.Column(
        db.String(50)
    )

    record_id = db.Column(
        db.Integer
    )

    requested_by = db.Column(
        db.String(100)
    )

    requested_on = db.Column(
        db.DateTime,
        default=datetime.now
    )

    status = db.Column(
        db.String(20),
        default='PENDING'
    )

with app.app_context():

    db.create_all()

@app.route('/')
def root():

    return redirect(url_for('login'))

@app.route('/login',
           methods=['GET','POST'])

def login():

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user and user.is_active == 'YES':

            session['user_id'] = user.user_id

            session['username'] = user.username

            session['role'] = user.role

            return redirect(
                url_for('dashboard')
            )

        return "Invalid Username or Password"

    return render_template(
        'login.html'
    )

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:

        return redirect(
            url_for('login')
        )

    today = date.today()

    lead_followups = Lead.query.filter(
        Lead.next_to_call <= today
    ).all()

    meeting_followups = Meeting.query.filter(
        Meeting.date_to_call_next <= today
    ).all()

    proposal_followups = Proposal.query.filter(
        Proposal.next_to_call <= today
    ).all()

    service_due_clients = []

    for client in Client.query.all():

        if client.last_service_date:

            due_date = (
                client.last_service_date
                + timedelta(
                    days=client.service_interval_days
                )
            )

        elif client.activation_date:

            due_date = (
                client.activation_date
                + timedelta(
                    days=client.service_interval_days
                )
            )

        else:

            continue

        if due_date <= today:

            service_due_clients.append(
                client
            )

    service_due_clients.sort(

        key=lambda x:
        x.last_service_date
        or x.activation_date
        or date.min
    )

    cmc_due_clients = Client.query.filter(
        Client.cmc_applicable == 'YES',
        Client.next_cmc_renewal_date != None,
        Client.next_cmc_renewal_date <= today
    ).order_by(
        Client.next_cmc_renewal_date.asc()
    ).all()

    followups_due = (
        len(lead_followups)
        + len(meeting_followups)
        + len(proposal_followups)
    )
    services_due = len(
        service_due_clients
    )

    cmc_due = len(
        cmc_due_clients
    )    

    monthly_filters = db.session.query(
        func.sum(
            CustomerCareCard.no_of_filters
        )
    ).filter(
        extract(
            'month',
            CustomerCareCard.service_date
        ) == datetime.now().month,

        extract(
            'year',
            CustomerCareCard.service_date
        ) == datetime.now().year
    ).scalar()

    monthly_filters = monthly_filters or 0

    yearly_filters = db.session.query(
        func.sum(
            CustomerCareCard.no_of_filters
        )
    ).filter(
        extract(
            'year',
            CustomerCareCard.service_date
        ) == datetime.now().year
    ).scalar()

    yearly_filters = yearly_filters or 0

    return render_template(
        'index.html',
        monthly_filters=monthly_filters,
        yearly_filters=yearly_filters,
        lead_followups=lead_followups,
        meeting_followups=meeting_followups,
        proposal_followups=proposal_followups,
        service_due_clients=service_due_clients,
        cmc_due_clients=cmc_due_clients,
        followups_due=followups_due,
        services_due=services_due,
        cmc_due=cmc_due      
    )

@app.route('/manage-users')
def manage_users():
    if session.get('role') != 'ADMIN':

        return redirect(
            url_for('dashboard')
        )
    if session.get('role') != 'ADMIN':

        return redirect(
            url_for('dashboard')
        )

    users = User.query.order_by(
        User.user_id.asc()
    ).all()

    return render_template(

        'manage_users.html',

        users=users

    )

@app.route(
    '/add-user',
    methods=['GET', 'POST']
)
def add_user():
    if session.get('role') != 'ADMIN':

        return redirect(
            url_for('dashboard')
        )
    if request.method == 'POST':

        username = request.form.get(
            'username'
        ).strip()

        existing_user = User.query.filter_by(

            username=username

        ).first()

        if existing_user:

            flash(
                'Username already exists.'
            )

            return redirect(
                url_for(
                    'add_user'
                )
            )
        user = User(

            username=username,

            password=request.form.get(
                'password'
            ),

            role=request.form.get(
                'role'
            ),

            full_name=request.form.get(
                'full_name'
            ),

            email=request.form.get(
                'email'
            ),

            is_active='YES'

        )

        db.session.add(
            user
        )

        db.session.commit()

        return redirect(
            url_for(
                'manage_users'
            )
        )

    return render_template(
        'add_user.html'
    )

@app.route(
    '/edit-user/<int:user_id>',
    methods=['GET', 'POST']
)
def edit_user(user_id):
    if session.get('role') != 'ADMIN':

        return redirect(
            url_for('dashboard')
        )
    if session.get('role') != 'ADMIN':

        return redirect(
            url_for('dashboard')
        )

    user = User.query.get_or_404(
        user_id
    )

    if request.method == 'POST':

        user.full_name = request.form.get(
            'full_name'
        )

        user.email = request.form.get(
            'email'
        )

        user.role = request.form.get(
            'role'
        )

        user.is_active = request.form.get(
            'is_active'
        )

        db.session.commit()

        return redirect(
            url_for(
                'manage_users'
            )
        )

    return render_template(

        'edit_user.html',

        user=user

    )

@app.route('/add-lead',
           methods=['GET','POST'])
def add_lead():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )

    if request.method == 'POST':
        name = request.form['name']
        reference = request.form['reference']
        location = request.form['location']
        phone = request.form['phone']
        responses = request.form['responses']
        date_of_1st_followup = datetime.strptime( request.form['date_of_1st_followup'], '%Y-%m-%d' ).date()
        next_to_call = datetime.strptime( request.form['next_to_call'], '%Y-%m-%d' ).date()
        recent = request.form['recent']
        lead = Lead(
            name=name,
            reference=reference,
            location=location,
            phone=phone,
            responses=responses,
            date_of_1st_followup=date_of_1st_followup,
            next_to_call=next_to_call,
            recent=recent
        )
        db.session.add(lead)
        db.session.commit()
        return redirect(url_for('add_lead'))
    search = request.args.get(
        'search'
    )

    if search:

        all_leads = Lead.query.filter(
            or_(
                Lead.name.ilike(
                    f'%{search}%'
                ),
                Lead.reference.ilike(
                    f'%{search}%'
                ),
                Lead.location.ilike(
                    f'%{search}%'
                ),
                Lead.phone.ilike(
                    f'%{search}%'
                ),
                Lead.responses.ilike(
                    f'%{search}%'
                ),
                Lead.recent.ilike(
                    f'%{search}%'
                )
            )
        ).all()

    else:

        all_leads = Lead.query.all()
    return render_template('add_lead.html', leads=all_leads)

@app.route('/lead/<int:lead_id>')
def lead_details(lead_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    lead = Lead.query.get_or_404(
        lead_id
    )

    return render_template(
        'lead_details.html',
        lead=lead
    )

@app.route(
    '/edit-lead/<int:lead_id>',
    methods=['GET','POST']
)
def edit_lead(lead_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    lead = Lead.query.get_or_404(
        lead_id
    )

    if request.method == 'POST':

        lead.name = request.form.get(
            'name'
        )

        lead.reference = request.form.get(
            'reference'
        )

        lead.location = request.form.get(
            'location'
        )

        lead.phone = request.form.get(
            'phone'
        )

        lead.responses = request.form.get(
            'responses'
        )

        lead.recent = request.form.get(
            'recent'
        )

        lead.date_of_1st_followup = (
            datetime.strptime(
                request.form.get(
                    'date_of_1st_followup'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'date_of_1st_followup'
            )
            else None
        )

        lead.next_to_call = (
            datetime.strptime(
                request.form.get(
                    'next_to_call'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'next_to_call'
            )
            else None
        )

        db.session.commit()

        return redirect(
            url_for(
                'add_lead'
            )
        )

    return render_template(
        'edit_lead.html',
        lead=lead
    )

@app.route('/delete-lead/<int:lead_id>')
def delete_lead(lead_id):
    if session.get('role') != 'ADMIN':

        flash(
            'Only Admin can delete records.'
        )

        return redirect(
            url_for('add_lead')
        )
    lead = Lead.query.get_or_404(
        lead_id
    )

    try:

        db.session.delete(
            lead
        )

        db.session.commit()

    except:

        db.session.rollback()

        flash(
            'Cannot delete lead because it is linked to other records.'
        )

    return redirect(
        url_for(
            'add_lead'
        )
    )

@app.route('/add-meeting',
           methods=['GET','POST'])
def add_meeting():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )

    if request.method == 'POST':
        
        meeting_fixed_by = request.form.get('meeting_fixed_by')
        source = request.form.get('source')
        name = request.form.get('name')
        reference = request.form.get('reference')
        firm_name = request.form.get('firm_name')
        designation = request.form.get('designation')
        address = request.form.get('address')
        state = request.form.get('state')
        contact_no = request.form.get('contact_no')
        email = request.form.get('email')
        company_info_shared = request.form.get('company_info_shared')
        meeting_fixed = request.form.get('meeting_fixed')
        date_of_meeting = request.form.get('date_of_meeting')
        if date_of_meeting:
            date_of_meeting = datetime.strptime( date_of_meeting, '%Y-%m-%d' ).date()
        else:
            date_of_meeting = None
        mode_of_meeting = request.form.get('mode_of_meeting')
        meeting_status = request.form.get('meeting_status')
        meeting_conducted_by = request.form.get('meeting_conducted_by')
        floor_plan_shared = request.form.get('floor_plan_shared')
        site_visit = request.form.get('site_visit')
        post_meeting_mail = request.form.get('post_meeting_mail')
        date_of_last_followup = request.form.get('date_of_last_followup')
        if date_of_last_followup:
            date_of_last_followup = datetime.strptime( date_of_last_followup, '%Y-%m-%d' ).date()
        else:
            date_of_last_followup = None
        date_to_call_next = request.form.get('date_to_call_next')
        if date_to_call_next:
            date_to_call_next = datetime.strptime( date_to_call_next, '%Y-%m-%d' ).date()
        else:
            date_to_call_next = None
        final_remarks = request.form.get('final_remarks')
        reschedule_date_input = request.form.get('reschedule_date')
        if reschedule_date_input:
            reschedule_date = datetime.strptime( reschedule_date_input, '%Y-%m-%d' ).date()
        else:
            reschedule_date = None
        reason_for_reschedule = request.form.get('reason_for_reschedule')
        remarks = request.form.get('remarks')
        lead_id = request.form.get('lead_id')
        meeting = Meeting(
            meeting_fixed_by=meeting_fixed_by,
            source=source,
            name=name,
            reference=reference,
            firm_name=firm_name,
            designation=designation,
            address=address,
            state=state,
            contact_no=contact_no,
            email=email,
            company_info_shared=company_info_shared,
            meeting_fixed=meeting_fixed,
            date_of_meeting=date_of_meeting,
            mode_of_meeting=mode_of_meeting,
            meeting_status=meeting_status,
            meeting_conducted_by=meeting_conducted_by,
            floor_plan_shared=floor_plan_shared,
            site_visit=site_visit,
            post_meeting_mail=post_meeting_mail,
            date_of_last_followup=date_of_last_followup,
            date_to_call_next=date_to_call_next,
            final_remarks=final_remarks,
            reschedule_date=reschedule_date,
            reason_for_reschedule=reason_for_reschedule,
            remarks=remarks,
            lead_id=lead_id
        )
        db.session.add(meeting)
        db.session.commit()
        return redirect(url_for('add_meeting'))
    search=request.args.get(
        'search'
    )
    if search:
        all_meetings=Meeting.query.filter(
            or_(
                Meeting.meeting_fixed_by.ilike(
                    f'%{search}%'
                ),
                Meeting.source.ilike(
                    f'%{search}%'
                ),
                Meeting.name.ilike(
                    f'%{search}%'
                ),
                Meeting.reference.ilike(
                    f'%{search}%'
                ),
                Meeting.firm_name.ilike(
                    f'%{search}%'
                ),
                Meeting.designation.ilike(
                    f'%{search}%'
                ),
                Meeting.address.ilike(
                    f'%{search}%'
                ),
                Meeting.state.ilike(
                    f'%{search}%'
                ),
                Meeting.contact_no.ilike(
                    f'%{search}%'
                ),
                Meeting.email.ilike(
                    f'%{search}%'
                ),
                Meeting.mode_of_meeting.ilike(
                    f'%{search}%'
                ),
                Meeting.meeting_status.ilike(
                    f'%{search}%'
                ),
                Meeting.meeting_conducted_by.ilike(
                    f'%{search}%'
                ),
                Meeting.final_remarks.ilike(
                    f'%{search}%'
                ),
                Meeting.reason_for_reschedule.ilike(
                    f'%{search}%'
                ),
                Meeting.remarks.ilike(
                    f'%{search}%'
                )
            )
        ).all()
    else:
        all_meetings=Meeting.query.all()
    all_leads = Lead.query.all()
    return render_template('add_meeting.html', meetings=all_meetings, leads=all_leads)

@app.route('/meeting/<int:meeting_id>')
def meeting_details(meeting_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    meeting = Meeting.query.get_or_404(
        meeting_id
    )

    return render_template(
        'meeting_details.html',
        meeting=meeting
    )

@app.route(
    '/edit-meeting/<int:meeting_id>',
    methods=['GET', 'POST']
)
def edit_meeting(meeting_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    meeting = Meeting.query.get_or_404(
        meeting_id
    )

    if request.method == 'POST':

        meeting.meeting_fixed_by = request.form.get(
            'meeting_fixed_by'
        )

        meeting.source = request.form.get(
            'source'
        )

        meeting.name = request.form.get(
            'name'
        )

        meeting.reference = request.form.get(
            'reference'
        )

        meeting.firm_name = request.form.get(
            'firm_name'
        )

        meeting.designation = request.form.get(
            'designation'
        )

        meeting.address = request.form.get(
            'address'
        )

        meeting.state = request.form.get(
            'state'
        )

        meeting.contact_no = request.form.get(
            'contact_no'
        )

        meeting.email = request.form.get(
            'email'
        )

        meeting.company_info_shared = request.form.get(
            'company_info_shared'
        )

        meeting.meeting_fixed = request.form.get(
            'meeting_fixed'
        )

        meeting.mode_of_meeting = request.form.get(
            'mode_of_meeting'
        )

        meeting.meeting_status = request.form.get(
            'meeting_status'
        )

        meeting.meeting_conducted_by = request.form.get(
            'meeting_conducted_by'
        )

        meeting.floor_plan_shared = request.form.get(
            'floor_plan_shared'
        )

        meeting.site_visit = request.form.get(
            'site_visit'
        )

        meeting.post_meeting_mail = request.form.get(
            'post_meeting_mail'
        )

        meeting.final_remarks = request.form.get(
            'final_remarks'
        )

        meeting.reason_for_reschedule = request.form.get(
            'reason_for_reschedule'
        )

        meeting.remarks = request.form.get(
            'remarks'
        )

        meeting.date_of_meeting = (
            datetime.strptime(
                request.form.get(
                    'date_of_meeting'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'date_of_meeting'
            )
            else None
        )

        meeting.date_of_last_followup = (
            datetime.strptime(
                request.form.get(
                    'date_of_last_followup'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'date_of_last_followup'
            )
            else None
        )

        meeting.date_to_call_next = (
            datetime.strptime(
                request.form.get(
                    'date_to_call_next'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'date_to_call_next'
            )
            else None
        )

        meeting.reschedule_date = (
            datetime.strptime(
                request.form.get(
                    'reschedule_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'reschedule_date'
            )
            else None
        )

        db.session.commit()

        return redirect(
            url_for(
                'add_meeting'
            )
        )
    all_leads = Lead.query.all()

    return render_template(
        'edit_meeting.html',
        meeting=meeting,
        leads=all_leads
    )

@app.route(
    '/delete-meeting/<int:meeting_id>'
)
def delete_meeting(meeting_id):
    if session.get('role') != 'ADMIN':

        flash(
            'Only Admin can delete records.'
        )

        return redirect(
            url_for('add_meeting')
        )
    meeting = Meeting.query.get_or_404(
        meeting_id
    )

    try:

        db.session.delete(
            meeting
        )

        db.session.commit()

    except:

        db.session.rollback()

        flash(
            'Cannot delete this meeting because it is linked to a proposal.'
        )

    return redirect(
        url_for(
            'add_meeting'
        )
    )

@app.route('/add-visit',
           methods=['GET','POST'])
def add_visit():
    if not has_access(
        'ADMIN',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    if request.method == 'POST':

        meeting_id = request.form.get(
            'meeting_id'
        )

        state = request.form.get(
            'state'
        )

        region = request.form.get(
            'region'
        )

        abc = request.form.get(
            'abc'
        )

        company_name = request.form.get(
            'company_name'
        )

        person_name = request.form.get(
            'person_name'
        )

        designation = request.form.get(
            'designation'
        )

        contact_no = request.form.get(
            'contact_no'
        )

        address = request.form.get(
            'address'
        )

        brief = request.form.get(
            'brief'
        )

        visit_date = request.form.get(
            'visit_date'
        )

        if visit_date:

            visit_date = datetime.strptime(
                visit_date,
                '%Y-%m-%d'
            ).date()

        else:

            visit_date = None

        leads_generated = request.form.get(
            'leads_generated'
        )

        m2 = request.form.get(
            'm2'
        )

        m3 = request.form.get(
            'm3'
        )

        visit = Visit(

            meeting_id=meeting_id,

            state=state,

            region=region,

            abc=abc,

            company_name=company_name,

            person_name=person_name,

            designation=designation,

            contact_no=contact_no,

            address=address,

            brief=brief,

            visit_date=visit_date,

            leads_generated=leads_generated,

            m2=m2,

            m3=m3

        )

        db.session.add(
            visit
        )

        db.session.commit()

        return redirect(
            url_for(
                'add_visit'
            )
        )

    search=request.args.get(
        'search'
    )
    if search:
        all_visits=Visit.query.filter(
            or_(
                Visit.state.ilike(
                    f'%{search}%'
                ),
                Visit.region.ilike(
                    f'%{search}%'
                ),
                Visit.abc.ilike(
                    f'%{search}%'
                ),
                Visit.company_name.ilike(
                    f'%{search}%'
                ),
                Visit.person_name.ilike(
                    f'%{search}%'
                ),
                Visit.designation.ilike(
                    f'%{search}%'
                ),
                Visit.contact_no.ilike(
                    f'%{search}%'
                ),
                Visit.address.ilike(
                    f'%{search}%'
                ),
                Visit.brief.ilike(
                    f'%{search}%'
                )
            )
        ).all()
    else:
        all_visits=Visit.query.all()

    all_meetings = Meeting.query.all()

    return render_template(
        'add_visit.html',
        visits=all_visits,
        meetings=all_meetings
    )

@app.route('/visit/<int:visit_id>')
def visit_details(visit_id):
    if not has_access(
        'ADMIN',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    visit = Visit.query.get_or_404(
        visit_id
    )

    return render_template(
        'visit_details.html',
        visit=visit
    )

@app.route(
    '/edit-visit/<int:visit_id>',
    methods=['GET', 'POST']
)
def edit_visit(visit_id):
    if not has_access(
        'ADMIN',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    visit = Visit.query.get_or_404(
        visit_id
    )

    all_meetings = Meeting.query.all()

    if request.method == 'POST':

        visit.meeting_id = request.form.get(
            'meeting_id'
        )

        visit.state = request.form.get(
            'state'
        )

        visit.region = request.form.get(
            'region'
        )

        visit.abc = request.form.get(
            'abc'
        )

        visit.company_name = request.form.get(
            'company_name'
        )

        visit.person_name = request.form.get(
            'person_name'
        )

        visit.designation = request.form.get(
            'designation'
        )

        visit.contact_no = request.form.get(
            'contact_no'
        )

        visit.address = request.form.get(
            'address'
        )

        visit.brief = request.form.get(
            'brief'
        )

        visit.leads_generated = request.form.get(
            'leads_generated'
        )

        visit.m2 = request.form.get(
            'm2'
        )

        visit.m3 = request.form.get(
            'm3'
        )

        visit.visit_date = (
            datetime.strptime(
                request.form.get(
                    'visit_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'visit_date'
            )
            else None
        )

        db.session.commit()

        return redirect(
            url_for(
                'add_visit'
            )
        )

    return render_template(
        'edit_visit.html',
        visit=visit,
        meetings=all_meetings
    )

@app.route(
    '/delete-visit/<int:visit_id>'
)
def delete_visit(visit_id):
    if session.get('role') != 'ADMIN':

        flash(
            'Only Admin can delete records.'
        )

        return redirect(
            url_for('add_visit')
        )
    visit = Visit.query.get_or_404(
        visit_id
    )

    try:

        db.session.delete(
            visit
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            'Cannot delete this visit because it is linked to other records.'
        )

    return redirect(
        url_for(
            'add_visit'
        )
    )

@app.route('/add-drawing',
           methods=['GET','POST'])
def add_drawing():
    if not has_access(
        'ADMIN',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    if request.method == 'POST':

        visit_id = request.form.get(
            'visit_id'
        )

        name = request.form.get(
            'name'
        )

        address = request.form.get(
            'address'
        )

        iterations = request.form.get(
            'iterations'
        )

        moca = request.form.get(
            'moca'
        )

        drawing_file = request.files.get(
            'drawing_pdf'
        )

        drawing_pdf_path = None

        if drawing_file and drawing_file.filename:

            filename = secure_filename(
                drawing_file.filename
            )

            drawing_pdf_path = (
                'drawings/' + filename
            )

            drawing_file.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    drawing_pdf_path
                )
            )

        drawing = Drawing(

            visit_id=visit_id,

            name=name,

            address=address,

            iterations=iterations,

            moca=moca,

            drawing_pdf=drawing_pdf_path

        )

        db.session.add(
            drawing
        )

        db.session.commit()

        return redirect(
            url_for(
                'add_drawing'
            )
        )

    search=request.args.get(
        'search'
    )
    if search:
        all_drawings=Drawing.query.filter(
            or_(
                Drawing.name.ilike(
                    f'%{search}%'
                ),
                Drawing.address.ilike(
                    f'%{search}%'
                ),
                Drawing.moca.ilike(
                    f'%{search}%'
                )
            )
        ).all()
    else:
        all_drawings=Drawing.query.all()

    all_visits = Visit.query.all()

    return render_template(
        'add_drawing.html',
        drawings=all_drawings,
        visits=all_visits
    )

@app.route('/drawing/<int:drawing_id>')
def drawing_details(drawing_id):
    if not has_access(
        'ADMIN',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    drawing = Drawing.query.get_or_404(
        drawing_id
    )

    return render_template(
        'drawing_details.html',
        drawing=drawing
    )

@app.route(
    '/edit-drawing/<int:drawing_id>',
    methods=['GET', 'POST']
)
def edit_drawing(drawing_id):
    if not has_access(
        'ADMIN',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    drawing = Drawing.query.get_or_404(
        drawing_id
    )

    drawing_pdf=drawing.drawing_pdf

    all_visits = Visit.query.all()

    if request.method == 'POST':

        drawing.visit_id = (
            int(
                request.form.get(
                    'visit_id'
                )
            )
            if request.form.get(
                'visit_id'
            )
            else None
        )

        drawing.name = request.form.get(
            'name'
        )

        drawing.address = request.form.get(
            'address'
        )

        drawing.iterations = (
            int(
                request.form.get(
                    'iterations'
                )
            )
            if request.form.get(
                'iterations'
            )
            else None
        )

        drawing.moca = request.form.get(
            'moca'
        )

        if 'drawing_pdf' in request.files:

            file = request.files[
                'drawing_pdf'
            ]

            if file.filename != '':

                filename = secure_filename(
                    file.filename
                )

                file.save(
                    os.path.join(
                        app.config[
                            'UPLOAD_FOLDER'
                        ],
                        'drawings',
                        filename
                    )
                )

                drawing_pdf = (
                    'drawings/' +
                filename
                )

        drawing.drawing_pdf = drawing_pdf

        db.session.commit()

        return redirect(
            url_for(
                'add_drawing'
            )
        )

    return render_template(
        'edit_drawing.html',
        drawing=drawing,
        visits=all_visits
    )

@app.route(
    '/delete-drawing/<int:drawing_id>'
)
def delete_drawing(drawing_id):
    if session.get('role') != 'ADMIN':

        flash(
            'Only Admin can delete records.'
        )

        return redirect(
            url_for('add_drawing')
        )
    drawing = Drawing.query.get_or_404(
        drawing_id
    )

    try:

        db.session.delete(
            drawing
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            'Cannot delete this drawing because it is linked to other records.'
        )

    return redirect(
        url_for(
            'add_drawing'
        )
    )

@app.route('/add-proposal',
            methods=['GET', 'POST'])
def add_proposal():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )

    if request.method == 'POST':

        meeting_id = request.form.get('meeting_id')

        drawing_id = request.form.get('drawing_id')

        reference_no = request.form.get('reference_no')

        name = request.form.get('name')

        phone_no_client = request.form.get('phone_no_client')

        source = request.form.get('source')

        type = request.form.get('type')

        reference_source_details = request.form.get('reference_source_details')

        phone_no_source = request.form.get('phone_no_source')

        contact_person = request.form.get('contact_person')

        phone_no_contact_person = request.form.get('phone_no_contact_person')

        email = request.form.get('email')

        site_address = request.form.get('site_address')

        state = request.form.get('state')

        total_area_sqft = request.form.get('total_area_sqft')

        no_of_mvd_units = request.form.get('no_of_mvd_units')
        no_of_mvd_max_units = request.form.get('no_of_mvd_max_units')

        total_no_of_units = request.form.get('total_no_of_units')

        type_of_units = request.form.get('type_of_units')

        product = request.form.get('product')

        cost_total_per_unit = request.form.get('cost_total_per_unit')

        no_of_monitors = request.form.get('no_of_monitors')

        cmc = request.form.get('cmc')

        per_unit_cost = request.form.get('per_unit_cost')

        per_unit_cost_max_unit = request.form.get('per_unit_cost_max_unit')

        cmc_cost = request.form.get('cmc_cost')

        monitor_cost = request.form.get('monitor_cost')

        installation_cost = request.form.get('installation_cost')
    
        total_amount = request.form.get('total_amount')

        cmc_starting_period = request.form.get('cmc_starting_period')

        discount = request.form.get('discount')

        final_amount = request.form.get('final_amount')

        proposal_prepared_by = request.form.get('proposal_prepared_by')

        proposal_shared_by = request.form.get('proposal_shared_by')

        status = request.form.get('status')

        remarks = request.form.get('remarks')

        date_of_proposal_sent = request.form.get('date_of_proposal_sent')
        if date_of_proposal_sent:

            date_of_proposal_sent = datetime.strptime(
                date_of_proposal_sent,
                '%Y-%m-%d'
            ).date()

        else:

            date_of_proposal_sent = None

        date_of_last_followup = request.form.get('date_of_last_followup')

        if date_of_last_followup:

            date_of_last_followup = datetime.strptime(
                date_of_last_followup,
                '%Y-%m-%d'
            ).date()

        else:

            date_of_last_followup = None

        next_to_call = request.form.get('next_to_call')

        if next_to_call:

            next_to_call = datetime.strptime(
                next_to_call,
                '%Y-%m-%d'
            ).date()

        else:

            next_to_call = None

        proposal_pdf = None

        if 'proposal_pdf' in request.files:

            file = request.files[
                'proposal_pdf'
            ]

            if file.filename != '':

                filename = secure_filename(
                    file.filename
                )

                file.save(
                    os.path.join(
                        app.config[
                            'UPLOAD_FOLDER'],
                            'proposals',
                        filename
                    )
                )

                proposal_pdf = (
                    'proposals/' +
                    filename
                )

        proposal = Proposal(

            meeting_id=meeting_id,

            drawing_id=drawing_id,

            reference_no=reference_no,

            name=name,

            phone_no_client=phone_no_client,

            source=source,

            type=type,

            reference_source_details=
                reference_source_details,

            phone_no_source=
                phone_no_source,

            contact_person=
                contact_person,

            phone_no_contact_person=
                phone_no_contact_person,

            email=email,

            site_address=site_address,

            state=state,

            total_area_sqft=
                total_area_sqft,

            type_of_units=
                type_of_units,

            no_of_mvd_units=
                no_of_mvd_units,

            no_of_mvd_max_units=
                no_of_mvd_max_units,

            total_no_of_units=
                total_no_of_units,

            product=product,

            cost_total_per_unit=
                cost_total_per_unit,

            no_of_monitors=
                no_of_monitors,

            cmc=cmc,

            per_unit_cost=
                per_unit_cost,

            per_unit_cost_max_unit=
                per_unit_cost_max_unit,

            cmc_cost=cmc_cost,

            monitor_cost=
                monitor_cost,

            installation_cost=
                installation_cost,

            total_amount=
                total_amount,

            cmc_starting_period=
                cmc_starting_period,

            discount=discount,

            final_amount=
                final_amount,

            date_of_proposal_sent=
                date_of_proposal_sent,

            proposal_prepared_by=
                proposal_prepared_by,

            proposal_shared_by=
                proposal_shared_by,

            status=status,

            date_of_last_followup=
                date_of_last_followup,

            next_to_call=
                next_to_call,

            remarks=remarks,

            proposal_pdf=
                proposal_pdf

        )

        db.session.add(
            proposal
        )  

        db.session.commit()

        return redirect(
            url_for(
                'add_proposal'
            )
        ) 
    search=request.args.get(
        'search'
    )
    if search:
        all_proposals=Proposal.query.filter(
            or_(
                Proposal.reference_no.ilike(
                    f'%{search}%'
                ),
                Proposal.name.ilike(
                    f'%{search}%'
                ),
                Proposal.phone_no_client.ilike(
                    f'%{search}%'
                ),
                Proposal.source.ilike(
                    f'%{search}%'
                ),
                Proposal.type.ilike(
                    f'%{search}%'
                ),
                Proposal.reference_source_details.ilike(
                    f'%{search}%'
                ),
                Proposal.phone_no_source.ilike(
                    f'%{search}%'
                ),
                Proposal.contact_person.ilike(
                    f'%{search}%'
                ),
                Proposal.phone_no_contact_person.ilike(
                    f'%{search}%'
                ),
                Proposal.email.ilike(
                    f'%{search}%'
                ),
                Proposal.site_address.ilike(
                    f'%{search}%'
                ),
                Proposal.state.ilike(
                    f'%{search}%'
                ),
                Proposal.type_of_units.ilike(
                    f'%{search}%'
                ),
                Proposal.product.ilike(
                    f'%{search}%'
                ),
                Proposal.proposal_prepared_by.ilike(
                    f'%{search}%'
                ),
                Proposal.proposal_shared_by.ilike(
                    f'%{search}%'
                ),
                Proposal.status.ilike(
                    f'%{search}%'
                ),
                Proposal.remarks.ilike(
                    f'%{search}%'
                )
            )
        ).all()
    else:
        all_proposals = Proposal.query.all()
    all_meetings = Meeting.query.all()
    all_drawings = Drawing.query.all()
    return render_template(
        'add_proposal.html',
        proposals=all_proposals,
        meetings=all_meetings,
        drawings=all_drawings
    )

@app.route(
    '/edit-proposal/<int:proposal_id>',
    methods=['GET', 'POST']
)
def edit_proposal(proposal_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    proposal = Proposal.query.get_or_404(
        proposal_id
    )

    all_meetings = Meeting.query.all()

    all_drawings = Drawing.query.all()

    if request.method == 'POST':
        proposal.meeting_id = request.form.get(
            'meeting_id'
        )

        proposal.drawing_id = request.form.get(
            'drawing_id'
        )

        proposal.reference_no = request.form.get(
            'reference_no'
        )
        proposal.name = request.form.get(
            'name'
        )
        proposal.phone_no_client = request.form.get(
            'phone_no_client'
        )
        proposal.source = request.form.get(
            'source'
        )
        proposal.type = request.form.get(
            'type'
        )
        proposal.reference_source_details = request.form.get(
            'reference_source_details'
        )
        proposal.phone_no_source = request.form.get(
            'phone_no_source'
        )
        proposal.contact_person = request.form.get(
            'contact_person'
        )
        proposal.phone_no_contact_person = request.form.get(
            'phone_no_contact_person'
        )
        proposal.email = request.form.get(
            'email'
        )
        proposal.site_address = request.form.get(
            'site_address'
        )
        proposal.state = request.form.get(
            'state'
        )
        proposal.total_area_sqft = request.form.get(
            'total_area_sqft'
        )
        proposal.type_of_units = request.form.get(
            'type_of_units'
        )
        proposal.no_of_mvd_units = request.form.get(
            'no_of_mvd_units'
        )
        proposal.no_of_mvd_max_units = request.form.get(
            'no_of_mvd_max_units'
        )
        proposal.total_no_of_units = request.form.get(
            'total_no_of_units'
        )
        proposal.product = request.form.get(
            'product'
        )
        proposal.cost_total_per_unit = request.form.get(
            'cost_total_per_unit'
        )
        proposal.no_of_monitors = request.form.get(
            'no_of_monitors'
        )
        proposal.cmc = request.form.get(
            'cmc'
        )
        proposal.per_unit_cost = request.form.get(
            'per_unit_cost'
        )
        proposal.per_unit_cost_max_unit = request.form.get(
            'per_unit_cost_max_unit'
        )
        proposal.cmc_cost = request.form.get(
            'cmc_cost'
        )
        proposal.monitor_cost = request.form.get(
            'monitor_cost'
        )
        proposal.installation_cost = request.form.get(
            'installation_cost'
        )
        proposal.total_amount = request.form.get(
            'total_amount'
        )
        proposal.cmc_starting_period = request.form.get(
            'cmc_starting_period'
        )
        proposal.discount = request.form.get(
            'discount'
        )
        proposal.final_amount = request.form.get(
            'final_amount'
        )
        proposal.proposal_prepared_by = request.form.get(
            'proposal_prepared_by'
        )
        proposal.proposal_shared_by = request.form.get(
            'proposal_shared_by'
        )
        proposal.status = request.form.get(
            'status'
        )
        proposal.remarks = request.form.get(
            'remarks'
        )
        date_of_proposal_sent = request.form.get(
            'date_of_proposal_sent'
        )
        if date_of_proposal_sent:

            proposal.date_of_proposal_sent = datetime.strptime(
                date_of_proposal_sent,
                '%Y-%m-%d'
            ).date()

        else:

            proposal.date_of_proposal_sent = None
        date_of_last_followup = request.form.get(
            'date_of_last_followup'
        )
        if date_of_last_followup:
            proposal.date_of_last_followup = datetime.strptime(
                date_of_last_followup,
                '%Y-%m-%d'
            ).date()

        else:
            proposal.date_of_last_followup = None
        next_to_call = request.form.get(
            'next_to_call'
        )
        if next_to_call:
            proposal.next_to_call = datetime.strptime(
                next_to_call,
                '%Y-%m-%d'
            ).date()
        else:
            proposal.next_to_call = None
        proposal_pdf = proposal.proposal_pdf
        if 'proposal_pdf' in request.files:
            file = request.files[
                'proposal_pdf'
            ]
            if file.filename != '':
                filename = secure_filename(
                    file.filename
                )
                file.save(
                    os.path.join(
                        app.config[
                            'UPLOAD_FOLDER'],
                            'proposals',
                        filename
                    )
                )
                proposal_pdf = (
                    'proposals/' +
                    filename
                )
        proposal.proposal_pdf = proposal_pdf
        db.session.commit()
        return redirect(
            url_for(
                'add_proposal'
            )
        )
    
    return render_template(
        'edit_proposal.html',
        proposal=proposal,
        meetings=all_meetings,
        drawings=all_drawings
    )

@app.route(
    '/delete-proposal/<int:proposal_id>'
)
def delete_proposal(proposal_id):
    if session.get('role') != 'ADMIN':

        flash(
            'Only Admin can delete records.'
        )

        return redirect(
            url_for('add_proposal')
        )
    proposal = Proposal.query.get_or_404(
        proposal_id
    )

    try:

        db.session.delete(
            proposal
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            'Cannot delete proposal because it is linked to sales records.'
        )

    return redirect(
        url_for(
            'add_proposal'
        )
    )

@app.route('/proposal/<int:proposal_id>')
def proposal_details(proposal_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    proposal = Proposal.query.get_or_404(
        proposal_id
    )

    return render_template(
        'proposal_details.html',
        proposal=proposal
    )

@app.route('/add-sales',
           methods=['GET','POST'])
def add_sales():
    if not has_access(
        'ADMIN',
        'SALES',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    if request.method == 'POST':

        proposal_id = request.form.get(
            'proposal_id'
        )

        name = request.form.get(
            'name'
        )

        reference_no = request.form.get(
            'reference_no'
        )

        source = request.form.get(
            'source'
        )

        address = request.form.get(
            'address'
        )

        contact_no = request.form.get(
            'contact_no'
        )

        email_id = request.form.get(
            'email_id'
        )

        project_stage = request.form.get(
            'project_stage'
        )

        moc = request.form.get(
            'moc'
        )

        next_action = request.form.get(
            'next_action'
        )

        sales_person = request.form.get(
            'sales_person'
        )

        sales = SalesPipeline(
            proposal_id=proposal_id,

            name=name,

            reference_no=reference_no,

            source=source,

            address=address,

            contact_no=contact_no,

            email_id=email_id,

            project_stage=project_stage,

            moc=moc,

            next_action=next_action,

            sales_person=sales_person,

            project_type=request.form.get('project_type'),

            category=request.form.get('category'),

            site_incharge=request.form.get('site_incharge'),

            site_incharge_contact=request.form.get('site_incharge_contact'),

            first_contact=datetime.strptime(request.form.get('first_contact'), '%Y-%m-%d').date() if request.form.get('first_contact') else None,

            last_contact=datetime.strptime(request.form.get('last_contact'), '%Y-%m-%d').date() if request.form.get('last_contact') else None,

            followup_date=datetime.strptime(request.form.get('followup_date'), '%Y-%m-%d').date() if request.form.get('followup_date') else None,
            
            no_of_site_visits=request.form.get('no_of_site_visits'),

            area_covered=request.form.get('area_covered'),

            total_units=request.form.get('total_units'),

            price_of_units=request.form.get('price_of_units'),

            first_year_cmc=request.form.get('first_year_cmc'),

            installation=request.form.get('installation'),

            total_sensor=request.form.get('total_sensor'),

            sensor_cost=request.form.get('sensor_cost'),

            discount=request.form.get('discount'),

            revenue=request.form.get('revenue'),

            amount_received=request.form.get('amount_received'),

            amount_due=request.form.get('amount_due'),

            total_revenue=request.form.get('total_revenue'),

            gst_no=request.form.get('gst_no'),

            cmc_onwards=request.form.get('cmc_onwards'),

            total_cmc=request.form.get('total_cmc')
        )

        db.session.add(
            sales
        )

        db.session.commit()

        return redirect(
            url_for(
                'add_sales'
            )
        )

    search=request.args.get(
        'search'
    )
    if search:
        all_sales=SalesPipeline.query.filter(
            or_(
                SalesPipeline.name.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.reference_no.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.project_stage.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.moc.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.source.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.next_action.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.address.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.contact_no.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.project_type.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.category.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.email_id.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.site_incharge.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.site_incharge_contact.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.gst_no.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.sales_person.ilike(
                    f'%{search}%'
                )
            )
        ).all()
    else:
        all_sales=SalesPipeline.query.all()

    all_proposals = Proposal.query.all()

    return render_template(

        'add_sales.html',

        sales=all_sales,

        proposals=all_proposals

    )

@app.route('/sales/<int:sales_id>')
def sales_details(sales_id):
    if not has_access(
        'ADMIN',
        'SALES',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    sale = SalesPipeline.query.get_or_404(
        sales_id
    )

    return render_template(
        'sales_details.html',
        sale=sale
    )

@app.route(
    '/edit-sales/<int:sales_id>',
    methods=['GET', 'POST']
)
def edit_sales(sales_id):
    if not has_access(
        'ADMIN',
        'SALES',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    sales = SalesPipeline.query.get_or_404(
        sales_id
    )

    all_proposals = Proposal.query.all()

    if request.method == 'POST':

        sales.proposal_id = request.form.get(
            'proposal_id'
        )

        sales.name = request.form.get(
            'name'
        )

        sales.reference_no = request.form.get(
            'reference_no'
        )

        sales.source = request.form.get(
            'source'
        )

        sales.address = request.form.get(
            'address'
        )

        sales.contact_no = request.form.get(
            'contact_no'
        )

        sales.email_id = request.form.get(
            'email_id'
        )

        sales.project_stage = request.form.get(
            'project_stage'
        )

        sales.moc = request.form.get(
            'moc'
        )

        sales.next_action = request.form.get(
            'next_action'
        )

        sales.sales_person = request.form.get(
            'sales_person'
        )

        sales.project_type = request.form.get(
            'project_type'
        )

        sales.category = request.form.get(
            'category'
        )

        sales.site_incharge = request.form.get(
            'site_incharge'
        )

        sales.site_incharge_contact = request.form.get(
            'site_incharge_contact'
        )

        sales.first_contact = (
            datetime.strptime(
                request.form.get(
                    'first_contact'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'first_contact'
            )
            else None
        )

        sales.last_contact = (
            datetime.strptime(
                request.form.get(
                    'last_contact'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'last_contact'
            )
            else None
        )

        sales.followup_date = (
            datetime.strptime(
                request.form.get(
                    'followup_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'followup_date'
            )
            else None
        )

        sales.no_of_site_visits = request.form.get(
            'no_of_site_visits'
        )

        sales.area_covered = request.form.get(
            'area_covered'
        )

        sales.total_units = request.form.get(
            'total_units'
        )

        sales.price_of_units = request.form.get(
            'price_of_units'
        )

        sales.first_year_cmc = request.form.get(
            'first_year_cmc'
        )

        sales.installation = request.form.get(
            'installation'
        )

        sales.total_sensor = request.form.get(
            'total_sensor'
        )

        sales.sensor_cost = request.form.get(
            'sensor_cost'
        )

        sales.discount = request.form.get(
            'discount'
        )

        sales.revenue = request.form.get(
            'revenue'
        )

        sales.amount_received = request.form.get(
            'amount_received'
        )

        sales.amount_due = request.form.get(
            'amount_due'
        )

        sales.total_revenue = request.form.get(
            'total_revenue'
        )

        sales.gst_no = request.form.get(
            'gst_no'
        )

        sales.cmc_onwards = request.form.get(
            'cmc_onwards'
        )

        sales.total_cmc = request.form.get(
            'total_cmc'
        )

        db.session.commit()

        return redirect(
            url_for(
                'add_sales'
            )
        )

    return render_template(
        'edit_sales.html',
        sales=sales,
        proposals=all_proposals
    )

@app.route(
    '/delete-sales/<int:sales_id>'
)
def delete_sales(sales_id):
    if session.get('role') != 'ADMIN':

        flash(
            'Only Admin can delete records.'
        )

        return redirect(
            url_for('add_sales')
        )
    sales = SalesPipeline.query.get_or_404(
        sales_id
    )

    try:

        db.session.delete(
            sales
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            'Cannot delete this sales record because it is linked to invoices.'
        )

    return redirect(
        url_for(
            'add_sales'
        )
    )

@app.route('/add-invoice',
           methods=['GET','POST'])
def add_invoice():
    if not has_access(
        'ADMIN',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    if request.method == 'POST':

        sales_id = request.form.get(
            'sales_id'
        )

        doi_input = request.form.get(
            'doi'
        )

        if doi_input:

            doi = datetime.strptime(
                doi_input,
                '%Y-%m-%d'
            ).date()

        else:

            doi = None

        invoice_no = request.form.get(
            'invoice_no'
        )

        name = request.form.get(
            'name'
        )

        gst_no = request.form.get(
            'gst_no'
        )

        product_sold = request.form.get(
            'product_sold'
        )

        invoice_pdf = request.files.get(
            'invoice_pdf'
        )

        total_units = request.form.get(
            'total_units'
        )

        price_of_units = request.form.get(
            'price_of_units'
        )

        first_year_cmc = request.form.get(
            'first_year_cmc'
        )

        installation = request.form.get(
            'installation'
        )

        total_sensor = request.form.get(
            'total_sensor'
        )

        sensor_cost = request.form.get(
            'sensor_cost'
        )

        revenue = request.form.get(
            'revenue'
        )

        total_revenue = request.form.get(
            'total_revenue'
        )

        pdf_path = None

        if invoice_pdf and invoice_pdf.filename != '':
            filename = secure_filename(
                invoice_pdf.filename
            )

            invoice_pdf.save(

                os.path.join(

                    app.config['UPLOAD_FOLDER'],

                    'invoices',

                    filename

                )

            )

            pdf_path = (
                'invoices/' +
                filename
            )



        invoice = Invoice(

            sales_id=sales_id,

            name=name,

            doi=doi,

            invoice_no=invoice_no,

            gst_no=gst_no,

            product_sold=product_sold,

            total_units=total_units,

            price_of_units=price_of_units,

            first_year_cmc=first_year_cmc,

            installation=installation,

            total_sensor=total_sensor,

            sensor_cost=sensor_cost,

            revenue=revenue,

            total_revenue=total_revenue,

            invoice_pdf=pdf_path

        )

        db.session.add(
            invoice
        )

        db.session.commit()

        return redirect(
            url_for(
                'add_invoice'
            )
        )

    search=request.args.get(
        'search'
    )
    if search:
        all_invoices=Invoice.query.filter(
            or_(
                Invoice.name.ilike(
                    f'%{search}%'
                ),
                Invoice.invoice_no.ilike(
                    f'%{search}%'
                ),
                Invoice.gst_no.ilike(
                    f'%{search}%'
                ),
                Invoice.product_sold.ilike(
                    f'%{search}%'
                )
            )
        ).all()
    else:
        all_invoices=Invoice.query.all()

    all_sales = SalesPipeline.query.all()

    return render_template(

        'add_invoice.html',

        invoices=all_invoices,

        sales=all_sales

    )

@app.route('/invoice/<int:invoice_id>')
def invoice_details(invoice_id):
    if not has_access(
        'ADMIN',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    invoice = Invoice.query.get_or_404(
        invoice_id
    )

    return render_template(
        'invoice_details.html',
        invoice=invoice
    )

@app.route(
    '/edit-invoice/<int:invoice_id>',
    methods=['GET', 'POST']
)
def edit_invoice(invoice_id):
    if not has_access(
        'ADMIN',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    invoice = Invoice.query.get_or_404(
        invoice_id
    )

    all_sales = SalesPipeline.query.all()

    if request.method == 'POST':
        invoice.sales_id = request.form.get(
            'sales_id'
        )

        doi_input = request.form.get(
            'doi'
        )

        if doi_input:

            invoice.doi = datetime.strptime(
                doi_input,
                '%Y-%m-%d'
            ).date()

        else:

            invoice.doi = None

        invoice.invoice_no = request.form.get(
            'invoice_no'
        )

        invoice.name = request.form.get(
            'name'
        )

        invoice.gst_no = request.form.get(
            'gst_no'
        )

        invoice.product_sold = request.form.get(
            'product_sold'
        )

        invoice.total_units = request.form.get(
            'total_units'
        )

        invoice.price_of_units = request.form.get(
            'price_of_units'
        )

        invoice.first_year_cmc = request.form.get(
            'first_year_cmc'
        )
        invoice.installation = request.form.get(
            'installation'
        )
        invoice.total_sensor = request.form.get(
            'total_sensor'
        )
        invoice.sensor_cost = request.form.get(
            'sensor_cost'
        )
        invoice.revenue = request.form.get(
            'revenue'
        )
        invoice.total_revenue = request.form.get(
            'total_revenue'
        )
        pdf_path = invoice.invoice_pdf
        invoice_pdf = request.files.get(
            'invoice_pdf'
        )
        if invoice_pdf and invoice_pdf.filename != '':
            filename = secure_filename(
                invoice_pdf.filename
            )
            invoice_pdf.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    'invoices',
                    filename
                )
            )
            pdf_path = (
                'invoices/' +
                filename
            )
        invoice.invoice_pdf = pdf_path

        db.session.commit()

        return redirect(
            url_for(
                'add_invoice'
            )
        )

    return render_template(
        'edit_invoice.html',
        invoice=invoice,
        sales=all_sales
    )

@app.route(
    '/delete-invoice/<int:invoice_id>'
)
def delete_invoice(invoice_id):
    if session.get('role') != 'ADMIN':

        flash(
            'Only Admin can delete records.'
        )

        return redirect(
            url_for('add_invoice')
        )
    invoice = Invoice.query.get_or_404(
        invoice_id
    )

    try:

        db.session.delete(
            invoice
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            'Cannot delete this invoice because it is linked to other records.'
        )

    return redirect(
        url_for(
            'add_invoice'
        )
    )

@app.route('/add-client',
           methods=['GET', 'POST'])
def add_client():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )    

    if request.method == 'POST':

        proposal_id = request.form.get(
            'proposal_id'
        )

        invoice_id = request.form.get(
            'invoice_id'
        )

        installation_date = (
            datetime.strptime(
                request.form.get(
                    'installation_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'installation_date'
            )
            else None
        )

        activation_date = (
            datetime.strptime(
                request.form.get(
                    'activation_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'activation_date'
            )
            else None
        )

        next_cmc_renewal_date = (
            datetime.strptime(
                request.form.get(
                    'next_cmc_renewal_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'next_cmc_renewal_date'
            )
            else None
        )

        last_service_date = (
            datetime.strptime(
                request.form.get(
                    'last_service_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'last_service_date'
            )
            else None
        )

        today = datetime.today().date()

        # CMC CALCULATIONS

        if installation_date:

            cmc_due_days = (
                today -
                installation_date
            ).days

        else:

            cmc_due_days = 0

        if cmc_due_days >= 345:

            cmc_due = 'YES'

        else:

            cmc_due = 'NO'

        # SERVICE CALCULATIONS
        service_interval_days = request.form.get(
            'service_interval_days'
        )

        if service_interval_days:

            service_interval_days = int(
                service_interval_days
            )

        else:

            service_interval_days = 30

        if last_service_date:

            last_service_days = (
                today -
                last_service_date
            ).days

        else:
            if activation_date:

                last_service_days = (
                    today -
                    activation_date
                ).days
            else:
                last_service_days=0
        
        if last_service_days >= service_interval_days:

            service_due = 'YES'

        else:

            service_due = 'NO'


        client = Client(

            proposal_id=proposal_id,

            invoice_id=invoice_id,

            client_name=request.form.get(
                'client_name'
            ),

            monitor_present=request.form.get(
                'monitor_present'
            ),

            property_type=request.form.get(
                'property_type'
            ),

            address=request.form.get(
                'address'
            ),

            location_link=request.form.get(
                'location_link'
            ),

            nearest_metrostation=request.form.get(
                'nearest_metrostation'
            ),

            mail_id=request.form.get(
                'mail_id'
            ),

            state=request.form.get(
                'state'
            ),

            mobile_no=request.form.get(
                'mobile_no'
            ),

            product=request.form.get(
                'product'
            ),

            installation_date=
            installation_date,

            activation_date=
            activation_date,

            filter_colour=request.form.get(
                'filter_colour'
            ),

            no_of_units_installed=request.form.get(
                'no_of_units_installed'
            ),

            solution_working=request.form.get(
                'solution_working'
            ),

            cmc_applicable=request.form.get(
                'cmc_applicable'
            ),

            cmc_due_days=
            cmc_due_days,

            cmc_due=
            cmc_due,

            next_cmc_renewal_date=
            next_cmc_renewal_date,

            cmc_amount=request.form.get(
                'cmc_amount'
            ),

            last_service_days=
            last_service_days,

            last_service_date=
            last_service_date,

            service_interval_days=
            service_interval_days,

            service_due=
            service_due,

            filter_clean=request.form.get(
                'filter_clean'
            ),

            service_for=request.form.get(
                'service_for'
            ),

            no_of_filters_replaced=request.form.get(
                'no_of_filters_replaced'
            ),

            pre_service_msg=request.form.get(
                'pre_service_msg'
            ),

            post_service_msg=request.form.get(
                'post_service_msg'
            ),

            remark=request.form.get(
                'remark'
            )

        )

        db.session.add(
            client
        )

        db.session.commit()

        return redirect(
            url_for(
                'add_client'
            )
        )

    search=request.args.get(
        'search'
    )
    if search:
        all_clients=Client.query.filter(
            or_(
                Client.client_name.ilike(
                    f'%{search}%'
                ),
                Client.property_type.ilike(
                    f'%{search}%'
                ),
                Client.nearest_metrostation.ilike(
                    f'%{search}%'
                ),
                Client.mail_id.ilike(
                    f'%{search}%'
                ),
                Client.state.ilike(
                    f'%{search}%'
                ),
                Client.mobile_no.ilike(
                    f'%{search}%'
                ),
                Client.product.ilike(
                    f'%{search}%'
                ),
                Client.filter_colour.ilike(
                    f'%{search}%'
                ),
                Client.remark.ilike(
                    f'%{search}%'
                )
            )
        ).all()
    else:
        all_clients=Client.query.all()

    all_proposals = Proposal.query.all()

    all_invoices = Invoice.query.all()

    return render_template(

        'add_client.html',

        clients=all_clients,

        proposals=all_proposals,

        invoices=all_invoices

    )

@app.route('/client/<int:client_id>')
def client_details(client_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    client = Client.query.get_or_404(
        client_id
    )

    return render_template(
        'client_details.html',
        client=client
    )

@app.route(
    '/edit-client/<int:client_id>',
    methods=['GET', 'POST']
)
def edit_client(client_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    client = Client.query.get_or_404(
        client_id
    )

    all_proposals = Proposal.query.all()

    all_invoices = Invoice.query.all()

    if request.method == 'POST':
        client.proposal_id = request.form.get(
            'proposal_id'
        )

        client.invoice_id = request.form.get(
            'invoice_id'
        )
        installation_date = (
            datetime.strptime(
                request.form.get(
                    'installation_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'installation_date'
            )
            else None
        )

        activation_date = (
            datetime.strptime(
                request.form.get(
                    'activation_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'activation_date'
            )
            else None
        )

        next_cmc_renewal_date = (
            datetime.strptime(
                request.form.get(
                    'next_cmc_renewal_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'next_cmc_renewal_date'
            )
            else None
        )

        last_service_date = (
            datetime.strptime(
                request.form.get(
                    'last_service_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'last_service_date'
            )
            else None
        )

        today = datetime.today().date()

        # CMC CALCULATIONS

        if installation_date:

            cmc_due_days = (
                today -
                installation_date
            ).days

        else:

            cmc_due_days = 0

        if cmc_due_days >= 345:

            cmc_due = 'YES'

        else:

            cmc_due = 'NO'

        # SERVICE CALCULATIONS

        service_interval_days = request.form.get(
            'service_interval_days'
        )

        if service_interval_days:

            service_interval_days = int(
                service_interval_days
            )

        else:

            service_interval_days = 30

        if last_service_date:

            last_service_days = (
                today -
                last_service_date
            ).days

        else:
            if activation_date:

                last_service_days = (
                    today -
                    activation_date
                ).days
            else:
                last_service_days=0
        
        if last_service_days >= service_interval_days:

            service_due = 'YES'

        else:

            service_due = 'NO'

        client.client_name=request.form.get(
            'client_name'
        )

        client.monitor_present=request.form.get(
            'monitor_present'
        )

        client.property_type=request.form.get(
            'property_type'
        )

        client.address=request.form.get(
            'address'
        )

        client.location_link=request.form.get(
            'location_link'
        )

        client.nearest_metrostation=request.form.get(
            'nearest_metrostation'
        )

        client.mail_id=request.form.get(
            'mail_id'
        )

        client.state=request.form.get(
            'state'
        )

        client.mobile_no=request.form.get(
            'mobile_no'
        )

        client.product=request.form.get(
            'product'
        )

        client.installation_date= installation_date

        client.activation_date= activation_date

        client.filter_colour=request.form.get(
            'filter_colour'
        )

        client.no_of_units_installed=request.form.get(
            'no_of_units_installed'
        )

        client.solution_working=request.form.get(
            'solution_working'
        )

        client.cmc_applicable=request.form.get(
            'cmc_applicable'
        )

        client.cmc_due_days=cmc_due_days

        client.cmc_due=cmc_due

        client.next_cmc_renewal_date=next_cmc_renewal_date

        client.cmc_amount=request.form.get(
            'cmc_amount'
        )

        client.last_service_days=last_service_days

        client.last_service_date=last_service_date

        client.service_interval_days=service_interval_days

        client.service_due=service_due

        client.filter_clean=request.form.get(
            'filter_clean'
        )

        client.service_for=request.form.get(
            'service_for'
        )

        client.no_of_filters_replaced=request.form.get(
            'no_of_filters_replaced'
        )

        client.pre_service_msg=request.form.get(
            'pre_service_msg'
        )

        client.post_service_msg=request.form.get(
            'post_service_msg'
        )

        client.remark=request.form.get(
            'remark'
        )

        db.session.commit()

        return redirect(
            url_for(
                'add_client'
            )
        )

    return render_template(

        'edit_client.html',

        client=client,

        proposals=all_proposals,

        invoices=all_invoices

    )        

@app.route(
    '/delete-client/<int:client_id>'
)
def delete_client(client_id):
    if session.get('role') != 'ADMIN':

        flash(
            'Only Admin can delete records.'
        )

        return redirect(
            url_for('add_client')
        )
    client = Client.query.get_or_404(
        client_id
    )

    try:

        db.session.delete(
            client
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            'Cannot delete this client because it is linked to service records.'
        )

    return redirect(
        url_for(
            'add_client'
        )
    )

@app.route('/client-services/<int:client_id>')
def client_services(client_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    client = Client.query.get_or_404(
        client_id
    )

    search = request.args.get(
        'search'
    )

    if search:

        services = CustomerCareCard.query.filter(
            CustomerCareCard.client_id == client_id
        ).filter(

            or_(

                CustomerCareCard.service_of.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.serviced_by.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.remark.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.miscellaneous_messages.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.tips_and_tricks.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.referrals_program.ilike(
                    f'%{search}%'
                )

            )

        ).order_by(
            CustomerCareCard.service_date.desc()
        ).all()

    else:

        services = CustomerCareCard.query.filter_by(
            client_id=client_id
        ).order_by(
            CustomerCareCard.service_date.desc()
        ).all()

    service_count = len(
        services
    )

    return render_template(

        'client_services.html',

        client=client,

        services=services,

        service_count=service_count

    )

@app.route(
    '/add-service/<int:client_id>',
    methods=['GET', 'POST']
)
def add_service(client_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    client = Client.query.get_or_404(
        client_id
    )

    if request.method == 'POST':

        service_date = (
            datetime.strptime(
                request.form.get(
                    'service_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'service_date'
            )
            else None
        )

        communication_date = (
            datetime.strptime(
                request.form.get(
                    'communication_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'communication_date'
            )
            else None
        )

        service = CustomerCareCard(

            client_id=client_id,

            service_date=
            service_date,

            service_of=request.form.get(
                'service_of'
            ),

            no_of_filters=request.form.get(
                'no_of_filters'
            ),

            controller_changed=request.form.get(
                'controller_changed'
            ),

            fan_changed=request.form.get(
                'fan_changed'
            ),

            serviced_by=request.form.get(
                'serviced_by'
            ),

            pre_service_msgd=request.form.get(
                'pre_service_msgd'
            ),

            post_service_report_sent=request.form.get(
                'post_service_report_sent'
            ),

            miscellaneous_messages=request.form.get(
                'miscellaneous_messages'
            ),

            tips_and_tricks=request.form.get(
                'tips_and_tricks'
            ),

            referrals_program=request.form.get(
                'referrals_program'
            ),

            news_sent=request.form.get(
                'news_sent'
            ),

            communication_date=
            communication_date,

            remark=request.form.get(
                'remark'
            )

        )

        db.session.add(
            service
        )

        # UPDATE CLIENT STATUS

        if service_date:

            client.last_service_date = (
                service_date
            )

            client.last_service_days = 0

            client.service_due = 'NO'

        db.session.commit()

        return redirect(

            url_for(

                'client_services',

                client_id=client_id

            )

        )

    return render_template(

        'add_service.html',

        client=client

    )

@app.route('/service/<int:card_id>')
def service_details(card_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    service = CustomerCareCard.query.get_or_404(
        card_id
    )

    client = Client.query.get(
        service.client_id
    )

    return render_template(

        'service_details.html',

        service=service,

        client=client

    )

@app.route(
    '/edit-service/<int:card_id>',
    methods=['GET', 'POST']
)
def edit_service(card_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    service = CustomerCareCard.query.get_or_404(
        card_id
    )

    if request.method == 'POST':

        service.service_date = (
            datetime.strptime(
                request.form.get(
                    'service_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'service_date'
            )
            else None
        )

        service.communication_date = (
            datetime.strptime(
                request.form.get(
                    'communication_date'
                ),
                '%Y-%m-%d'
            ).date()
            if request.form.get(
                'communication_date'
            )
            else None
        )

        service.service_of = request.form.get(
            'service_of'
        )

        service.no_of_filters = request.form.get(
            'no_of_filters'
        )

        service.controller_changed = request.form.get(
            'controller_changed'
        )

        service.fan_changed = request.form.get(
            'fan_changed'
        )

        service.serviced_by = request.form.get(
            'serviced_by'
        )

        service.pre_service_msgd = request.form.get(
            'pre_service_msgd'
        )

        service.post_service_report_sent = request.form.get(
            'post_service_report_sent'
        )

        service.miscellaneous_messages = request.form.get(
            'miscellaneous_messages'
        )

        service.tips_and_tricks = request.form.get(
            'tips_and_tricks'
        )

        service.referrals_program = request.form.get(
            'referrals_program'
        )

        service.news_sent = request.form.get(
            'news_sent'
        )

        service.remark = request.form.get(
            'remark'
        )

        client = Client.query.get(
            service.client_id
        )

        latest_service = CustomerCareCard.query.filter_by(
            client_id=service.client_id
        ).order_by(
            CustomerCareCard.service_date.desc()
        ).first()

        if latest_service:

            client.last_service_date = (
                latest_service.service_date
            )

            client.last_service_days = 0

            client.service_due = 'NO'

        else:

            client.last_service_date=None

            client.last_service_days=0

        db.session.commit()

        return redirect(
            url_for(
                'client_services',
                client_id=service.client_id
            )
        )
    client= Client.query.get(
        service.client_id
    )

    return render_template(
        'edit_service.html',
        service=service,
        client=client
    )

@app.route(
    '/delete-service/<int:card_id>'
)
def delete_service(card_id):
    if session.get('role') != 'ADMIN':

        flash(
            'Only Admin can delete records.'
        )

        return redirect(
            url_for('client_services')
        )
    service = CustomerCareCard.query.get_or_404(
        card_id
    )

    client_id = service.client_id

    db.session.delete(
        service
    )

    db.session.commit()

    client = Client.query.get(
        client_id
    )

    latest_service = CustomerCareCard.query.filter_by(
        client_id=client_id
    ).order_by(
        CustomerCareCard.service_date.desc()
    ).first()

    if latest_service:

        client.last_service_date = (
            latest_service.service_date
        )

        client.last_service_days = 0

        client.service_due = 'NO'

    else:

        client.last_service_date = None

        client.last_service_days = 0

        client.service_due = 'YES'

    db.session.commit()

    return redirect(
        url_for(
            'client_services',
            client_id=client_id
        )
    )

@app.route('/global-search')
def global_search():

    search = request.args.get(
        'search'
    )

    leads = []
    meetings = []
    visits = []
    drawings = []
    proposals = []
    sales = []
    invoices = []
    clients = []
    services = []

    if search:

        leads = Lead.query.filter(
            or_(
                Lead.name.ilike(
                    f'%{search}%'
                ),
                Lead.reference.ilike(
                    f'%{search}%'
                ),
                Lead.location.ilike(
                    f'%{search}%'
                ),
                Lead.phone.ilike(
                    f'%{search}%'
                ),
                Lead.responses.ilike(
                    f'%{search}%'
                ),
                Lead.recent.ilike(
                    f'%{search}%'
                )
            )
        ).all()

        meetings = Meeting.query.filter(
            or_(
                Meeting.meeting_fixed_by.ilike(
                    f'%{search}%'
                ),
                Meeting.source.ilike(
                    f'%{search}%'
                ),
                Meeting.name.ilike(
                    f'%{search}%'
                ),
                Meeting.reference.ilike(
                    f'%{search}%'
                ),
                Meeting.firm_name.ilike(
                    f'%{search}%'
                ),
                Meeting.designation.ilike(
                    f'%{search}%'
                ),
                Meeting.address.ilike(
                    f'%{search}%'
                ),
                Meeting.state.ilike(
                    f'%{search}%'
                ),
                Meeting.contact_no.ilike(
                    f'%{search}%'
                ),
                Meeting.email.ilike(
                    f'%{search}%'
                ),
                Meeting.mode_of_meeting.ilike(
                    f'%{search}%'
                ),
                Meeting.meeting_status.ilike(
                    f'%{search}%'
                ),
                Meeting.meeting_conducted_by.ilike(
                    f'%{search}%'
                ),
                Meeting.final_remarks.ilike(
                    f'%{search}%'
                ),
                Meeting.reason_for_reschedule.ilike(
                    f'%{search}%'
                ),
                Meeting.remarks.ilike(
                    f'%{search}%'
                )
            )
        ).all()

        visits=Visit.query.filter(
            or_(
                Visit.state.ilike(
                    f'%{search}%'
                ),
                Visit.region.ilike(
                    f'%{search}%'
                ),
                Visit.abc.ilike(
                    f'%{search}%'
                ),
                Visit.company_name.ilike(
                    f'%{search}%'
                ),
                Visit.person_name.ilike(
                    f'%{search}%'
                ),
                Visit.designation.ilike(
                    f'%{search}%'
                ),
                Visit.contact_no.ilike(
                    f'%{search}%'
                ),
                Visit.address.ilike(
                    f'%{search}%'
                ),
                Visit.brief.ilike(
                    f'%{search}%'
                )
            )
        ).all()        

        drawings=Drawing.query.filter(
            or_(
                Drawing.name.ilike(
                    f'%{search}%'
                ),
                Drawing.address.ilike(
                    f'%{search}%'
                ),
                Drawing.moca.ilike(
                    f'%{search}%'
                )
            )
        ).all()

        proposals=Proposal.query.filter(
            or_(
                Proposal.reference_no.ilike(
                    f'%{search}%'
                ),
                Proposal.name.ilike(
                    f'%{search}%'
                ),
                Proposal.phone_no_client.ilike(
                    f'%{search}%'
                ),
                Proposal.source.ilike(
                    f'%{search}%'
                ),
                Proposal.type.ilike(
                    f'%{search}%'
                ),
                Proposal.reference_source_details.ilike(
                    f'%{search}%'
                ),
                Proposal.phone_no_source.ilike(
                    f'%{search}%'
                ),
                Proposal.contact_person.ilike(
                    f'%{search}%'
                ),
                Proposal.phone_no_contact_person.ilike(
                    f'%{search}%'
                ),
                Proposal.email.ilike(
                    f'%{search}%'
                ),
                Proposal.site_address.ilike(
                    f'%{search}%'
                ),
                Proposal.state.ilike(
                    f'%{search}%'
                ),
                Proposal.type_of_units.ilike(
                    f'%{search}%'
                ),
                Proposal.product.ilike(
                    f'%{search}%'
                ),
                Proposal.proposal_prepared_by.ilike(
                    f'%{search}%'
                ),
                Proposal.proposal_shared_by.ilike(
                    f'%{search}%'
                ),
                Proposal.status.ilike(
                    f'%{search}%'
                ),
                Proposal.remarks.ilike(
                    f'%{search}%'
                )
            )
        ).all()

        sales=SalesPipeline.query.filter(
            or_(
                SalesPipeline.name.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.reference_no.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.project_stage.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.moc.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.source.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.next_action.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.address.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.contact_no.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.project_type.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.category.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.email_id.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.site_incharge.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.site_incharge_contact.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.gst_no.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.sales_person.ilike(
                    f'%{search}%'
                )
            )
        ).all()

        invoices=Invoice.query.filter(
            or_(
                Invoice.name.ilike(
                    f'%{search}%'
                ),
                Invoice.invoice_no.ilike(
                    f'%{search}%'
                ),
                Invoice.gst_no.ilike(
                    f'%{search}%'
                ),
                Invoice.product_sold.ilike(
                    f'%{search}%'
                )
            )
        ).all()

        clients=Client.query.filter(
            or_(
                Client.client_name.ilike(
                    f'%{search}%'
                ),
                Client.property_type.ilike(
                    f'%{search}%'
                ),
                Client.nearest_metrostation.ilike(
                    f'%{search}%'
                ),
                Client.mail_id.ilike(
                    f'%{search}%'
                ),
                Client.state.ilike(
                    f'%{search}%'
                ),
                Client.mobile_no.ilike(
                    f'%{search}%'
                ),
                Client.product.ilike(
                    f'%{search}%'
                ),
                Client.filter_colour.ilike(
                    f'%{search}%'
                ),
                Client.remark.ilike(
                    f'%{search}%'
                )
            )
        ).all()

        services = CustomerCareCard.query.filter(
            or_(

                CustomerCareCard.service_of.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.serviced_by.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.remark.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.miscellaneous_messages.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.tips_and_tricks.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.referrals_program.ilike(
                    f'%{search}%'
                )
            )
        ).all()
        services = CustomerCareCard.query.join(
            Client,
            CustomerCareCard.client_id == Client.client_id
        ).filter(

            or_(

                Client.client_name.ilike(
                    f'%{search}%'
                ),

                Client.mobile_no.ilike(
                    f'%{search}%'
                ),

                Client.product.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.service_of.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.serviced_by.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.remark.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.miscellaneous_messages.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.tips_and_tricks.ilike(
                    f'%{search}%'
                ),

                CustomerCareCard.referrals_program.ilike(
                    f'%{search}%'
                )

            )

        ).all()
    

    return render_template(
        'global_search.html',
        search=search,
        leads=leads,
        meetings=meetings,
        visits=visits,
        drawings=drawings,
        proposals=proposals,
        sales=sales,
        invoices=invoices,
        clients=clients,
        services=services
    )

@app.route('/tasks')
def tasks():

    if 'user_id' not in session:

        return redirect(
            url_for('login')
        )
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    today = date.today()

    lead_followups = Lead.query.filter(
        Lead.next_to_call <= today
    ).all()

    meeting_followups = Meeting.query.filter(
        Meeting.date_to_call_next <= today
    ).all()

    proposal_followups = Proposal.query.filter(
        Proposal.next_to_call <= today
    ).all()

    service_due_clients = []

    for client in Client.query.all():

        if client.last_service_date:

            due_date = (
                client.last_service_date
                + timedelta(
                    days=client.service_interval_days
                )
            )

        elif client.activation_date:

            due_date = (
                client.activation_date
                + timedelta(
                    days=client.service_interval_days
                )
            )

        else:

            continue

        if due_date <= today:

            service_due_clients.append(
                client
            )

    service_due_clients.sort(
        key=lambda x:
        x.last_service_date
        or x.activation_date
        or date.min
    )

    cmc_due_clients = Client.query.filter(
        Client.cmc_applicable == 'YES',
        Client.next_cmc_renewal_date != None,
        Client.next_cmc_renewal_date <= today
    ).order_by(
        Client.next_cmc_renewal_date.asc()
    ).all()

    return render_template(

        'tasks.html',

        today=today,

        lead_followups=
            lead_followups,

        meeting_followups=
            meeting_followups,

        proposal_followups=
            proposal_followups,

        service_due_clients=
            service_due_clients,

        cmc_due_clients=
            cmc_due_clients

    )

@app.route(
    '/complete-lead-followup/<int:lead_id>'
)
def complete_lead_followup(lead_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    lead = Lead.query.get_or_404(
        lead_id
    )

    completed_task = CompletedTask(

        module_type='LEAD',

        record_id=lead.lead_id,

        task_name=lead.name,

        completed_by=session.get(
            'username'
        )

    )

    db.session.add(
        completed_task
    )

    lead.next_to_call = None

    db.session.commit()

    return redirect(
        url_for('tasks')
    )

@app.route(
    '/complete-meeting-followup/<int:meeting_id>'
)
def complete_meeting_followup(meeting_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    meeting = Meeting.query.get_or_404(
        meeting_id
    )

    completed_task = CompletedTask(

        module_type='MEETING',

        record_id=meeting.meeting_id,

        task_name=meeting.name,

        completed_by=session.get(
            'username',
            'Unknown User'
        )

    )

    db.session.add(
        completed_task
    )

    meeting.date_to_call_next = None

    db.session.commit()

    return redirect(
        url_for('tasks')
    )

@app.route(
    '/complete-proposal-followup/<int:proposal_id>'
)
def complete_proposal_followup(
    proposal_id
):
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    proposal = Proposal.query.get_or_404(
        proposal_id
    )

    completed_task = CompletedTask(

        module_type='PROPOSAL',

        record_id=proposal.proposal_id,

        task_name=proposal.name,

        completed_by=session.get(
            'username',
            'Unknown User'
        )

    )

    db.session.add(
        completed_task
    )

    proposal.next_to_call = None

    db.session.commit()

    return redirect(
        url_for('tasks')
    )

@app.route('/completed-tasks')
def completed_tasks():

    if 'user_id' not in session:

        return redirect(
            url_for('login')
        )
    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    search = request.args.get(
        'search'
    )

    query = CompletedTask.query

    if search:

        query = query.filter(

            or_(

                CompletedTask.module_type.ilike(
                    f'%{search}%'
                ),

                CompletedTask.task_name.ilike(
                    f'%{search}%'
                ),

                CompletedTask.completed_by.ilike(
                    f'%{search}%'
                )

            )

        )

    tasks = query.order_by(
        CompletedTask.completed_on.desc()
    ).all()

    return render_template(

        'completed_tasks.html',

        tasks=tasks,

        search=search

    )

if __name__ == '__main__':

    app.run(debug=True)

    