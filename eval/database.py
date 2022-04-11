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

    def get_top_matrix_scores(self, n=5):
        self.cursor.execute(f"SELECT * FROM MatrixCompletionScores ORDER BY lpips DESC LIMIT {n};")
        results = self.cursor.fetchall()
        output = []
        for row in results:
            output.append({
                "team": row[0],
                "psnr": row[1],
                "ssim": row[2],
                "lpips": row[3],
                "fid": row[4]
            })
        return output

    def get_top_estimation_scores(self, n=5):
        self.cursor.execute(f"SELECT * FROM EstimationScores ORDER BY pixel DESC LIMIT {n};")
        results = self.cursor.fetchall()
        output = []
        for row in results:
            output.append({
                "team": row[0],
                "pixel": row[1],
                "f1": row[2],
                "iou": row[3]
            })
        return output
        
    def get_completion_score_by_team(self, team):
        self.cursor.execute(f"SELECT lpips FROM matrixcompletionscores WHERE team = '{team}';")
        results = self.cursor.fetchall()
        if not results:
            self.cursor.execute(f"INSERT INTO matrixcompletionscores (team, lpips, psnr, ssim) VALUES ('{team}', 1, 0, 0);")
            return 1
        else:
            return results[0][0]

    def get_estimation_score_by_team(self, team):
        self.cursor.execute(f"SELECT pixel from EstimationScores WHERE team = '{team}';")
        results = self.cursor.fetchall()
        if not results:
            self.cursor.execute(f"INSERT INTO EstimationScores (team, pixel, f1, iou) VALUES ('{team}', 0, 0, 0);")
            return 1
        else:
            return results[0][0]

    def create_database(self):
        self.__enter__()
        table_creation = [
            """
            CREATE TABLE MatrixCompletionScores
            (
                team TEXT PRIMARY KEY,
                psnr REAL NOT NULL,
                ssim REAL NOT NULL,
                lpips REAL NOT NULL,
                fid REAL NOT NULL
            );
            """,
            """
            CREATE TABLE EstimationScores
            (
                team TEXT PRIMARY KEY,
                pixel REAL NOT NULL,
                f1 REAL NOT NULL, 
                iou REAL NOT NULL
            );
            """,
            """
            CREATE TABLE ImageToImageScores
            (
                team TEXT PRIMARY KEY,
                score REAL NOT NULL
            );
            """
        ]
        for command in table_creation:
            self.cursor.execute(command)
        self.__exit__(None, None, None)
