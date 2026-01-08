# Автор проекта: Ли Никита
# Тема: Цифровая система управления гостиницей
# Hotel Management System - Main Application

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = 'li_nikita_hotel_system_2024'

# Custom Jinja2 filters
@app.template_filter('format_number')
def format_number(value):
    """Format number with thousand separators"""
    if value is None:
        return "0"
    try:
        return "{:,.0f}".format(float(value)).replace(',', ' ')
    except (ValueError, TypeError):
        return str(value)

@app.template_filter('format_decimal')
def format_decimal(value, decimals=1):
    """Format decimal number"""
    if value is None:
        return "0.0"
    try:
        return "{:.{}f}".format(float(value), decimals)
    except (ValueError, TypeError):
        return str(value)

# Database initialization
def init_db():
    conn = sqlite3.connect('hotel_system.db')
    c = conn.cursor()
    
    # Rooms table
    c.execute('''CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT UNIQUE NOT NULL,
        room_type TEXT NOT NULL,
        status TEXT DEFAULT 'available',
        price REAL NOT NULL,
        created_by TEXT DEFAULT 'Li Nikita'
    )''')
    
    # Guests table
    c.execute('''CREATE TABLE IF NOT EXISTS guests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        check_in DATE,
        check_out DATE,
        room_id INTEGER,
        status TEXT DEFAULT 'active',
        FOREIGN KEY (room_id) REFERENCES rooms (id)
    )''')
    
    # Tasks table
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id INTEGER,
        task_type TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        assigned_to TEXT,
        FOREIGN KEY (room_id) REFERENCES rooms (id)
    )''')
    
    # Quality checks table
    c.execute('''CREATE TABLE IF NOT EXISTS quality_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id INTEGER,
        cleanliness_score INTEGER,
        amenities_score INTEGER,
        maintenance_score INTEGER,
        notes TEXT,
        checked_by TEXT,
        check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (room_id) REFERENCES rooms (id)
    )''')
    
    # Insert sample data if tables are empty
    c.execute('SELECT COUNT(*) FROM rooms')
    if c.fetchone()[0] == 0:
        sample_rooms = [
            ('101', 'Standard', 'available', 350000.00),
            ('102', 'Standard', 'occupied', 350000.00),
            ('201', 'Deluxe', 'cleaning', 500000.00),
            ('202', 'Deluxe', 'maintenance', 500000.00),
            ('301', 'Suite', 'available', 750000.00)
        ]
        c.executemany('INSERT INTO rooms (room_number, room_type, status, price) VALUES (?, ?, ?, ?)', sample_rooms)
    
    conn.commit()
    conn.close()

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('hotel_system.db')
    conn.row_factory = sqlite3.Row
    return conn

def sync_room_statuses():
    """Синхронизирует статусы номеров с активными гостями"""
    conn = get_db_connection()
    
    # Устанавливаем статус 'occupied' для номеров с активными гостями
    conn.execute('''
        UPDATE rooms 
        SET status = 'occupied' 
        WHERE id IN (
            SELECT DISTINCT room_id 
            FROM guests 
            WHERE status = 'active'
        ) AND status NOT IN ('maintenance', 'cleaning')
    ''')
    
    # Устанавливаем статус 'available' для пустых номеров (кроме тех, что на ремонте или уборке)
    conn.execute('''
        UPDATE rooms 
        SET status = 'available' 
        WHERE status = 'occupied' 
        AND id NOT IN (
            SELECT DISTINCT room_id 
            FROM guests 
            WHERE status = 'active'
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def dashboard():
    # Синхронизируем статусы номеров перед отображением
    sync_room_statuses()
    
    conn = get_db_connection()
    
    # Get room statistics
    room_stats = conn.execute('''
        SELECT status, COUNT(*) as count 
        FROM rooms 
        GROUP BY status
    ''').fetchall()
    
    # Get recent tasks
    recent_tasks = conn.execute('''
        SELECT t.*, r.room_number 
        FROM tasks t 
        JOIN rooms r ON t.room_id = r.id 
        ORDER BY t.created_at DESC 
        LIMIT 5
    ''').fetchall()
    
    # Get quality scores
    quality_avg = conn.execute('''
        SELECT AVG(cleanliness_score) as cleanliness,
               AVG(amenities_score) as amenities,
               AVG(maintenance_score) as maintenance
        FROM quality_checks 
        WHERE check_date >= date('now', '-30 days')
    ''').fetchone()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         room_stats=room_stats, 
                         recent_tasks=recent_tasks,
                         quality_avg=quality_avg)

@app.route('/rooms')
def rooms():
    # Синхронизируем статусы номеров перед отображением
    sync_room_statuses()
    
    conn = get_db_connection()
    rooms = conn.execute('SELECT * FROM rooms ORDER BY room_number').fetchall()
    conn.close()
    return render_template('rooms.html', rooms=rooms)

@app.route('/update_room_status', methods=['POST'])
def update_room_status():
    room_id = request.form['room_id']
    new_status = request.form['status']
    
    conn = get_db_connection()
    conn.execute('UPDATE rooms SET status = ? WHERE id = ?', (new_status, room_id))
    conn.commit()
    conn.close()
    
    flash('Статус номера обновлен!', 'success')
    return redirect(url_for('rooms'))

@app.route('/guests')
def guests():
    conn = get_db_connection()
    guests = conn.execute('''
        SELECT g.*, r.room_number 
        FROM guests g 
        LEFT JOIN rooms r ON g.room_id = r.id 
        WHERE g.status = 'active'
        ORDER BY g.check_in DESC
    ''').fetchall()
    conn.close()
    return render_template('guests.html', guests=guests)

@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        room_id = request.form['room_id']
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        
        conn = get_db_connection()
        
        # Add guest
        conn.execute('''
            INSERT INTO guests (name, phone, email, room_id, check_in, check_out)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, phone, email, room_id, check_in, check_out))
        
        # Update room status
        conn.execute('UPDATE rooms SET status = "occupied" WHERE id = ?', (room_id,))
        
        conn.commit()
        conn.close()
        
        flash('Гость успешно заселен!', 'success')
        return redirect(url_for('guests'))
    
    # GET request - show form
    conn = get_db_connection()
    available_rooms = conn.execute(
        'SELECT * FROM rooms WHERE status = "available" ORDER BY room_number'
    ).fetchall()
    conn.close()
    
    return render_template('checkin.html', rooms=available_rooms)

@app.route('/checkout/<int:guest_id>')
def checkout(guest_id):
    conn = get_db_connection()
    
    # Get guest info
    guest = conn.execute('SELECT * FROM guests WHERE id = ?', (guest_id,)).fetchone()
    
    if guest:
        # Update guest status
        conn.execute('UPDATE guests SET status = "checked_out" WHERE id = ?', (guest_id,))
        
        # Update room status to cleaning
        conn.execute('UPDATE rooms SET status = "cleaning" WHERE id = ?', (guest['room_id'],))
        
        # Create cleaning task
        conn.execute('''
            INSERT INTO tasks (room_id, task_type, description, status)
            VALUES (?, 'cleaning', 'Уборка после выселения гостя', 'pending')
        ''', (guest['room_id'],))
        
        conn.commit()
        flash('Гость выселен. Номер отправлен на уборку.', 'success')
    
    conn.close()
    return redirect(url_for('guests'))

@app.route('/tasks')
def tasks():
    conn = get_db_connection()
    tasks = conn.execute('''
        SELECT t.*, r.room_number 
        FROM tasks t 
        JOIN rooms r ON t.room_id = r.id 
        ORDER BY t.created_at DESC
    ''').fetchall()
    
    # Get rooms for task creation modal
    rooms = conn.execute('SELECT * FROM rooms ORDER BY room_number').fetchall()
    
    conn.close()
    return render_template('tasks.html', tasks=tasks, rooms=rooms)

@app.route('/create_task', methods=['POST'])
def create_task():
    try:
        room_id = request.form['room_id']
        task_type = request.form['task_type']
        description = request.form['description']
        assigned_to = request.form.get('assigned_to', '')
        
        print(f"Создание задачи: room_id={room_id}, task_type={task_type}, description={description}, assigned_to={assigned_to}")
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO tasks (room_id, task_type, description, assigned_to)
            VALUES (?, ?, ?, ?)
        ''', (room_id, task_type, description, assigned_to))
        conn.commit()
        conn.close()
        
        flash('Задача создана!', 'success')
        print("Задача успешно создана")
        
    except Exception as e:
        print(f"Ошибка при создании задачи: {e}")
        flash(f'Ошибка при создании задачи: {str(e)}', 'error')
    
    return redirect(url_for('tasks'))

@app.route('/test_tasks')
def test_tasks():
    return render_template('test_tasks.html')

@app.route('/simple_task_form')
def simple_task_form():
    return render_template('simple_task_form.html')

@app.route('/debug_form')
def debug_form():
    return render_template('debug_form.html')

@app.route('/modal_test')
def modal_test():
    return render_template('modal_test.html')

@app.route('/complete_task/<int:task_id>')
def complete_task(task_id):
    conn = get_db_connection()
    
    # Get task info
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    
    if task:
        # Update task status
        conn.execute('''
            UPDATE tasks 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (task_id,))
        
        # If it's a cleaning task, update room status to available
        if task['task_type'] == 'cleaning':
            conn.execute('UPDATE rooms SET status = "available" WHERE id = ?', (task['room_id'],))
        
        conn.commit()
        flash('Задача выполнена!', 'success')
    
    conn.close()
    return redirect(url_for('tasks'))

@app.route('/quality_check', methods=['GET', 'POST'])
def quality_check():
    if request.method == 'POST':
        room_id = request.form['room_id']
        cleanliness = request.form['cleanliness_score']
        amenities = request.form['amenities_score']
        maintenance = request.form['maintenance_score']
        notes = request.form['notes']
        checked_by = request.form['checked_by']
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO quality_checks 
            (room_id, cleanliness_score, amenities_score, maintenance_score, notes, checked_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (room_id, cleanliness, amenities, maintenance, notes, checked_by))
        conn.commit()
        conn.close()
        
        flash('Проверка качества сохранена!', 'success')
        return redirect(url_for('quality_check'))
    
    # GET request
    conn = get_db_connection()
    rooms = conn.execute('SELECT * FROM rooms ORDER BY room_number').fetchall()
    recent_checks = conn.execute('''
        SELECT qc.*, r.room_number 
        FROM quality_checks qc 
        JOIN rooms r ON qc.room_id = r.id 
        ORDER BY qc.check_date DESC 
        LIMIT 10
    ''').fetchall()
    conn.close()
    
    return render_template('quality_check.html', rooms=rooms, recent_checks=recent_checks)

@app.route('/api/room_status/<int:room_id>')
def api_room_status(room_id):
    conn = get_db_connection()
    room = conn.execute('SELECT * FROM rooms WHERE id = ?', (room_id,)).fetchone()
    conn.close()
    
    if room:
        return jsonify({
            'id': room['id'],
            'room_number': room['room_number'],
            'status': room['status'],
            'room_type': room['room_type'],
            'price': room['price']
        })
    return jsonify({'error': 'Room not found'}), 404

@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    if request.method == 'POST':
        room_number = request.form['room_number']
        room_type = request.form['room_type']
        price = float(request.form['price'])
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO rooms (room_number, room_type, price)
                VALUES (?, ?, ?)
            ''', (room_number, room_type, price))
            conn.commit()
            flash(f'Номер {room_number} успешно добавлен!', 'success')
        except sqlite3.IntegrityError:
            flash(f'Номер {room_number} уже существует!', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('rooms'))
    
    return render_template('add_room.html')

@app.route('/edit_room/<int:room_id>', methods=['GET', 'POST'])
def edit_room(room_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        room_number = request.form['room_number']
        room_type = request.form['room_type']
        price = float(request.form['price'])
        
        conn.execute('''
            UPDATE rooms 
            SET room_number = ?, room_type = ?, price = ?
            WHERE id = ?
        ''', (room_number, room_type, price, room_id))
        conn.commit()
        conn.close()
        
        flash('Номер успешно обновлен!', 'success')
        return redirect(url_for('rooms'))
    
    room = conn.execute('SELECT * FROM rooms WHERE id = ?', (room_id,)).fetchone()
    conn.close()
    
    if not room:
        flash('Номер не найден!', 'error')
        return redirect(url_for('rooms'))
    
    return render_template('edit_room.html', room=room)

@app.route('/delete_room/<int:room_id>')
def delete_room(room_id):
    conn = get_db_connection()
    
    # Check if room has active guests
    active_guest = conn.execute('''
        SELECT COUNT(*) as count 
        FROM guests 
        WHERE room_id = ? AND status = 'active'
    ''', (room_id,)).fetchone()
    
    if active_guest['count'] > 0:
        flash('Нельзя удалить номер с активными гостями!', 'error')
    else:
        conn.execute('DELETE FROM rooms WHERE id = ?', (room_id,))
        conn.commit()
        flash('Номер успешно удален!', 'success')
    
    conn.close()
    return redirect(url_for('rooms'))

@app.route('/reports')
def reports():
    conn = get_db_connection()
    
    # Occupancy statistics
    total_rooms = conn.execute('SELECT COUNT(*) as count FROM rooms').fetchone()['count']
    occupied_rooms = conn.execute('SELECT COUNT(*) as count FROM rooms WHERE status = "occupied"').fetchone()['count']
    occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    
    # Revenue statistics
    revenue_today = conn.execute('''
        SELECT SUM(r.price) as revenue
        FROM guests g
        JOIN rooms r ON g.room_id = r.id
        WHERE g.check_in = date('now') AND g.status = 'active'
    ''').fetchone()['revenue'] or 0
    
    # Task completion statistics
    total_tasks = conn.execute('SELECT COUNT(*) as count FROM tasks').fetchone()['count']
    completed_tasks = conn.execute('SELECT COUNT(*) as count FROM tasks WHERE status = "completed"').fetchone()['count']
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Quality average
    quality_avg = conn.execute('''
        SELECT AVG((cleanliness_score + amenities_score + maintenance_score) / 3.0) as avg_score
        FROM quality_checks
        WHERE check_date >= date('now', '-30 days')
    ''').fetchone()['avg_score'] or 0
    
    # Recent activity
    recent_checkins = conn.execute('''
        SELECT g.name, g.check_in, r.room_number
        FROM guests g
        JOIN rooms r ON g.room_id = r.id
        WHERE g.check_in >= date('now', '-7 days')
        ORDER BY g.check_in DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return render_template('reports.html',
                         occupancy_rate=occupancy_rate,
                         revenue_today=revenue_today,
                         completion_rate=completion_rate,
                         quality_avg=quality_avg,
                         recent_checkins=recent_checkins)

@app.route('/update_task_status/<int:task_id>/<status>')
def update_task_status(task_id, status):
    conn = get_db_connection()
    
    if status == 'in_progress':
        conn.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))
        flash('Задача взята в работу!', 'success')
    elif status == 'completed':
        # Get task info
        task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
        
        conn.execute('''
            UPDATE tasks 
            SET status = ?, completed_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (status, task_id))
        
        # If it's a cleaning task, update room status to available
        if task and task['task_type'] == 'cleaning':
            conn.execute('UPDATE rooms SET status = "available" WHERE id = ?', (task['room_id'],))
        
        flash('Задача выполнена!', 'success')
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('tasks'))

@app.route('/guest_details/<int:guest_id>')
def guest_details(guest_id):
    conn = get_db_connection()
    
    guest = conn.execute('''
        SELECT g.*, r.room_number, r.room_type, r.price
        FROM guests g
        JOIN rooms r ON g.room_id = r.id
        WHERE g.id = ?
    ''', (guest_id,)).fetchone()
    
    if not guest:
        flash('Гость не найден!', 'error')
        return redirect(url_for('guests'))
    
    # Calculate stay duration and cost
    check_in = datetime.strptime(guest['check_in'], '%Y-%m-%d').date()
    check_out = datetime.strptime(guest['check_out'], '%Y-%m-%d').date()
    stay_duration = (check_out - check_in).days
    total_cost = stay_duration * (guest['price'] or 0)
    
    conn.close()
    
    return render_template('guest_details.html', 
                         guest=guest, 
                         stay_duration=stay_duration,
                         total_cost=total_cost)

@app.route('/api/dashboard_stats')
def api_dashboard_stats():
    """API endpoint for real-time dashboard updates"""
    conn = get_db_connection()
    
    # Room statistics
    room_stats = {}
    stats = conn.execute('''
        SELECT status, COUNT(*) as count 
        FROM rooms 
        GROUP BY status
    ''').fetchall()
    
    for stat in stats:
        room_stats[stat['status']] = stat['count']
    
    # Task statistics
    task_stats = {}
    task_counts = conn.execute('''
        SELECT status, COUNT(*) as count 
        FROM tasks 
        GROUP BY status
    ''').fetchall()
    
    for task in task_counts:
        task_stats[task['status']] = task['count']
    
    conn.close()
    
    return jsonify({
        'room_stats': room_stats,
        'task_stats': task_stats,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)