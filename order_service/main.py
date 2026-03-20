from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aio_pika
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, select

# Database Settings
DATABASE_URL = "postgresql+asyncpg://user:password@order_db/orders_db"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class OrderDB(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    item = Column(String)
    amount = Column(Float)

app = FastAPI(title="Order Service")

class OrderSchema(BaseModel):
    item: str
    amount: float

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.post("/orders")
async def create_order(order: OrderSchema):
    # 1. Save to PostgreSQL
    async with AsyncSessionLocal() as session:
        new_order = OrderDB(item=order.item, amount=order.amount)
        session.add(new_order)
        await session.commit()
        await session.refresh(new_order)

    # 2. Publish event to RabbitMQ
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue("order.created", durable=True)
        
        message_body = json.dumps({
            "id": new_order.id, 
            "item": order.item, 
            "amount": order.amount
        }).encode()
        
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body),
            routing_key="order.created",
        )
    
    return {"status": "Order saved and event published", "order_id": new_order.id}

@app.get("/orders/{order_id}")
async def get_order(order_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(OrderDB).where(OrderDB.id == order_id))
        order = result.scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return order