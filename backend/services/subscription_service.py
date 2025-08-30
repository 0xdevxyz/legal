"""Subscription management service"""
class SubscriptionService:
    async def create_subscription(self, user_id: str, plan: str) -> dict:
        return {"id": "sub_123", "user_id": user_id, "plan": plan, "status": "active"}
