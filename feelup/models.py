from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


# SQLAlchemy instance (initialized in app.py)
db = SQLAlchemy()


# Association tables
room_members = db.Table(
'room_members',
db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
db.Column('room_id', db.Integer, db.ForeignKey('memory_room.id')),
)


event_members = db.Table(
'event_members',
db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
)


class User(UserMixin, db.Model):
id = db.Column(db.Integer, primary_key=True)
name = db.Column(db.String(120), nullable=False)
email = db.Column(db.String(120), unique=True, nullable=False)
password_hash = db.Column(db.String(256), nullable=False)
created_at = db.Column(db.DateTime, default=datetime.utcnow)


posts = db.relationship('Post', backref='author', lazy=True)


def set_password(self, password: str):
self.password_hash = generate_password_hash(password)


def check_password(self, password: str) -> bool:
return check_password_hash(self.password_hash, password)


class Post(db.Model):
id = db.Column(db.Integer, primary_key=True)
body = db.Column(db.Text, nullable=False)
mood = db.Column(db.String(50), nullable=True) # e.g., "anxious", "hopeful"
is_anonymous = db.Column(db.Boolean, default=False)
created_at = db.Column(db.DateTime, default=datetime.utcnow)


user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
room_id = db.Column(db.Integer, db.ForeignKey('memory_room.id'), nullable=True) # optional link to a memory room


class MemoryRoom(db.Model):
id = db.Column(db.Integer, primary_key=True)
title = db.Column(db.String(140), nullable=False) # e.g., "9th Grade - 2017 - XYZ School"
description = db.Column(db.Text, nullable=True)
created_at = db.Column(db.DateTime, default=datetime.utcnow)


members = db.relationship('User', secondary=room_members, backref='rooms')
posts = db.relationship('Post', backref='room', lazy=True)


class Event(db.Model):
id = db.Column(db.Integer, primary_key=True)
title = db.Column(db.String(140), nullable=False)
description = db.Column(db.Text, nullable=True)
location = db.Column(db.String(140), nullable=True) # e.g., "Marina Beach"
attendees = db.relationship('User', secondary=event_members, backref='events')