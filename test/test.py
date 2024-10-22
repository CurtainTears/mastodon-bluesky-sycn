from atproto import Client

client = Client("")
client.login("", "")


token = client.export_session_string()

print(token)



