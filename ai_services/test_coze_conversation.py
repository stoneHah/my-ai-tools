# Init the Coze client through the access_token.
from dotenv import load_dotenv
import os
from cozepy import Coze, TokenAuth

load_dotenv()

coze_api_token = os.getenv("COZE_API_TOKEN")
coze_api_base = os.getenv("COZE_API_BASE")

print(coze_api_token)
print(coze_api_base)

coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=coze_api_base)

conversation = coze.conversations.create()

print(conversation)