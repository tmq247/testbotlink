import time
import logging
from collections import defaultdict, deque
from typing import Dict, Deque
from config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Simple rate limiter to prevent spam and abuse.
    """
    
    def __init__(self, max_requests: int = RATE_LIMIT_REQUESTS, window_seconds: int = RATE_LIMIT_WINDOW):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests: Dict[int, Deque[float]] = defaultdict(deque)
    
    def is_allowed(self, user_id: int) -> bool:
        """
        Check if user is allowed to make a request.
        """
        current_time = time.time()
        user_queue = self.user_requests[user_id]
        
        # Remove old requests outside the window
        while user_queue and current_time - user_queue[0] > self.window_seconds:
            user_queue.popleft()
        
        # Check if user has exceeded the limit
        if len(user_queue) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False
        
        # Add current request
        user_queue.append(current_time)
        return True
    
    def get_remaining_requests(self, user_id: int) -> int:
        """
        Get remaining requests for user in current window.
        """
        current_time = time.time()
        user_queue = self.user_requests[user_id]
        
        # Remove old requests
        while user_queue and current_time - user_queue[0] > self.window_seconds:
            user_queue.popleft()
        
        return max(0, self.max_requests - len(user_queue))
    
    def get_reset_time(self, user_id: int) -> float:
        """
        Get time when rate limit resets for user.
        """
        user_queue = self.user_requests[user_id]
        if not user_queue:
            return 0
        
        return user_queue[0] + self.window_seconds
    
    def clear_user(self, user_id: int):
        """
        Clear rate limit data for a specific user.
        """
        if user_id in self.user_requests:
            del self.user_requests[user_id]
            logger.info(f"Cleared rate limit data for user {user_id}")
