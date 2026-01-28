import sqlite3
import pandas as pd
import sys
from pathlib import Path

# Add project root to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
import config

class TransportDB:
    def __init__(self, db_path=None):
        self.db_path = db_path or str(config.DB_PATH)

    def get_conn(self):
        """Create a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable row access by name
        return conn

    def get_locations(self):
        """Fetch all unique locations"""
        conn = self.get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT from_location FROM schedules UNION SELECT DISTINCT to_location FROM schedules")
        locs = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        return sorted(locs)

    def get_route_details(self, from_loc, to_loc, transport_type=None):
        """Fetch distance and intermediate stops for a route"""
        conn = self.get_conn()
        cursor = conn.cursor()
        try:
            # We use distinct column names from schema
            query = "SELECT * FROM schedules WHERE From_Location = ? AND To_Location = ?"
            params = [from_loc, to_loc]
            
            if transport_type:
                query += " AND Transport_Type = ?"
                params.append(transport_type)
                
            query += " LIMIT 1"
            
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
            if row:
                # Normalize keys to lowercase for the frontend
                return {k.lower(): row[k] for k in row.keys()}
            
            # Fallback: if specific mode not found, try any mode
            if transport_type and not row:
                cursor.execute("SELECT * FROM schedules WHERE From_Location = ? AND To_Location = ? LIMIT 1", (from_loc, to_loc))
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
        """Fetch schedules matching criteria with fallback to template dates"""
        conn = self.get_conn()
        
        mode_filter = "AND Transport_Type = ?" if transport_type.lower() != 'all' else ""
        params = [from_loc, to_loc]
        if transport_type.lower() != 'all':
            params.append(transport_type)
        params.append(date)

        # 1. Try exact date match first
        query = f"""
        SELECT * FROM schedules 
        WHERE From_Location = ? 
        AND To_Location = ? 
        {mode_filter}
        AND Date = ?
        ORDER BY Scheduled_Departure ASC
        """
        df = pd.read_sql_query(query, conn, params=tuple(params))
        
        # 2. Fallback: Template Date
        if df.empty:
            cursor = conn.cursor()
            check_q = f"SELECT DISTINCT Date FROM schedules WHERE From_Location = ? AND To_Location = ? {mode_filter} ORDER BY Date DESC LIMIT 1"
            check_params = [from_loc, to_loc]
            if transport_type.lower() != 'all':
                check_params.append(transport_type)
            
            cursor.execute(check_q, tuple(check_params))
            row = cursor.fetchone()
            
            if row:
                template_date = row[0]
                df_params = [from_loc, to_loc]
                if transport_type.lower() != 'all':
                    df_params.append(transport_type)
                df_params.append(template_date)
                df = pd.read_sql_query(query, conn, params=tuple(df_params))
                
            # 3. Fallback: ANY mode if specific mode failed
            if df.empty and transport_type.lower() != 'all':
                alt_query = """
                SELECT * FROM schedules 
                WHERE From_Location = ? 
                AND To_Location = ? 
                AND Date = ?
                ORDER BY Scheduled_Departure ASC
                """
                df = pd.read_sql_query(alt_query, conn, params=(from_loc, to_loc, date))
                
                # 4. Fallback: ANY mode, template date
                if df.empty:
                    check_q_alt = "SELECT DISTINCT Date FROM schedules WHERE From_Location = ? AND To_Location = ? ORDER BY Date DESC LIMIT 1"
                    cursor.execute(check_q_alt, (from_loc, to_loc))
                    row_alt = cursor.fetchone()
                    if row_alt:
                        template_alt = row_alt[0]
                        df = pd.read_sql_query(alt_query, conn, params=(from_loc, to_loc, template_alt))
        
        conn.close()
        return df


    def save_prediction(self, from_loc, to_loc, t_type, sched_time, delay, reason):
        """Audit log for predictions made via the application"""
        conn = self.get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO predictions (from_location, to_location, transport_type, scheduled_time, predicted_delay, reason)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (from_loc, to_loc, t_type, sched_time, delay, reason))
            conn.commit()
            print(f"✅ Prediction audit logged: {from_loc} -> {to_loc}")
        except Exception as e:
            print(f"❌ Error saving prediction audit: {e}")
        finally:
            conn.close()

    def get_recent_predictions(self, limit=10):
        """Fetch recent prediction history"""
        query = "SELECT * FROM predictions ORDER BY timestamp DESC LIMIT ?"
        conn = self.get_conn()
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df

if __name__ == "__main__":
    db = TransportDB()
    print(f"🗄️  Database Utilities connected to: {db.db_path}")
