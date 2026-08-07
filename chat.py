"""chat.py — interactive PhenoAssistant session."""
from agents import user_proxy, manager

print("\nPhenoAssistant is ready. Type a task, or 'exit' to quit.\n")
task = input("You: ")
if task.strip().lower() not in ("exit", "quit", ""):
    user_proxy.initiate_chat(recipient=manager, message=task)
print("\nSession ended.")
