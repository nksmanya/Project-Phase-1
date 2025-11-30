# ===============================
# app.py - FeelUP Flask App (Updated with AI Mood Journal & Fixes)
# ===============================

from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from sqlalchemy import func
from flask_login import LoginManager, login_user, login_required, logout_user, current_user as flask_current_user, UserMixin

# NLP for AI Mood Journal
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

# ===============================
# Models
# ===============================

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def check_password(self, pwd):
        return check_password_hash(self.password_hash, pwd)

class MoodPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(120))
    content = db.Column(db.Text, nullable=False)
    emotion = db.Column(db.String(50))
    anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reactions = db.Column(db.PickleType, default=dict)
    comments = db.relationship('Comment', backref='mood', cascade="all, delete-orphan")
    likes = db.relationship('Like', backref='mood', cascade="all, delete-orphan")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mood_id = db.Column(db.Integer, db.ForeignKey('mood_post.id'))
    user = db.Column(db.String(120))
    text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mood_id = db.Column(db.Integer, db.ForeignKey('mood_post.id'))
    user = db.Column(db.String(120))

class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    username = db.Column(db.String(120))
    title = db.Column(db.String(200))
    body = db.Column(db.Text)
    tag = db.Column(db.String(120))
    anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_name = db.Column(db.String(120))
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    datetime_event = db.Column(db.DateTime)  # <- updated column
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    joins = db.relationship('EventJoin', backref='event', cascade="all, delete-orphan")


class EventJoin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    name = db.Column(db.String(120))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

# Follow System
class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

# AI Mood Journal
class MoodJournal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.Date, default=datetime.utcnow().date())
    emotion = db.Column(db.String(50))
    text = db.Column(db.Text)
    sentiment_score = db.Column(db.Float)  # -1 (negative) to +1 (positive)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# New: store individual mood check-ins (multiple per day allowed)
class MoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    mood = db.Column(db.String(50))        # emoji or label
    score = db.Column(db.Float)            # optional numeric score (-1..1)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# New: Journal notes separate from MoodJournal (free-form private notes)
class JournalNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200))
    body = db.Column(db.Text)
    tags = db.Column(db.String(200))
    pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ===============================
# Initialize Database
# ===============================
with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None

# ===============================
# Helper Functions
# ===============================
def current_user():
    # Prefer Flask-Login's current_user when available
    try:
        if flask_current_user and flask_current_user.is_authenticated:
            return flask_current_user
    except Exception:
        pass
    uid = session.get('user_id')
    if uid:
        return User.query.get(uid)
    return None

def mood_stats():
    from collections import Counter
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    moods = MoodPost.query.filter(MoodPost.created_at >= one_week_ago).all()
    mood_list = [m.emotion for m in moods]
    stats = Counter(mood_list)
    return stats

def memory_suggestions(user):
    if not user:
        return []
    my_tags = [m.tag for m in Memory.query.filter_by(user_id=user.id).all()]
    suggestions = Memory.query.filter(Memory.tag.in_(my_tags), Memory.user_id != user.id).limit(5).all()
    return suggestions

def analyze_mood(text):
    scores = sia.polarity_scores(text)
    compound = scores['compound']
    if compound >= 0.05:
        return "positive", compound
    elif compound <= -0.05:
        return "negative", compound
    else:
        return "neutral", compound


def compute_streak(user_id):
    # Compute consecutive-day streak ending today based on MoodEntry dates
    from sqlalchemy import func
    dates = db.session.query(func.date(MoodEntry.created_at)).filter(MoodEntry.user_id==user_id).distinct().order_by(MoodEntry.created_at.desc()).all()
    dates = [d[0] for d in dates]
    if not dates:
        return 0
    streak = 0
    today = datetime.utcnow().date()
    current = today
    for d in dates:
        # SQL returns strings for sqlite, ensure date
        try:
            entry_date = d if isinstance(d, datetime) else datetime.strptime(str(d), '%Y-%m-%d').date()
        except Exception:
            entry_date = d
        if entry_date == current:
            streak += 1
            current = current - timedelta(days=1)
        elif entry_date < current:
            break
    return streak


def ai_recommendations(user, recent_entries):
    # Simple rule-based recommendations using recent sentiment
    if not user:
        return { 'message': 'Login to get personalized recommendations.' }
    if not recent_entries:
        return {
            'message': 'No recent entries found. Try a quick check-in to get started.',
            'suggestions': ['Take a 5-minute breathing break', 'Write one positive thing that happened today']
        }
    pos = sum(1 for e in recent_entries if (e.score or 0) > 0.05)
    neg = sum(1 for e in recent_entries if (e.score or 0) < -0.05)
    neutral = len(recent_entries) - pos - neg

    suggestions = []
    if neg > pos:
        suggestions = [
            'Take a 10-minute walk in nature',
            'Try a grounding exercise: 5 senses check',
            'Write down 3 things you are grateful for'
        ]
        tone = 'It seems you had more challenging moments recently. That is okay — small steps help.'
    elif pos >= neg:
        suggestions = [
            'Keep up the momentum — try a small creative task',
            'Share a positive moment in your journal',
            'Try a short gratitude list before bed'
        ]
        tone = 'Nice work — you have several positive check-ins. Keep nurturing these moments.'

    goal = 'Try to check in at least once a day this week.'

    return {
        'message': tone,
        'suggestions': suggestions,
        'daily_goal': goal
    }

# ===============================
# Routes
# ===============================

@app.route('/')
def index():
    if current_user():
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        name = request.form.get('name') or "Anonymous"
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already registered','danger')
            return redirect(url_for('register'))
        user = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        # Log the user in immediately after registration for a smoother flow
        login_user(user)
        session['user_id'] = user.id
        flash('Registration successful — welcome!','success')
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        flash('Invalid credentials','danger')
        return redirect(url_for('index'))
    # Use Flask-Login to manage the session
    login_user(user)
    session['user_id'] = user.id
    flash('Welcome, '+(user.name or user.email),'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    try:
        logout_user()
    except Exception:
        pass
    session.clear()
    flash('Logged out','info')
    return redirect(url_for('index'))

# ----- Dashboard with Mood Analytics -----
@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()
    if not user:
        return redirect(url_for('index'))

    recent_moods = MoodPost.query.order_by(MoodPost.created_at.desc()).limit(5).all()

    # -------------------------------
    # Upcoming events: use Event.datetime_event (DateTime column)
    all_events = Event.query.filter(Event.datetime_event != None).order_by(Event.datetime_event.asc()).all()
    upcoming_events = [ev for ev in all_events if ev.datetime_event >= datetime.utcnow()]
    upcoming_events = upcoming_events[:5]
    # -------------------------------

    analytics = mood_stats()
    suggestions = memory_suggestions(user)

    users = User.query.all()
    followed_ids = [f.followed_id for f in Follow.query.filter_by(follower_id=user.id).all()]
    followed_users = [User.query.get(uid) for uid in followed_ids]

    # Mood Journal Analytics (simple journal scores)
    last_week = datetime.utcnow().date() - timedelta(days=6)
    journal_entries = MoodJournal.query.filter(MoodJournal.user_id==user.id, MoodJournal.date >= last_week).order_by(MoodJournal.date.asc()).all()
    journal_dates = [e.date.strftime("%a") for e in journal_entries]
    journal_scores = [e.sentiment_score for e in journal_entries]

    # -------------------------------
    # MoodEntry analytics: weekly averages, 30-day counts/averages, mood distribution
    seven_days_ago = datetime.utcnow().date() - timedelta(days=6)
    weekly_q = db.session.query(
        func.date(MoodEntry.created_at).label('d'),
        func.avg(MoodEntry.score).label('avg_score')
    ).filter(
        MoodEntry.user_id==user.id,
        func.date(MoodEntry.created_at) >= seven_days_ago
    ).group_by(func.date(MoodEntry.created_at)).order_by(func.date(MoodEntry.created_at).asc()).all()

    weekly_labels = []
    weekly_scores = []
    for i in range(7):
        d = seven_days_ago + timedelta(days=i)
        weekly_labels.append(d.strftime('%a'))
        matched = next((r.avg_score for r in weekly_q if str(r.d) == d.strftime('%Y-%m-%d')), None)
        weekly_scores.append(round(matched,3) if matched is not None else None)

    thirty_days_ago = datetime.utcnow().date() - timedelta(days=29)
    monthly_q = db.session.query(
        func.date(MoodEntry.created_at).label('d'),
        func.count(MoodEntry.id).label('cnt'),
        func.avg(MoodEntry.score).label('avg')
    ).filter(
        MoodEntry.user_id==user.id,
        func.date(MoodEntry.created_at) >= thirty_days_ago
    ).group_by(func.date(MoodEntry.created_at)).order_by(func.date(MoodEntry.created_at).asc()).all()

    monthly_labels = []
    monthly_counts = []
    monthly_avgs = []
    for i in range(30):
        d = thirty_days_ago + timedelta(days=i)
        monthly_labels.append(d.strftime('%b %d'))
        matched = next((r for r in monthly_q if str(r.d) == d.strftime('%Y-%m-%d')), None)
        if matched:
            monthly_counts.append(matched.cnt)
            monthly_avgs.append(round(matched.avg,3) if matched.avg is not None else 0)
        else:
            monthly_counts.append(0)
            monthly_avgs.append(0)

    dist_q = db.session.query(MoodEntry.mood, func.count(MoodEntry.id)).filter(
        MoodEntry.user_id==user.id,
        func.date(MoodEntry.created_at) >= thirty_days_ago
    ).group_by(MoodEntry.mood).all()
    dist_labels = [r[0] or 'unknown' for r in dist_q]
    dist_counts = [r[1] for r in dist_q]

    return render_template(
        'dashboard.html',
        user=user, moods=recent_moods, events=upcoming_events,
        analytics=analytics, suggestions=suggestions,
        users=users, followed_users=followed_users,
        journal_dates=journal_dates, journal_scores=journal_scores,
        weekly_labels=weekly_labels, weekly_scores=weekly_scores,
        monthly_labels=monthly_labels, monthly_counts=monthly_counts, monthly_avgs=monthly_avgs,
        dist_labels=dist_labels, dist_counts=dist_counts
    )
# ===============================
# Mood Feed
# ===============================
@app.route('/mood', methods=['GET','POST'])
@login_required
def mood_feed():
    user = current_user()
    if request.method=='POST':
        content = request.form.get('content')
        emotion = request.form.get('emotion') or 'neutral'
        anonymous = True if request.form.get('anonymous')=='on' else False
        username = "Anonymous" if anonymous or not user else user.name
        uid = None if anonymous or not user else user.id
        if not content:
            flash('Enter something to post','warning')
            return redirect(url_for('mood_feed'))
        post = MoodPost(user_id=uid, username=username, content=content, emotion=emotion, anonymous=anonymous)
        db.session.add(post)
        db.session.commit()
        flash('Mood posted','success')
        return redirect(url_for('mood_feed'))
    moods = MoodPost.query.order_by(MoodPost.created_at.desc()).all()
    return render_template('mood_feed.html', moods=moods, user=user)

@app.route('/mood/<int:post_id>/react/<emoji>', methods=['POST'])
def react_to_mood(post_id, emoji):
    mood = MoodPost.query.get_or_404(post_id)
    if not mood.reactions:
        mood.reactions = {}
    mood.reactions[emoji] = mood.reactions.get(emoji, 0) + 1
    db.session.commit()
    return jsonify({"emoji": emoji, "count": mood.reactions[emoji]})

@app.route('/mood/<int:post_id>/comment', methods=['POST'])
def comment_post(post_id):
    name = request.form.get('name') or (current_user().name if current_user() else 'Guest')
    text = request.form.get('comment')
    if not text:
        flash('Comment cannot be empty','warning')
        return redirect(request.referrer or url_for('mood_feed'))
    c = Comment(mood_id=post_id, user=name, text=text)
    db.session.add(c)
    db.session.commit()
    return redirect(request.referrer or url_for('mood_feed'))

# ===============================
# Memory
# ===============================
@app.route('/memory', methods=['GET','POST'])
@login_required
def memory():
    user = current_user()
    if request.method=='POST':
        title = request.form.get('title')
        body = request.form.get('body')
        tag = request.form.get('tag') or 'General'
        anonymous = True if request.form.get('anonymous')=='on' else False
        username = "Anonymous" if anonymous or not user else user.name
        uid = None if anonymous or not user else user.id
        mem = Memory(user_id=uid, username=username, title=title, body=body, tag=tag, anonymous=anonymous)
        db.session.add(mem)
        db.session.commit()
        flash('Memory shared','success')
        return redirect(url_for('memory'))
    tag = request.args.get('tag')
    if tag:
        memories = Memory.query.filter_by(tag=tag).order_by(Memory.created_at.desc()).all()
    else:
        memories = Memory.query.order_by(Memory.created_at.desc()).limit(50).all()
    return render_template('memory.html', memories=memories, user=user)

# ===============================
# Events
# ===============================
@app.route('/events')
@login_required
def events():
    user = current_user()
    # Show events ordered by upcoming datetime
    events = Event.query.order_by(Event.datetime_event.asc()).all()
    return render_template('events.html', user=user, events=events)

@app.route('/events/create', methods=['GET','POST'])
@login_required
def create_event():
    user = current_user()
    if request.method=='POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        datetime_input = request.form.get('datetime')  # e.g. "2025-08-29 15:30"
        host_name = user.name if user else "Anonymous"

        dt_event = datetime.strptime(datetime_input, "%Y-%m-%d %H:%M")
        ev = Event(title=title, description=description, location=location, datetime_event=dt_event, host_name=host_name)
        db.session.add(ev)
        db.session.commit()
        flash('Event created','success')
        return redirect(url_for('events'))
    return render_template('event_create.html', user=user)
@app.route('/events/<int:event_id>/join', methods=['POST'])
@login_required
def join_event(event_id):
    user = current_user()
    event = Event.query.get_or_404(event_id)
    name = user.name if user else request.form.get('name') or 'Guest'
    
    # Prevent joining same event multiple times
    existing_join = EventJoin.query.filter_by(event_id=event.id, name=name).first()
    if not existing_join:
        join = EventJoin(event_id=event.id, name=name)
        db.session.add(join)
        db.session.commit()
        flash('You joined the event', 'success')
    else:
        flash('You have already joined this event', 'info')
    
    return redirect(url_for('events'))

# ===============================
# Follow System
# ===============================
@app.route('/follow/<int:user_id>', methods=['POST'])
@login_required
def follow_user(user_id):
    user = current_user()
    if not user or user.id==user_id:
        return redirect(request.referrer or url_for('dashboard'))
    if not Follow.query.filter_by(follower_id=user.id, followed_id=user_id).first():
        f = Follow(follower_id=user.id, followed_id=user_id)
        db.session.add(f)
        db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/unfollow/<int:user_id>', methods=['POST'])
@login_required
def unfollow_user(user_id):
    user = current_user()
    if not user:
        return redirect(request.referrer or url_for('dashboard'))
    f = Follow.query.filter_by(follower_id=user.id, followed_id=user_id).first()
    if f:
        db.session.delete(f)
        db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))

# ===============================
# Messaging
# ===============================
@app.route('/messages')
def messages():
    user = current_user()
    if not user:
        return redirect(url_for('index'))
    conversations = db.session.query(User).join(
        Message, ((Message.sender_id==User.id)&(Message.receiver_id==user.id)) |
                 ((Message.receiver_id==User.id)&(Message.sender_id==user.id))
    ).distinct().all()
    return render_template('messages.html', user=user, conversations=conversations)

@app.route('/messages/<int:other_user_id>', methods=['GET','POST'])
def chat(other_user_id):
    user = current_user()
    if not user:
        return redirect(url_for('index'))
    other_user = User.query.get_or_404(other_user_id)
    if request.method=='POST':
        text = request.form.get('text')
        if text:
            msg = Message(sender_id=user.id, receiver_id=other_user.id, text=text)
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for('chat', other_user_id=other_user.id))
    msgs = Message.query.filter(
        ((Message.sender_id==user.id)&(Message.receiver_id==other_user.id)) |
        ((Message.sender_id==other_user.id)&(Message.receiver_id==user.id))
    ).order_by(Message.created_at.asc()).all()
    return render_template('chat.html', user=user, other_user=other_user, messages=msgs)


@app.route('/users')
def users_list():
    user = current_user()
    if not user:
        return redirect(url_for('index'))
    
    users = User.query.all()
    followed_ids = [f.followed_id for f in Follow.query.filter_by(follower_id=user.id).all()]
    followed_users = [User.query.get(uid) for uid in followed_ids]

    # Pass list of followed IDs directly to template
    return render_template('users.html', user=user, users=users, followed_ids=followed_ids)


# ===============================
# AI Mood Journal Routes
# ===============================
@app.route('/journal', methods=['GET', 'POST'])
def journal():
    user = current_user()
    if not user:
        return redirect(url_for('index'))

    if request.method == 'POST':
        text = request.form.get('text')
        emotion = request.form.get('emotion')
        if not text:
            flash('Please write something about your mood.', 'warning')
            return redirect(url_for('journal'))

        detected_emotion, score = analyze_mood(text)
        final_emotion = emotion if emotion else detected_emotion

        entry = MoodJournal(user_id=user.id, text=text, emotion=final_emotion, sentiment_score=score)
        db.session.add(entry)
        db.session.commit()
        flash('Mood journal entry saved!', 'success')
        return redirect(url_for('journal'))

    today_entry = MoodJournal.query.filter_by(user_id=user.id, date=datetime.utcnow().date()).first()
    # load recent entries for listing
    # pagination for previous entries
    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            page = 1
    except Exception:
        page = 1
    page_size = 10
    base_q = MoodJournal.query.filter_by(user_id=user.id)
    total = base_q.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    if page > total_pages:
        page = total_pages
    entries = base_q.order_by(MoodJournal.date.desc(), MoodJournal.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return render_template('journal.html', user=user, today_entry=today_entry, entries=entries, page=page, total_pages=total_pages)


@app.route('/checkin', methods=['GET','POST'])
def checkin():
    user = current_user()
    if not user:
        return redirect(url_for('index'))
    if request.method == 'POST':
        mood = request.form.get('mood')
        note = request.form.get('note')
        # If user provided text note, analyze sentiment
        score = None
        if note:
            _, score = analyze_mood(note)
        entry = MoodEntry(user_id=user.id, mood=mood, note=note, score=score)
        db.session.add(entry)
        db.session.commit()
        flash('Check-in saved','success')
        return redirect(url_for('dashboard'))

    # show last check-in for today if exists
    today = datetime.utcnow().date()
    last = MoodEntry.query.filter(MoodEntry.user_id==user.id, MoodEntry.created_at >= datetime.combine(today, datetime.min.time())).order_by(MoodEntry.created_at.desc()).first()
    return render_template('checkin.html', user=user, last=last)


@app.route('/coach')
def coach():
    user = current_user()
    if not user:
        return redirect(url_for('index'))
    # recent 14 entries
    recent_entries = MoodEntry.query.filter_by(user_id=user.id).order_by(MoodEntry.created_at.desc()).limit(14).all()
    recs = ai_recommendations(user, recent_entries)
    streak = compute_streak(user.id)
    # last note
    last_note = JournalNote.query.filter_by(user_id=user.id).order_by(JournalNote.created_at.desc()).first()
    return render_template('coach.html', user=user, recs=recs, streak=streak, last_note=last_note)

@app.route('/journal/analytics')
def journal_analytics():
    user = current_user()
    if not user:
        return redirect(url_for('index'))
    last_30_days = datetime.utcnow().date() - timedelta(days=29)
    entries = MoodJournal.query.filter(MoodJournal.user_id==user.id, MoodJournal.date>=last_30_days).order_by(MoodJournal.date.asc()).all()
    dates = [e.date.strftime("%b %d") for e in entries]
    scores = [e.sentiment_score for e in entries]
    return render_template('journal_analytics.html', user=user, dates=dates, scores=scores)

@app.route('/profile/<int:user_id>')
def profile(user_id):
    user = current_user()
    other_user = User.query.get_or_404(user_id)
    
    # Optional: show user's moods, memories, etc.
    moods = MoodPost.query.filter_by(user_id=other_user.id).order_by(MoodPost.created_at.desc()).all()
    memories = Memory.query.filter_by(user_id=other_user.id).order_by(Memory.created_at.desc()).all()
    
    return render_template('profile.html', user=user, other_user=other_user, moods=moods, memories=memories)

# Mood Edit/Delete
@app.route('/mood/<int:post_id>/edit', methods=['GET','POST'])
def edit_mood(post_id):
    user = current_user()
    mood = MoodPost.query.get_or_404(post_id)
    if not user or mood.user_id != user.id:
        flash('Not authorized', 'danger')
        return redirect(url_for('mood_feed'))
    if request.method=='POST':
        mood.content = request.form.get('content')
        mood.emotion = request.form.get('emotion')
        db.session.commit()
        flash('Mood updated', 'success')
        return redirect(url_for('mood_feed'))
    return render_template('edit_mood.html', mood=mood)

@app.route('/mood/<int:post_id>/delete')
def delete_mood(post_id):
    user = current_user()
    mood = MoodPost.query.get_or_404(post_id)
    if not user or mood.user_id != user.id:
        flash('Not authorized', 'danger')
        return redirect(url_for('mood_feed'))
    db.session.delete(mood)
    db.session.commit()
    flash('Mood deleted', 'success')
    return redirect(url_for('mood_feed'))

# Memory Edit/Delete
@app.route('/memory/<int:memory_id>/edit', methods=['GET','POST'])
def edit_memory(memory_id):
    user = current_user()
    mem = Memory.query.get_or_404(memory_id)
    if not user or mem.user_id != user.id:
        flash('Not authorized', 'danger')
        return redirect(url_for('memory'))
    if request.method=='POST':
        mem.title = request.form.get('title')
        mem.body = request.form.get('body')
        mem.tag = request.form.get('tag')
        db.session.commit()
        flash('Memory updated', 'success')
        return redirect(url_for('memory'))
    return render_template('edit_memory.html', memory=mem)

@app.route('/memory/<int:memory_id>/delete')
def delete_memory(memory_id):
    user = current_user()
    mem = Memory.query.get_or_404(memory_id)
    if not user or mem.user_id != user.id:
        flash('Not authorized', 'danger')
        return redirect(url_for('memory'))
    db.session.delete(mem)
    db.session.commit()
    flash('Memory deleted', 'success')
    return redirect(url_for('memory'))


# ===============================
# Run App
# ===============================
if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  
