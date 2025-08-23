import os


@app.route('/rooms/create', methods=['GET', 'POST'])
@login_required
def memory_room_create():
if request.method == 'POST':
title = request.form.get('title', '').strip()
desc = request.form.get('description', '').strip()
if not title:
flash('Title is required', 'danger')
return redirect(url_for('memory_room_create'))
room = MemoryRoom(title=title, description=desc)
room.members.append(current_user)
db.session.add(room)
db.session.commit()
flash('Memory room created', 'success')
return redirect(url_for('memory_rooms'))
return render_template('memory_room_create.html')


@app.route('/rooms/<int:room_id>')
@login_required
def memory_room_detail(room_id):
room = db.session.get(MemoryRoom, room_id)
if not room:
flash('Room not found', 'warning')
return redirect(url_for('memory_rooms'))
return render_template('memory_room_detail.html', room=room)


@app.route('/rooms/<int:room_id>/join')
@login_required
def memory_room_join(room_id):
room = db.session.get(MemoryRoom, room_id)
if not room:
flash('Room not found', 'warning')
return redirect(url_for('memory_rooms'))
if current_user not in room.members:
room.members.append(current_user)
db.session.commit()
flash('Joined room', 'success')
return redirect(url_for('memory_room_detail', room_id=room_id))


# ---------- Events ----------
@app.route('/events')
@login_required
def events():
upcoming = Event.query.order_by(Event.when.asc()).all()
return render_template('events.html', events=upcoming)


@app.route('/events/create', methods=['GET', 'POST'])
@login_required
def event_create():
if request.method == 'POST':
title = request.form.get('title', '').strip()
desc = request.form.get('description', '').strip()
location = request.form.get('location', '').strip()
when_str = request.form.get('when', '').strip()
try:
when = datetime.fromisoformat(when_str)
except Exception:
flash('Invalid date/time. Use ISO format: YYYY-MM-DD HH:MM', 'danger')
return redirect(url_for('event_create'))
if not title:
flash('Title is required', 'danger')
return redirect(url_for('event_create'))
event = Event(title=title, description=desc, location=location, when=when, host=current_user)
event.attendees.append(current_user)
db.session.add(event)
db.session.commit()
flash('Event created', 'success')
return redirect(url_for('events'))
return render_template('event_create.html')