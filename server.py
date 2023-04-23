import json

import asyncio
import aio_pika

from common.async_create_store import create_store

STORE = None

INBOUND_STATE_UPDATE_QUEUE = "serverbound"
CLIENT_EXCHANGE = "clients"

def sample_reducer(state, action):
    if state is None:
        state = {}
    if action is None:
        return state
    elif action["type"] == "CHANGE_TEXT":
        return {"text":action["text"]}
    return state

async def main(loop):

    
    # Explicit type annotation
    connection: aio_pika.RobustConnection = await aio_pika.connect_robust(
        "amqp://myuser:mypassword@rabbitmq/", loop=loop
    )

    async with connection:

        print("creating channel")
        channel: aio_pika.abc.AbstractChannel = await connection.channel()

        print("creating state update queue")
        inbound_state_update_queue: aio_pika.abc.AbstractQueue = await channel.declare_queue(
            INBOUND_STATE_UPDATE_QUEUE,
            auto_delete=True
        )

        print("declaring client exchange")
        client_exchange = await channel.declare_exchange(name=CLIENT_EXCHANGE, type=aio_pika.ExchangeType.FANOUT, auto_delete=True)

        async def publish_update():
            print("publishing update")
            await client_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(STORE.get_state()).encode()
                ),
                routing_key=""
            )

        print("subscribing to store")
        STORE.subscribe(publish_update)

        print("listening for state changes")
        async with inbound_state_update_queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    print("received message")
                    decoded_message = message.body.decode()
                    state_change = json.loads(decoded_message)
                    new_state = await STORE.dispatch(state_change)
                    print(f"new state: {new_state}")


if __name__ == "__main__":
    STORE = create_store(sample_reducer)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
