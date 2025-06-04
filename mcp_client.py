import asyncio
import json

class MCPClient:
    def __init__(self, host='localhost', port=1337):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.host, self.port
        )

    async def send_message(self, message):
        # Convert message to JSON and encode
        message_bytes = json.dumps(message).encode()
        
        # Send length prefix
        self.writer.write(len(message_bytes).to_bytes(4, 'big'))
        # Send message
        self.writer.write(message_bytes)
        await self.writer.drain()

        # Read response length
        length_bytes = await self.reader.read(4)
        response_length = int.from_bytes(length_bytes, 'big')

        # Read response
        response_bytes = await self.reader.read(response_length)
        return json.loads(response_bytes.decode())

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

async def main():
    client = MCPClient()
    try:
        await client.connect()
        
        # Test the query command
        print("\nTesting query_test_cdc command...")
        response = await client.send_message({'command': 'query_test_cdc'})
        print("Response:")
        print(response['output'] if response['status'] == 'success' else f"Error: {response['message']}")

        # Test the export command
        print("\nTesting export_to_csv command...")
        response = await client.send_message({'command': 'export_to_csv'})
        print("Response:")
        print(response['output'] if response['status'] == 'success' else f"Error: {response['message']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main()) 