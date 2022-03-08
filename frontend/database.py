# built in
import sqlite3
import os

class Database:
    def __init__(self, path):
        # path to file
        self.path = path

        # whether we're connected or not
        self.connection = None
        self.cursor = None

        # create the database if none exists
        if not os.path.exists(self.path):
            self.create_database()

    def __enter__(self):
        """
        Enables the "with X as Y:" syntax
        """
        if not self.connection:
            self.connection = sqlite3.connect(self.path)
            self.cursor = self.connection.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Defines what to do when "with X as Y:" closes
        """
        if not self.connection:
            return
        else:
            self.connection.commit()
            self.connection.close()
            self.connection = None
            self.cursor = None

    def query(self, query_string):
        self.cursor.execute(query_string)
        return self.cursor.fetchall()

    def get_top_scores(self, n=5):
        self.cursor.execute(f"SELECT * FROM scores ORDER BY score DESC LIMIT {n};")
        results = self.cursor.fetchall()
        output = []
        for pair in results:
            output.append({
                "team": pair[0],
                "score": pair[1]
            })
        return output

    def get_score_by_team(self, team):
        self.cursor.execute(f"SELECT * FROM scores WHERE team = {team};")
        results = self.cursor.fetchall()
        if not results:
            self.cursor.execute(f'INSERT INTO scores (team, score) VALUES ({team}, 0);')
            return 0
        else:
            return results[0][0]

    def create_database(self):
        self.__enter__()
        table_creation = """
        CREATE TABLE scores
        (
            team TEXT PRIMARY KEY,
            score REAL NOT NULL
        );
        """
        self.cursor.execute(table_creation)
        self.__exit__(None, None, None)
