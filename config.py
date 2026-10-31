import os
 
 
class Config:
    # MySQL connection settings
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "chandu@17@07")
    MYSQL_DB = "student_management_db"
 
    # Flask session security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")