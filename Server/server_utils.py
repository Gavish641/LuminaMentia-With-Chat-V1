import sqlite3
import json
import random

class UsersDB:

    def __init__(self):
        self.database = 'users.db'

    def connect_to_db(self):
        conn = sqlite3.connect(self.database)
        return conn

    def create_table(self):
        conn = self.connect_to_db()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY NOT NULL, 
                password TEXT NOT NULL
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()

    def insert_user(self, username, password):
        self.create_table()
        conn = self.connect_to_db()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO users (username, password) VALUES (?, ?)''', (username, password))
        conn.commit()
        cursor.close()
        conn.close()

    def check_user_registered(self, username):
        self.create_table()
        conn = self.connect_to_db()
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM users WHERE username=(?)''', (username,))
        result = cursor.fetchone() is not None
        conn.commit()
        cursor.close()
        conn.close()
        return result
        # returns true or false

    def update_username(self, new_username, old_username):
        self.create_table()
        conn = self.connect_to_db()
        cursor = conn.cursor()
        cursor.execute('''UPDATE users SET username=(?) WHERE username=(?)''', (new_username, old_username))
        conn.commit()
        cursor.close()
        conn.close()

    def try_login(self, username, password):
        self.create_table()
        conn = self.connect_to_db()
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM users WHERE username=(?) AND password=(?)''', (username, password))
        result = cursor.fetchone() is not None
        cursor.close()
        conn.commit()
        conn.close()
        return result


class ScoresDB:
    def __init__(self):
        self.database = 'scores.db'

    def connect_to_db(self):
        conn = sqlite3.connect(self.database)
        return conn

    def create_table(self):
        conn = self.connect_to_db()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                username TEXT, 
                game TEXT,
                lastScore INTEGER,
                mean INTEGER,
                numOfGames INTEGER,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()

    def insert_score(self, username, game, newScore):
        self.create_table()
        conn = self.connect_to_db()
        cursor = conn.cursor()
        if self.checkUserExists(username):
            cursor.execute('''SELECT numOfGames FROM scores WHERE username=(?) AND game=(?)''', (username, game)) 
            numOfGames = (cursor.fetchone()[0])
            numOfGames += 1
            mean = int(((self.getMean(username) * (numOfGames-1)) + newScore) / numOfGames) # Calculating the new mean
            cursor.execute('''UPDATE scores SET lastScore=(?), mean=(?), numOfGames=(?) WHERE username=(?) AND game=(?)''', (newScore, mean, numOfGames, username, game))
        else:
            numOfGames = 1
            mean = newScore
            cursor.execute('''INSERT INTO scores (username, game, lastScore, mean, numOfGames) VALUES (?, ?, ?, ?, ?)''', (username, game, newScore, mean, numOfGames))
        conn.commit()
        cursor.close()
        conn.close()

    def checkUserExists(self, username):
        conn = self.connect_to_db()
        print(1)
        cursor = conn.cursor()
        print(2)
        cursor.execute('''SELECT * FROM scores WHERE username=(?)''', (username,))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        print(result)
        return not result == []

    def getMean(self, username):
        conn = self.connect_to_db()
        cursor = conn.cursor()
        cursor.execute('''SELECT mean FROM scores WHERE username=(?) AND game=(?)''', (username, "sorting numbers"))
        mean = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return mean

    def get_scores(self, username):
        conn_scores = sqlite3.connect('scores.db')
        cursor_scores = conn_scores.cursor()

        # Build the query based on provided parameters
        query = 'SELECT * FROM scores'
        if username:
            query += f" WHERE username = '{username}'"


        cursor_scores.execute(query)
        scores = cursor_scores.fetchall()

        conn_scores.close()

        return scores

    def getMeanScore(self, username):
        pass



class Message:

    def __init__(self):
        self.username = ''
        self.password = ''
        self.database = UsersDB()
    
    def decode_json(self, data):
        try:
            decoded_data = data.decode()
            if decoded_data:
                return json.loads(decoded_data)
            else:
                # Handle the case when the decoded data is empty
                return None
        except json.decoder.JSONDecodeError as e:
            # Handle the invalid JSON case
            print(f"Error decoding JSON: {e}")
            return None
        
    def encode_json(self, data):
        try:
            json_data = json.dumps(data)
            return json_data.encode()
        except json.decoder.JSONDecodeError as e:
            # Handle the invalid JSON case
            print(f"Error decoding JSON: {e}")
            return None
        

class Sorting_Numbers:
    def __init__(self):
        self.numbers_to_sort = []
    
    def generate_numbers(self):
        numbers_to_sort = random.sample(range(1, 10), 5)
        random.shuffle(numbers_to_sort)
        self.numbers_to_sort = numbers_to_sort
        return numbers_to_sort


class Chat:
    def __init__(self):
        self.current_chats = {}
        self.waiting_client = None