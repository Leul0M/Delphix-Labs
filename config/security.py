import hashlib
import time
from functools import wraps

class SecurityManager:
    def __init__(self):
        self.allowed_users = set()  # Add your Telegram user ID
        self.rate_limits = {}
        
    def check_auth(self, user_id: int) -> bool:
        return not self.allowed_users or user_id in self.allowed_users
    
    def rate_limit(self, max_requests=10, window=60):
        def decorator(func):
            @wraps(func)
            async def wrapper(update, context):
                user_id = update.effective_user.id
                now = time.time()
                
                # Check auth
                if not self.check_auth(user_id):
                    await update.message.reply_text("⛔ Unauthorized")
                    return
                
                # Rate limiting
                user_requests = self.rate_limits.get(user_id, [])
                user_requests = [t for t in user_requests if now - t < window]
                
                if len(user_requests) >= max_requests:
                    await update.message.reply_text("⏳ Rate limit exceeded. Please wait.")
                    return
                
                user_requests.append(now)
                self.rate_limits[user_id] = user_requests
                
                return await func(update, context)
            return wrapper
        return decorator

security = SecurityManager()