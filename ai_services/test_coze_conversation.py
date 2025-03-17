# Init the Coze client through the access_token.
from dotenv import load_dotenv
import os
from cozepy import Coze, TokenAuth

load_dotenv()

coze_api_token = os.getenv("COZE_API_TOKEN")
coze_api_base = os.getenv("COZE_API_BASE")

print(coze_api_token)
print(coze_api_base)

coze = Coze(auth=TokenAuth(token="pat_YHtqeSA2IjDvQCVBJKB7kZmqj1rhQUQ2rUd4l04iC728VwQ5CL8VB0y9OBs7Rlq4"), base_url=coze_api_base)

conversation = coze.conversations.create()

print(conversation)