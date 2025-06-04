import asyncio
import json

async def test_connection():
    try:
        # Connect to the server
        reader, writer = await asyncio.open_connection('localhost', 1337)
        print("Connected to MCP server")

        # Test query_test_cdc command
        message = {
            'command': 'query_test_cdc'
        }
        
        # Send the message
        message_bytes = json.dumps(message).encode()
        writer.write(len(message_bytes).to_bytes(4, 'big'))
        writer.write(message_bytes)
        await writer.drain()
        print("Sent query_test_cdc command")

        # Read the response
        length_bytes = await reader.read(4)
        message_length = int.from_bytes(length_bytes, 'big')
        response_bytes = await reader.read(message_length)
        response = json.loads(response_bytes.decode())
        
        print("\nServer Response:")
        print(json.dumps(response, indent=2))

        # Close the connection
        writer.close()
        await writer.wait_closed()
        print("\nConnection closed")

    except ConnectionRefusedError:
        print("Could not connect to the server. Make sure it's running on localhost:1337")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing MCP Server connection...")
    asyncio.run(test_connection()) 