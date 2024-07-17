import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_balances (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 100
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pending_gambles (
        user_id INTEGER PRIMARY KEY,
        amount INTEGER,
        multiplier INTEGER,
        win BOOLEAN
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sold_items (
        user_id INTEGER,
        item TEXT,
        PRIMARY KEY (user_id, item)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gamble_stats (
        user_id INTEGER PRIMARY KEY,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        bets_won INTEGER DEFAULT 0,
        amount_won INTEGER DEFAULT 0,
        amount_lost INTEGER DEFAULT 0,
        items_sold INTEGER DEFAULT 0
    )
    ''')
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT balance FROM user_balances WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        return 50  # Default balance for new users
    return result[0]

def update_balance(user_id, amount):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_balances (user_id, balance)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET balance = balance + excluded.balance
    ''', (user_id, amount))
    conn.commit()
    conn.close()

def store_pending_gamble(user_id, amount, multiplier, win):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO pending_gambles (user_id, amount, multiplier, win)
        VALUES (?, ?, ?, ?)
    ''', (user_id, amount, multiplier, win))
    conn.commit()
    conn.close()

def get_pending_gamble(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT amount, multiplier, win FROM pending_gambles WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def clear_pending_gamble(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM pending_gambles WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def has_sold_item(user_id, item):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT 1 FROM sold_items WHERE user_id = ? AND item = ?', (user_id, item))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def add_sold_item(user_id, item):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO sold_items (user_id, item) VALUES (?, ?)', (user_id, item))
    conn.commit()
    conn.close()

def update_gamble_stats(user_id, win, bet_on_win, amount_won, amount_lost, item_sold=False):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if win:
        cursor.execute('''
            INSERT INTO gamble_stats (user_id, wins, bets_won, amount_won, items_sold)
            VALUES (?, 1, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                wins = wins + 1,
                bets_won = bets_won + excluded.bets_won,
                amount_won = amount_won + excluded.amount_won,
                items_sold = items_sold + excluded.items_sold
        ''', (user_id, 1 if bet_on_win else 0, amount_won, 1 if item_sold else 0))
    else:
        cursor.execute('''
            INSERT INTO gamble_stats (user_id, losses, bets_won, amount_lost, items_sold)
            VALUES (?, 1, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                losses = losses + 1,
                bets_won = bets_won + excluded.bets_won,
                amount_lost = amount_lost + excluded.amount_lost,
                items_sold = items_sold + excluded.items_sold
        ''', (user_id, 1 if bet_on_win else 0, amount_lost, 1 if item_sold else 0))
    conn.commit()
    conn.close()

def get_gamble_stats(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT wins, losses, bets_won, amount_won, amount_lost, items_sold FROM gamble_stats WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        return (0, 0, 0, 0, 0, 0)  # Default stats for new users
    return result

def get_leaderboard(stat):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(f'SELECT user_id, {stat} FROM gamble_stats ORDER BY {stat} DESC LIMIT 10')
    result = cursor.fetchall()
    conn.close()
    return result
