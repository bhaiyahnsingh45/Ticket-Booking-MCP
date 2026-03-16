import sqlite3

DB_PATH = "train_booking.db"


def get_connection():
    """Get a new SQLite connection."""
    return sqlite3.connect(DB_PATH)


def init_database():
    """Initialize SQLite database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trains (
            train_number TEXT PRIMARY KEY,
            train_name TEXT NOT NULL,
            route TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS train_classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            train_number TEXT NOT NULL,
            class_type TEXT NOT NULL,
            fare INTEGER NOT NULL,
            total_seats INTEGER NOT NULL,
            FOREIGN KEY (train_number) REFERENCES trains(train_number),
            UNIQUE(train_number, class_type)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS train_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            train_number TEXT NOT NULL,
            station TEXT NOT NULL,
            departure_time TEXT,
            arrival_time TEXT,
            FOREIGN KEY (train_number) REFERENCES trains(train_number)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            pnr TEXT PRIMARY KEY,
            train_number TEXT NOT NULL,
            train_name TEXT NOT NULL,
            passenger_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            travel_date TEXT NOT NULL,
            class_type TEXT NOT NULL,
            num_seats INTEGER NOT NULL,
            total_fare INTEGER NOT NULL,
            status TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            departure_time TEXT,
            arrival_time TEXT,
            cancellation_time TEXT,
            refund_amount REAL,
            FOREIGN KEY (train_number) REFERENCES trains(train_number)
        )
    ''')

    conn.commit()
    conn.close()


def seed_database():
    """Seed database with initial train, station, schedule, and fare data."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM stations")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Stations
    stations = ["New Delhi", "Prayagraj", "Ballia", "Mumbai", "Dehradun"]
    for station in stations:
        cursor.execute("INSERT INTO stations (name) VALUES (?)", (station,))

    # Trains
    trains_data = [
        ("12301", "Rajdhani Express", "New Delhi,Prayagraj,Mumbai"),
        ("12302", "Shatabdi Express", "New Delhi,Dehradun"),
        ("13009", "Doon Express", "Dehradun,Prayagraj,Ballia"),
        ("12533", "Pushpak Express", "Mumbai,Prayagraj,Ballia,New Delhi"),
        ("15004", "Ganga Kaveri Express", "New Delhi,Prayagraj,Ballia,Mumbai"),
        ("19019", "Dehradun Express", "Mumbai,New Delhi,Dehradun"),
    ]
    for train_no, name, route in trains_data:
        cursor.execute("INSERT INTO trains VALUES (?, ?, ?)", (train_no, name, route))

    # Classes and fares
    classes_data = [
        ("12301", "1A", 2500, 20),
        ("12301", "2A", 1500, 50),
        ("12301", "3A", 1000, 80),
        ("12301", "SL", 400, 200),
        ("12302", "CC", 800, 100),
        ("12302", "EC", 1200, 40),
        ("13009", "SL", 300, 150),
        ("13009", "2S", 150, 200),
        ("12533", "2A", 1300, 45),
        ("12533", "3A", 900, 70),
        ("12533", "SL", 350, 180),
        ("15004", "3A", 850, 65),
        ("15004", "SL", 320, 160),
        ("15004", "2S", 140, 180),
        ("19019", "2A", 1400, 40),
        ("19019", "3A", 950, 75),
        ("19019", "SL", 380, 170),
    ]
    for train_no, class_type, fare, seats in classes_data:
        cursor.execute(
            "INSERT INTO train_classes (train_number, class_type, fare, total_seats) VALUES (?, ?, ?, ?)",
            (train_no, class_type, fare, seats),
        )

    # Schedules
    schedules_data = [
        ("12301", "New Delhi", "16:00", None),
        ("12301", "Prayagraj", "22:30", "22:30"),
        ("12301", "Mumbai", None, "08:00"),
        ("12302", "New Delhi", "06:45", None),
        ("12302", "Dehradun", None, "12:30"),
        ("13009", "Dehradun", "21:50", None),
        ("13009", "Prayagraj", "12:30", "12:30"),
        ("13009", "Ballia", None, "16:45"),
        ("12533", "Mumbai", "18:05", None),
        ("12533", "Prayagraj", "10:20", "10:20"),
        ("12533", "Ballia", "14:30", "14:30"),
        ("12533", "New Delhi", None, "22:45"),
        ("15004", "New Delhi", "09:25", None),
        ("15004", "Prayagraj", "18:15", "18:15"),
        ("15004", "Ballia", "21:00", "21:00"),
        ("15004", "Mumbai", None, "14:30"),
        ("19019", "Mumbai", "11:50", None),
        ("19019", "New Delhi", "06:15", "06:15"),
        ("19019", "Dehradun", None, "12:00"),
    ]
    for train_no, station, dept, arr in schedules_data:
        cursor.execute(
            "INSERT INTO train_schedule (train_number, station, departure_time, arrival_time) VALUES (?, ?, ?, ?)",
            (train_no, station, dept, arr),
        )

    conn.commit()
    conn.close()


def get_available_seats(train_no: str, date: str, class_type: str) -> int:
    """Get available seats for a train on a specific date."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT total_seats FROM train_classes WHERE train_number = ? AND class_type = ?",
        (train_no, class_type),
    )
    result = cursor.fetchone()

    if not result:
        conn.close()
        return 0

    total_seats = result[0]

    cursor.execute(
        "SELECT SUM(num_seats) FROM bookings WHERE train_number = ? AND travel_date = ? AND class_type = ? AND status = 'CONFIRMED'",
        (train_no, date, class_type),
    )
    booked = cursor.fetchone()[0] or 0

    conn.close()
    return max(0, total_seats - booked)


# Initialize and seed on import
init_database()
seed_database()
