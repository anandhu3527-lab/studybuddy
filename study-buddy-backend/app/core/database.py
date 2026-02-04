from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb+srv://anandhakrishnanr868_db_user:w7atCTWvuAmB4Par@agromarket.amjhuf7.mongodb.net/"

client = AsyncIOMotorClient(MONGO_URL)

database = client.study_finder
user_collection = database.users
feedback_collection = database.feedback
request_collection = database.request_table
friends_collection = database.friends
def create_unique_index():
 user_collection.create_index("number",unique=True)

