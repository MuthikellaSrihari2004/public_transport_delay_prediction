"""
queries.py — Database Query Utilities
=======================================
Provides the TransportDB class for all database read/write operations.
"""

import sqlite3
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config


class TransportDB:
    """Database access layer for transport schedules and predictions."""

    def __init__(self, db_path=None):
        self.db_path = db_path or str(config.DB_PATH)

    def _connect(self):
        """Create a database connection with row-factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_locations(self):
        """Return all unique locations sorted alphabetically."""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT From_Location FROM schedules "
                "UNION "
                "SELECT DISTINCT To_Location FROM schedules"
            )
            locations = sorted([row[0] for row in cursor.fetchall() if row[0]])
            return locations
        except Exception as e:
            print(f"Error fetching locations: {e}")
            return config.HYDERABAD_LOCATIONS[:5]
        finally:
            conn.close()

    def get_route_details(self, from_loc, to_loc, transport_type=None):
        """Fetch distance and stop details for a specific route."""
        conn = self._connect()
        try:
            query = "SELECT * FROM schedules WHERE From_Location = ? AND To_Location = ?"
            params = [from_loc, to_loc]

            if transport_type and transport_type.lower() != 'all':
                query += " AND Transport_Type = ?"
                params.append(transport_type)

            query += " LIMIT 1"
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()

            if row:
                return {k.lower(): row[k] for k in row.keys()}

            # Fallback: try without transport type filter
            if transport_type and transport_type.lower() != 'all':
                cursor.execute(
                    "SELECT * FROM schedules WHERE From_Location = ? AND To_Location = ? LIMIT 1",
                    (from_loc, to_loc)
                )
                row = cursor.fetchone()
                if row:
                    return {k.lower(): row[k] for k in row.keys()}

            return None
        except Exception as e:
            print(f"Error fetching route details: {e}")
            return None
        finally:
            conn.close()

    def get_schedules_by_route(self, from_loc, to_loc, transport_type, date):
        """Fetch schedules with automatic fallback to nearest available date."""
        conn = self._connect()

        mode_filter = "AND Transport_Type = ?" if transport_type.lower() != 'all' else ""

        base_query = f"""
            SELECT * FROM schedules
            WHERE From_Location = ? AND To_Location = ?
            {mode_filter} AND Date = ?
            ORDER BY Scheduled_Departure ASC
        """

        def build_params(date_val):
            params = [from_loc, to_loc]
            if transport_type.lower() != 'all':
                params.append(transport_type)
            params.append(date_val)
            return tuple(params)

        # 1. Try exact date match
        df = pd.read_sql_query(base_query, conn, params=build_params(date))

        # 2. Fallback: use nearest available date for this route + mode
        if df.empty:
            cursor = conn.cursor()
            find_date_query = f"""
                SELECT DISTINCT Date FROM schedules
                WHERE From_Location = ? AND To_Location = ? {mode_filter}
                ORDER BY Date DESC LIMIT 1
            """
            find_params = [from_loc, to_loc]
            if transport_type.lower() != 'all':
                find_params.append(transport_type)

            cursor.execute(find_date_query, tuple(find_params))
            row = cursor.fetchone()
            if row:
                df = pd.read_sql_query(base_query, conn, params=build_params(row[0]))

        # 3. Fallback: try any transport mode
        if df.empty and transport_type.lower() != 'all':
            any_mode_query = """
                SELECT * FROM schedules
                WHERE From_Location = ? AND To_Location = ? AND Date = ?
                ORDER BY Scheduled_Departure ASC
            """
            df = pd.read_sql_query(any_mode_query, conn, params=(from_loc, to_loc, date))

            # 4. Any mode + nearest date
            if df.empty:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT Date FROM schedules WHERE From_Location = ? AND To_Location = ? ORDER BY Date DESC LIMIT 1",
                    (from_loc, to_loc)
                )
                row = cursor.fetchone()
                if row:
                    df = pd.read_sql_query(any_mode_query, conn, params=(from_loc, to_loc, row[0]))

        conn.close()
        return df

    def save_prediction(self, from_loc, to_loc, t_type, sched_time, delay, reason):
        """Save a prediction to the audit log."""
        conn = self._connect()
        try:
            conn.cursor().execute(
                "INSERT INTO predictions (from_location, to_location, transport_type, scheduled_time, predicted_delay, reason) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (from_loc, to_loc, t_type, sched_time, delay, reason)
            )
            conn.commit()
        except Exception as e:
            print(f"Error saving prediction: {e}")
        finally:
            conn.close()


if __name__ == "__main__":
    db = TransportDB()
    print(f"Database: {db.db_path}")
    print(f"Locations: {db.get_locations()[:5]}...")
