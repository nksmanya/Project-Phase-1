import os


class Config:
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
SQLALCHEMY_DATABASE_URI = os.environ.get(
"DATABASE_URL", f"sqlite:///{os.path.join(os.getcwd(), 'instance', 'relate.sqlite3')}"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False