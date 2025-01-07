# src/langgraph/graph.py

# from langchain_core.messages import HumanMessage

# class MessagesState:
#     def __init__(self, messages=None, **kwargs):
#         self.messages = messages if messages else []
#         for key, value in kwargs.items():
#             setattr(self, key, value)

#     def get(self, key, default=None):
#         return getattr(self, key, default)

#     def set(self, key, value):
#         setattr(self, key, value)

#     def get_last_user_message(self):
#         for msg in reversed(self.messages):
#             if isinstance(msg, HumanMessage):
#                 return msg
#         return None
