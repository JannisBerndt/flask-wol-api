from app.main import app
from app import db

if __name__ == "__main__": 
        app.run()
        db.init_db()
