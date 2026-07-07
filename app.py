from flask import Flask, flash, render_template, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date, UTC
import os
from werkzeug.utils import secure_filename
from sqlalchemy import func, extract
from sqlalchemy import or_
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from docxtpl import DocxTemplate
from num2words import num2words
from openpyxl import Workbook
from flask import send_file
from io import BytesIO

app = Flask(__name__)
UPLOAD_FOLDER = 'static'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "mevachi_demo_secret_key_2026_change_before_production"
)

import os

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:RIYA1234@localhost/crm_db"
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def get_greeting():

    hour = datetime.now().hour

    if 5 <= hour < 12:

        return "Good Morning"

    elif 12 <= hour < 17:

        return "Good Afternoon"

    elif 17 <= hour < 22:

        return "Good Evening"

    else:

        return "Working Late"

def get_dashboard_notifications(

    username,

    role

):

    today = date.today()

    notifications = []



    if role == 'SALES':

        lead_base = Lead.query.filter(
            Lead.record_owner == username
        )

        meeting_base = Meeting.query.filter(
            Meeting.record_owner == username
        )

        proposal_base = Proposal.query.filter(
            Proposal.record_owner == username
        )

    elif role == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        lead_base = Lead.query.filter(
            Lead.record_owner.in_(usernames)
        )

        meeting_base = Meeting.query.filter(
            Meeting.record_owner.in_(usernames)
        )

        proposal_base = Proposal.query.filter(
            Proposal.record_owner.in_(usernames)
        )

    else:

        lead_base = Lead.query

        meeting_base = Meeting.query

        proposal_base = Proposal.query

    # ========================================
    # PERSONAL REMINDERS
    # ========================================

    reminders = Reminder.query.filter(

        Reminder.created_by == username,

        Reminder.status == 'PENDING',

        Reminder.is_dismissed == False,

        or_(

            Reminder.snooze_until == None,

            Reminder.snooze_until <= datetime.now()

        )

    ).order_by(

        Reminder.reminder_date.asc(),

        Reminder.reminder_time.asc()

    ).all()

    for reminder in reminders:

        if reminder.reminder_date < today:

            status = 'OVERDUE'

        elif reminder.reminder_date == today:

            status = 'TODAY'

        else:

            status = 'UPCOMING'

        notifications.append({

            'module': 'REMINDER',

            'title': reminder.title,

            'subtitle': reminder.description,

            'date': reminder.reminder_date,

            'priority': reminder.priority,

            'status': status,

            'record_id': reminder.reminder_id

        })

    # ========================================
    # LEAD FOLLOWUPS
    # ========================================

    leads = lead_base.filter(

        Lead.next_to_call != None

    ).all()

    for lead in leads:

        if lead.next_to_call < today:

            status = 'OVERDUE'

        elif lead.next_to_call == today:

            status = 'TODAY'

        else:

            status = 'UPCOMING'

        notifications.append({

            'module': 'LEAD',

            'title': lead.name,

            'subtitle': 'Lead Follow-up',

            'date': lead.next_to_call,

            'priority': 'HIGH',

            'status': status,

            'record_id': lead.lead_id

        })

    # ========================================
    # MEETING FOLLOWUPS
    # ========================================

    meetings = meeting_base.filter(

        Meeting.date_to_call_next != None

    ).all()

    for meeting in meetings:

        if meeting.date_to_call_next < today:

            status = 'OVERDUE'

        elif meeting.date_to_call_next == today:

            status = 'TODAY'

        else:

            status = 'UPCOMING'

        notifications.append({

            'module': 'MEETING',

            'title': meeting.name,

            'subtitle': 'Meeting Follow-up',

            'date': meeting.date_to_call_next,

            'priority': 'HIGH',

            'status': status,

            'record_id': meeting.meeting_id

        })

    # ========================================
    # PROPOSAL FOLLOWUPS
    # ========================================

    proposals = proposal_base.filter(

        Proposal.next_to_call != None

    ).all()

    for proposal in proposals:

        if proposal.next_to_call < today:

            status = 'OVERDUE'

        elif proposal.next_to_call == today:

            status = 'TODAY'

        else:

            status = 'UPCOMING'

        notifications.append({

            'module': 'PROPOSAL',

            'title': proposal.name,

            'subtitle': 'Proposal Follow-up',

            'date': proposal.next_to_call,

            'priority': 'HIGH',

            'status': status,

            'record_id': proposal.proposal_id

        })

    # ========================================
    # SERVICE DUE
    # ========================================

    if role in [

        'ADMIN',

        'COMMERCIALS'

    ]:

        for client in Client.query.all():

            update_client_status(

                client

            )

            if client.service_due == 'YES':

                notifications.append({

                    'module': 'SERVICE',

                    'title': client.client_name,

                    'subtitle': 'Service Due',

                    'date': client.last_service_date,

                    'priority': 'HIGH',

                    'status': 'TODAY',

                    'record_id': client.client_id

                })

    # ========================================
    # CMC DUE
    # ========================================

    if role in [

        'ADMIN',

        'COMMERCIALS'

    ]:

        cmc_clients = Client.query.filter(

            Client.cmc_applicable == 'YES',

            Client.next_cmc_renewal_date != None,

            Client.next_cmc_renewal_date <= (

                today + timedelta(days=20)

            )

        ).all()

        for client in cmc_clients:

            notifications.append({

                'module': 'CMC',

                'title': client.client_name,

                'subtitle': 'CMC Renewal Due',

                'date': client.next_cmc_renewal_date,

                'priority': 'MEDIUM',

                'status': 'UPCOMING',

                'record_id': client.client_id

            })

    notifications.sort(

        key=lambda x: (

            x['date'] is None,

            x['date']

        )

    )

    return notifications

def has_access(*allowed_roles):

    return session.get(
        'role'
    ) in allowed_roles

def can_access_record(owner):

    if session.get(
        'role'
    ) == 'ADMIN':

        return True

    if session.get(
        'role'
    ) == 'SALES':

        return owner == session[
            'username'
        ]

    if session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        return owner in usernames

    return False

def can_view_record(
    record_owner
):

    if session.get(
        'role'
    ) in [
        'ADMIN',
        'COMMERCIALS'
    ]:

        return True

    return session.get(
        'username'
    ) == record_owner

def can_edit_record(record_owner):

    if session.get(
        'role'
    ) == 'ADMIN':

        return True

    return (
        record_owner ==
        session.get(
            'username'
        )
    )


def can_delete_record(record_owner):

    if session.get(
        'role'
    ) == 'ADMIN':

        return True

    return (
        record_owner ==
        session.get(
            'username'
        )
    )

def get_record_query(model):

    role = session.get(
        'role'
    )

    username = session.get(
        'username'
    )

    if role == 'ADMIN':

        return model.query

    if model == Installation:

        return model.query

    if role == 'SALES':

        if model in [

            Client,

            CustomerCareCard

        ]:

            return model.query.filter(
                False
            )

        return model.query.filter(

            model.record_owner ==
            username

        )

    if role == 'COMMERCIALS':

        if model in [

            Client,

            CustomerCareCard

        ]:

            return model.query

        return model.query

    return model.query.filter(
        False
    )

def can_view_search_result(
    module,
    record
):

    role = session.get(
        'role'
    )

    username = session.get(
        'username'
    )

    if role == 'ADMIN':

        return True

    if module == 'INSTALLATION':

        return True

    if role == 'SALES':

        if module in [

            'CLIENT',

            'SERVICE'

        ]:

            return False

        return (

            record.record_owner ==
            username

        )

    if role == 'COMMERCIALS':

        return True

    return False

def can_edit_search_result(record):

    role = session.get(
        'role'
    )

    username = session.get(
        'username'
    )

    if role == 'ADMIN':

        return True

    if isinstance(
        record,
        Installation
    ):

        return True

    if role == 'COMMERCIALS':

        if isinstance(
            record,
            (
                Client,
                CustomerCareCard
            )
        ):

            return True

    return (

        record.record_owner ==
        username

    )

def can_delete_search_result(record):

    role = session.get(
        'role'
    )

    username = session.get(
        'username'
    )

    if role == 'ADMIN':

        return True

    if isinstance(
        record,
        Installation
    ):

        return True

    if role == 'COMMERCIALS':

        if isinstance(
            record,
            (
                Client,
                CustomerCareCard
            )
        ):

            return True

    return (

        record.record_owner ==
        username

    )

def search_records(
    model,
    columns,
    search
):

    query = get_record_query(
        model
    )

    conditions = []

    for column in columns:

        conditions.append(

            column.ilike(

                f'%{search}%'

            )

        )

    query = query.filter(

        or_(

            *conditions

        )

    )

    return query.all()

def parse_date(value):

    if not value:

        return None

    # Already a datetime object

    if isinstance(

        value,

        datetime

    ):

        return value.date()

    # Already a date object

    if hasattr(

        value,

        "year"

    ) and hasattr(

        value,

        "month"

    ) and hasattr(

        value,

        "day"

    ):

        return value

    value = str(

        value

    ).strip()

    formats = [

        "%Y-%m-%d",

        "%d-%m-%Y",

        "%d/%m/%Y",

        "%d-%b-%Y",

        "%d-%B-%Y",

        "%d.%m.%Y",

        "%m/%d/%Y",

        "%Y/%m/%d"

    ]

    for fmt in formats:

        try:

            return datetime.strptime(

                value,

                fmt

            ).date()

        except ValueError:

            continue

    return None

def log_activity(

    module_name,

    record_id,

    action,

    details=None

):

    log = ActivityLog(

        module_name=module_name,

        record_id=record_id,

        action=action,

        details=details,

        performed_by=session.get(
            'username'
        )

    )

    db.session.add(log)

def update_client_status(client):

    today = datetime.today().date()

    if client.installation_date:

        client.cmc_due_days = (
            today -
            client.installation_date
        ).days

    else:

        client.cmc_due_days = 0

    client.cmc_due = (
        'YES'
        if client.cmc_due_days >= 345
        else 'NO'
    )

    if client.last_service_date:

        client.last_service_days = (
            today -
            client.last_service_date
        ).days

    elif client.activation_date:

        client.last_service_days = (
            today -
            client.activation_date
        ).days

    else:

        client.last_service_days = 0

    client.service_due = (
        'YES'
        if client.last_service_days >= client.service_interval_days
        else 'NO'
    )

def admin_delete_or_request(
    model,
    record_id,
    module_name
):

    record = model.query.get_or_404(
        record_id
    )

    if session.get(
        'role'
    ) == 'ADMIN':

        try:

            db.session.delete(
                record
            )

            log_activity(

                module_name,

                record_id,

                'DELETED'

            )

            db.session.commit()

            flash(
                'Record deleted successfully.',
                'success'
            )

        except Exception:

            db.session.rollback()

            flash(

                'Cannot delete this record because it is linked with other records.',

                'danger'

            )

    else:

        delete_request = DeleteRequest(

            module_name=
                module_name,

            record_id=
                record_id,

            requested_by=
                session['username']

        )

        db.session.add(
            delete_request
        )

        db.session.commit()

        flash(

            'Delete request sent to Admin.',

            'success'

        )

AIR_QUALITY = {

    "West Delhi": (94, 117),

    "East Delhi": (110, 137),

    "South Delhi": (87, 112),

    "North Delhi": (96, 137),

    "Gurgaon": (94, 124),

    "Ghaziabad": (100, 128),

    "Greater Noida": (97, 125),

    "Noida": (90, 114),

    "Others": (119, 219)

}

def get_current_quarter():

    month = datetime.now().month

    if month in [

        1,
        2,
        3

    ]:

        return 1

    elif month in [

        4,
        5,
        6

    ]:

        return 2

    elif month in [

        7,
        8,
        9

    ]:

        return 3

    return 4

def get_air_quality(location):

    print("FUNCTION CALLED")
    print("LOCATION =", repr(location))

    print(AIR_QUALITY)

    if location in AIR_QUALITY:

        print("MATCH FOUND")

    else:

        print("NO MATCH")

    pm25, pm10 = AIR_QUALITY.get(
        location,
        AIR_QUALITY["Others"]
    )

    print(pm25, pm10)

    quarter = get_current_quarter()

    multiplier = {

        1: 1.15,

        2: 1.00,

        3: 1.05,

        4: 1.10

    }

    factor = multiplier[quarter]

    pm25 = round(pm25 * factor)

    pm10 = round(pm10 * factor)

    return {

        "pm25": pm25,

        "pm10": pm10,

        "co2": 500

    }

def get_proposal_template(

    proposal

):

    if (

        proposal.discount

        and

        float(

            proposal.discount

        ) > 0

    ):

        return "discounted_proposal_template.docx"

    return "proposal_template.docx"

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

    must_change_password = db.Column(
        db.String(10),
        default='YES'
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

    record_owner = db.Column(
        db.String(100)
    )


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
        db.ForeignKey('leads.lead_id'),
        nullable=True    
    )

    history = db.relationship(

        'MeetingHistory',

        backref='meeting',

        cascade='all, delete-orphan'

    )

    record_owner = db.Column(
        db.String(100)
    )    

class MeetingHistory(db.Model):

    __tablename__ = 'meeting_history'

    history_id = db.Column(
        db.Integer,
        primary_key=True
    )

    meeting_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'meetings.meeting_id'
        )
    )

    name = db.Column(
        db.String(100)
    )

    designation = db.Column(
        db.String(100)
    )

    contact_no = db.Column(
        db.String(20)
    )

    email = db.Column(
        db.String(100)
    )

    meeting_fixed_by = db.Column(
        db.String(100)
    )

    company_info_shared = db.Column(
        db.String(10)
    )

    meeting_fixed = db.Column(
        db.String(10)
    )

    date_of_meeting = db.Column(
        db.Date
    )

    mode_of_meeting = db.Column(
        db.String(50)
    )

    meeting_status = db.Column(
        db.String(50)
    )

    meeting_conducted_by = db.Column(
        db.String(100)
    )

    floor_plan_shared = db.Column(
        db.String(10)
    )

    site_visit = db.Column(
        db.String(10)
    )

    post_meeting_mail = db.Column(
        db.String(10)
    )

    date_of_last_followup = db.Column(
        db.Date
    )

    date_to_call_next = db.Column(
        db.Date
    )

    reschedule_date = db.Column(
        db.Date
    )

    reason_for_reschedule = db.Column(
        db.Text
    )

    remarks = db.Column(
        db.Text
    )

    final_remarks = db.Column(
        db.Text
    )

    record_owner = db.Column(
        db.String(100)
    )

class Visit(db.Model):

    __tablename__ = 'visits'

    visit_id = db.Column(
        db.Integer,
        primary_key=True
    )

    meeting_id = db.Column(
        db.Integer,
        db.ForeignKey('meetings.meeting_id'),
        nullable=True
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

    record_owner = db.Column(
        db.String(100)
    )

    last_updated = db.Column(

        db.DateTime,

        default=datetime.utcnow,

        onupdate=datetime.utcnow

    )

class VisitHistory(db.Model):

    __tablename__ = 'visit_history'

    history_id = db.Column(

        db.Integer,

        primary_key=True

    )

    visit_id = db.Column(

        db.Integer,

        db.ForeignKey(

            'visits.visit_id'

        ),
        nullable=True
    )

    meeting_id = db.Column(

        db.Integer,

        db.ForeignKey(

            'meetings.meeting_id'

        ),
        nullable=True
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

    record_owner = db.Column(

        db.String(100)

    )

    last_updated = db.Column(

        db.DateTime,

        default=datetime.utcnow

    )

class Drawing(db.Model):

    __tablename__ = 'drawings'

    drawing_id = db.Column(
        db.Integer,
        primary_key=True
    )

    visit_id = db.Column(
        db.Integer,
        db.ForeignKey('visits.visit_id'),
        nullable=True
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

    files = db.relationship(

        'DrawingFile',

        backref='drawing',

        cascade='all, delete-orphan'

    )

    record_owner = db.Column(
        db.String(100)
    )

class DrawingFile(db.Model):

    __tablename__ = 'drawing_files'

    file_id = db.Column(

        db.Integer,

        primary_key=True

    )

    drawing_id = db.Column(

        db.Integer,

        db.ForeignKey(

            'drawings.drawing_id'

        )

    )

    file_name = db.Column(

        db.String(255)

    )

    file_path = db.Column(

        db.String(500)

    )

    file_type = db.Column(

        db.String(500)

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

    meeting_id = db.Column(
        db.Integer,
        db.ForeignKey('meetings.meeting_id'),
        nullable=True
    )
    drawing_id = db.Column(
        db.Integer,
        db.ForeignKey('drawings.drawing_id'),
        nullable=True
    )

    files = db.relationship(

        'ProposalFile',

        backref='proposal',

        cascade='all, delete-orphan'

    )

    record_owner = db.Column(
        db.String(100)
    )


class ProposalFile(db.Model):

    __tablename__ = 'proposal_files'

    file_id = db.Column(

        db.Integer,

        primary_key=True

    )

    proposal_id = db.Column(

        db.Integer,

        db.ForeignKey(

            'proposals.proposal_id'

        )

    )

    file_name = db.Column(

        db.String(500)

    )

    file_path = db.Column(

        db.String(500)

    )

    file_type = db.Column(

        db.String(500)

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
        ),
        nullable=True
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

    record_owner = db.Column(
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
        db.ForeignKey('sales_pipeline.sales_id'),
        nullable=True
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



    record_owner = db.Column(
        db.String(100)
    )

    files = db.relationship(

    'InvoiceFile',

    backref='invoice',

    cascade='all, delete-orphan'

)
    
class InvoiceFile(db.Model):

    __tablename__ = 'invoice_files'

    file_id = db.Column(
        db.Integer,
        primary_key=True
    )

    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'invoices.invoice_id'
        )
    )

    file_name = db.Column(
        db.String(500)
    )

    file_path = db.Column(
        db.String(500)
    )

    file_type = db.Column(
        db.String(500)
    )

class Installation(db.Model):

    __tablename__ = 'installation'

    installation_id = db.Column(
        db.Integer,
        primary_key=True
    )

    sales_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'sales_pipeline.sales_id'
        ),
        nullable=True
    )

    installation_for = db.Column(
        db.String(200)
    )

    installation_type = db.Column(
        db.String(100)
    )

    piping_type = db.Column(
        db.String(100)
    )

    machine_position = db.Column(
        db.String(100)
    )

    installation_status = db.Column(
        db.String(50),
        default='PENDING'
    )

    installation_notes = db.Column(
        db.Text
    )

    created_by = db.Column(
        db.String(100)
    )

    created_on = db.Column(
        db.DateTime,
        default=datetime.now
    )

    record_owner = db.Column(
        db.String(100)
    )

    files = db.relationship(
        'InstallationFile',
        backref='installation',
        cascade='all, delete-orphan'
    )

    cuttings = db.relationship(

        'InstallationCutting',

        backref='installation',

        cascade='all, delete-orphan'

    )

    sales = db.relationship(

        'SalesPipeline',

        backref='installations'

    )

class InstallationFile(db.Model):

    __tablename__ = 'installation_files'

    file_id = db.Column(
        db.Integer,
        primary_key=True
    )

    installation_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'installation.installation_id'
        )
    )

    file_name = db.Column(
        db.String(255)
    )

    file_path = db.Column(
        db.String(500)
    )

    file_type = db.Column(
        db.String(500)
    )

class InstallationCutting(db.Model):

    __tablename__ = 'installation_cuttings'

    cutting_id = db.Column(
        db.Integer,
        primary_key=True
    )

    installation_id = db.Column(
        db.Integer,
        db.ForeignKey(
            'installation.installation_id'
        )
    )

    cutting_type = db.Column(
        db.String(50)
    )

    size = db.Column(
        db.String(150)
    )

    quantity = db.Column(
        db.Integer,
        default=1
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
        db.ForeignKey('proposals.proposal_id'),
        nullable=True
    )

    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey('invoices.invoice_id'),
        nullable=True
   )
    
    record_owner = db.Column(
        db.String(100)
    )

class CustomerCareCard(db.Model):

    __tablename__ = 'customer_care_card'

    card_id = db.Column(db.Integer, primary_key=True)

    client_id = db.Column(
        db.Integer,
        db.ForeignKey('client.client_id'),
        nullable=False
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

    record_owner = db.Column(
        db.String(100)
    )

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

class ActivityLog(db.Model):

    __tablename__ = 'activity_logs'

    log_id = db.Column(
        db.Integer,
        primary_key=True
    )

    module_name = db.Column(
        db.String(50)
    )

    record_id = db.Column(
        db.Integer
    )

    action = db.Column(
        db.String(50)
    )

    performed_by = db.Column(
        db.String(100)
    )

    performed_on = db.Column(
        db.DateTime,
        default=datetime.now
    )

    details = db.Column(
        db.String(500)
    )

class DeleteRequest(db.Model):

    __tablename__ = 'delete_requests'

    request_id = db.Column(
        db.Integer,
        primary_key=True
    )

    module_name = db.Column(
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

    reason = db.Column(
        db.String(500)
    )

class Reminder(db.Model):

    __tablename__ = 'reminders'

    reminder_id = db.Column(

        db.Integer,

        primary_key=True

    )

    title = db.Column(

        db.String(200),

        nullable=False

    )

    description = db.Column(

        db.Text

    )

    reminder_date = db.Column(

        db.Date,

        nullable=False

    )

    reminder_time = db.Column(

        db.Time

    )

    priority = db.Column(

        db.String(20),

        default='MEDIUM'

    )

    repeat_type = db.Column(

        db.String(20),

        default='NONE'

    )

    status = db.Column(

        db.String(20),

        default='PENDING'

    )

    snooze_until = db.Column(

        db.DateTime

    )

    created_by = db.Column(

        db.String(100),

        nullable=False

    )

    created_on = db.Column(

        db.DateTime,

        default=datetime.utcnow

    )

    is_dismissed = db.Column(

        db.Boolean,

        default=False

    )

def indian_format(number):

    number = int(float(number))

    s = str(number)

    if len(s) <= 3:

        return s

    last3 = s[-3:]

    rest = s[:-3]

    parts = []

    while len(rest) > 2:

        parts.insert(
            0,
            rest[-2:]
        )

        rest = rest[:-2]

    if rest:

        parts.insert(
            0,
            rest
        )

    return ",".join(
        parts + [last3]
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

        password=request.form['password']


        user = User.query.filter_by(
            username=username,
        ).first()

        if (

            user

            and

            check_password_hash(
                user.password,
                password
            )

            and

            user.is_active == 'YES'

        ):

            session['user_id'] = user.user_id

            session['username'] = user.username

            session['role'] = user.role

            session['show_morning_brief'] = True

            if user.must_change_password == 'YES':

                return redirect(
                    url_for(
                        'change_password'
                    )
                )

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
    
    greeting = get_greeting()

    show_morning_brief = session.get(

        'show_morning_brief',

        False

    )

    my_notifications = get_dashboard_notifications(

        session['username'],

        session['role']

    )

    notifications = my_notifications

    notification_count = len(

        my_notifications

    )

    
 
    team_notifications = []

    commercial_notifications = []

    if session.get('role') == 'ADMIN':

        sales_users = User.query.filter_by(

            role='SALES'

        ).order_by(

            User.username

        ).all()

        commercial_user = User.query.filter_by(

            role='COMMERCIALS'

        ).first()

        

        for user in sales_users:

            employee_notifications = get_dashboard_notifications(

                user.username,

                user.role

            )

            if employee_notifications:

                team_notifications.append({

                    'username': user.username,

                    'count': len(employee_notifications),

                    'notifications': employee_notifications

                })

        if commercial_user:

            commercial_notifications = get_dashboard_notifications(

                commercial_user.username,

                'COMMERCIALS'

            )

    overdue_notifications = [

        item

        for item in notifications

        if item['status'] == 'OVERDUE'

    ]

    today_notifications = [

        item

        for item in notifications

        if item['status'] == 'TODAY'

    ]

    upcoming_notifications = [

        item

        for item in notifications

        if item['status'] == 'UPCOMING'

    ]

    notification_count = len(
        notifications
    )

    tomorrow = today + timedelta(days=1)

    week_end = today + timedelta(days=7)

    if session.get('role') == 'SALES':

        lead_base = Lead.query.filter(
            Lead.record_owner == session['username']
        )

        meeting_base = Meeting.query.filter(
            Meeting.record_owner == session['username']
        )

        proposal_base = Proposal.query.filter(
            Proposal.record_owner == session['username']
        )

    elif session.get('role') == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]

        lead_base = Lead.query.filter(
            Lead.record_owner.in_(usernames)
        )

        meeting_base = Meeting.query.filter(
            Meeting.record_owner.in_(usernames)
        )

        proposal_base = Proposal.query.filter(
            Proposal.record_owner.in_(usernames)
        )

    else:

        lead_base = Lead.query

        meeting_base = Meeting.query

        proposal_base = Proposal.query

    commercial_count = (

        lead_base.count()

        +

        meeting_base.count()

        +

        proposal_base.count()

    )
    # OVERDUE

    overdue_leads = lead_base.filter(
        Lead.next_to_call < today
    ).all()

    overdue_meetings = meeting_base.filter(
        Meeting.date_to_call_next < today
    ).all()

    overdue_proposals = proposal_base.filter(
        Proposal.next_to_call < today
    ).all()


    # DUE TODAY

    today_leads = lead_base.filter(
        Lead.next_to_call == today
    ).all()

    today_meetings = meeting_base.filter(
        Meeting.date_to_call_next == today
    ).all()

    today_proposals = proposal_base.filter(
        Proposal.next_to_call == today
    ).all()


    # DUE TOMORROW

    tomorrow_leads = lead_base.filter(
        Lead.next_to_call == tomorrow
    ).all()

    tomorrow_meetings = meeting_base.filter(
        Meeting.date_to_call_next == tomorrow
    ).all()

    tomorrow_proposals = proposal_base.filter(
        Proposal.next_to_call == tomorrow
    ).all()


    # DUE THIS WEEK

    week_leads = lead_base.filter(
        Lead.next_to_call > tomorrow,
        Lead.next_to_call <= week_end
    ).all()

    week_meetings = meeting_base.filter(
        Meeting.date_to_call_next > tomorrow,
        Meeting.date_to_call_next <= week_end
    ).all()

    week_proposals = proposal_base.filter(
        Proposal.next_to_call > tomorrow,
        Proposal.next_to_call <= week_end
    ).all()

    service_due_clients = []

    for client in Client.query.all():
        update_client_status(client)
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
        Client.next_cmc_renewal_date <= today + timedelta(days=20)
    ).order_by(
        Client.next_cmc_renewal_date.asc()
    ).all()

    overdue_count = (
        len(overdue_leads)
        + len(overdue_meetings)
        + len(overdue_proposals)
    )

    today_count = (
        len(today_leads)
        + len(today_meetings)
        + len(today_proposals)
    )

    tomorrow_count = (
        len(tomorrow_leads)
        + len(tomorrow_meetings)
        + len(tomorrow_proposals)
    )

    week_count = (
        len(week_leads)
        + len(week_meetings)
        + len(week_proposals)
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
    pending_delete_requests = DeleteRequest.query.filter_by(
        status='PENDING'
    ).count()

# ==========================================
# ROLE BASED QUERIES
# ==========================================

    if session.get('role') == 'SALES':

        lead_query = Lead.query.filter_by(

            record_owner=session['username']

        )

        meeting_query = Meeting.query.filter_by(

            record_owner=session['username']

        )

        proposal_query = Proposal.query.filter_by(

            record_owner=session['username']

        )

        client_query = Client.query.filter_by(

            record_owner=session['username']

        )

        invoice_query = Invoice.query.filter_by(

            record_owner=session['username']

        )

    elif session.get('role') == 'COMMERCIALS':

        commercial_users = User.query.filter_by(

            role='COMMERCIALS'

        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        lead_query = Lead.query.filter(

            Lead.record_owner.in_(usernames)

        )

        meeting_query = Meeting.query.filter(

            Meeting.record_owner.in_(usernames)

        )

        proposal_query = Proposal.query.filter(

            Proposal.record_owner.in_(usernames)

        )

        client_query = Client.query.filter(

            Client.record_owner.in_(usernames)

        )

        invoice_query = Invoice.query.filter(

            Invoice.record_owner.in_(usernames)

        )

    else:

        lead_query = Lead.query

        meeting_query = Meeting.query

        proposal_query = Proposal.query

        client_query = Client.query

        invoice_query = Invoice.query

    lead_count = lead_query.count()

    meeting_count = meeting_query.count()

    proposal_count = proposal_query.count()

    client_count = client_query.count()

# ==========================================
# MEETING SOURCE PIE CHART
# ==========================================

    meeting_source = meeting_query.with_entities(

        Meeting.source,

        func.count(Meeting.meeting_id)

    ).group_by(

        Meeting.source

    ).all()

    meeting_labels = []

    meeting_values = []

    for source, count in meeting_source:

        meeting_labels.append(

            source if source else "Unknown"

        )

        meeting_values.append(

            count

        )

# ==========================================
# PROPOSAL STATUS BAR CHART
# ==========================================

    proposal_status = proposal_query.with_entities(

        Proposal.status,

        func.count(Proposal.proposal_id)

    ).group_by(

        Proposal.status

    ).all()

    proposal_labels = []

    proposal_values = []

    for status, count in proposal_status:

        proposal_labels.append(

            status if status else "Unknown"

        )

        proposal_values.append(

            count

        )

    current_year = datetime.now().year

    available_years = list(

        range(

            current_year-5,

            current_year+1

        )

    )

# ==========================================
# FILTER REPLACEMENT TREND
# ==========================================

    selected_year = request.args.get(

        'year',

        datetime.now().year,

        type=int

    )

    filter_data = []

    if session.get('role') in ['ADMIN', 'COMMERCIALS']:

        if session.get('role') == 'COMMERCIALS':

            filter_data = db.session.query(

                extract(

                    'month',

                    CustomerCareCard.service_date

                ),

                func.sum(

                    CustomerCareCard.no_of_filters

                )

            ).filter(

                extract(

                    'year',

                    CustomerCareCard.service_date

                ) == selected_year

            ).group_by(

                extract(

                    'month',

                    CustomerCareCard.service_date

                )

            ).order_by(

                extract(

                    'month',

                    CustomerCareCard.service_date

                )

            ).all()            

        else:

            filter_data = db.session.query(

                extract(

                    'month',

                    CustomerCareCard.service_date

                ),

                func.sum(

                    CustomerCareCard.no_of_filters

                )

            ).filter(

                extract(

                    'year',

                    CustomerCareCard.service_date

                ) == selected_year

            ).group_by(

                extract(

                    'month',

                    CustomerCareCard.service_date

                )

            ).all()


    month_names = [

        'Jan','Feb','Mar','Apr','May','Jun',

        'Jul','Aug','Sep','Oct','Nov','Dec'

    ]

    filter_dict = {

        int(month): int(value or 0)

        for month, value in filter_data

    }

    filter_months = month_names

    filter_values = []

    for i in range(1,13):

        filter_values.append(

            int(

                filter_dict.get(i,0)

            )

        )

# ==========================================
# MONTHLY REVENUE TREND
# ==========================================
    
    revenue_year = request.args.get(

        'revenue_year',

        datetime.now().year,

        type=int

    )

    monthly_revenue = []

    if session.get('role') == 'ADMIN':

        monthly_revenue = invoice_query.with_entities(

            extract(

                'month',

                Invoice.doi

            ),

            func.sum(

                Invoice.total_revenue

            )

        ).filter(

            extract(

                'year',

                Invoice.doi

            ) == revenue_year

        ).group_by(

            extract(

                'month',

                Invoice.doi

            )

        ).order_by(

            extract(

                'month',

                Invoice.doi

            )

        ).all()

    month_names = [

        'Jan','Feb','Mar','Apr','May','Jun',

        'Jul','Aug','Sep','Oct','Nov','Dec'

    ]

    revenue_dict = {

        int(month): float(amount or 0)

        for month, amount in monthly_revenue

    }

    months = month_names

    revenues = []

    for i in range(1,13):

        revenues.append(

            revenue_dict.get(i,0)

        )

    response = render_template(
        'index.html',
        lead_count=lead_count,
        meeting_count=meeting_count,
        proposal_count=proposal_count,
        client_count=client_count,
        meeting_labels=meeting_labels,
        meeting_values=meeting_values,
        proposal_labels=proposal_labels,
        proposal_values=proposal_values,
        months=months,
        available_years=available_years,
        selected_year=selected_year,
        filter_months=filter_months,
        filter_values=filter_values,
        revenue_year=revenue_year,
        revenues=revenues,
        greeting=greeting,
        show_morning_brief=show_morning_brief,
        commercial_notifications=commercial_notifications,    
        notifications=notifications,
        my_notifications=my_notifications,
        team_notifications=team_notifications,
        overdue_notifications=overdue_notifications,
        today_notifications=today_notifications,
        upcoming_notifications=upcoming_notifications,
        notification_count=notification_count,
        monthly_filters=monthly_filters,
        yearly_filters=yearly_filters,
        overdue_leads=overdue_leads,
        overdue_meetings=overdue_meetings,
        overdue_proposals=overdue_proposals,

        today_leads=today_leads,
        today_meetings=today_meetings,
        today_proposals=today_proposals,

        tomorrow_leads=tomorrow_leads,
        tomorrow_meetings=tomorrow_meetings,
        tomorrow_proposals=tomorrow_proposals,

        week_leads=week_leads,
        week_meetings=week_meetings,
        week_proposals=week_proposals,

        overdue_count=overdue_count,
        today_count=today_count,
        tomorrow_count=tomorrow_count,
        week_count=week_count,
        service_due_clients=service_due_clients,
        cmc_due_clients=cmc_due_clients,
        services_due=services_due,
        cmc_due=cmc_due,
        pending_delete_requests=pending_delete_requests      
    )

    session['show_morning_brief'] = False
    
    return response

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

            password=generate_password_hash(

                request.form.get(
                'password'
                )

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

            is_active='YES',

            must_change_password='YES'

        )

        db.session.add(
            user
        )
        db.session.flush()
        log_activity(

            'USER',

            user.user_id,

            'CREATED'
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
        db.session.flush()
        log_activity(

            'USER',

            user.user_id,

            'UPDATED'
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

@app.route(
    '/change-password',
    methods=['GET', 'POST']
)
def change_password():

    if 'user_id' not in session:

        return redirect(
            url_for('login')
        )

    user = User.query.get(
        session['user_id']
    )

    if request.method == 'POST':

        new_password = request.form.get(
            'new_password'
        )

        confirm_password = request.form.get(
            'confirm_password'
        )

        if new_password != confirm_password:

            flash(
                'Passwords do not match.'
            )

            return redirect(
                url_for(
                    'change_password'
                )
            )

        user.password = generate_password_hash(
            new_password
        )

        user.must_change_password = 'NO'

        db.session.commit()

        flash(
            'Password changed successfully.'
        )

        return redirect(
            url_for(
                'dashboard'
            )
        )

    return render_template(
        'change_password.html'
    )

@app.route(
    '/reset-password/<int:user_id>'
)
def reset_password(user_id):

    if session.get('role') != 'ADMIN':

        return redirect(
            url_for('dashboard')
        )

    user = User.query.get_or_404(
        user_id
    )

    temp_password = 'Temp@123'

    user.password = generate_password_hash(
        temp_password
    )

    user.must_change_password = 'YES'

    db.session.flush()
     
    log_activity(

        'USER',

        user.user_id,

        'PASSWORD RESET',

        f'Password reset for {user.username}'

    )

    db.session.commit()

    flash(

        f'Temporary Password: {temp_password}'

    )

    return redirect(
        url_for(
            'manage_users'
        )
    )


@app.route('/add-lead',
           methods=['GET','POST'])
def add_lead():

    if not has_access(
        'ADMIN',
        'COMMERCIALS',
        'SALES'
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
            recent=recent,
            record_owner=session[
                'username'
            ]    
        )
        db.session.add(lead)
        db.session.flush()
        log_activity(

            'LEAD',

            lead.lead_id,

            'CREATED'

        )
        db.session.commit()
        return redirect(url_for('add_lead'))
    search = request.args.get(
        'search'
    )

    if session.get(
        'role'
    ) == 'SALES':

        base_query = Lead.query.filter_by(

            record_owner=session[
                'username'
            ]

        )

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(

            role='COMMERCIALS'

        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        base_query = Lead.query.filter(

            Lead.record_owner.in_(
                usernames
            )

        )

    else:

        base_query = Lead.query

    if search:

        all_leads = base_query.filter(
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
        all_leads=base_query.all()

    return render_template(
        'add_lead.html',
        leads=all_leads,
        admin_view=session.get(
            'role'
        ) == 'ADMIN'
    )

@app.route('/lead/<int:lead_id>')
def lead_details(lead_id):

    if not has_access(
        'ADMIN',
        'COMMERCIALS',
        'SALES'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    lead = Lead.query.get_or_404(
        lead_id
    )

    if not can_view_record(

        lead.record_owner

    ):

        return redirect(
            url_for(
                'dashboard'
            )
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
        'COMMERCIALS',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    lead = Lead.query.get_or_404(
        lead_id
    )
    if not can_access_record(

        lead.record_owner

    ):

        return redirect(
            url_for(
                'dashboard'
            )
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
        db.session.flush()
        log_activity(

            'LEAD',

            lead.lead_id,

            'UPDATED'

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

@app.route(
    '/request-delete-lead/<int:lead_id>',
    methods=['GET', 'POST']
)
def request_delete_lead(lead_id):

    lead = Lead.query.get_or_404(
        lead_id
    )

    # ADMIN -> DELETE DIRECTLY
    if session.get(
        'role'
    ) == 'ADMIN':

        try:

            db.session.delete(
                lead
            )

            db.session.flush()

            log_activity(

                'LEAD',

                lead_id,

                'DELETED'

            )

            db.session.commit()

            flash(

                'Lead deleted successfully.'

            )

        except Exception:

            db.session.rollback()

            flash(

                'Cannot delete this Lead because it is linked with other records.'

            )

        return redirect(

            url_for(
                'add_lead'
            )

        )

    # EMPLOYEE -> DELETE REQUEST
    if request.method == 'POST':

        delete_request = DeleteRequest(

            module_name='LEAD',

            record_id=lead_id,

            requested_by=session[
                'username'
            ],

            reason=request.form.get(
                'reason'
            )

        )

        db.session.add(
            delete_request
        )

        db.session.flush()

        log_activity(

            'LEAD',

            lead_id,

            'DELETE REQUESTED',

            request.form.get(
                'reason'
            )

        )

        db.session.commit()

        flash(
            'Delete request sent.'
        )

        return redirect(

            url_for(
                'add_lead'
            )

        )

    return render_template(

        'delete_request.html',

        module='LEAD',

        record_id=lead_id

    )

@app.route('/delete-lead/<int:lead_id>')
def delete_lead(lead_id):

    if not has_access(
        'ADMIN'
    ):

        return redirect(
            url_for('dashboard')
        )

    lead = Lead.query.get_or_404(
        lead_id
    )

    try:

        db.session.delete(
            lead
        )

        db.session.flush()

        log_activity(

            'LEAD',

            lead_id,

            'DELETED'

        )

        db.session.commit()

        flash(

            'Lead deleted successfully.'

        )

    except Exception:

        db.session.rollback()

        flash(

            'Cannot delete this Lead because it is linked with other records.'

        )

    return redirect(

        url_for(
            'add_lead'
        )

    )

@app.route(
    '/add-meeting',
    methods=['GET', 'POST']
)
def add_meeting():

    if not has_access(

        'ADMIN',

        'COMMERCIALS',

        'SALES'

    ):

        return redirect(

            url_for(
                'dashboard'
            )

        )

    if request.method == 'POST':

        # ===========================
        # COMPANY DETAILS
        # ===========================

        lead_id = request.form.get(

            'lead_id'

        )

        source = request.form.get(

            'source'

        )

        reference = request.form.get(

            'reference'

        )

        firm_name = request.form.get(

            'firm_name'

        )

        address = request.form.get(

            'address'

        )

        state = request.form.get(

            'state'

        )

        # ===========================
        # ALL MEETING RECORDS
        # ===========================

        names = request.form.getlist(

            'name[]'

        )

        designations = request.form.getlist(

            'designation[]'

        )

        contact_numbers = request.form.getlist(

            'contact_no[]'

        )

        emails = request.form.getlist(

            'email[]'

        )

        meeting_fixed_bys = request.form.getlist(

            'meeting_fixed_by[]'

        )

        company_info_shareds = request.form.getlist(

            'company_info_shared[]'

        )

        meeting_fixeds = request.form.getlist(

            'meeting_fixed[]'

        )

        meeting_dates = request.form.getlist(

            'date_of_meeting[]'

        )

        meeting_modes = request.form.getlist(

            'mode_of_meeting[]'

        )

        meeting_statuses = request.form.getlist(

            'meeting_status[]'

        )

        meeting_conducted_bys = request.form.getlist(

            'meeting_conducted_by[]'

        )

        floor_plan_shareds = request.form.getlist(

            'floor_plan_shared[]'

        )

        site_visits = request.form.getlist(

            'site_visit[]'

        )

        post_meeting_mails = request.form.getlist(

            'post_meeting_mail[]'

        )

        last_followups = request.form.getlist(

            'date_of_last_followup[]'

        )

        next_calls = request.form.getlist(

            'date_to_call_next[]'

        )

        reschedule_dates = request.form.getlist(

            'reschedule_date[]'

        )

        reasons = request.form.getlist(

            'reason_for_reschedule[]'

        )

        remarks_list = request.form.getlist(

            'remarks[]'

        )

        final_remarks_list = request.form.getlist(

            'final_remarks[]'

        )

        # ===========================
        # CREATE MASTER MEETING
        # ===========================

        first_meeting_date = None

        if meeting_dates[0]:

            first_meeting_date = datetime.strptime(

                meeting_dates[0],

                '%Y-%m-%d'

            ).date()

        first_last_followup = None

        if last_followups[0]:

            first_last_followup = datetime.strptime(

                last_followups[0],

                '%Y-%m-%d'

            ).date()

        first_next_call = None

        if next_calls[0]:

            first_next_call = datetime.strptime(

                next_calls[0],

                '%Y-%m-%d'

            ).date()

        first_reschedule = None

        if reschedule_dates[0]:

            first_reschedule = datetime.strptime(

                reschedule_dates[0],

                '%Y-%m-%d'

            ).date()

        meeting = Meeting(

            lead_id=lead_id,

            source=source,

            reference=reference,

            firm_name=firm_name,

            address=address,

            state=state,

            name=names[0],

            designation=designations[0],

            contact_no=contact_numbers[0],

            email=emails[0],

            meeting_fixed_by=meeting_fixed_bys[0],

            company_info_shared=company_info_shareds[0],

            meeting_fixed=meeting_fixeds[0],

            date_of_meeting=first_meeting_date,

            mode_of_meeting=meeting_modes[0],

            meeting_status=meeting_statuses[0],

            meeting_conducted_by=meeting_conducted_bys[0],

            floor_plan_shared=floor_plan_shareds[0],

            site_visit=site_visits[0],

            post_meeting_mail=post_meeting_mails[0],

            date_of_last_followup=first_last_followup,

            date_to_call_next=first_next_call,

            reschedule_date=first_reschedule,

            reason_for_reschedule=reasons[0],

            remarks=remarks_list[0],

            final_remarks=final_remarks_list[0],

            record_owner=session[
                'username'
            ]

        )

        db.session.add(

            meeting

        )

        db.session.flush()
        # ===========================
        # SAVE ADDITIONAL MEETINGS
        # ===========================

        for i in range(

            1,

            len(names)

        ):

            history_meeting_date = None

            if meeting_dates[i]:

                history_meeting_date = datetime.strptime(

                    meeting_dates[i],

                    '%Y-%m-%d'

                ).date()

            history_last_followup = None

            if last_followups[i]:

                history_last_followup = datetime.strptime(

                    last_followups[i],

                    '%Y-%m-%d'

                ).date()

            history_next_call = None

            if next_calls[i]:

                history_next_call = datetime.strptime(

                    next_calls[i],

                    '%Y-%m-%d'

                ).date()

            history_reschedule = None

            if reschedule_dates[i]:

                history_reschedule = datetime.strptime(

                    reschedule_dates[i],

                    '%Y-%m-%d'

                ).date()

            history = MeetingHistory(

                meeting_id=meeting.meeting_id,

                name=names[i],

                designation=designations[i],

                contact_no=contact_numbers[i],

                email=emails[i],

                meeting_fixed_by=meeting_fixed_bys[i],

                company_info_shared=company_info_shareds[i],

                meeting_fixed=meeting_fixeds[i],

                date_of_meeting=history_meeting_date,

                mode_of_meeting=meeting_modes[i],

                meeting_status=meeting_statuses[i],

                meeting_conducted_by=meeting_conducted_bys[i],

                floor_plan_shared=floor_plan_shareds[i],

                site_visit=site_visits[i],

                post_meeting_mail=post_meeting_mails[i],

                date_of_last_followup=history_last_followup,

                date_to_call_next=history_next_call,

                reschedule_date=history_reschedule,

                reason_for_reschedule=reasons[i],

                remarks=remarks_list[i],

                final_remarks=final_remarks_list[i],

                record_owner=session[
                    'username'
                ]

            )

            db.session.add(

                history

            )

        log_activity(

            'MEETING',

            meeting.meeting_id,

            'CREATED'

        )

        db.session.commit()

        return redirect(

            url_for(

                'add_meeting'

            )

        )
    search = request.args.get(

        'search'

    )

    if session.get(

        'role'

    ) == 'SALES':

        base_query = Meeting.query.filter_by(

            record_owner=session[
                'username'
            ]

        )

    elif session.get(

        'role'

    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(

            role='COMMERCIALS'

        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        base_query = Meeting.query.filter(

            Meeting.record_owner.in_(

                usernames

            )

        )

    else:

        base_query = Meeting.query

    if search:

        base_query = base_query.filter(

            or_(

                Meeting.firm_name.ilike(

                    f'%{search}%'

                ),

                Meeting.name.ilike(

                    f'%{search}%'

                ),

                Meeting.contact_no.ilike(

                    f'%{search}%'

                ),

                Meeting.reference.ilike(

                    f'%{search}%'

                ),

                Meeting.source.ilike(

                    f'%{search}%'

                ),

                Meeting.email.ilike(

                    f'%{search}%'

                ),

                Meeting.meeting_status.ilike(

                    f'%{search}%'

                )

            )

        )

    all_meetings = base_query.order_by(

        Meeting.date_of_meeting.desc()

    ).all()        
    if session.get(

        'role'

    ) == 'SALES':

        all_leads = Lead.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(

        'role'

    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(

            role='COMMERCIALS'

        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        all_leads = Lead.query.filter(

            Lead.record_owner.in_(

                usernames

            )

        ).all()

    else:

        all_leads = Lead.query.all()

    return render_template(

        'add_meeting.html',

        meetings=all_meetings,

        leads=all_leads,

        admin_view=session.get(

            'role'

        ) == 'ADMIN'

    )

@app.route('/delete-meeting/<int:meeting_id>')
def delete_meeting(meeting_id):

    if not has_access('ADMIN'):
        return redirect(url_for('dashboard'))

    meeting = Meeting.query.get_or_404(meeting_id)

    try:
        db.session.delete(meeting)

        log_activity(
            'MEETING',
            meeting_id,
            'DELETED'
        )

        db.session.commit()

        flash(
            'Meeting deleted successfully.',
            'success'
        )

    except Exception:

        db.session.rollback()

        flash(
            'Cannot delete this Meeting because it is linked with other records.',
            'danger'
        )

    return redirect(
        url_for('add_meeting')
    )

@app.route(
    '/meeting-history/<int:history_id>'
)
def meeting_history_details(
    history_id
):

    if not has_access(

        'ADMIN',
        'COMMERCIALS',
        'SALES'

    ):

        return redirect(

            url_for(
                'dashboard'
            )

        )

    history = MeetingHistory.query.get_or_404(

        history_id

    )

    meeting = Meeting.query.get_or_404(

        history.meeting_id

    )

    if not can_view_record(

        meeting.record_owner

    ):

        return redirect(

            url_for(
                'dashboard'
            )

        )

    return render_template(

        'meeting_history_details.html',

        history=history,

        meeting=meeting

    )

@app.route('/meeting/<int:meeting_id>')
def meeting_details(meeting_id):

    if not has_access(
        'ADMIN',
        'COMMERCIALS',
        'SALES'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    meeting = Meeting.query.get_or_404(
        meeting_id
    )

    history = MeetingHistory.query.filter_by(

        meeting_id=meeting_id

    ).order_by(

        MeetingHistory.date_of_meeting.desc()

    ).all()

    if not can_view_record(

        meeting.record_owner

    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    

    return render_template(

        'meeting_details.html',

        meeting=meeting,

        history=history

    )

@app.route(
    '/edit-meeting/<int:meeting_id>',
    methods=['GET', 'POST']
)
def edit_meeting(

    meeting_id

):

    if not has_access(

        'ADMIN',
        'COMMERCIALS',
        'SALES'

    ):

        return redirect(

            url_for(

                'dashboard'

            )

        )

    meeting = Meeting.query.get_or_404(

        meeting_id

    )

    if not can_access_record(

        meeting.record_owner

    ):

        return redirect(

            url_for(

                'dashboard'

            )

        )

    history = MeetingHistory.query.filter_by(

        meeting_id=meeting_id

    ).order_by(

        MeetingHistory.date_of_meeting.desc()

    ).all()

    history_id = request.args.get(

        'history_id',

        type=int

    )

    editing_record = meeting

    if history_id:

        editing_record = MeetingHistory.query.get_or_404(

            history_id

        )

    if session.get(

        'role'

    ) == 'SALES':

        all_leads = Lead.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(

        'role'

    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(

            role='COMMERCIALS'

        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        all_leads = Lead.query.filter(

            Lead.record_owner.in_(

                usernames

            )

        ).all()

    else:

        all_leads = Lead.query.all()

    if request.method == 'POST':
        action = request.form.get(

            'action'

        )

        delete_history_id = request.form.get(

            'delete_history'

        )

        if action == 'delete_current':

            if session.get(

                'role'

            ) == 'ADMIN':

                db.session.delete(

                    meeting

                )

                log_activity(

                    'MEETING',

                    meeting.meeting_id,

                    'DELETED'

                )

                db.session.commit()

                flash(

                    'Meeting deleted successfully.',

                    'success'

                )

                return redirect(

                    url_for(

                        'add_meeting'

                    )

                )

            delete_request = DeleteRequest(

                module_name='MEETING',

                record_id=meeting.meeting_id,

                requested_by=session[
                    'username'
                ],

                reason='Requested from Edit Meeting'

            )

            db.session.add(

                delete_request

            )

            log_activity(

                'MEETING',

                meeting.meeting_id,

                'DELETE REQUESTED',

                'Requested from Edit Meeting'

            )

            db.session.commit()

            flash(

                'Delete request sent to Admin.',

                'info'

            )

            return redirect(

                url_for(

                    'edit_meeting',

                    meeting_id=meeting.meeting_id

                )

            )


        company_details = {

            'source': request.form.get(

                'source'

            ),

            'reference': request.form.get(

                'reference'

            ),

            'firm_name': request.form.get(

                'firm_name'

            ),

            'address': request.form.get(

                'address'

            ),

            'state': request.form.get(

                'state'

            )

        }

        edited_meeting = {

            'name': request.form.get(

                'name'

            ),

            'designation': request.form.get(

                'designation'

            ),

            'contact_no': request.form.get(

                'contact_no'

            ),

            'email': request.form.get(

                'email'

            ),

            'meeting_fixed_by': request.form.get(

                'meeting_fixed_by'

            ),

            'company_info_shared': request.form.get(

                'company_info_shared'

            ),

            'meeting_fixed': request.form.get(

                'meeting_fixed'

            ),

            'date_of_meeting': (

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

            ),

            'mode_of_meeting': request.form.get(

                'mode_of_meeting'

            ),

            'meeting_status': request.form.get(

                'meeting_status'

            ),

            'meeting_conducted_by': request.form.get(

                'meeting_conducted_by'

            ),

            'floor_plan_shared': request.form.get(

                'floor_plan_shared'

            ),

            'site_visit': request.form.get(

                'site_visit'

            ),

            'post_meeting_mail': request.form.get(

                'post_meeting_mail'

            ),

            'date_of_last_followup': (

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

            ),

            'date_to_call_next': (

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

            ),

            'reschedule_date': (

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

            ),

            'reason_for_reschedule': request.form.get(

                'reason_for_reschedule'

            ),

            'final_remarks': request.form.get(

                'final_remarks'

            ),

            'remarks': request.form.get(

                'remarks'

            )

        }
        meeting_list = []

        if history_id:

            meeting_list.append(

                edited_meeting

            )

            current_record = {

                'name': meeting.name,

                'designation': meeting.designation,

                'contact_no': meeting.contact_no,

                'email': meeting.email,

                'meeting_fixed_by': meeting.meeting_fixed_by,

                'company_info_shared': meeting.company_info_shared,

                'meeting_fixed': meeting.meeting_fixed,

                'date_of_meeting': meeting.date_of_meeting,

                'mode_of_meeting': meeting.mode_of_meeting,

                'meeting_status': meeting.meeting_status,

                'meeting_conducted_by': meeting.meeting_conducted_by,

                'floor_plan_shared': meeting.floor_plan_shared,

                'site_visit': meeting.site_visit,

                'post_meeting_mail': meeting.post_meeting_mail,

                'date_of_last_followup': meeting.date_of_last_followup,

                'date_to_call_next': meeting.date_to_call_next,

                'reschedule_date': meeting.reschedule_date,

                'reason_for_reschedule': meeting.reason_for_reschedule,

                'final_remarks': meeting.final_remarks,

                'remarks': meeting.remarks

            }

            meeting_list.append(

                current_record

            )

        else:

            meeting_list.append(

                edited_meeting

            )

        existing_history = MeetingHistory.query.filter_by(

            meeting_id=meeting.meeting_id

        ).all()

        for item in existing_history:

            if history_id and item.history_id == history_id:

                continue

            meeting_list.append(

                {

                    'name': item.name,

                    'designation': item.designation,

                    'contact_no': item.contact_no,

                    'email': item.email,

                    'meeting_fixed_by': item.meeting_fixed_by,

                    'company_info_shared': item.company_info_shared,

                    'meeting_fixed': item.meeting_fixed,

                    'date_of_meeting': item.date_of_meeting,

                    'mode_of_meeting': item.mode_of_meeting,

                    'meeting_status': item.meeting_status,

                    'meeting_conducted_by': item.meeting_conducted_by,

                    'floor_plan_shared': item.floor_plan_shared,

                    'site_visit': item.site_visit,

                    'post_meeting_mail': item.post_meeting_mail,

                    'date_of_last_followup': item.date_of_last_followup,

                    'date_to_call_next': item.date_to_call_next,

                    'reschedule_date': item.reschedule_date,

                    'reason_for_reschedule': item.reason_for_reschedule,

                    'final_remarks': item.final_remarks,

                    'remarks': item.remarks

                }

            )

        new_names = request.form.getlist(

            'new_name[]'

        )

        new_designations = request.form.getlist(

            'new_designation[]'

        )

        new_contacts = request.form.getlist(

            'new_contact_no[]'

        )

        new_emails = request.form.getlist(

            'new_email[]'

        )

        new_meeting_fixed_bys = request.form.getlist(

            'new_meeting_fixed_by[]'

        )

        new_company_info_shareds = request.form.getlist(

            'new_company_info_shared[]'

        )

        new_meeting_fixeds = request.form.getlist(

            'new_meeting_fixed[]'

        )

        new_dates = request.form.getlist(

            'new_date_of_meeting[]'

        )

        new_modes = request.form.getlist(

            'new_mode_of_meeting[]'

        )

        new_statuses = request.form.getlist(

            'new_meeting_status[]'

        )

        new_conducted_bys = request.form.getlist(

            'new_meeting_conducted_by[]'

        )

        new_floor_plan_shareds = request.form.getlist(

            'new_floor_plan_shared[]'

        )

        new_site_visits = request.form.getlist(

            'new_site_visit[]'

        )

        new_post_meeting_mails = request.form.getlist(

            'new_post_meeting_mail[]'

        )

        new_last_followups = request.form.getlist(

            'new_date_of_last_followup[]'

        )

        new_next_calls = request.form.getlist(

            'new_date_to_call_next[]'

        )

        new_reschedule_dates = request.form.getlist(

            'new_reschedule_date[]'

        )

        new_reason_for_reschedules = request.form.getlist(

            'new_reason_for_reschedule[]'

        )

        new_final_remarks = request.form.getlist(

            'new_final_remarks[]'

        )

        new_remarks = request.form.getlist(

            'new_remarks[]'

        )

        for i in range(

            len(

                new_names

            )

        ):

            if not new_names[i].strip():

                continue

            meeting_list.append(

                {

                    'name': new_names[i],

                    'designation': new_designations[i],

                    'contact_no': new_contacts[i],

                    'email': new_emails[i],

                    'meeting_fixed_by': new_meeting_fixed_bys[i],

                    'company_info_shared': new_company_info_shareds[i],

                    'meeting_fixed': new_meeting_fixeds[i],

                    'date_of_meeting': (

                        datetime.strptime(

                            new_dates[i],

                            '%Y-%m-%d'

                        ).date()

                        if new_dates[i]

                        else None

                    ),

                    'mode_of_meeting': new_modes[i],

                    'meeting_status': new_statuses[i],

                    'meeting_conducted_by': new_conducted_bys[i],

                    'floor_plan_shared': new_floor_plan_shareds[i],

                    'site_visit': new_site_visits[i],

                    'post_meeting_mail': new_post_meeting_mails[i],

                    'date_of_last_followup': (

                        datetime.strptime(

                            new_last_followups[i],

                            '%Y-%m-%d'

                        ).date()

                        if new_last_followups[i]

                        else None

                    ),

                    'date_to_call_next': (

                        datetime.strptime(

                            new_next_calls[i],

                            '%Y-%m-%d'

                        ).date()

                        if new_next_calls[i]

                        else None

                    ),

                    'reschedule_date': (

                        datetime.strptime(

                            new_reschedule_dates[i],

                            '%Y-%m-%d'

                        ).date()

                        if new_reschedule_dates[i]

                        else None

                    ),

                    'reason_for_reschedule': new_reason_for_reschedules[i],

                    'final_remarks': new_final_remarks[i],

                    'remarks': new_remarks[i]

                }

            )
        meeting_list.sort(

            key=lambda x: (

                x['date_of_meeting']

                if x['date_of_meeting']

                else date.min

            ),

            reverse=True

        )

        latest = meeting_list.pop(

            0

        )

        for field, value in company_details.items():

            setattr(

                meeting,

                field,

                value

            )

        for field, value in latest.items():

            setattr(

                meeting,

                field,

                value

            )

        MeetingHistory.query.filter_by(

            meeting_id=meeting.meeting_id

        ).delete(

            synchronize_session=False

        )

        for item in meeting_list:

            db.session.add(

                MeetingHistory(

                    meeting_id=meeting.meeting_id,

                    name=item['name'],

                    designation=item['designation'],

                    contact_no=item['contact_no'],

                    email=item['email'],

                    meeting_fixed_by=item['meeting_fixed_by'],

                    company_info_shared=item['company_info_shared'],

                    meeting_fixed=item['meeting_fixed'],

                    date_of_meeting=item['date_of_meeting'],

                    mode_of_meeting=item['mode_of_meeting'],

                    meeting_status=item['meeting_status'],

                    meeting_conducted_by=item['meeting_conducted_by'],

                    floor_plan_shared=item['floor_plan_shared'],

                    site_visit=item['site_visit'],

                    post_meeting_mail=item['post_meeting_mail'],

                    date_of_last_followup=item['date_of_last_followup'],

                    date_to_call_next=item['date_to_call_next'],

                    reschedule_date=item['reschedule_date'],

                    reason_for_reschedule=item['reason_for_reschedule'],

                    final_remarks=item['final_remarks'],

                    remarks=item['remarks'],

                    record_owner=meeting.record_owner

                )

            )

        log_activity(

            'MEETING',

            meeting.meeting_id,

            'UPDATED'

        )

        db.session.commit()

        return redirect(

            url_for(

                'edit_meeting',

                meeting_id=meeting.meeting_id

            )

        )

    return render_template(

        'edit_meeting.html',

        meeting=meeting,

        editing_record=editing_record,

        history=history,

        leads=all_leads

    )

@app.route(
    '/request-delete-meeting/<int:meeting_id>',
    methods=['GET', 'POST']
)
def request_delete_meeting(meeting_id):

    meeting = Meeting.query.get_or_404(
        meeting_id
    )

    # ADMIN -> DELETE DIRECTLY
    if session.get(
        'role'
    ) == 'ADMIN':

        try:

            db.session.delete(
                meeting
            )

            db.session.flush()

            log_activity(

                'MEETING',

                meeting_id,

                'DELETED'

            )

            db.session.commit()

            flash(

                'Meeting deleted successfully.'

            )

        except Exception:

            db.session.rollback()

            flash(

                'Cannot delete this Meeting because it is linked with other records.'

            )

        return redirect(

            url_for(
                'add_meeting'
            )

        )

    # EMPLOYEE -> DELETE REQUEST
    if request.method == 'POST':

        delete_request = DeleteRequest(

            module_name='MEETING',

            record_id=meeting_id,

            requested_by=session[
                'username'
            ],

            reason=request.form.get(
                'reason'
            )

        )

        db.session.add(
            delete_request
        )

        db.session.flush()

        log_activity(

            'MEETING',

            meeting_id,

            'DELETE REQUESTED',

            request.form.get(
                'reason'
            )

        )

        db.session.commit()

        flash(
            'Delete request sent.'
        )

        return redirect(

            url_for(
                'add_meeting'
            )

        )

    return render_template(

        'delete_request.html',

        module='MEETING',

        record_id=meeting_id

    )

@app.route(

    '/add-visit',

    methods=['GET', 'POST']

)
def add_visit():

    if not has_access(

        'ADMIN',

        'COMMERCIALS',

        'SALES'

    ):

        return redirect(

            url_for(

                'dashboard'

            )

        )

    if session.get(

        'role'

    ) == 'SALES':

        meetings = Meeting.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

        visits = Visit.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).order_by(

            Visit.visit_date.desc()

        ).all()

    elif session.get(

        'role'

    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(

            role='COMMERCIALS'

        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        meetings = Meeting.query.filter(

            Meeting.record_owner.in_(

                usernames

            )

        ).all()

        visits = Visit.query.filter(

            Visit.record_owner.in_(

                usernames

            )

        ).order_by(

            Visit.visit_date.desc()

        ).all()

    else:

        meetings = Meeting.query.order_by(

            Meeting.date_of_meeting.desc()

        ).all()

        visits = Visit.query.order_by(

            Visit.visit_date.desc()

        ).all()

    if request.method == 'POST':

        # ===========================
        # COMPANY DETAILS
        # ===========================

        meeting_id = request.form.get(

            'meeting_id'

        )

        company_name = request.form.get(

            'company_name'

        )

        address = request.form.get(

            'address'

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

        # ===========================
        # ALL VISIT RECORDS
        # ===========================

        person_names = request.form.getlist(

            'person_name[]'

        )

        designations = request.form.getlist(

            'designation[]'

        )

        contact_numbers = request.form.getlist(

            'contact_no[]'

        )

        briefs = request.form.getlist(

            'brief[]'

        )

        visit_dates = request.form.getlist(

            'visit_date[]'

        )

        leads_generated_list = request.form.getlist(

            'leads_generated[]'

        )

        # ===========================
        # CREATE MASTER VISIT
        # ===========================

        first_visit_date = None

        if visit_dates[0]:

            first_visit_date = datetime.strptime(

                visit_dates[0],

                '%Y-%m-%d'

            ).date()
        meeting = Meeting.query.get_or_404(

            meeting_id

        )

        visit = Visit(

            meeting_id=meeting.meeting_id,

            state=state,

            region=region,

            abc=abc,

            company_name=company_name,

            person_name=person_names[0],

            designation=designations[0],

            contact_no=contact_numbers[0],

            address=address,

            brief=briefs[0],

            visit_date=first_visit_date,

            leads_generated=(

                int(

                    leads_generated_list[0]

                )

                if leads_generated_list[0]

                else 0

            ),

            m2=None,

            m3=None,

            record_owner=session[

                'username'

            ]

        )

        db.session.add(

            visit

        )

        db.session.flush()

        # ===========================
        # SAVE ADDITIONAL VISITS
        # ===========================

        for i in range(

            1,

            len(

                person_names

            )

        ):

            history_visit_date = None

            if visit_dates[i]:

                history_visit_date = datetime.strptime(

                    visit_dates[i],

                    '%Y-%m-%d'

                ).date()

            history = VisitHistory(

                visit_id=visit.visit_id,

                meeting_id=meeting.meeting_id,

                state=state,

                region=region,

                abc=abc,

                company_name=company_name,

                person_name=person_names[i],

                designation=designations[i],

                contact_no=contact_numbers[i],

                address=address,

                brief=briefs[i],

                visit_date=history_visit_date,

                leads_generated=(

                    int(

                        leads_generated_list[i]

                    )

                    if leads_generated_list[i]

                    else 0

                ),

                record_owner=session[

                    'username'

                ]

            )

            db.session.add(

                history

            )
        log_activity(

            'VISIT',

            visit.visit_id,

            'CREATED'

        )

        db.session.commit()

        flash(

            'Visit added successfully.',

            'success'

        )

        return redirect(

            url_for(

                'add_visit'

            )

        )

    search = request.args.get(

        'search'

    )

    if search:

        visits = [

            visit

            for visit in visits

            if (

                search.lower() in (visit.company_name or '').lower()

                or search.lower() in (visit.person_name or '').lower()

                or search.lower() in (visit.contact_no or '').lower()

                or search.lower() in (visit.region or '').lower()

                or search.lower() in (visit.state or '').lower()

            )

        ]

    return render_template(

        'add_visit.html',

        visits=visits,

        meetings=meetings,

        admin_view=session.get(

            'role'

        ) == 'ADMIN'

    )

@app.route(
    '/visit/<int:visit_id>'
)
def visit_details(visit_id):

    if not has_access(

        'ADMIN',

        'SALES',

        'COMMERCIALS'

    ):

        return redirect(

            url_for(

                'dashboard'

            )

        )

    visit = Visit.query.get_or_404(

        visit_id

    )

    if not can_view_record(

        visit.record_owner

    ):

        return redirect(

            url_for(

                'dashboard'

            )

        )

    history = VisitHistory.query.filter_by(

        visit_id=visit.visit_id

    ).order_by(

        VisitHistory.visit_date.desc()

    ).all()

    return render_template(

        'visit_details.html',

        visit=visit,

        history=history

    )

@app.route(

    '/edit-visit/<int:visit_id>',

    methods=['GET', 'POST']

)
def edit_visit(

    visit_id

):

    if not has_access(

        'ADMIN',

        'COMMERCIALS',

        'SALES'

    ):

        return redirect(

            url_for(

                'dashboard'

            )

        )

    visit = Visit.query.get_or_404(

        visit_id

    )

    if not can_access_record(

        visit.record_owner

    ):

        return redirect(

            url_for(

                'dashboard'

            )

        )

    history_id = request.args.get(

        'history_id',

        type=int

    )

    history = VisitHistory.query.filter_by(

        visit_id=visit.visit_id

    ).order_by(

        VisitHistory.visit_date.desc()

    ).all()

    editing_record = visit

    if history_id:

        editing_record = VisitHistory.query.get_or_404(

            history_id

        )

    if session.get(

        'role'

    ) == 'SALES':

        all_meetings = Meeting.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(

        'role'

    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(

            role='COMMERCIALS'

        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        all_meetings = Meeting.query.filter(

            Meeting.record_owner.in_(

                usernames

            )

        ).all()

    else:

        all_meetings = Meeting.query.all()

    if request.method == 'POST':

        action = request.form.get(

            'action'

        )

        delete_history_id = request.form.get(

            'delete_history'

        )

        static_data = {

            'meeting_id': request.form.get(

                'meeting_id'

            ),

            'company_name': request.form.get(

                'company_name'

            ),

            'address': request.form.get(

                'address'

            ),

            'state': request.form.get(

                'state'

            ),

            'region': request.form.get(

                'region'

            ),

            'abc': request.form.get(

                'abc'

            )

        }

        current_visit = {

            'person_name': request.form.get(

                'person_name'

            ),

            'designation': request.form.get(

                'designation'

            ),

            'contact_no': request.form.get(

                'contact_no'

            ),

            'brief': request.form.get(

                'brief'

            ),

            'visit_date': (

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

            ),

            'leads_generated': (

                int(

                    request.form.get(

                        'leads_generated'

                    ) or 0

                )

            )

        }

        if action == 'delete_current':

            if session.get(

                'role'

            ) == 'ADMIN':

                db.session.delete(

                    visit

                )

                log_activity(

                    'VISIT',

                    visit.visit_id,

                    'DELETED'

                )

                db.session.commit()

                flash(

                    'Visit deleted successfully.',

                    'success'

                )

                return redirect(

                    url_for(

                        'add_visit'

                    )

                )

            delete_request = DeleteRequest(

                module_name='VISIT',

                record_id=visit.visit_id,

                requested_by=session[
                    'username'
                ],

                reason='Requested from Edit Visit'

            )

            db.session.add(

                delete_request

            )

            log_activity(

                'VISIT',

                visit.visit_id,

                'DELETE REQUESTED',

                'Requested from Edit Visit'

            )

            db.session.commit()

            flash(

                'Delete request sent to Admin.',

                'info'

            )

            return redirect(

                url_for(

                    'edit_visit',

                    visit_id=visit.visit_id

                )

            )

        if delete_history_id:

            history_record = VisitHistory.query.get_or_404(

                delete_history_id

            )

            if session.get(

                'role'

            ) == 'ADMIN':

                db.session.delete(

                    history_record

                )

                log_activity(

                    'VISIT_HISTORY',

                    history_record.history_id,

                    'DELETED'

                )

                db.session.commit()

                flash(

                    'Visit history deleted successfully.',

                    'success'

                )

            else:

                delete_request = DeleteRequest(

                    module_name='VISIT_HISTORY',

                    record_id=history_record.history_id,

                    requested_by=session[
                        'username'
                    ],

                    reason='Requested from Edit Visit'

                )

                db.session.add(

                    delete_request

                )

                log_activity(

                    'VISIT_HISTORY',

                    history_record.history_id,

                    'DELETE REQUESTED'

                )

                db.session.commit()

                flash(

                    'Delete request sent to Admin.',

                    'info'

                )

            return redirect(

                url_for(

                    'edit_visit',

                    visit_id=visit.visit_id

                )

            )

        existing_history = VisitHistory.query.filter_by(

            visit_id=visit.visit_id

        ).all()

        visit_list = [

            current_visit

        ]

        for item in existing_history:

            visit_list.append({

                'person_name': item.person_name,

                'designation': item.designation,

                'contact_no': item.contact_no,

                'brief': item.brief,

                'visit_date': item.visit_date,

                'leads_generated': item.leads_generated

            })

        new_person_name = request.form.getlist(

            'new_person_name[]'

        )

        new_designation = request.form.getlist(

            'new_designation[]'

        )

        new_contact_no = request.form.getlist(

            'new_contact_no[]'

        )

        new_brief = request.form.getlist(

            'new_brief[]'

        )

        new_visit_date = request.form.getlist(

            'new_visit_date[]'

        )

        new_leads_generated = request.form.getlist(

            'new_leads_generated[]'

        )

        for i in range(

            len(

                new_person_name

            )

        ):

            if not (

                new_person_name[i]

                or new_visit_date[i]

            ):

                continue

            visit_list.append({

                'person_name': new_person_name[i],

                'designation': new_designation[i],

                'contact_no': new_contact_no[i],

                'brief': new_brief[i],

                'visit_date': (

                    datetime.strptime(

                        new_visit_date[i],

                        '%Y-%m-%d'

                    ).date()

                    if new_visit_date[i]

                    else None

                ),

                'leads_generated': (

                    int(

                        new_leads_generated[i]

                        or 0

                    )

                )

            })

        visit_list = [

            item

            for item in visit_list

            if item.get(

                'visit_date'

            )

        ]

        visit_list.sort(

            key=lambda x: x.get(

                'visit_date'

            ),

            reverse=True

        )

        if not visit_list:

            flash(

                'At least one visit is required.',

                'danger'

            )

            return redirect(

                url_for(

                    'edit_visit',

                    visit_id=visit.visit_id

                )

            )

        latest_visit = visit_list[0]

        visit.meeting_id = static_data['meeting_id']

        visit.company_name = static_data['company_name']

        visit.address = static_data['address']

        visit.state = static_data['state']

        visit.region = static_data['region']

        visit.abc = static_data['abc']

        visit.person_name = latest_visit['person_name']

        visit.designation = latest_visit['designation']

        visit.contact_no = latest_visit['contact_no']

        visit.brief = latest_visit['brief']

        visit.visit_date = latest_visit['visit_date']

        visit.leads_generated = latest_visit['leads_generated']

        db.session.query(

            VisitHistory

        ).filter_by(

            visit_id=visit.visit_id

        ).delete()

        for item in visit_list[1:]:

            history = VisitHistory(

                visit_id=visit.visit_id,

                meeting_id=visit.meeting_id,

                company_name=visit.company_name,

                address=visit.address,

                state=visit.state,

                region=visit.region,

                abc=visit.abc,

                person_name=item['person_name'],

                designation=item['designation'],

                contact_no=item['contact_no'],

                brief=item['brief'],

                visit_date=item['visit_date'],

                leads_generated=item['leads_generated'],

                record_owner=visit.record_owner

            )

            db.session.add(

                history

            )

        log_activity(

            'VISIT',

            visit.visit_id,

            'UPDATED'

        )

        db.session.commit()

        flash(

            'Visit updated successfully.',

            'success'

        )

        return redirect(

            url_for(

                'edit_visit',

                visit_id=visit.visit_id

            )

        )

    return render_template(

        'edit_visit.html',

        visit=visit,

        editing_record=editing_record,

        history=history,

        meetings=all_meetings

    )

@app.route(
    '/request-delete-visit/<int:visit_id>',
    methods=['GET', 'POST']
)
def request_delete_visit(visit_id):

    visit = Visit.query.get_or_404(
        visit_id
    )

    # ADMIN -> DELETE DIRECTLY
    if session.get(
        'role'
    ) == 'ADMIN':

        try:

            db.session.delete(
                visit
            )

            db.session.flush()

            log_activity(

                'VISIT',

                visit_id,

                'DELETED'

            )

            db.session.commit()

            flash(

                'Visit deleted successfully.'

            )

        except Exception:

            db.session.rollback()

            flash(

                'Cannot delete this Visit because it is linked with other records.'

            )

        return redirect(

            url_for(
                'add_visit'
            )

        )

    # EMPLOYEE -> DELETE REQUEST
    if request.method == 'POST':

        delete_request = DeleteRequest(

            module_name='VISIT',

            record_id=visit_id,

            requested_by=session[
                'username'
            ],

            reason=request.form.get(
                'reason'
            )

        )

        db.session.add(
            delete_request
        )

        db.session.flush()

        log_activity(

            'VISIT',

            visit_id,

            'DELETE REQUESTED',

            request.form.get(
                'reason'
            )

        )

        db.session.commit()

        flash(
            'Delete request sent.'
        )

        return redirect(

            url_for(
                'add_visit'
            )

        )

    return render_template(

        'delete_request.html',

        module='VISIT',

        record_id=visit_id

    )

@app.route('/add-drawing',
           methods=['GET','POST'])
def add_drawing():
    if not has_access(
        'ADMIN',
        'SALES',
        'COMMERCIALS'
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

        

        drawing = Drawing(

            visit_id=visit_id,

            name=name,

            address=address,

            iterations=iterations,

            moca=moca,

            
            record_owner=session[
                'username'
            ]    
        )

        db.session.add(
            drawing
        )
        db.session.flush()
        drawing_files = request.files.getlist(
            'drawing_files'
        )

        for file in drawing_files:

            if file and file.filename:

                filename = secure_filename(
                    file.filename
                )

                relative_path = (
                    'drawings/' +
                    filename
                )

                file.save(

                    os.path.join(

                        app.config[
                            'UPLOAD_FOLDER'
                        ],

                        relative_path

                    )

                )

                drawing_file = DrawingFile(

                    drawing_id=
                    drawing.drawing_id,

                    file_name=filename,

                    file_path=relative_path,

                    file_type=file.content_type

                )

                db.session.add(
                    drawing_file
                )
        log_activity(

            'DRAWING',

            drawing.drawing_id,

            'CREATED'

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
    if session.get(
        'role'
    ) == 'SALES':

        base_query = Drawing.query.filter_by(

            record_owner=session[
                'username'
            ]

        )

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(

            role='COMMERCIALS'

        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        base_query = Drawing.query.filter(

            Drawing.record_owner.in_(
                usernames
            )

        )

    else:

        base_query = Drawing.query

    if search:

        all_drawings = base_query.filter(

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

        all_drawings = base_query.all()

    if session.get(
        'role'
    ) == 'SALES':

        all_visits = Visit.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(

            role='COMMERCIALS'

        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        all_visits = Visit.query.filter(

            Visit.record_owner.in_(
                usernames
            )

        ).all()

    else:

        all_visits = Visit.query.all()

    return render_template(
        'add_drawing.html',
        drawings=all_drawings,
        visits=all_visits,
        admin_view=session.get(
            'role'
        ) == 'ADMIN'
    )

@app.route('/drawing/<int:drawing_id>')
def drawing_details(drawing_id):
    if not has_access(
        'ADMIN',
        'SALES',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    drawing = Drawing.query.get_or_404(
        drawing_id
    )
    if not can_view_record(
        drawing.record_owner
    ):

        return redirect(
            url_for(
                'dashboard'
            )
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
        'SALES',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    drawing = Drawing.query.get_or_404(
        drawing_id
    )
    if not can_access_record(

        drawing.record_owner

    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )
    

    if session.get(
        'role'
    ) == 'SALES':

        all_visits = Visit.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(

            role='COMMERCIALS'

        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        all_visits = Visit.query.filter(

            Visit.record_owner.in_(
                usernames
            )

        ).all()

    else:

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

        drawing_files = request.files.getlist(
            'drawing_files'
        )

        for file in drawing_files:

            if file and file.filename:

                filename = secure_filename(
                    file.filename
                )

                relative_path = (
                    'drawings/' +
                    filename
                )

                file.save(

                    os.path.join(

                        app.config[
                            'UPLOAD_FOLDER'
                        ],

                        relative_path

                    )

                )

                new_file = DrawingFile(

                    drawing_id=
                    drawing.drawing_id,

                    file_name=filename,

                    file_path=relative_path,

                    file_type=file.content_type

                )

                db.session.add(
                    new_file
                )
        db.session.flush()
        log_activity(

            'DRAWING',

            drawing.drawing_id,

            'UPDATED'

        )  
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
    '/request-delete-drawing/<int:drawing_id>',
    methods=['GET', 'POST']
)
def request_delete_drawing(drawing_id):

    drawing = Drawing.query.get_or_404(
        drawing_id
    )

    # ADMIN -> DELETE DIRECTLY
    if session.get(
        'role'
    ) == 'ADMIN':

        try:

            db.session.delete(
                drawing
            )

            db.session.flush()

            log_activity(

                'DRAWING',

                drawing_id,

                'DELETED'

            )

            db.session.commit()

            flash(

                'Drawing deleted successfully.'

            )

        except Exception:

            db.session.rollback()

            flash(

                'Cannot delete this Drawing because it is linked with other records.'

            )

        return redirect(

            url_for(
                'add_drawing'
            )

        )

    # EMPLOYEE -> DELETE REQUEST
    if request.method == 'POST':

        delete_request = DeleteRequest(

            module_name='DRAWING',

            record_id=drawing_id,

            requested_by=session[
                'username'
            ],

            reason=request.form.get(
                'reason'
            )

        )

        db.session.add(
            delete_request
        )

        db.session.flush()

        log_activity(

            'DRAWING',

            drawing_id,

            'DELETE REQUESTED',

            request.form.get(
                'reason'
            )

        )

        db.session.commit()

        flash(
            'Delete request sent.'
        )

        return redirect(

            url_for(
                'add_drawing'
            )

        )

    return render_template(

        'delete_request.html',

        module='DRAWING',

        record_id=drawing_id

    )

@app.route(
    '/delete-drawing-file/<int:file_id>'
)
def delete_drawing_file(file_id):

    file_record = DrawingFile.query.get_or_404(
        file_id
    )

    drawing_id = file_record.drawing_id

    full_path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        file_record.file_path
    )

    if os.path.exists(full_path):
        os.remove(full_path)

    db.session.delete(file_record)
    db.session.commit()

    flash(
        'File deleted successfully.'
    )

    return redirect(
        url_for(
            'drawing_details',
            drawing_id=drawing_id
        )
    )

@app.route('/add-proposal',
            methods=['GET', 'POST'])
def add_proposal():

    if not has_access(
        'ADMIN',
        'COMMERCIALS',
        'SALES'
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

            
            record_owner=session[
                'username'
            ]    
        )

        db.session.add(
            proposal
        )
        db.session.flush()
        proposal_files = request.files.getlist(
            'proposal_files'
        )

        for file in proposal_files:

            if file and file.filename:

                filename = secure_filename(
                    file.filename
                )

                relative_path = (
                    'proposals/' +
                    filename
                )

                file.save(

                    os.path.join(

                        app.config[
                            'UPLOAD_FOLDER'
                        ],

                        relative_path

                    )

                )

                new_file = ProposalFile(

                    proposal_id=proposal.proposal_id,

                    file_name=filename,

                    file_path=relative_path,

                    file_type=file.content_type

                )

                db.session.add(
                    new_file
                )  
        log_activity(

            'PROPOSAL',

            proposal.proposal_id,

            'CREATED'

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
    if session.get(
        'role'
    ) == 'SALES':

        base_query = Proposal.query.filter_by(

            record_owner=session[
                'username'
            ]

        )

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(

            role='COMMERCIALS'

        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        base_query = Proposal.query.filter(

            Proposal.record_owner.in_(
                usernames
            )

        )

    else:

        base_query = Proposal.query

    if search:

        all_proposals = base_query.filter(

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

        all_proposals = base_query.all()
    if session.get(
        'role'
    ) == 'SALES':

        all_meetings = Meeting.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]

        all_meetings = Meeting.query.filter(
            Meeting.record_owner.in_(
                usernames
            )
        ).all()

    else:

        all_meetings = Meeting.query.all()
    if session.get(
        'role'
    ) == 'SALES':

        all_drawings = Drawing.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]

        all_drawings = Drawing.query.filter(
            Drawing.record_owner.in_(
                usernames
            )
        ).all()

    else:

        all_drawings = Drawing.query.all()
    return render_template(
        'add_proposal.html',
        proposals=all_proposals,
        meetings=all_meetings,
        drawings=all_drawings,
        admin_view=session.get(
            'role'
        ) == 'ADMIN'
    )

@app.route('/proposal/<int:proposal_id>')
def proposal_details(proposal_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    proposal = Proposal.query.get_or_404(
        proposal_id
    )
    if not can_view_record(

        proposal.record_owner

    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )
    return render_template(
        'proposal_details.html',
        proposal=proposal
    )

@app.route(
    '/edit-proposal/<int:proposal_id>',
    methods=['GET', 'POST']
)
def edit_proposal(proposal_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    proposal = Proposal.query.get_or_404(
        proposal_id
    )
    if not can_access_record(

        proposal.record_owner

    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )
    if session.get(
        'role'
    ) == 'SALES':

        all_meetings = Meeting.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]

        all_meetings = Meeting.query.filter(
            Meeting.record_owner.in_(
                usernames
            )
        ).all()

    else:

        all_meetings = Meeting.query.all()
    if session.get(
        'role'
    ) == 'SALES':

        all_drawings = Drawing.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]

        all_drawings = Drawing.query.filter(
            Drawing.record_owner.in_(
                usernames
            )
        ).all()

    else:

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

        proposal_files = request.files.getlist(
            'proposal_files'
        )

        for file in proposal_files:

            if file and file.filename:

                filename = secure_filename(
                    file.filename
                )

                relative_path = (
                    'proposals/' +
                    filename
                )

                file.save(

                    os.path.join(

                        app.config[
                            'UPLOAD_FOLDER'
                        ],

                        relative_path

                    )

                )

                new_file = ProposalFile(

                    proposal_id=
                    proposal.proposal_id,

                    file_name=filename,

                    file_path=relative_path,

                    file_type=file.content_type

                )

                db.session.add(
                    new_file
                )
        db.session.flush()
        log_activity(

            'PROPOSAL',

            proposal.proposal_id,

            'UPDATED'

        )          
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
    '/request-delete-proposal/<int:proposal_id>',
    methods=['GET', 'POST']
)
def request_delete_proposal(proposal_id):

    proposal = Proposal.query.get_or_404(
        proposal_id
    )

    # ADMIN -> DELETE DIRECTLY
    if session.get(
        'role'
    ) == 'ADMIN':

        try:

            db.session.delete(
                proposal
            )

            db.session.flush()

            log_activity(

                'PROPOSAL',

                proposal_id,

                'DELETED'

            )

            db.session.commit()

            flash(

                'Proposal deleted successfully.'

            )

        except Exception:

            db.session.rollback()

            flash(

                'Cannot delete this Proposal because it is linked with other records.'

            )

        return redirect(

            url_for(
                'add_proposal'
            )

        )

    # EMPLOYEE -> DELETE REQUEST
    if request.method == 'POST':

        delete_request = DeleteRequest(

            module_name='PROPOSAL',

            record_id=proposal_id,

            requested_by=session[
                'username'
            ],

            reason=request.form.get(
                'reason'
            )

        )

        db.session.add(
            delete_request
        )

        db.session.flush()

        log_activity(

            'PROPOSAL',

            proposal_id,

            'DELETE REQUESTED',

            request.form.get(
                'reason'
            )

        )

        db.session.commit()

        flash(
            'Delete request sent.'
        )

        return redirect(

            url_for(
                'add_proposal'
            )

        )

    return render_template(

        'delete_request.html',

        module='PROPOSAL',

        record_id=proposal_id

    )

@app.route(
    '/delete-proposal-file/<int:file_id>'
)
def delete_proposal_file(file_id):

    file_record = ProposalFile.query.get_or_404(
        file_id
    )

    proposal_id = file_record.proposal_id

    full_path = os.path.join(

        app.config[
            'UPLOAD_FOLDER'
        ],

        file_record.file_path

    )

    if os.path.exists(
        full_path
    ):

        os.remove(
            full_path
        )

    db.session.delete(
        file_record
    )

    db.session.commit()

    flash(

        'File deleted successfully.'

    )

    return redirect(

        url_for(

            'proposal_details',

            proposal_id=proposal_id

        )

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

            total_cmc=request.form.get('total_cmc'),
            record_owner=session[
                'username'
            ]    
        )

        db.session.add(
            sales
        )
        db.session.flush()
        log_activity(

            'SALES',

            sales.sales_id,

            'CREATED'

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
    if session.get(
        'role'
    ) == 'SALES':

        base_query = SalesPipeline.query.filter_by(

            record_owner=session[
                'username'
            ]

        )

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]

        base_query = SalesPipeline.query.filter(

            SalesPipeline.record_owner.in_(
                usernames
            )

        )

    else:

        base_query = SalesPipeline.query

    if search:

        all_sales = base_query.filter(

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

        all_sales = base_query.all()
    if session.get(
        'role'
    ) == 'SALES':

        all_proposals = Proposal.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]

        all_proposals = Proposal.query.filter(

            Proposal.record_owner.in_(
                usernames
            )

        ).all()

    else:

        all_proposals = Proposal.query.all()

    return render_template(

        'add_sales.html',

        sales=all_sales,

        proposals=all_proposals,

        admin_view=session.get(
            'role'
        ) == 'ADMIN'        

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
    if not can_view_record(

        sale.record_owner

    ):

        return redirect(
            url_for(
                'dashboard'
            )
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
    if not can_access_record(

        sales.record_owner

    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )
    if session.get(
        'role'
    ) == 'SALES':

        all_proposals = Proposal.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]

        all_proposals = Proposal.query.filter(

            Proposal.record_owner.in_(
                usernames
            )

        ).all()

    else:

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
        db.session.flush()
        log_activity(

            'SALES',

            sales.sales_id,

            'UPDATED'

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
    '/request-delete-sales/<int:sales_id>',
    methods=['GET', 'POST']
)
def request_delete_sales(sales_id):

    sales = SalesPipeline.query.get_or_404(
        sales_id
    )

    # ADMIN -> DELETE DIRECTLY
    if session.get(
        'role'
    ) == 'ADMIN':

        try:

            db.session.delete(
                sales
            )

            db.session.flush()

            log_activity(

                'SALES',

                sales_id,

                'DELETED'

            )

            db.session.commit()

            flash(

                'Sales record deleted successfully.'

            )

        except Exception:

            db.session.rollback()

            flash(

                'Cannot delete this Sales record because it is linked with other records.'

            )

        return redirect(

            url_for(
                'add_sales'
            )

        )

    # EMPLOYEE -> DELETE REQUEST
    if request.method == 'POST':

        delete_request = DeleteRequest(

            module_name='SALES',

            record_id=sales_id,

            requested_by=session[
                'username'
            ],

            reason=request.form.get(
                'reason'
            )

        )

        db.session.add(
            delete_request
        )

        db.session.flush()

        log_activity(

            'SALES',

            sales_id,

            'DELETE REQUESTED',

            request.form.get(
                'reason'
            )

        )

        db.session.commit()

        flash(
            'Delete request sent.'
        )

        return redirect(

            url_for(
                'add_sales'
            )

        )

    return render_template(

        'delete_request.html',

        module='SALES',

        record_id=sales_id

    )

@app.route('/add-invoice',
           methods=['GET','POST'])
def add_invoice():
    if not has_access(
        'ADMIN',
        'SALES',
        'COMMERCIALS'
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


            record_owner=session[
                'username'
            ]    
        )

        db.session.add(
            invoice
        )
        db.session.flush()
        invoice_files = request.files.getlist(
            'invoice_files'
        )

        for file in invoice_files:

            if file and file.filename:

                filename = secure_filename(
                    file.filename
                )

                relative_path = (
                    'invoices/' +
                    filename
                )

                file.save(

                    os.path.join(

                        app.config[
                            'UPLOAD_FOLDER'
                        ],

                        relative_path

                    )

                )

                new_file = InvoiceFile(

                    invoice_id=
                    invoice.invoice_id,

                    file_name=filename,

                    file_path=relative_path,

                    file_type=file.content_type

                )

                db.session.add(
                    new_file
                )
        log_activity(

            'INVOICE',

            invoice.invoice_id,

            'CREATED'

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
    if session.get(
        'role'
    ) == 'SALES':

        base_query = Invoice.query.filter_by(

            record_owner=session[
                'username'
            ]

        )

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]

        base_query = Invoice.query.filter(

            Invoice.record_owner.in_(
                usernames
            )

        )

    else:

        base_query = Invoice.query

    if search:

        all_invoices = base_query.filter(

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

        all_invoices = base_query.all()

    if session.get(
        'role'
    ) == 'SALES':

        all_sales = SalesPipeline.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]
    
        all_sales = SalesPipeline.query.filter(

            SalesPipeline.record_owner.in_(
                usernames
            )

        ).all()

    else:

        all_sales = SalesPipeline.query.all()

    return render_template(

        'add_invoice.html',

        invoices=all_invoices,

        sales=all_sales,

        admin_view=session.get(
            'role'
        ) == 'ADMIN'        

    )

@app.route('/invoice/<int:invoice_id>')
def invoice_details(invoice_id):
    if not has_access(
        'ADMIN',
        'SALES',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    invoice = Invoice.query.get_or_404(
        invoice_id
    )
    if not can_view_record(

        invoice.record_owner

    ):

        return redirect(
            url_for(
                'dashboard'
            )
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
        'SALES',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )
    invoice = Invoice.query.get_or_404(
        invoice_id
    )
    if not can_access_record(

        invoice.record_owner

    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )
    if session.get(
        'role'
    ) == 'SALES':

        all_sales = SalesPipeline.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]
    
        all_sales = SalesPipeline.query.filter(

            SalesPipeline.record_owner.in_(
                usernames
            )

        ).all()

    else:

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
        invoice_files = request.files.getlist(
            'invoice_files'
        )

        for file in invoice_files:

            if file and file.filename:

                filename = secure_filename(
                    file.filename
                )

                relative_path = (
                    'invoices/' +
                    filename
                )

                file.save(

                    os.path.join(

                        app.config[
                            'UPLOAD_FOLDER'
                        ],

                        relative_path

                    )

                )

                new_file = InvoiceFile(

                    invoice_id=
                    invoice.invoice_id,

                    file_name=filename,

                    file_path=relative_path,

                    file_type=file.content_type

                )

                db.session.add(
                    new_file
                )
        db.session.flush()
        log_activity(

            'INVOICE',

            invoice.invoice_id,

            'UPDATED'

        )  
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
    '/request-delete-invoice/<int:invoice_id>',
    methods=['GET', 'POST']
)
def request_delete_invoice(invoice_id):

    invoice = Invoice.query.get_or_404(
        invoice_id
    )

    # ADMIN -> DELETE DIRECTLY
    if session.get(
        'role'
    ) == 'ADMIN':

        try:

            db.session.delete(
                invoice
            )

            db.session.flush()

            log_activity(

                'INVOICE',

                invoice_id,

                'DELETED'

            )

            db.session.commit()

            flash(

                'Invoice deleted successfully.'

            )

        except Exception:

            db.session.rollback()

            flash(

                'Cannot delete this Invoice because it is linked with other records.'

            )

        return redirect(

            url_for(
                'add_invoice'
            )

        )

    # EMPLOYEE -> DELETE REQUEST
    if request.method == 'POST':

        delete_request = DeleteRequest(

            module_name='INVOICE',

            record_id=invoice_id,

            requested_by=session[
                'username'
            ],

            reason=request.form.get(
                'reason'
            )

        )

        db.session.add(
            delete_request
        )

        db.session.flush()

        log_activity(

            'INVOICE',

            invoice_id,

            'DELETE REQUESTED',

            request.form.get(
                'reason'
            )

        )

        db.session.commit()

        flash(
            'Delete request sent.'
        )

        return redirect(

            url_for(
                'add_invoice'
            )

        )

    return render_template(

        'delete_request.html',

        module='INVOICE',

        record_id=invoice_id

    )

@app.route(
    '/delete-invoice-file/<int:file_id>'
)
def delete_invoice_file(file_id):

    file_record = InvoiceFile.query.get_or_404(
        file_id
    )

    invoice_id = file_record.invoice_id

    full_path = os.path.join(

        app.config[
            'UPLOAD_FOLDER'
        ],

        file_record.file_path

    )

    if os.path.exists(
        full_path
    ):

        os.remove(
            full_path
        )

    db.session.delete(
        file_record
    )

    db.session.commit()

    flash(
        'File deleted successfully.'
    )

    return redirect(

        url_for(

            'invoice_details',

            invoice_id=invoice_id

        )

    )

@app.route(
    '/add-installation',
    methods=['GET', 'POST']
)
def add_installation():

    if not has_access(
        'ADMIN',
        'SALES',
        'COMMERCIALS'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    if request.method == 'POST':

        installation = Installation(

            sales_id=request.form.get(
                'sales_id'
            ),

            installation_for=request.form.get(
                'installation_for'
            ),

            piping_type=request.form.get(
                'piping_type'
            ),

            machine_position=request.form.get(
                'machine_position'
            ),

            installation_status=request.form.get(
                'installation_status'
            ),

            installation_notes=request.form.get(
                'installation_notes'
            ),

            created_by=session[
                'username'
            ],
            record_owner=session[
                'username'
            ],

        )

        db.session.add(
            installation
        )

        db.session.flush()
        diffuser_files = request.files.getlist(
            'diffuser_files'
        )

        machine_files = request.files.getlist(
            'machine_files'
        )
        for file in diffuser_files:

            if file and file.filename:

                filename = secure_filename(
                    file.filename
                )

                file_path = (
                    'installations/' +
                    filename
                )

                file.save(

                    os.path.join(

                        app.config[
                            'UPLOAD_FOLDER'
                        ],

                        file_path

                    )

                )

                installation_file = InstallationFile(

                    installation_id=
                        installation.installation_id,

                    file_name=
                        filename,

                    file_path=
                        file_path,

                    file_type=
                        'DIFFUSER'

                )

                db.session.add(
                    installation_file
                )
        for file in machine_files:

            if file and file.filename:

                filename = secure_filename(
                    file.filename
                )

                file_path = (
                    'installations/' +
                    filename
                )

                file.save(

                    os.path.join(

                        app.config[
                            'UPLOAD_FOLDER'
                        ],

                        file_path

                    )

                )

                installation_file = InstallationFile(

                    installation_id=
                        installation.installation_id,

                    file_name=
                        filename,

                    file_path=
                        file_path,

                    file_type=
                        'MACHINE'

                )

                db.session.add(
                    installation_file
                )
        cutting_types = request.form.getlist(
            'cutting_type[]'
        )

        core_sizes = request.form.getlist(
            'core_size[]'
        )

        glass_sizes = request.form.getlist(
            'glass_size[]'
        )

        quantities = request.form.getlist(
            'quantity[]'
        )

        for i in range(
            len(cutting_types)
        ):

            if cutting_types[i] == 'Core Cutting':

                cutting_size = core_sizes[i]

            else:

                cutting_size = glass_sizes[i]

            cutting = InstallationCutting(

                installation_id=
                    installation.installation_id,

                cutting_type=
                    cutting_types[i],

                size=
                    cutting_size,

                quantity=
                    int(
                        quantities[i]
                    )

            )

            db.session.add(
                cutting
            )
        log_activity(

            'INSTALLATION',

            installation.installation_id,

            'CREATED'

        )
            
        db.session.commit()

        return redirect(
            url_for(
                'add_installation'
            )
        )

    search = request.args.get(
        'search'
    )

    query = Installation.query.join(
        SalesPipeline,
        Installation.sales_id ==
        SalesPipeline.sales_id
    )

    if search:

        query = query.filter(

            or_(

                Installation.installation_for.ilike(
                    f'%{search}%'
                ),

                Installation.piping_type.ilike(
                    f'%{search}%'
                ),

                Installation.machine_position.ilike(
                    f'%{search}%'
                ),

                Installation.installation_status.ilike(
                    f'%{search}%'
                ),
                SalesPipeline.name.ilike(
                    f'%{search}%'
                ),

                SalesPipeline.reference_no.ilike(
                    f'%{search}%'
                )

            )

        )

    installations = query.order_by(

        Installation.created_on.asc()

    ).all()

    sales_records = SalesPipeline.query.all()

    return render_template(

        'add_installation.html',

        installations=installations,

        sales=sales_records,

        search=search,

        admin_view=session.get(
            'role'
        ) == 'ADMIN'

    )

@app.route(
    '/installation/<int:installation_id>'
)
def installation_details(
    installation_id
):

    if not has_access(

        'ADMIN',
        'SALES',
        'COMMERCIALS'

    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    installation = Installation.query.get_or_404(

        installation_id

    )

    diffuser_files = InstallationFile.query.filter_by(
        installation_id=installation_id,
        file_type='DIFFUSER'
    ).all()

    machine_files = InstallationFile.query.filter_by(
        installation_id=installation_id,
        file_type='MACHINE'
    ).all()

    cuttings = InstallationCutting.query.filter_by(

        installation_id=installation_id

    ).all()

    return render_template(

        'installation_details.html',

        installation=installation,

        diffuser_files=diffuser_files,

        machine_files=machine_files,

        cuttings=cuttings

    )

@app.route(
    '/edit-installation/<int:installation_id>',
    methods=['GET', 'POST']
)
def edit_installation(
    installation_id
):

    if not has_access(
        'ADMIN',
        'SALES',
        'COMMERCIALS'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    installation = Installation.query.get_or_404(
        installation_id
    )

    sales_records = SalesPipeline.query.all()

    cuttings = InstallationCutting.query.filter_by(
        installation_id=installation_id
    ).all()

    diffuser_files = InstallationFile.query.filter_by(
        installation_id=installation_id,
        file_type='DIFFUSER'
    ).all()

    machine_files = InstallationFile.query.filter_by(
        installation_id=installation_id,
        file_type='MACHINE'
    ).all()

    if request.method == 'POST':

        installation.sales_id = request.form.get(
            'sales_id'
        )

        installation.installation_for = request.form.get(
            'installation_for'
        )

        installation.piping_type = request.form.get(
            'piping_type'
        )

        installation.machine_position = request.form.get(
            'machine_position'
        )

        installation.installation_status = request.form.get(
            'installation_status'
        )

        installation.installation_notes = request.form.get(
            'installation_notes'
        )

        files_to_delete = request.form.getlist(
            'delete_files'
        )

        for file_id in files_to_delete:

            file_record = InstallationFile.query.get(
                file_id
            )

            if file_record:

                try:

                    os.remove(
                        os.path.join(
                            app.config[
                                'UPLOAD_FOLDER'
                            ],
                            file_record.file_path
                        )
                    )

                except:

                    pass

                db.session.delete(
                    file_record
                )

        InstallationCutting.query.filter_by(
            installation_id=installation_id
        ).delete()

        cutting_types = request.form.getlist(
            'cutting_type[]'
        )

        core_sizes = request.form.getlist(
            'core_size[]'
        )

        glass_sizes = request.form.getlist(
            'glass_size[]'
        )

        quantities = request.form.getlist(
            'quantity[]'
        )

        for i in range(
            len(cutting_types)
        ):

            if cutting_types[i] == 'Core Cutting':

                cutting_size = core_sizes[i]

            else:

                cutting_size = glass_sizes[i]

            db.session.add(

                InstallationCutting(

                    installation_id=
                        installation_id,

                    cutting_type=
                        cutting_types[i],

                    size=
                        cutting_size,

                    quantity=
                        int(
                            quantities[i]
                        )

                )

            )
        diffuser_uploads = request.files.getlist(
            'diffuser_files'
        )

        for file in diffuser_uploads:

            if file and file.filename:

                filename = secure_filename(
                    file.filename
                )

                file_path = (
                    'installations/' +
                    filename
                )

                file.save(

                    os.path.join(

                        app.config[
                            'UPLOAD_FOLDER'
                        ],

                        file_path

                    )

                )

                db.session.add(

                    InstallationFile(

                        installation_id=
                            installation.installation_id,

                        file_name=
                            filename,

                        file_path=
                            file_path,

                        file_type=
                            'DIFFUSER'

                    )

                )

        machine_uploads = request.files.getlist(
            'machine_files'
        )

        for file in machine_uploads:

            if file and file.filename:

                filename = secure_filename(
                    file.filename
                )

                file_path = (
                    'installations/' +
                    filename
                )

                file.save(

                    os.path.join(

                        app.config[
                            'UPLOAD_FOLDER'
                        ],

                        file_path

                    )

                )

                db.session.add(

                    InstallationFile(

                        installation_id=
                            installation.installation_id,

                        file_name=
                            filename,

                        file_path=
                            file_path,

                        file_type=
                            'MACHINE'

                    )

                )

        log_activity(

            'INSTALLATION',

            installation.installation_id,

            'UPDATED'

        )

        db.session.commit()

        return redirect(

            url_for(

                'add_installation'

            )

        )

    return render_template(

        'edit_installation.html',

        installation=installation,

        sales=sales_records,

        cuttings=cuttings,

        diffuser_files=diffuser_files,

        machine_files=machine_files

    )

@app.route(
    '/request-delete-installation/<int:installation_id>',
    methods=['GET', 'POST']
)
def request_delete_installation(installation_id):

    installation = Installation.query.get_or_404(
        installation_id
    )

    # ADMIN -> DELETE DIRECTLY
    if session.get(
        'role'
    ) == 'ADMIN':

        try:

            db.session.delete(
                installation
            )

            db.session.flush()

            log_activity(

                'INSTALLATION',

                installation_id,

                'DELETED'

            )

            db.session.commit()

            flash(

                'Installation deleted successfully.'

            )

        except Exception:

            db.session.rollback()

            flash(

                'Cannot delete this Installation because it is linked with other records.'

            )

        return redirect(

            url_for(
                'add_installation'
            )

        )

    # EMPLOYEE -> DELETE REQUEST
    if request.method == 'POST':

        delete_request = DeleteRequest(

            module_name='INSTALLATION',

            record_id=installation_id,

            requested_by=session[
                'username'
            ],

            reason=request.form.get(
                'reason'
            )

        )

        db.session.add(
            delete_request
        )

        db.session.flush()

        log_activity(

            'INSTALLATION',

            installation_id,

            'DELETE REQUESTED',

            request.form.get(
                'reason'
            )

        )

        db.session.commit()

        flash(
            'Delete request sent.'
        )

        return redirect(

            url_for(
                'add_installation'
            )

        )

    return render_template(

        'delete_request.html',

        module='INSTALLATION',

        record_id=installation_id

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
            ),
            record_owner=session[
                'username'
            ]    
        )

        db.session.add(
            client
        )
        db.session.flush()
        log_activity(

            'CLIENT',

            client.client_id,

            'CREATED'

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

        all_clients = Client.query.filter(

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

        all_clients = Client.query.all()



    today = datetime.today().date()

    for client in all_clients:
        if client.installation_date:

            client.cmc_due_days = (

                today -

                client.installation_date

            ).days

        else:

            client.cmc_due_days = 0


        client.cmc_due = (

            'YES'

            if client.cmc_due_days >= 345

            else 'NO'

        )


        if client.last_service_date:

            client.last_service_days = (

                today -

                client.last_service_date

            ).days

        elif client.activation_date:

            client.last_service_days = (

                today -

                client.activation_date

            ).days

        else:

            client.last_service_days = 0


        client.service_due = (

            'YES'

            if client.last_service_days >=

            client.service_interval_days

            else 'NO'

        )
    db.session.commit()
    all_proposals = Proposal.query.all()

    all_invoices = Invoice.query.all()

    return render_template(

        'add_client.html',

        clients=all_clients,

        proposals=all_proposals,

        invoices=all_invoices,

        admin_view=session.get(
            'role'
        ) == 'ADMIN'

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
    update_client_status(client)

    db.session.commit()
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
    client = Client.query.get_or_404(client_id)

    update_client_status(client)

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
        db.session.flush()
        log_activity(

            'CLIENT',

            client.client_id,

            'UPDATED'

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
    '/request-delete-client/<int:client_id>',
    methods=['GET', 'POST']
)
def request_delete_client(client_id):

    client = Client.query.get_or_404(
        client_id
    )

    # ADMIN -> DELETE DIRECTLY
    if session.get(
        'role'
    ) == 'ADMIN':

        try:
            service_count = CustomerCareCard.query.filter_by(
                client_id=client_id
            ).count()

            if service_count > 0:

                flash(

                    f'Cannot delete this client. {service_count} service record(s) exist.'

                )

                return redirect(

                    url_for(
                        'add_client'
                    )

                )
            db.session.delete(
                client
            )

            db.session.flush()

            log_activity(

                'CLIENT',

                client_id,

                'DELETED'

            )

            db.session.commit()

            flash(

                'Client deleted successfully.'

            )

        except Exception:

            db.session.rollback()

            flash(

                'Cannot delete this Client because it is linked with other records.'

            )

        return redirect(

            url_for(
                'add_client'
            )

        )

    # EMPLOYEE -> DELETE REQUEST
    if request.method == 'POST':

        delete_request = DeleteRequest(

            module_name='CLIENT',

            record_id=client_id,

            requested_by=session[
                'username'
            ],

            reason=request.form.get(
                'reason'
            )

        )

        db.session.add(
            delete_request
        )

        db.session.flush()

        log_activity(

            'CLIENT',

            client_id,

            'DELETE REQUESTED',

            request.form.get(
                'reason'
            )

        )

        db.session.commit()

        flash(
            'Delete request sent.'
        )

        return redirect(

            url_for(
                'add_client'
            )

        )

    return render_template(

        'delete_request.html',

        module='CLIENT',

        record_id=client_id

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

        service_count=service_count,

        admin_view=session.get(
            'role'
        ) == 'ADMIN'

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
            ),
            record_owner=session[
                'username'
            ]    
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
        db.session.flush()
        log_activity(

            'SERVICE',

            service.client_id,

            'CREATED'

        )  
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
        db.session.flush()
        log_activity(

            'SERVICE',

            service.client_id,

            'UPDATED'

        )  
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
    '/request-delete-service/<int:card_id>',
    methods=['GET', 'POST']
)
def request_delete_service(card_id):

    service = CustomerCareCard.query.get_or_404(
        card_id
    )

    # ADMIN
    if session.get(
        'role'
    ) == 'ADMIN':

        try:

            db.session.delete(
                service
            )

            db.session.flush()

            log_activity(

                'SERVICE',

                card_id,

                'DELETED'

            )

            db.session.commit()

            flash(

                'Service deleted successfully.'

            )

        except Exception:

            db.session.rollback()

            flash(

                'Cannot delete this Service.'

            )

        return redirect(

            url_for(

                'client_services',

                client_id=service.client_id

            )

        )

    # EMPLOYEE

    if request.method == 'POST':

        delete_request = DeleteRequest(

            module_name='SERVICE',

            record_id=card_id,

            requested_by=session[
                'username'
            ],

            reason=request.form.get(
                'reason'
            )

        )

        db.session.add(
            delete_request
        )

        db.session.flush()

        log_activity(

            'SERVICE',

            card_id,

            'DELETE REQUESTED',

            request.form.get(
                'reason'
            )

        )

        db.session.commit()

        flash(
            'Delete request sent.'
        )

        return redirect(

            url_for(

                'client_services',

                client_id=service.client_id

            )

        )

    return render_template(

        'delete_request.html',

        module='SERVICE',

        record_id=card_id

    )

@app.route('/sales-department')
def sales_department():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    sales_users = User.query.filter_by(
        role='SALES'
    ).all()

    return render_template(
        'sales_department.html',
        sales_users=sales_users
    )

@app.route(
    '/sales-employee/<username>'
)
def sales_employee(
    username
):

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    user = User.query.filter_by(
        username=username
    ).first_or_404()

    lead_count = Lead.query.filter_by(
        record_owner=username
    ).count()

    meeting_count = Meeting.query.filter_by(
        record_owner=username
    ).count()

    visit_count = Visit.query.filter_by(
        record_owner=username
    ).count()

    drawing_count = Drawing.query.filter_by(
        record_owner=username
    ).count()

    proposal_count = Proposal.query.filter_by(
        record_owner=username
    ).count()

    sales_count = SalesPipeline.query.filter_by(
        record_owner=username
    ).count()

    invoice_count = Invoice.query.filter_by(
        record_owner=username
    ).count()

    return render_template(

        'sales_employee.html',

        user=user,

        lead_count=lead_count,

        meeting_count=meeting_count,

        visit_count=visit_count,

        drawing_count=drawing_count,

        proposal_count=proposal_count,

        sales_count=sales_count,

        invoice_count=invoice_count

    )

@app.route(
    '/employee-leads/<username>'
)
def employee_leads(
    username
):

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    user = User.query.filter_by(
        username=username
    ).first_or_404()

    search = request.args.get(
        'search'
    )

    query = Lead.query.filter_by(
        record_owner=username
    )

    if search:

        query = query.filter(
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
                )
            )
        )

    leads = query.order_by(
        Lead.lead_id.desc()
    ).all()

    return render_template(

        'employee_leads.html',

        user=user,

        leads=leads,

        search=search

    )


@app.route(
    '/employee-meetings/<username>'
)
def employee_meetings(
    username
):

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    user = User.query.filter_by(
        username=username
    ).first_or_404()

    search = request.args.get(
        'search'
    )

    query = Meeting.query.filter_by(
        record_owner=username
    )

    if search:

        query = query.filter(
            or_(
                Meeting.name.ilike(
                    f'%{search}%'
                ),
                Meeting.reference.ilike(
                    f'%{search}%'
                ),
                Meeting.firm_name.ilike(
                    f'%{search}%'
                ),
                Meeting.contact_no.ilike(
                    f'%{search}%'
                )
            )
        )

    meetings = query.order_by(
        Meeting.meeting_id.desc()
    ).all()

    return render_template(

        'employee_meetings.html',

        user=user,

        meetings=meetings,

        search=search

    )

@app.route(
    '/employee-visits/<username>'
)
def employee_visits(
    username
):

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    user = User.query.filter_by(
        username=username
    ).first_or_404()

    search = request.args.get(
        'search'
    )

    query = Visit.query.filter_by(
        record_owner=username
    )

    if search:

        query = query.filter(
            or_(
                Visit.company_name.ilike(
                    f'%{search}%'
                ),
                Visit.person_name.ilike(
                    f'%{search}%'
                ),
                Visit.contact_no.ilike(
                    f'%{search}%'
                ),
                Visit.state.ilike(
                    f'%{search}%'
                )
            )
        )

    visits = query.order_by(
        Visit.visit_id.desc()
    ).all()

    return render_template(

        'employee_visits.html',

        user=user,

        visits=visits,

        search=search

    )

@app.route(
    '/employee-drawings/<username>'
)
def employee_drawings(
    username
):

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    user = User.query.filter_by(
        username=username
    ).first_or_404()

    search = request.args.get(
        'search'
    )

    query = Drawing.query.filter_by(
        record_owner=username
    )

    if search:

        query = query.filter(
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
        )

    drawings = query.order_by(
        Drawing.drawing_id.desc()
    ).all()

    return render_template(

        'employee_drawings.html',

        user=user,

        drawings=drawings,

        search=search

    )

@app.route(
    '/employee-proposals/<username>'
)
def employee_proposals(
    username
):

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    user = User.query.filter_by(
        username=username
    ).first_or_404()

    search = request.args.get(
        'search'
    )

    query = Proposal.query.filter_by(
        record_owner=username
    )

    if search:

        query = query.filter(
            or_(
                Proposal.name.ilike(
                    f'%{search}%'
                ),
                Proposal.reference_no.ilike(
                    f'%{search}%'
                ),
                Proposal.address.ilike(
                    f'%{search}%'
                ),
                Proposal.contact_no.ilike(
                    f'%{search}%'
                )
            )
        )

    proposals = query.order_by(
        Proposal.proposal_id.desc()
    ).all()

    return render_template(

        'employee_proposals.html',

        user=user,

        proposals=proposals,

        search=search

    )

@app.route(
    '/employee-sales/<username>'
)
def employee_sales(
    username
):

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    user = User.query.filter_by(
        username=username
    ).first_or_404()

    search = request.args.get(
        'search'
    )

    query = SalesPipeline.query.filter_by(
        record_owner=username
    )

    if search:

        query = query.filter(
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
                SalesPipeline.contact_no.ilike(
                    f'%{search}%'
                )
            )
        )

    sales = query.order_by(
        SalesPipeline.sales_id.desc()
    ).all()

    return render_template(

        'employee_sales.html',

        user=user,

        sales=sales,

        search=search

    )

@app.route(
    '/employee-invoices/<username>'
)
def employee_invoices(
    username
):

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    user = User.query.filter_by(
        username=username
    ).first_or_404()

    search = request.args.get(
        'search'
    )

    query = Invoice.query.filter_by(
        record_owner=username
    )

    if search:

        query = query.filter(
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
        )

    invoices = query.order_by(
        Invoice.invoice_id.desc()
    ).all()

    return render_template(

        'employee_invoices.html',

        user=user,

        invoices=invoices,

        search=search

    )

@app.route(
    '/commercial-department'
)
def commercial_department():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    return render_template(
        'commercial_department.html'
    )

@app.route(
    '/commercial-leads'
)
def commercial_leads():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for(
                'dashboard'
            )
        )

    commercial_users = User.query.filter_by(
        role='COMMERCIALS'
    ).all()

    usernames = [
        user.username
        for user in commercial_users
    ]

    leads = Lead.query.filter(
        Lead.record_owner.in_(
            usernames
        )
    ).all()

    return render_template(

        'add_lead.html',

        leads=leads,

        admin_view=(
            session.get('role')
            == 'ADMIN'
        )

    )

@app.route('/commercial-meetings')
def commercial_meetings():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):
        return redirect(
            url_for('dashboard')
        )

    commercial_users = User.query.filter_by(
        role='COMMERCIALS'
    ).all()

    usernames = [
        user.username
        for user in commercial_users
    ]

    meetings = Meeting.query.filter(
        Meeting.record_owner.in_(
            usernames
        )
    ).all()

    leads = Lead.query.filter(
        Lead.record_owner.in_(
            usernames
        )
    ).all()

    return render_template(

        'add_meeting.html',

        meetings=meetings,

        leads=leads,

        admin_view=(
            session.get('role')
            == 'ADMIN'
        )

    )

@app.route('/commercial-visits')
def commercial_visits():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):
        return redirect(
            url_for('dashboard')
        )

    commercial_users = User.query.filter_by(
        role='COMMERCIALS'
    ).all()

    usernames = [
        user.username
        for user in commercial_users
    ]

    visits = Visit.query.filter(
        Visit.record_owner.in_(
            usernames
        )
    ).all()

    meetings = Meeting.query.filter(
        Meeting.record_owner.in_(
            usernames
        )
    ).all()

    return render_template(

        'add_visit.html',

        visits=visits,

        meetings=meetings,

        admin_view=(
            session.get('role')
            == 'ADMIN'
        )

    )

@app.route('/commercial-drawings')
def commercial_drawings():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):
        return redirect(
            url_for('dashboard')
        )

    commercial_users = User.query.filter_by(
        role='COMMERCIALS'
    ).all()

    usernames = [
        user.username
        for user in commercial_users
    ]

    drawings = Drawing.query.filter(
        Drawing.record_owner.in_(
            usernames
        )
    ).all()

    visits = Visit.query.filter(
        Visit.record_owner.in_(
            usernames
        )
    ).all()

    return render_template(

        'add_drawing.html',

        drawings=drawings,

        visits=visits,

        admin_view=(
            session.get('role')
            == 'ADMIN'
        )

    )

@app.route('/commercial-proposals')
def commercial_proposals():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):
        return redirect(
            url_for('dashboard')
        )

    commercial_users = User.query.filter_by(
        role='COMMERCIALS'
    ).all()

    usernames = [
        user.username
        for user in commercial_users
    ]

    proposals = Proposal.query.filter(
        Proposal.record_owner.in_(
            usernames
        )
    ).all()

    meetings = Meeting.query.filter(
        Meeting.record_owner.in_(
            usernames
        )
    ).all()

    drawings = Drawing.query.filter(
        Drawing.record_owner.in_(
            usernames
        )
    ).all()

    return render_template(

        'add_proposal.html',

        proposals=proposals,

        meetings=meetings,

        drawings=drawings,

        admin_view=(
            session.get('role')
            == 'ADMIN'
        )

    )

@app.route('/commercial-sales')
def commercial_sales():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):
        return redirect(
            url_for('dashboard')
        )

    commercial_users = User.query.filter_by(
        role='COMMERCIALS'
    ).all()

    usernames = [
        user.username
        for user in commercial_users
    ]

    sales = SalesPipeline.query.filter(
        SalesPipeline.record_owner.in_(
            usernames
        )
    ).all()

    proposals = Proposal.query.filter(
        Proposal.record_owner.in_(
            usernames
        )
    ).all()

    return render_template(

        'add_sales.html',

        sales=sales,

        proposals=proposals,

        admin_view=(
            session.get('role')
            == 'ADMIN'
        )

    )

@app.route('/commercial-invoices')
def commercial_invoices():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):
        return redirect(
            url_for('dashboard')
        )

    commercial_users = User.query.filter_by(
        role='COMMERCIALS'
    ).all()

    usernames = [
        user.username
        for user in commercial_users
    ]

    invoices = Invoice.query.filter(
        Invoice.record_owner.in_(
            usernames
        )
    ).all()

    sales = SalesPipeline.query.filter(
        SalesPipeline.record_owner.in_(
            usernames
        )
    ).all()

    return render_template(

        'add_invoice.html',

        invoices=invoices,

        sales=sales,

        admin_view=(
            session.get('role')
            == 'ADMIN'
        )

    )

@app.route('/commercial-clients')
def commercial_clients():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):
        return redirect(
            url_for('dashboard')
        )

    clients = Client.query.all()

    proposals = Proposal.query.all()

    invoices = Invoice.query.all()

    return render_template(

        'add_client.html',

        clients=clients,

        proposals=proposals,

        invoices=invoices,

        admin_view=(
            session.get('role')
            == 'ADMIN'
        )

    )

@app.route(
    '/organization'
)
def organization():

    if session.get(
        'role'
    ) != 'ADMIN':

        return redirect(
            url_for(
                'dashboard'
            )
        )
    total_leads = Lead.query.count()
    total_meetings = Meeting.query.count()
    total_visits = Visit.query.count()
    total_drawings = Drawing.query.count()
    total_proposals = Proposal.query.count()
    total_sales = SalesPipeline.query.count()
    total_invoices = Invoice.query.count()
    total_clients = Client.query.count()
    return render_template(
        'organization.html',
        total_leads=total_leads,
        total_meetings=total_meetings,
        total_visits=total_visits,
        total_drawings=total_drawings,
        total_proposals=total_proposals,
        total_sales=total_sales,
        total_invoices=total_invoices,
        total_clients=total_clients
    )

@app.route(
    '/organization-leads'
)
def organization_leads():

    if session.get(
        'role'
    ) != 'ADMIN':

        return redirect(
            url_for(
                'dashboard'
            )
        )

    search = request.args.get(
        'search'
    )

    query = Lead.query

    if search:

        query = query.filter(

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

                Lead.record_owner.ilike(
                    f'%{search}%'
                )

            )

        )

    leads = query.all()

    return render_template(

        'organization_leads.html',

        leads=leads,

        search=search

    )

@app.route('/organization-meetings')
def organization_meetings():

    if session.get('role') != 'ADMIN':
        return redirect(url_for('dashboard'))

    search = request.args.get('search')

    query = Meeting.query

    if search:

        query = query.filter(

            or_(

                Meeting.name.ilike(
                    f'%{search}%'
                ),

                Meeting.firm_name.ilike(
                    f'%{search}%'
                ),

                Meeting.contact_no.ilike(
                    f'%{search}%'
                ),

                Meeting.record_owner.ilike(
                    f'%{search}%'
                )

            )

        )

    meetings = query.all()

    return render_template(

        'organization_meetings.html',

        meetings=meetings,

        search=search

    )

@app.route('/organization-visits')
def organization_visits():

    if session.get('role') != 'ADMIN':
        return redirect(url_for('dashboard'))

    search = request.args.get('search')

    query = Visit.query

    if search:

        query = query.filter(

            or_(

                Visit.company_name.ilike(
                    f'%{search}%'
                ),

                Visit.person_name.ilike(
                    f'%{search}%'
                ),

                Visit.contact_no.ilike(
                    f'%{search}%'
                ),

                Visit.record_owner.ilike(
                    f'%{search}%'
                )

            )

        )

    visits = query.all()

    return render_template(

        'organization_visits.html',

        visits=visits,

        search=search

    )

@app.route('/organization-drawings')
def organization_drawings():

    if session.get('role') != 'ADMIN':
        return redirect(url_for('dashboard'))

    search = request.args.get('search')

    query = Drawing.query

    if search:

        query = query.filter(

            or_(

                Drawing.name.ilike(
                    f'%{search}%'
                ),

                Drawing.address.ilike(
                    f'%{search}%'
                ),

                Drawing.record_owner.ilike(
                    f'%{search}%'
                )

            )

        )

    drawings = query.all()

    return render_template(

        'organization_drawings.html',

        drawings=drawings,

        search=search

    )

@app.route('/organization-proposals')
def organization_proposals():

    if session.get('role') != 'ADMIN':
        return redirect(url_for('dashboard'))

    search = request.args.get('search')

    query = Proposal.query

    if search:

        query = query.filter(

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

                Proposal.record_owner.ilike(
                    f'%{search}%'
                )

            )

        )

    proposals = query.all()

    return render_template(

        'organization_proposals.html',

        proposals=proposals,

        search=search

    )

@app.route('/organization-sales')
def organization_sales():

    if session.get('role') != 'ADMIN':
        return redirect(url_for('dashboard'))

    search = request.args.get('search')

    query = SalesPipeline.query

    if search:

        query = query.filter(

            or_(

                SalesPipeline.name.ilike(
                    f'%{search}%'
                ),

                SalesPipeline.contact_no.ilike(
                    f'%{search}%'
                ),

                SalesPipeline.project_stage.ilike(
                    f'%{search}%'
                ),

                SalesPipeline.record_owner.ilike(
                    f'%{search}%'
                )

            )

        )

    sales = query.all()

    return render_template(

        'organization_sales.html',

        sales=sales,

        search=search

    )

@app.route(
    '/organization-invoices',
    methods=['GET', 'POST']
)
def organization_invoices():

    if session.get('role') != 'ADMIN':
        return redirect(url_for('dashboard'))

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


            record_owner=session[
                'username'
            ]    
        )

        db.session.add(
            invoice
        )
        db.session.flush()
        invoice_files = request.files.getlist(
            'invoice_files'
        )

        for file in invoice_files:

            if file and file.filename:

                filename = secure_filename(
                    file.filename
                )

                relative_path = (
                    'invoices/' +
                    filename
                )

                file.save(

                    os.path.join(

                        app.config[
                            'UPLOAD_FOLDER'
                        ],

                        relative_path

                    )

                )

                new_file = InvoiceFile(

                    invoice_id=
                    invoice.invoice_id,

                    file_name=filename,

                    file_path=relative_path,

                    file_type=file.content_type

                )

                db.session.add(
                    new_file
                )
        log_activity(

            'INVOICE',

            invoice.invoice_id,

            'CREATED'

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
    if session.get(
        'role'
    ) == 'SALES':

        base_query = Invoice.query.filter_by(

            record_owner=session[
                'username'
            ]

        )

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]

        base_query = Invoice.query.filter(

            Invoice.record_owner.in_(
                usernames
            )

        )

    else:

        base_query = Invoice.query

    if search:

        all_invoices = base_query.filter(

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

        all_invoices = base_query.all()

    if session.get(
        'role'
    ) == 'SALES':

        all_sales = SalesPipeline.query.filter_by(

            record_owner=session[
                'username'
            ]

        ).all()

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]
    
        all_sales = SalesPipeline.query.filter(

            SalesPipeline.record_owner.in_(
                usernames
            )

        ).all()

    else:

        all_sales = SalesPipeline.query.all()

    return render_template(

        'organization_invoices.html',

        invoices=all_invoices,

        sales=all_sales,

        search=search        

    )

@app.route('/organization-clients')
def organization_clients():

    if session.get('role') != 'ADMIN':
        return redirect(url_for('dashboard'))

    search = request.args.get('search')

    query = Client.query

    if search:

        query = query.filter(

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

                Client.record_owner.ilike(
                    f'%{search}%'
                )

            )

        )

    clients = query.all()

    return render_template(

        'organization_clients.html',

        clients=clients,

        search=search

    )

@app.route(
    '/global-search'
)
def global_search():

    search = request.args.get(
        'search',
        ''
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
    installations = []

    if search:

        leads = search_records(

            Lead,

            [

                Lead.name,

                Lead.reference,

                Lead.location,

                Lead.phone,

                Lead.responses,

                Lead.recent

            ],

            search

        )

        meetings = search_records(

            Meeting,

            [

                Meeting.meeting_fixed_by,

                Meeting.source,

                Meeting.name,

                Meeting.reference,

                Meeting.firm_name,

                Meeting.designation,

                Meeting.address,

                Meeting.state,

                Meeting.contact_no,

                Meeting.email,

                Meeting.mode_of_meeting,

                Meeting.meeting_status,

                Meeting.meeting_conducted_by,

                Meeting.final_remarks,

                Meeting.reason_for_reschedule,

                Meeting.remarks

            ],

            search

        )

        visits = search_records(

            Visit,

            [

                Visit.state,

                Visit.region,

                Visit.abc,

                Visit.company_name,

                Visit.person_name,

                Visit.designation,

                Visit.contact_no,

                Visit.address,

                Visit.brief

            ],

            search

        )

        drawings = search_records(

            Drawing,

            [

                Drawing.name,

                Drawing.address,

                Drawing.moca

            ],

            search

        )

        proposals = search_records(

            Proposal,

            [

                Proposal.reference_no,

                Proposal.name,

                Proposal.phone_no_client,

                Proposal.source,

                Proposal.type,

                Proposal.reference_source_details,

                Proposal.phone_no_source,

                Proposal.contact_person,

                Proposal.phone_no_contact_person,

                Proposal.email,

                Proposal.site_address,

                Proposal.state,

                Proposal.type_of_units,

                Proposal.product,

                Proposal.proposal_prepared_by,

                Proposal.proposal_shared_by,

                Proposal.status,

                Proposal.remarks

            ],

            search

        )
        sales = search_records(

            SalesPipeline,

            [

                SalesPipeline.name,

                SalesPipeline.reference_no,

                SalesPipeline.project_stage,

                SalesPipeline.moc,

                SalesPipeline.source,

                SalesPipeline.next_action,

                SalesPipeline.address,

                SalesPipeline.contact_no,

                SalesPipeline.project_type,

                SalesPipeline.category,

                SalesPipeline.email_id,

                SalesPipeline.site_incharge,

                SalesPipeline.site_incharge_contact,

                SalesPipeline.gst_no,

                SalesPipeline.sales_person

            ],

            search

        )

        invoices = search_records(

            Invoice,

            [

                Invoice.name,

                Invoice.invoice_no,

                Invoice.gst_no,

                Invoice.product_sold

            ],

            search

        )

        clients = search_records(

            Client,

            [

                Client.client_name,

                Client.property_type,

                Client.nearest_metrostation,

                Client.mail_id,

                Client.state,

                Client.mobile_no,

                Client.product,

                Client.filter_colour,

                Client.remark

            ],

            search

        )

        services = get_record_query(
            CustomerCareCard
        )

        services = services.join(

            Client,

            CustomerCareCard.client_id ==
            Client.client_id

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

        installation_query = get_record_query(
            Installation
        )

        installation_query = installation_query.join(

            SalesPipeline,

            Installation.sales_id ==
            SalesPipeline.sales_id

        ).filter(

            or_(

                Installation.installation_for.ilike(
                    f'%{search}%'
                ),

                Installation.piping_type.ilike(
                    f'%{search}%'
                ),

                Installation.machine_position.ilike(
                    f'%{search}%'
                ),

                Installation.installation_status.ilike(
                    f'%{search}%'
                ),

                SalesPipeline.name.ilike(
                    f'%{search}%'
                ),

                SalesPipeline.reference_no.ilike(
                    f'%{search}%'
                )

            )

        )

        installations = installation_query.all()

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

        services=services,

        installations=installations,

        can_view_search_result=
            can_view_search_result,

        can_edit_search_result=
            can_edit_search_result,

        can_delete_search_result=
            can_delete_search_result

    )

@app.route('/tasks')
def tasks():

    if 'user_id' not in session:

        return redirect(
            url_for('login')
        )
    if not has_access(
        'ADMIN',
        'COMMERCIALS',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    today = date.today()

    tomorrow = today + timedelta(days=1)

    week_end = today + timedelta(days=7)

    if session.get('role') == 'SALES':

        lead_base = Lead.query.filter(
            Lead.record_owner == session['username']
        )

        meeting_base = Meeting.query.filter(
            Meeting.record_owner == session['username']
        )

        proposal_base = Proposal.query.filter(
            Proposal.record_owner == session['username']
        )

    elif session.get('role') == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [
            user.username
            for user in commercial_users
        ]

        lead_base = Lead.query.filter(
            Lead.record_owner.in_(usernames)
        )

        meeting_base = Meeting.query.filter(
            Meeting.record_owner.in_(usernames)
        )

        proposal_base = Proposal.query.filter(
            Proposal.record_owner.in_(usernames)
        )

    else:

        lead_base = Lead.query

        meeting_base = Meeting.query

        proposal_base = Proposal.query


    overdue_leads = lead_base.filter(
        Lead.next_to_call < today
    ).all()

    today_leads = lead_base.filter(
        Lead.next_to_call == today
    ).all()

    tomorrow_leads = lead_base.filter(
        Lead.next_to_call == tomorrow
    ).all()

    week_leads = lead_base.filter(
        Lead.next_to_call > tomorrow,
        Lead.next_to_call <= week_end
    ).all()


    overdue_meetings = meeting_base.filter(
        Meeting.date_to_call_next < today
    ).all()

    today_meetings = meeting_base.filter(
        Meeting.date_to_call_next == today
    ).all()

    tomorrow_meetings = meeting_base.filter(
        Meeting.date_to_call_next == tomorrow
    ).all()

    week_meetings = meeting_base.filter(
        Meeting.date_to_call_next > tomorrow,
        Meeting.date_to_call_next <= week_end
    ).all()

    overdue_proposals = proposal_base.filter(
        Proposal.next_to_call < today
    ).all()

    today_proposals = proposal_base.filter(
        Proposal.next_to_call == today
    ).all()

    tomorrow_proposals = proposal_base.filter(
        Proposal.next_to_call == tomorrow
    ).all()

    week_proposals = proposal_base.filter(
        Proposal.next_to_call > tomorrow,
        Proposal.next_to_call <= week_end
    ).all()


    return render_template(

        'tasks.html',

        today=today,

        overdue_leads=
            overdue_leads,

        today_leads=
            today_leads,

        tomorrow_leads=
            tomorrow_leads,

        week_leads=
            week_leads,

        overdue_meetings=
            overdue_meetings,

        today_meetings=
            today_meetings,

        tomorrow_meetings=
            tomorrow_meetings,

        week_meetings=
            week_meetings,

        overdue_proposals=
            overdue_proposals,

        today_proposals=
            today_proposals,

        tomorrow_proposals=
            tomorrow_proposals,

        week_proposals=
            week_proposals

    )

@app.route('/services-due')
def service_due():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )

    today = date.today()

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

    return render_template(
        'service_due.html',
        service_due_clients=service_due_clients
    )

@app.route('/cmc-due')
def cmc_due():

    if not has_access(
        'ADMIN',
        'COMMERCIALS'
    ):

        return redirect(
            url_for('dashboard')
        )

    today = date.today()

    cmc_due_clients = Client.query.filter(
        Client.cmc_applicable == 'YES',
        Client.next_cmc_renewal_date != None,
        Client.next_cmc_renewal_date <= (
            today + timedelta(days=20)
        )
    ).order_by(
        Client.next_cmc_renewal_date.asc()
    ).all()

    return render_template(
        'cmc_due.html',
        cmc_due_clients=cmc_due_clients
    )

@app.route(
    '/complete-lead-followup/<int:lead_id>'
)
def complete_lead_followup(lead_id):
    if not has_access(
        'ADMIN',
        'COMMERCIALS',
        'SALES'
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
    db.session.flush()
    log_activity(

        'TASK',

        lead_id,

        'COMPLETED'

    )
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
        'COMMERCIALS',
        'SALES'
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
    db.session.flush()
    log_activity(

        'TASK',

        meeting_id,

        'COMPLETED'

    )

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
        'COMMERCIALS',
        'SALES'
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
    db.session.flush()
    log_activity(

        'TASK',

        proposal_id,

        'COMPLETED'

    )

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
        'COMMERCIALS',
        'SALES'
    ):

        return redirect(
            url_for('dashboard')
        )
    search = request.args.get(
        'search'
    )

    if session.get(
        'role'
    ) == 'SALES':

        query = CompletedTask.query.filter(

            CompletedTask.completed_by ==
            session['username']

        )

    elif session.get(
        'role'
    ) == 'COMMERCIALS':

        commercial_users = User.query.filter_by(
            role='COMMERCIALS'
        ).all()

        usernames = [

            user.username

            for user in commercial_users

        ]

        query = CompletedTask.query.filter(

            CompletedTask.completed_by.in_(
                usernames
            )

        )

    else:

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

@app.route('/activity-logs')
def activity_logs():

    if session.get('role') != 'ADMIN':

        return redirect(
            url_for('dashboard')
        )

    search = request.args.get(
        'search'
    )

    query = ActivityLog.query

    if search:

        query = query.filter(

            or_(

                ActivityLog.module_name.ilike(
                    f'%{search}%'
                ),

                ActivityLog.action.ilike(
                    f'%{search}%'
                ),

                ActivityLog.performed_by.ilike(
                    f'%{search}%'
                )

            )

        )

    logs = query.order_by(

        ActivityLog.performed_on.desc()

    ).all()

    return render_template(

        'activity_logs.html',

        logs=logs,

        search=search

    )

@app.route('/productivity')
def productivity():

    if session.get('role') != 'ADMIN':

        return redirect(
            url_for('dashboard')
        )

    today = date.today()

    week_start = today - timedelta(
        days=today.weekday()
    )

    month_start = today.replace(
        day=1
    )

    search = request.args.get(
    'search'
)

    query = User.query.filter(
        User.is_active == 'YES'
    )

    if search:

        query = query.filter(

            or_(

                User.username.ilike(
                    f'%{search}%'
                ),

                User.full_name.ilike(
                    f'%{search}%'
                ),

                User.role.ilike(
                    f'%{search}%'
                )

            )

        )

    users = query.all()

    productivity_data = []

    for user in users:

        today_count = ActivityLog.query.filter(

            ActivityLog.performed_by ==
            user.username,

            func.date(
                ActivityLog.performed_on
            ) == today

        ).count()

        week_count = ActivityLog.query.filter(

            ActivityLog.performed_by ==
            user.username,

            ActivityLog.performed_on >=
            week_start

        ).count()

        month_count = ActivityLog.query.filter(

            ActivityLog.performed_by ==
            user.username,

            ActivityLog.performed_on >=
            month_start

        ).count()

        productivity_data.append({

            'username':
                user.username,

            'full_name':
                user.full_name,

            'role':
                user.role,

            'today':
                today_count,

            'week':
                week_count,

            'month':
                month_count

        })

    return render_template(

        'productivity.html',

        productivity_data=
            productivity_data,

        search=search

    )

@app.route(
    '/employee-activity/<username>'
)
def employee_activity(username):

    if session.get('role') != 'ADMIN':

        return redirect(
            url_for('dashboard')
        )

    search = request.args.get(
        'search'
    )

    query = ActivityLog.query.filter(

        ActivityLog.performed_by ==
        username

    )

    if search:

        query = query.filter(

            or_(

                ActivityLog.module_name.ilike(
                    f'%{search}%'
                ),

                ActivityLog.action.ilike(
                    f'%{search}%'
                ),

                ActivityLog.details.ilike(
                    f'%{search}%'
                )

            )

        )

    logs = query.order_by(

        ActivityLog.performed_on.desc()

    ).all()
    return render_template(

        'employee_activity.html',

        logs=logs,

        username=username,

        search=search

    )

@app.route('/delete-requests')
def delete_requests():

    if session.get('role') != 'ADMIN':

        return redirect(
            url_for('dashboard')
        )

    search = request.args.get(
        'search'
    )

    query = DeleteRequest.query

    if search:

        query = query.filter(

            or_(

                DeleteRequest.module_name.ilike(
                    f'%{search}%'
                ),

                DeleteRequest.requested_by.ilike(
                    f'%{search}%'
                ),

                DeleteRequest.status.ilike(
                    f'%{search}%'
                ),

                DeleteRequest.reason.ilike(
                    f'%{search}%'
                )

            )

        )

    requests = query.order_by(

        DeleteRequest.requested_on.desc()

    ).all()

    return render_template(

        'delete_requests.html',

        requests=requests,

        search=search

    )

@app.route(
    '/reject-delete-request/<int:request_id>'
)
def reject_delete_request(request_id):

    if session.get('role') != 'ADMIN':

        return redirect(
            url_for('dashboard')
        )

    request_obj = DeleteRequest.query.get_or_404(
        request_id
    )

    request_obj.status = 'REJECTED'
    db.session.flush()
    log_activity(

        request_obj.module_name,

        request_obj.record_id,

        'DELETE REJECTED'

    )

    db.session.commit()

    return redirect(
        url_for(
            'delete_requests'
        )
    )

@app.route(
    '/approve-delete-request/<int:request_id>'
)
def approve_delete_request(
    request_id
):

    if session.get(
        'role'
    ) != 'ADMIN':

        return redirect(
            url_for(
                'dashboard'
            )
        )

    request_obj = DeleteRequest.query.get_or_404(
        request_id
    )

    if request_obj.module_name == 'LEAD':

        record = Lead.query.get(
            request_obj.record_id
        )

    elif request_obj.module_name == 'MEETING':

        record = Meeting.query.get(
            request_obj.record_id
        )

    elif request_obj.module_name == 'PROPOSAL':

        record = Proposal.query.get(
            request_obj.record_id
        )

    elif request_obj.module_name == 'VISIT':

        record = Visit.query.get(
            request_obj.record_id
        )

    elif request_obj.module_name == 'DRAWING':

        record = Drawing.query.get(
            request_obj.record_id
        )

    elif request_obj.module_name == 'SALES':

        record = SalesPipeline.query.get(
            request_obj.record_id
        )

    elif request_obj.module_name == 'INVOICE':

        record = Invoice.query.get(
            request_obj.record_id
        )

    elif request_obj.module_name == 'CLIENT':

        record = Client.query.get(
            request_obj.record_id
        )

    elif request_obj.module_name == 'SERVICE':

        record = CustomerCareCard.query.get(
            request_obj.record_id
        )

    elif request_obj.module_name == 'INSTALLATION':

        record = Installation.query.get(
            request_obj.record_id
        )

    else:

        record = None

    try:

        if record:

            db.session.delete(
                record
            )

        request_obj.status = 'APPROVED'

        log_activity(

            request_obj.module_name,

            request_obj.record_id,

            'DELETE APPROVED'

        )

        db.session.commit()

        flash(

            'Delete request approved successfully.'

        )

    except Exception:

        db.session.rollback()

        flash(

            'Cannot delete because record is linked.'

        )

    return redirect(
        url_for(
            'delete_requests'
        )
    )

@app.route(
    '/generate-proposal/<int:proposal_id>'
)
def generate_proposal(

    proposal_id

):

    proposal = Proposal.query.get_or_404(

        proposal_id

    )

    location = request.args.get(

        'location',

        'Others'

    )

    air_quality = get_air_quality(

        location

    )

    template_name = get_proposal_template(

        proposal

    )

    template_path = os.path.join(

        app.root_path,

        'templates',

        template_name

    )

    doc = DocxTemplate(

        template_path

    )

    total_mvd_cost = (

        proposal.no_of_mvd_units *

        float(

            proposal.cost_total_per_unit

        )

    )

    total_amount_in_words = (

        num2words(

            int(

                proposal.total_amount

            ),

            lang='en_IN'

        )

        .replace(

            ',',

            ''

        )

        .title()

        + ' Rupees Only'

    )

    final_amount_in_words = (

        num2words(

            int(

                proposal.final_amount

            ),

            lang='en_IN'

        )

        .replace(

            ',',

            ''

        )

        .title()

        + ' Rupees Only'

    )

    no_of_mvd_units_in_words = (

        num2words(

            proposal.no_of_mvd_units

        )

        .title()

    )

    context = {

        'reference_no':
        proposal.reference_no,

        'name':
        proposal.name,

        'site_address':
        proposal.site_address,

        'date_of_proposal_sent':
        proposal.date_of_proposal_sent.strftime(
            '%d-%m-%Y'
        )
        if proposal.date_of_proposal_sent
        else '',

        'total_area_sqft':
        indian_format(
            proposal.total_area_sqft
        ),

        'no_of_mvd_units':
        proposal.no_of_mvd_units,

        'no_of_mvd_units_in_words':
        no_of_mvd_units_in_words,

        'total_no_of_units':
        proposal.total_no_of_units,

        'cost_total_per_unit':
        indian_format(
            proposal.cost_total_per_unit
        ),

        'total_mvd_cost':
        indian_format(
            total_mvd_cost
        ),

        'cmc_starting_period':
        proposal.cmc_starting_period,

        'per_unit_cost':
        indian_format(
            proposal.per_unit_cost
        ),

        'cmc_cost':
        indian_format(
            proposal.cmc_cost
        ),

        'installation_cost':
        indian_format(
            proposal.installation_cost
        ),

        'total_amount':
        indian_format(
            proposal.total_amount
        ),

        'total_amount_in_words':
        total_amount_in_words,

        'discount':
        indian_format(
            proposal.discount
            or 0
        ),

        'final_amount':
        indian_format(
            proposal.final_amount
        ),

        'final_amount_in_words':
        final_amount_in_words,

        'outdoor_pm25':
        air_quality['pm25'],

        'outdoor_pm10':
        air_quality['pm10'],

        'outdoor_co2':
        air_quality['co2']
    

    }

    doc.render(

        context

    )

    output_folder = os.path.join(

        app.root_path,

        'generated_proposals'

    )

    os.makedirs(

        output_folder,

        exist_ok=True

    )

    filename = (

        f'Proposal_{proposal.proposal_id}.docx'

    )

    output_path = os.path.join(

        output_folder,

        filename

    )

    doc.save(

        output_path

    )

    return send_file(

        output_path,

        as_attachment=True

    )      

@app.route(
    '/generate-proforma/<int:proposal_id>'
)
def generate_proforma(

    proposal_id

):

    proposal = Proposal.query.get_or_404(

        proposal_id

    )

    proforma_no = request.args.get(

        'proforma_no'

    )

    proforma_date = parse_date(

        request.args.get(

            'proforma_date'

        )

    )

    hsn_code = request.args.get(

        'hsn_code'

    )

    template_path = os.path.join(

        app.root_path,

        'templates',

        'proforma_invoice_template.docx'

    )

    doc = DocxTemplate(

        template_path

    )
    taxable_amount = float(

        proposal.final_amount

    ) / 1.18

    gst = float(

        proposal.final_amount

    ) - taxable_amount

    final_amount = float(

        proposal.final_amount

    )

    total_amount_in_words = (

        num2words(

            int(

                final_amount

            ),

            lang='en_IN'

        )

        .replace(

            ',',

            ''

        )

        .title()

        + ' Rupees Only'

    )

    context = {

        'proforma_no':
        proforma_no,

        'proforma_date':
        proforma_date.strftime(
            '%d-%m-%Y'
        )
        if proforma_date
        else '',

        'hsn_code':
        hsn_code,

        'name':
        proposal.name,

        'site_address':
        proposal.site_address,

        'product':
        proposal.product,

        'total_no_of_units':
        proposal.total_no_of_units,

        'cost_total_per_unit':
        indian_format(
            proposal.cost_total_per_unit
        ),

        'total_amount':
        indian_format(
            taxable_amount
        ),

        'gst':
        indian_format(
            gst
        ),

        'final_amount':
        indian_format(
            final_amount
        ),

        'final_amount_in_words':
        total_amount_in_words

    }
    doc.render(

        context

    )

    output_folder = os.path.join(

        app.root_path,

        'generated_proformas'

    )

    os.makedirs(

        output_folder,

        exist_ok=True

    )

    filename = (

        f'Proforma_Invoice_{proposal.proposal_id}.docx'

    )

    output_path = os.path.join(

        output_folder,

        filename

    )

    doc.save(

        output_path

    )

    return send_file(

        output_path,

        as_attachment=True

    )

@app.route(
    '/generate-advance-receipt/<int:sales_id>'
)
def generate_advance_receipt(

    sales_id

):

    sale = SalesPipeline.query.get_or_404(

        sales_id

    )

    receipt_no = request.args.get(

        'receipt_no'

    )

    receipt_date = parse_date(

        request.args.get(

            'receipt_date'

        )

    )

    hsn_code = request.args.get(

        'hsn_code'

    )

    template_path = os.path.join(

        app.root_path,

        'templates',

        'advance_receipt_template.docx'

    )

    doc = DocxTemplate(

        template_path

    )

    amount_in_words = (

        num2words(

            int(

                sale.amount_received

            ),

            lang='en_IN'

        )

        .replace(

            ',',

            ''

        )

        .title()

        + ' Rupees Only'

    )

    context = {

        'receipt_no':
        receipt_no,

        'receipt_date':
        receipt_date.strftime(

            '%d-%m-%Y'

        )
        if receipt_date
        else '',

        'hsn_code':
        hsn_code,

        'name':
        sale.name,

        'address':
        sale.address,

        'revenue':
        indian_format(

            sale.revenue

        ),

        'total_revenue':
        indian_format(

            sale.total_revenue

        ),

        'amount_received':
        indian_format(

            sale.amount_received

        ),

        'amount_due':
        indian_format(

            sale.amount_due

        ),

        'amount_in_words':
        amount_in_words

    }

    doc.render(

        context

    )

    output_folder = os.path.join(

        app.root_path,

        'generated_advance_receipts'

    )

    os.makedirs(

        output_folder,

        exist_ok=True

    )

    filename = (

        f'Advance_Receipt_{sale.sales_id}.docx'

    )

    output_path = os.path.join(

        output_folder,

        filename

    )

    doc.save(

        output_path

    )

    return send_file(

        output_path,

        as_attachment=True

    )

@app.route(
    '/reminders'
)
def reminders():

    if 'user_id' not in session:

        return redirect(
            url_for(
                'login'
            )
        )

    today = date.today()

    pending_reminders = Reminder.query.filter(

        Reminder.created_by == session.get(
            'username'
        ),

        Reminder.status == 'PENDING',

        Reminder.is_dismissed == False,

        or_(

            Reminder.snooze_until == None,

            Reminder.snooze_until <= datetime.now()

        )

    ).order_by(

        Reminder.reminder_date.asc(),

        Reminder.reminder_time.asc()

    ).all()

    completed_reminders = Reminder.query.filter(

        Reminder.created_by == session.get(
            'username'
        ),

        Reminder.status == 'COMPLETED'

    ).order_by(

        Reminder.created_on.desc()

    ).all()

    overdue_count = sum(

        1

        for reminder in pending_reminders

        if reminder.reminder_date < today

    )

    today_count = sum(

        1

        for reminder in pending_reminders

        if reminder.reminder_date == today

    )

    upcoming_count = sum(

        1

        for reminder in pending_reminders

        if reminder.reminder_date > today

    )

    return render_template(

        'reminders.html',

        reminders=pending_reminders,

        completed_reminders=completed_reminders,

        overdue_count=overdue_count,

        today_count=today_count,

        upcoming_count=upcoming_count,

        today=today

    )

@app.route(

    '/add-reminder',

    methods=['POST']

)
def add_reminder():

    if 'user_id' not in session:

        return redirect(

            url_for(

                'login'

            )

        )

    reminder = Reminder(

        title=request.form.get(

            'title'

        ),

        description=request.form.get(

            'description'

        ),

        reminder_date=parse_date(

            request.form.get(

                'reminder_date'

            )

        ),

        reminder_time=(

            datetime.strptime(

                request.form.get(

                    'reminder_time'

                ),

                '%H:%M'

            ).time()

            if request.form.get(

                'reminder_time'

            )

            else None

        ),

        priority=request.form.get(

            'priority'

        ),

        repeat_type=request.form.get(

            'repeat_type'

        ),

        created_by=session.get(

            'username'

        )

    )

    db.session.add(

        reminder

    )

    db.session.commit()

    flash(

        'Reminder added successfully.',

        'success'

    )

    return redirect(

        url_for(

            'reminders'

        )

    )

@app.route(

    '/edit-reminder/<int:reminder_id>',

    methods=['POST']

)
def edit_reminder(

    reminder_id

):

    if 'user_id' not in session:

        return redirect(

            url_for(

                'login'

            )

        )

    reminder = Reminder.query.get_or_404(

        reminder_id

    )

    if reminder.created_by != session.get(

        'username'

    ):

        flash(

            'You cannot edit this reminder.',

            'danger'

        )

        return redirect(

            url_for(

                'reminders'

            )

        )

    reminder.title = request.form.get(

        'title'

    )

    reminder.description = request.form.get(

        'description'

    )

    reminder.reminder_date = parse_date(

        request.form.get(

            'reminder_date'

        )

    )

    reminder.reminder_time = (

        datetime.strptime(

            request.form.get(

                'reminder_time'

            ),

            '%H:%M'

        ).time()

        if request.form.get(

            'reminder_time'

        )

        else None

    )

    reminder.priority = request.form.get(

        'priority'

    )

    reminder.repeat_type = request.form.get(

        'repeat_type'

    )

    db.session.commit()

    flash(

        'Reminder updated successfully.',

        'success'

    )

    return redirect(

        url_for(

            'reminders'

        )

    )

@app.route(

    '/complete-reminder/<int:reminder_id>'

)
def complete_reminder(

    reminder_id

):

    if 'user_id' not in session:

        return redirect(

            url_for(

                'login'

            )

        )

    reminder = Reminder.query.get_or_404(

        reminder_id

    )

    if reminder.created_by != session.get(

        'username'

    ):

        flash(

            'You cannot modify this reminder.',

            'danger'

        )

        return redirect(

            url_for(

                'reminders'

            )

        )

    reminder.status = 'COMPLETED'

    db.session.commit()

    flash(

        'Reminder marked as completed.',

        'success'

    )

    return redirect(

        url_for(

            'reminders'

        )

    )

@app.route(

    '/snooze-reminder/<int:reminder_id>',

    methods=['POST']

)
def snooze_reminder(

    reminder_id

):

    if 'user_id' not in session:

        return redirect(

            url_for(

                'login'

            )

        )

    reminder = Reminder.query.get_or_404(

        reminder_id

    )

    if reminder.created_by != session.get(

        'username'

    ):

        flash(

            'You cannot modify this reminder.',

            'danger'

        )

        return redirect(

            url_for(

                'reminders'

            )

        )

    snooze_option = request.form.get(

        'snooze_option'

    )

    custom_date = request.form.get(

        'custom_date'

    )

    now = datetime.now()

    if snooze_option == 'tomorrow':

        reminder.snooze_until = now + timedelta(

            days=1

        )

    elif snooze_option == '3days':

        reminder.snooze_until = now + timedelta(

            days=3

        )

    elif snooze_option == 'week':

        reminder.snooze_until = now + timedelta(

            days=7

        )

    elif snooze_option == 'custom' and custom_date:

        reminder.snooze_until = datetime.combine(

            parse_date(

                custom_date

            ),

            datetime.min.time()

        )

    

    db.session.commit()

    flash(

        'Reminder snoozed successfully.',

        'success'

    )

    return redirect(

        url_for(

            'reminders'

        )

    )

@app.route(

    '/delete-reminder/<int:reminder_id>',

    methods=['POST']

)
def delete_reminder(

    reminder_id

):

    if 'user_id' not in session:

        return redirect(

            url_for(

                'login'

            )

        )

    reminder = Reminder.query.get_or_404(

        reminder_id

    )

    if reminder.created_by != session.get(

        'username'

    ):

        flash(

            'You cannot delete this reminder.',

            'danger'

        )

        return redirect(

            url_for(

                'reminders'

            )

        )

    db.session.delete(

        reminder

    )

    db.session.commit()

    flash(

        'Reminder deleted successfully.',

        'success'

    )

    return redirect(

        url_for(

            'reminders'

        )

    )

if __name__ == '__main__':

    app.run(debug=False)

    