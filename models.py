import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS influencers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            platform TEXT NOT NULL,
            account_id TEXT,
            follower_count INTEGER DEFAULT 0,
            genre TEXT,
            area TEXT,
            contact_info TEXT,
            notes TEXT,
            status TEXT DEFAULT '未連絡',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS dm_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            influencer_id INTEGER NOT NULL,
            sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            message_content TEXT,
            direction TEXT NOT NULL DEFAULT '送信',
            status TEXT DEFAULT '送信済',
            FOREIGN KEY (influencer_id) REFERENCES influencers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS collaborations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            influencer_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            start_date DATE,
            end_date DATE,
            compensation_type TEXT,
            compensation_amount TEXT,
            post_url TEXT,
            status TEXT DEFAULT '進行中',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (influencer_id) REFERENCES influencers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS collaboration_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collaboration_id INTEGER NOT NULL,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            new_followers INTEGER DEFAULT 0,
            new_customers INTEGER DEFAULT 0,
            revenue_impact INTEGER DEFAULT 0,
            measured_at DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (collaboration_id) REFERENCES collaborations(id) ON DELETE CASCADE
        );
    ''')

    conn.commit()
    conn.close()
