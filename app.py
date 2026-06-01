from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'static/proposals'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = "crm_secret_key"

app.config['SQLALCHEMY_DATABASE_URI'] = \
'mysql+pymysql://root:RIYA1234@localhost/crm_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
        db.ForeignKey('proposals.proposal_id')
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

        if user:

            session['user_id'] = user.user_id

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

    return render_template(
        'index.html'
    )

@app.route('/add-lead',
           methods=['GET','POST'])
def add_lead():
    
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
    all_leads = Lead.query.all()
    return render_template('add_lead.html', leads=all_leads)

@app.route('/lead/<int:lead_id>')
def lead_details(lead_id):

    lead = Lead.query.get_or_404(
        lead_id
    )

    return render_template(
        'lead_details.html',
        lead=lead
    )

@app.route('/add-meeting',
           methods=['GET','POST'])
def add_meeting():
    if request.method == 'POST':
        lead_id = request.form.get('lead_id')
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
            remarks=remarks
        )
        db.session.add(meeting)
        db.session.commit()
        return redirect(url_for('add_meeting'))
    all_meetings = Meeting.query.all()
    all_leads = Lead.query.all()
    return render_template('add_meeting.html', meetings=all_meetings, leads=all_leads)

@app.route('/meeting/<int:meeting_id>')
def meeting_details(meeting_id):

    meeting = Meeting.query.get_or_404(
        meeting_id
    )

    return render_template(
        'meeting_details.html',
        meeting=meeting
    )

@app.route('/add-visit',
           methods=['GET','POST'])
def add_visit():

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

    all_visits = Visit.query.all()

    all_meetings = Meeting.query.all()

    return render_template(
        'add_visit.html',
        visits=all_visits,
        meetings=all_meetings
    )

@app.route('/visit/<int:visit_id>')
def visit_details(visit_id):

    visit = Visit.query.get_or_404(
        visit_id
    )

    return render_template(
        'visit_details.html',
        visit=visit
    )

@app.route('/add-proposal',
            methods=['GET', 'POST'])
def add_proposal():
    if request.method == 'POST':

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
                            'UPLOAD_FOLDER'
                        ],
                        filename
                    )
                )

                proposal_pdf = (
                    'proposals/' +
                    filename
                )

        proposal = Proposal(

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
    all_proposals = Proposal.query.all()
    all_meetings = Meeting.query.all()
    return render_template(
        'add_proposal.html',
        proposals=all_proposals,
        meetings=all_meetings
    )
@app.route('/proposal/<int:proposal_id>')
def proposal_details(proposal_id):

    proposal = Proposal.query.get_or_404(
        proposal_id
    )

    return render_template(
        'proposal_details.html',
        proposal=proposal
    )

@app.route('/add-client', methods=['GET', 'POST']) 
def add_client():
    if request.method == 'POST':
        proposal_id = request.form['proposal_id']

        proposal = Proposal.query.get( 
            proposal_id
)
        client_name = proposal.name
        property_type = request.form['property_type']
        monitor_present = request.form['monitor_present']
        address = proposal.site_address
        location_link = request.form['location_link']
        nearest_metrostation = request.form['nearest_metrostation']
        mail_id = proposal.email
        state = request.form['state']
        mobile_no = proposal.phone_no_client
        product = proposal.product
        filter_colour = request.form['filter_colour']
        no_of_units_installed = int( request.form['no_of_units_installed'] )
        solution_working = request.form['solution_working']
        cmc_applicable = request.form['cmc_applicable']
        cmc_amount = float( request.form['cmc_amount'] )
        filter_clean = request.form['filter_clean']
        service_for = request.form['service_for']
        no_of_filters_replaced = int( request.form['no_of_filters_replaced'] )
        pre_service_msg = request.form['pre_service_msg']
        post_service_msg = request.form['post_service_msg']
        remark = request.form['remark']
        installation_date = datetime.strptime( request.form['installation_date'], '%Y-%m-%d' ).date()
        activation_date = datetime.strptime( request.form['activation_date'], '%Y-%m-%d' ).date()
        next_cmc_renewal_date = ( installation_date + timedelta(days=365) )
        today = datetime.today().date()
        cmc_due_days = ( today - installation_date ).days
        if cmc_due_days >= 345:
            cmc_due = "YES"
        else:
            cmc_due = "NO"
        last_service_input = request.form[ 'last_service_date' ]
        service_interval_days = int( request.form['service_interval_days'] )
        if last_service_input:
            last_service_date = datetime.strptime( last_service_input, '%Y-%m-%d' ).date()
            last_service_days = ( today - last_service_date ).days
        else:
            last_service_date = None
            last_service_days = ( today - activation_date ).days
        if last_service_days >= service_interval_days:
            service_due = "YES"
        else:
            service_due = "NO"
        client = Client(
            client_name=client_name,
            property_type=property_type,
            monitor_present=monitor_present,
            address=address,
            location_link=location_link,
            nearest_metrostation=nearest_metrostation,
            mail_id=mail_id,
            state=state,
            mobile_no=mobile_no,
            product=product,
            installation_date= installation_date,
            activation_date= activation_date,
            filter_colour= filter_colour,
            no_of_units_installed= no_of_units_installed,
            solution_working= solution_working,
            cmc_applicable= cmc_applicable,
            next_cmc_renewal_date= next_cmc_renewal_date,
            cmc_due_days= cmc_due_days,
            cmc_due= cmc_due,
            cmc_amount= cmc_amount,
            last_service_date= last_service_date,
            last_service_days= last_service_days,
            service_interval_days= service_interval_days,
            service_due= service_due,
            filter_clean= filter_clean,
            service_for= service_for,
            no_of_filters_replaced= no_of_filters_replaced,
            pre_service_msg= pre_service_msg,
            post_service_msg= post_service_msg,
            remark=remark
        ) 
        db.session.add(client)
        db.session.commit()
        return redirect(url_for('add_client'))
    all_clients = Client.query.all()
    return render_template('add_client.html', clients=all_clients)

@app.route('/client/<int:client_id>')
def client_details(client_id):

    client = Client.query.get_or_404(
        client_id
    )

    return render_template(
        'client_details.html',
        client=client
    )

@app.route('/client-services/<int:client_id>')
def client_services(client_id):

    client = Client.query.get_or_404(
        client_id
    )

    services = CustomerCareCard.query.filter_by(
        client_id=client_id
    ).all()

    last_service = CustomerCareCard.query.filter_by(
        client_id=client_id
    ).order_by(
        CustomerCareCard.service_date.desc()
    ).first()

    if last_service:
        last_service_date = last_service.service_date
        service_due_date = last_service_date + timedelta(days=30)
    else:
        last_service_date = None
        service_due_date = None

    service_count = len(services)

    return render_template(
        'client_services.html',
        client=client,
        services=services,
        last_service_date=last_service_date,
        service_due_date=service_due_date,
        service_count=service_count
    )
@app.route(
    '/add-service/<int:client_id>',
    methods=['GET','POST']
)
def add_service(client_id):

    client = Client.query.get_or_404(
        client_id
    )

    if request.method == 'POST':

        service = CustomerCareCard(

            client_id=client_id,

            service_date=datetime.strptime(
                request.form['service_date'],
                '%Y-%m-%d'
            ).date(),

            service_of=request.form['service_of'],

            no_of_filters=request.form['no_of_filters'],

            controller_changed=request.form['controller_changed'],

            fan_changed=request.form['fan_changed'],

            serviced_by=request.form['serviced_by'],

            pre_service_msgd=request.form[
                'pre_service_msgd'
            ],

            post_service_report_sent=request.form[
                'post_service_report_sent'
            ],

            miscellaneous_messages=request.form[
                'miscellaneous_messages'
            ],

            tips_and_tricks=request.form[
                'tips_and_tricks'
            ],

            referrals_program=request.form[
                'referrals_program'
            ],

            news_sent=request.form[
                'news_sent'
            ],

            communication_date=datetime.strptime(
                request.form[
                    'communication_date'
                ],
                '%Y-%m-%d'
            ).date(),

            remark=request.form['remark']
        )

        db.session.add(service)

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

    service = CustomerCareCard.query.get_or_404(
        card_id
    )

    return render_template(
        'service_details.html',
        service=service
    )





if __name__ == '__main__':

    app.run(debug=True)

    