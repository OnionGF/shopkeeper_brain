from pymilvus import MilvusClient
client = MilvusClient(uri="http://127.0.0.1:19530")
# 替换成你的集合名
client.drop_collection("kb_item_names_v1")
