from collections import deque
import discord.utils

class MessageHandler:
    def __init__(self, max_messages: int = 6, window_seconds: int = 8):
        self.history = {}  # author_id → deque of timestamps
        self.max = max_messages
        self.window = window_seconds

    def add(self, author_id: int):
        now = discord.utils.utcnow().timestamp()
        q = self.history.setdefault(author_id, deque())
        q.append(now)
        while q and now - q[0] > self.window:
            q.popleft()

    def is_spamming(self, author_id: int) -> bool:
        q = self.history.get(author_id, deque())
        return len(q) >= self.max

    def spam_count(self, author_id: int) -> int:
        return len(self.history.get(author_id, deque()))
