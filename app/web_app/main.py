from app.database import check_db_connection

from . import create_app

check_db_connection()
app = create_app()

if __name__ == "__main__":
    app.run()
