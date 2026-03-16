from fastmcp import FastMCP
from datetime import datetime
from typing import List, Dict, Optional

from database import get_connection, get_available_seats

mcp = FastMCP("Train Ticket Booking System")


@mcp.tool()
def search_trains(
    source: str,
    destination: str,
    date: str
) -> List[Dict]:
    """
    Search for available trains between two stations.

    Args:
        source: Source station (New Delhi, Prayagraj, Ballia, Mumbai, Dehradun)
        destination: Destination station
        date: Travel date in YYYY-MM-DD format

    Returns:
        List of available trains with details
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Validate stations
    cursor.execute("SELECT name FROM stations WHERE name = ?", (source,))
    if not cursor.fetchone():
        conn.close()
        return [{"error": "Invalid source station. Use get_all_stations() to see available stations"}]

    cursor.execute("SELECT name FROM stations WHERE name = ?", (destination,))
    if not cursor.fetchone():
        conn.close()
        return [{"error": "Invalid destination station. Use get_all_stations() to see available stations"}]

    if source == destination:
        conn.close()
        return [{"error": "Source and destination cannot be the same"}]

    # Find trains
    cursor.execute("SELECT train_number, train_name, route FROM trains")
    trains = cursor.fetchall()

    available_trains = []

    for train_no, train_name, route in trains:
        route_list = route.split(',')

        if source in route_list and destination in route_list:
            source_idx = route_list.index(source)
            dest_idx = route_list.index(destination)

            if source_idx < dest_idx:
                cursor.execute(
                    "SELECT departure_time FROM train_schedule WHERE train_number = ? AND station = ?",
                    (train_no, source)
                )
                dept_time = cursor.fetchone()[0] or "N/A"

                cursor.execute(
                    "SELECT arrival_time FROM train_schedule WHERE train_number = ? AND station = ?",
                    (train_no, destination)
                )
                arr_time = cursor.fetchone()[0] or "N/A"

                cursor.execute(
                    "SELECT class_type, fare FROM train_classes WHERE train_number = ?",
                    (train_no,)
                )
                classes = cursor.fetchall()

                seat_availability = {}
                for class_type, fare in classes:
                    available = get_available_seats(train_no, date, class_type)
                    seat_availability[class_type] = {
                        "available": available,
                        "price": fare
                    }

                train_info = {
                    "train_number": train_no,
                    "train_name": train_name,
                    "departure_time": dept_time,
                    "arrival_time": arr_time,
                    "date": date,
                    "seat_availability": seat_availability
                }
                available_trains.append(train_info)

    conn.close()

    if not available_trains:
        return [{"message": "No direct trains found between these stations"}]

    return available_trains


@mcp.tool()
def book_ticket(
    train_number: str,
    passenger_name: str,
    age: int,
    source: str,
    destination: str,
    date: str,
    class_type: str,
    num_seats: int = 1
) -> Dict:
    """
    Book train tickets.

    Args:
        train_number: Train number (e.g., "12301")
        passenger_name: Name of the passenger
        age: Age of passenger
        source: Boarding station
        destination: Destination station
        date: Travel date in YYYY-MM-DD format
        class_type: Class of travel (1A, 2A, 3A, SL, CC, EC, 2S)
        num_seats: Number of seats to book (default: 1)

    Returns:
        Booking confirmation with PNR and details
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Validate train
    cursor.execute("SELECT train_name FROM trains WHERE train_number = ?", (train_number,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return {"error": "Invalid train number"}

    train_name = result[0]

    # Validate class and get fare
    cursor.execute(
        "SELECT fare FROM train_classes WHERE train_number = ? AND class_type = ?",
        (train_number, class_type)
    )
    result = cursor.fetchone()
    if not result:
        conn.close()
        return {"error": "Invalid class for this train"}

    fare = result[0]

    # Check availability
    available = get_available_seats(train_number, date, class_type)
    if available < num_seats:
        conn.close()
        return {"error": f"Only {available} seats available in {class_type} class"}

    # Get schedule
    cursor.execute(
        "SELECT departure_time FROM train_schedule WHERE train_number = ? AND station = ?",
        (train_number, source)
    )
    dept_time = cursor.fetchone()[0] or "N/A"

    cursor.execute(
        "SELECT arrival_time FROM train_schedule WHERE train_number = ? AND station = ?",
        (train_number, destination)
    )
    arr_time = cursor.fetchone()[0] or "N/A"

    # Generate PNR
    cursor.execute("SELECT COUNT(*) FROM bookings")
    count = cursor.fetchone()[0]
    pnr = f"PNR{1000 + count + 1}"

    # Calculate total fare
    total_fare = fare * num_seats

    # Insert booking
    booking_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO bookings (
            pnr, train_number, train_name, passenger_name, age, source, destination,
            travel_date, class_type, num_seats, total_fare, status, booking_time,
            departure_time, arrival_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        pnr, train_number, train_name, passenger_name, age, source, destination,
        date, class_type, num_seats, total_fare, "CONFIRMED", booking_time,
        dept_time, arr_time
    ))

    conn.commit()

    cursor.execute("SELECT * FROM bookings WHERE pnr = ?", (pnr,))
    booking = cursor.fetchone()

    conn.close()

    booking_details = {
        "pnr": booking[0],
        "train_number": booking[1],
        "train_name": booking[2],
        "passenger_name": booking[3],
        "age": booking[4],
        "source": booking[5],
        "destination": booking[6],
        "date": booking[7],
        "class": booking[8],
        "num_seats": booking[9],
        "total_fare": booking[10],
        "status": booking[11],
        "booking_time": booking[12],
        "departure_time": booking[13],
        "arrival_time": booking[14]
    }

    return {
        "message": "Ticket booked successfully!",
        "booking_details": booking_details
    }


@mcp.tool()
def cancel_ticket(pnr: str) -> Dict:
    """
    Cancel a booked ticket.

    Args:
        pnr: PNR number of the booking to cancel

    Returns:
        Cancellation confirmation and refund details
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE pnr = ?", (pnr,))
    booking = cursor.fetchone()

    if not booking:
        conn.close()
        return {"error": f"No booking found with PNR: {pnr}"}

    if booking[11] == "CANCELLED":
        conn.close()
        return {"error": "This ticket is already cancelled"}

    total_fare = booking[10]
    refund_amount = total_fare * 0.8
    cancellation_charges = total_fare * 0.2
    cancellation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "UPDATE bookings SET status = ?, cancellation_time = ?, refund_amount = ? WHERE pnr = ?",
        ("CANCELLED", cancellation_time, refund_amount, pnr)
    )

    conn.commit()
    conn.close()

    return {
        "message": "Ticket cancelled successfully!",
        "pnr": pnr,
        "cancellation_charges": cancellation_charges,
        "refund_amount": refund_amount,
        "refund_note": "Refund will be credited within 5-7 working days"
    }


@mcp.tool()
def check_pnr_status(pnr: str) -> Dict:
    """
    Check the status of a booking using PNR.

    Args:
        pnr: PNR number to check

    Returns:
        Complete booking details and current status
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings WHERE pnr = ?", (pnr,))
    booking = cursor.fetchone()

    conn.close()

    if not booking:
        return {"error": f"No booking found with PNR: {pnr}"}

    result = {
        "pnr": booking[0],
        "train_number": booking[1],
        "train_name": booking[2],
        "passenger_name": booking[3],
        "age": booking[4],
        "source": booking[5],
        "destination": booking[6],
        "travel_date": booking[7],
        "class": booking[8],
        "num_seats": booking[9],
        "total_fare": booking[10],
        "status": booking[11],
        "booking_time": booking[12],
        "departure_time": booking[13],
        "arrival_time": booking[14]
    }

    if booking[15]:
        result["cancellation_time"] = booking[15]
    if booking[16]:
        result["refund_amount"] = booking[16]

    return result


@mcp.tool()
def get_all_stations() -> List[str]:
    """
    Get list of all available stations.

    Returns:
        List of station names
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM stations ORDER BY name")
    stations = [row[0] for row in cursor.fetchall()]

    conn.close()
    return stations


@mcp.tool()
def get_train_schedule(train_number: str) -> Dict:
    """
    Get complete schedule and details of a specific train.

    Args:
        train_number: Train number to get schedule for

    Returns:
        Complete train schedule with all stops
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT train_name, route FROM trains WHERE train_number = ?", (train_number,))
    result = cursor.fetchone()

    if not result:
        conn.close()
        return {"error": "Invalid train number"}

    train_name, route = result
    route_list = route.split(',')

    cursor.execute(
        "SELECT station, departure_time, arrival_time FROM train_schedule WHERE train_number = ?",
        (train_number,)
    )
    schedule_data = cursor.fetchall()

    stops = []
    for station, dept, arr in schedule_data:
        stops.append({
            "station": station,
            "departure": dept or "Terminates here",
            "arrival": arr or "Starts here"
        })

    cursor.execute(
        "SELECT class_type, fare FROM train_classes WHERE train_number = ?",
        (train_number,)
    )
    classes_data = cursor.fetchall()

    conn.close()

    return {
        "train_number": train_number,
        "train_name": train_name,
        "route": route_list,
        "stops": stops,
        "available_classes": [c[0] for c in classes_data],
        "fare_details": {c[0]: c[1] for c in classes_data}
    }


@mcp.tool()
def list_all_bookings(status: Optional[str] = None) -> Dict:
    """
    List all booked tickets in the system.

    Args:
        status: Filter by status - "CONFIRMED", "CANCELLED", or None for all bookings

    Returns:
        List of all bookings with their details
    """
    conn = get_connection()
    cursor = conn.cursor()

    if status:
        status = status.upper()
        if status not in ["CONFIRMED", "CANCELLED"]:
            conn.close()
            return {"error": "Invalid status. Use 'CONFIRMED' or 'CANCELLED'"}
        cursor.execute("SELECT * FROM bookings WHERE status = ?", (status,))
    else:
        cursor.execute("SELECT * FROM bookings")

    bookings = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'CONFIRMED'")
    confirmed_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'CANCELLED'")
    cancelled_count = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total_fare) FROM bookings WHERE status = 'CONFIRMED'")
    total_revenue = cursor.fetchone()[0] or 0

    conn.close()

    if not bookings:
        return {
            "message": "No bookings found",
            "total_bookings": 0,
            "bookings": []
        }

    bookings_list = []
    for b in bookings:
        booking_dict = {
            "pnr": b[0],
            "train_number": b[1],
            "train_name": b[2],
            "passenger_name": b[3],
            "age": b[4],
            "source": b[5],
            "destination": b[6],
            "travel_date": b[7],
            "class": b[8],
            "num_seats": b[9],
            "total_fare": b[10],
            "status": b[11],
            "booking_time": b[12],
            "departure_time": b[13],
            "arrival_time": b[14]
        }
        if b[15]:
            booking_dict["cancellation_time"] = b[15]
        if b[16]:
            booking_dict["refund_amount"] = b[16]
        bookings_list.append(booking_dict)

    return {
        "total_bookings": confirmed_count + cancelled_count,
        "confirmed_bookings": confirmed_count,
        "cancelled_bookings": cancelled_count,
        "total_revenue": total_revenue,
        "showing": len(bookings),
        "bookings": bookings_list
    }


@mcp.tool()
def list_bookings_by_passenger(passenger_name: str) -> Dict:
    """
    List all bookings for a specific passenger.

    Args:
        passenger_name: Name of the passenger to search for

    Returns:
        All bookings made by the passenger
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM bookings WHERE LOWER(passenger_name) = LOWER(?)",
        (passenger_name,)
    )
    bookings = cursor.fetchall()

    conn.close()

    if not bookings:
        return {
            "message": f"No bookings found for passenger: {passenger_name}",
            "bookings": []
        }

    bookings_list = []
    confirmed = 0
    cancelled = 0

    for b in bookings:
        if b[11] == "CONFIRMED":
            confirmed += 1
        else:
            cancelled += 1

        booking_dict = {
            "pnr": b[0],
            "train_number": b[1],
            "train_name": b[2],
            "passenger_name": b[3],
            "age": b[4],
            "source": b[5],
            "destination": b[6],
            "travel_date": b[7],
            "class": b[8],
            "num_seats": b[9],
            "total_fare": b[10],
            "status": b[11],
            "booking_time": b[12],
            "departure_time": b[13],
            "arrival_time": b[14]
        }
        if b[15]:
            booking_dict["cancellation_time"] = b[15]
        if b[16]:
            booking_dict["refund_amount"] = b[16]
        bookings_list.append(booking_dict)

    return {
        "passenger_name": passenger_name,
        "total_bookings": len(bookings),
        "confirmed_bookings": confirmed,
        "cancelled_bookings": cancelled,
        "bookings": bookings_list
    }


if __name__ == "__main__":
    mcp.run()
