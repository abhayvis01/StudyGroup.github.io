# app.py
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from forms import RegistrationForm, LoginForm
from data_manager import DataManager
import uuid
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
import pickle

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this!

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize DataManager
data_manager = DataManager()

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.created_at = user_data['created_at']
        self.meetings = user_data.get('meetings', [])

@login_manager.user_loader  
def load_user(user_id):
    user_data = data_manager.get_user_by_id(user_id)
    if user_data:
        return User(user_data)
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        success, message = data_manager.add_user(
            username=form.username.data,
            password=form.password.data
        )
        
        if success:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        success, user_data = data_manager.verify_user(
            username=form.username.data,
            password=form.password.data
        )
        
        if success:
            user = User(user_data)
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_data = data_manager.get_user_by_id(current_user.id)
    meetings = user_data.get('meetings', [])
    return render_template('dashboard.html', meetings=meetings)

SCOPES = ['https://www.googleapis.com/auth/calendar']
CLIENT_SECRETS_FILE = "path/to/your/client_secrets.json"

def get_calendar_service():
    creds = None
    # Check if we have stored credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials are invalid or don't exist, let's create them
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            flow.redirect_uri = url_for('oauth2callback', _external=True)
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            session['state'] = state
            return redirect(authorization_url)
            
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('calendar', 'v3', credentials=creds)

@app.route('/create-meeting', methods=['GET', 'POST'])
@login_required
def create_meeting():
    if request.method == 'POST':
        meeting_name = request.form.get('meeting_name')
        meeting_date = request.form.get('meeting_date')
        meeting_time = request.form.get('meeting_time')
        
        if not all([meeting_name, meeting_date, meeting_time]):
            flash('Please fill all fields', 'error')
            return redirect(url_for('create_meeting'))
        
        try:
            # Get Google Calendar service
            service = get_calendar_service()
            
            # Create datetime for meeting
            start_time = datetime.datetime.strptime(f"{meeting_date} {meeting_time}", "%Y-%m-%d %H:%M")
            end_time = start_time + datetime.timedelta(hours=1)  # Default 1-hour meeting
            
            # Create meeting event
            event = {
                'summary': meeting_name,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': str(uuid.uuid4()),
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
            }
            
            event = service.events().insert(
                calendarId='primary',
                body=event,
                conferenceDataVersion=1
            ).execute()
            
            # Get the Google Meet link from the created event
            meet_link = event['conferenceData']['entryPoints'][0]['uri']
            meeting_id = str(uuid.uuid4())
            
            # Save meeting details
            meeting_data = {
                'id': meeting_id,
                'name': meeting_name,
                'date': meeting_date,
                'time': meeting_time,
                'meet_link': meet_link,
                'created_by': current_user.username,
                'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'calendar_event_id': event['id']
            }
            
            success = data_manager.add_meeting(current_user.id, meeting_data)
            
            if success:
                flash('Meeting created successfully!', 'success')
                return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error creating meeting: {str(e)}', 'error')
            
    return render_template('create_meeting.html')

@app.route('/join-meeting/<meeting_id>')
@login_required
def join_meeting(meeting_id):
    meeting = data_manager.get_meeting(current_user.id, meeting_id)
    if meeting:
        # Redirect to the Google Meet link
        return redirect(meeting['meet_link'])
    flash('Meeting not found', 'error')
    return redirect(url_for('dashboard'))

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_authenticated or current_user.username != 'admin':
        return redirect(url_for('dashboard'))
    
    users = data_manager.get_all_users()
    return render_template('admin_users.html', users=users)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)
    
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    
    credentials = flow.credentials
    with open('token.pickle', 'wb') as token:
        pickle.dump(credentials, token)
    
    return redirect(url_for('create_meeting'))

if __name__ == '__main__':
    app.run(debug=True)
