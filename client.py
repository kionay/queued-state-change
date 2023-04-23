import json
import uuid
import random

import asyncio
import aio_pika

OUTBOUND_STATE_UPDATE_QUEUE = "serverbound"
CLIENT_EXCHANGE = "clients"

CLIENT_NAME = None

async def main(loop):
    # Explicit type annotation
    connection: aio_pika.RobustConnection = await aio_pika.connect_robust(
        "amqp://myuser:mypassword@rabbitmq/", loop=loop
    )

    async with connection:
        channel: aio_pika.abc.AbstractChannel = await connection.channel()
        client_exchange = await channel.declare_exchange(name=CLIENT_EXCHANGE, type=aio_pika.ExchangeType.FANOUT, auto_delete=True)
        this_client_queue = await channel.declare_queue(CLIENT_NAME, auto_delete=True)
        await this_client_queue.bind(client_exchange, "")
    
        publishing_message = {
            "type": "CHANGE_TEXT",
            "text": f"change stage to {random.randint(1,100)}"
        }


        async with this_client_queue.iterator() as queue_iter:
            print("publishing state change")
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(publishing_message).encode()
                ),
                routing_key=OUTBOUND_STATE_UPDATE_QUEUE
            )
            print("listening for server updates")
            async for message in queue_iter:
                async with message.process():
                    decoded_message = message.body.decode()
                    state_change = json.loads(decoded_message)
                    print(f"server communicated this is the new state: {state_change}")

        print("closing")
        await this_client_queue.unbind(client_exchange, "")
        await this_client_queue.delete()



if __name__ == "__main__":
    CLIENT_NAME = str(uuid.uuid4())
    print(f"client name: {CLIENT_NAME}")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()