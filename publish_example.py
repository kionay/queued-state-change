import json

import asyncio
import aio_pika

async def async_range(*args, **kwargs):
    for i in range(*args, **kwargs):
        yield(i)
        await asyncio.sleep(0.0)

async def main(loop):
    # Explicit type annotation
    connection: aio_pika.RobustConnection = await aio_pika.connect_robust(
        "amqp://myuser:mypassword@rabbitmq/", loop=loop
    )

    routing_key = "for_server"

    channel: aio_pika.abc.AbstractChannel = await connection.channel()

    publishing_message = {
        "type": "CHANGE_TEXT",
    }
    async for num in async_range(1,20):
        publishing_message["text"] = str(num)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(publishing_message).encode()
            ),
            routing_key=routing_key
        )

    await connection.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()