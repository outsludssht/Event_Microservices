import asyncio
import aio_pika
import json

async def process_order(message: aio_pika.IncomingMessage):
    async with message.process():
        order_data = json.loads(message.body.decode())
        print(f" [PAYMENT] Processing payment for order ID {order_data['id']} ({order_data['amount']} USD)...")
        
        # Simulate payment processing
        await asyncio.sleep(2)
        
        # Publish payment.completed event
        connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
        async with connection:
            channel = await connection.channel()
            await channel.declare_queue("payment.completed", durable=True)
            await channel.default_exchange.publish(
                aio_pika.Message(body=message.body),
                routing_key="payment.completed",
            )
        print(f" [PAYMENT] Success! Payment completed for order {order_data['id']}.")

async def main():
    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq/")
    channel = await connection.channel()
    queue = await channel.declare_queue("order.created", durable=True)
    
    await queue.consume(process_order)
    print(" [*] Payment Service started. Waiting for orders...")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())