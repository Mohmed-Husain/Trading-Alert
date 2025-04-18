import os
from dotenv import load_dotenv
# Load environment variables from .env file, overriding existing ones
load_dotenv(override=True)
token = os.getenv('ANGEL_TOKEN')
print(token)