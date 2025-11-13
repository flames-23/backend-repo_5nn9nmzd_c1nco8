"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Add your own schemas here:
# --------------------------------------------------

class PaymentReturn(BaseModel):
    """
    Payment returns collection schema
    Collection name: "paymentreturn" (lowercase of class name)
    Represents a returned/failed/refunded payment event
    """
    transaction_id: str = Field(..., description="Original transaction ID")
    customer_id: Optional[str] = Field(None, description="Customer identifier")
    amount: float = Field(..., ge=0, description="Return amount in USD")
    currency: str = Field("USD", description="Currency code")
    reason: Literal[
        "insufficient_funds",
        "card_expired",
        "fraud_suspected",
        "disputed",
        "technical_error",
        "account_closed",
        "other",
    ] = Field(..., description="Reason for payment return")
    status: Literal[
        "pending",
        "returned",
        "refunded",
        "reversed",
        "chargeback",
        "resolved",
    ] = Field("returned", description="Current state of the return")
    payment_method: Literal["card", "ach", "wire", "wallet"] = Field(
        "card", description="Payment method"
    )
    region: Optional[str] = Field(None, description="Geographic region/country code")
    customer_segment: Optional[str] = Field(None, description="Segment label")
    occurred_at: datetime = Field(default_factory=datetime.utcnow, description="Event time")
    days_to_return: Optional[int] = Field(None, ge=0, description="Days from payment to return")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
