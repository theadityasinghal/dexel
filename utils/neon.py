import psycopg2
import os

class Database():
    def __init__(self):
        pass
        DATABASE_URL = os.getenv("DATABASE_URL") 
        self.conn = psycopg2.connect(DATABASE_URL)
        self.cur = self.conn.cursor()

    def get_cursor(self):
        if self.conn.closed:
            self.conn = psycopg2.connect(os.getenv("DATABASE_URL"))
            self.cur = self.conn.cursor()
        return self.cur

    def get_greetings_config(self, guild_id):
        cur = self.get_cursor()
        cur.execute("""
            SELECT join_channel_id, join_message, leave_channel_id, leave_message
            FROM greetings_config
            WHERE guild_id = %s
            """,
            (guild_id,)
        )
        row = self.cur.fetchone()
        if not row:
            return {
                "join_channel_id": None,
                "join_message":    None,
                "leave_channel_id": None,
                "leave_message":   None,
            }
        return {
            "join_channel_id": row[0],
            "join_message":    row[1],
            "leave_channel_id": row[2],
            "leave_message":   row[3],
        }
    def set_join_message(self, guild_id, message):
        cur = self.get_cursor()
        cur.execute(
            """
            INSERT INTO greetings_config (guild_id, join_message)
            VALUES (%s, %s)
            ON CONFLICT (guild_id) DO UPDATE SET join_message = EXCLUDED.join_message
            """,
            (guild_id, message)
        )
        self.conn.commit()

    def set_leave_message(self, guild_id, message):
        cur = self.get_cursor()
        cur.execute(
            """
            INSERT INTO greetings_config (guild_id, leave_message)
            VALUES (%s, %s)
            ON CONFLICT (guild_id) DO UPDATE SET leave_message = EXCLUDED.leave_message
            """,
            (guild_id, message)
        )
        self.conn.commit()

    def set_join_channel(self, guild_id, channel_id):
        cur = self.get_cursor()
        cur.execute(
            """
            INSERT INTO greetings_config (guild_id, join_channel_id)
            VALUES (%s, %s)
            ON CONFLICT (guild_id) DO UPDATE SET join_channel_id = EXCLUDED.join_channel_id
            """,
            (guild_id, channel_id)
        )
        self.conn.commit()

    def set_leave_channel(self, guild_id, channel_id):
        cur = self.get_cursor()
        cur.execute(
            """
            INSERT INTO greetings_config (guild_id, leave_channel_id)
            VALUES (%s, %s)
            ON CONFLICT (guild_id) DO UPDATE SET leave_channel_id = EXCLUDED.leave_channel_id
            """,
            (guild_id, channel_id)
        )
        self.conn.commit()