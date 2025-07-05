import os
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", 3065))
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
SECRET_KEY = os.getenv("SECRET_KEY")
UPDATE_ORDER_STATUS_URL = os.getenv("UPDATE_ORDER_STATUS_URL")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
DECREASE_STOCK_URL = os.getenv("DECREASE_STOCK_URL")
RESTORE_STOCK_URL = os.getenv("RESTORE_STOCK_URL")
CHECK_STOCK_URL = os.getenv("CHECK_STOCK_URL")
