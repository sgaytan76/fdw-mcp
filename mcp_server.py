import asyncio
import json
from query_test_cdc import fetch_test_cdc_rows
from export_to_csv import export_test_cdc_to_csv
import io
import sys
from contextlib import redirect_stdout
import os

def debug_print(msg):
    print(msg, file=sys.stderr, flush=True)

class MCPServer:
    def __init__(self, host='localhost', port=1337):
        self.host = host
        self.port = port
        self.handlers = {
            'query_test_cdc': self.handle_query,
            'export_to_csv': self.handle_export
        }
        debug_print(f"Initializing MCP Server on {host}:{port}")

    async def send_message(self, writer, message):
        try:
            message_bytes = json.dumps(message).encode()
            writer.write(len(message_bytes).to_bytes(4, 'big'))
            writer.write(message_bytes)
            await writer.drain()
            debug_print(f"Sent message: {message}")
        except Exception as e:
            debug_print(f"Error sending message: {e}")
            raise

    async def handle_client(self, reader, writer):
        try:
            while True:
                # Read the length prefix (4 bytes)
                length_bytes = await reader.read(4)
                if not length_bytes:
                    debug_print("Client disconnected (no length bytes)")
                    break

                message_length = int.from_bytes(length_bytes, 'big')
                debug_print(f"Received message length: {message_length}")

                # Read the message
                message_bytes = await reader.read(message_length)
                if not message_bytes:
                    debug_print("Client disconnected (no message bytes)")
                    break

                # Parse the message
                message = json.loads(message_bytes.decode())
                debug_print(f"Received message: {message}")

                # Handle initialization specially
                if message.get('method') == 'initialize':
                    # Send immediate response
                    init_response = {
                        'jsonrpc': '2.0',
                        'id': message.get('id'),
                        'result': {
                            'protocolVersion': message['params']['protocolVersion'],
                            'capabilities': {}
                        }
                    }
                    await self.send_message(writer, init_response)

                    # Send ready notification
                    ready_notification = {
                        'jsonrpc': '2.0',
                        'method': 'server/ready',
                        'params': {}
                    }
                    await self.send_message(writer, ready_notification)
                    continue

                # Handle commands
                if message.get('command'):
                    command = message.get('command')
                    if command not in self.handlers:
                        error_response = {
                            'jsonrpc': '2.0',
                            'id': message.get('id'),
                            'error': {
                                'code': -32601,
                                'message': f'Unknown command: {command}'
                            }
                        }
                        await self.send_message(writer, error_response)
                        continue

                    handler = self.handlers[command]
                    try:
                        result = await handler(message)
                        await self.send_message(writer, result)
                    except Exception as e:
                        error_response = {
                            'jsonrpc': '2.0',
                            'id': message.get('id'),
                            'error': {
                                'code': -32000,
                                'message': str(e)
                            }
                        }
                        await self.send_message(writer, error_response)

        except Exception as e:
            debug_print(f"Error in handle_client: {e}")
            try:
                error_response = {
                    'jsonrpc': '2.0',
                    'id': message.get('id') if 'message' in locals() else None,
                    'error': {
                        'code': -32000,
                        'message': str(e)
                    }
                }
                await self.send_message(writer, error_response)
            except:
                pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except:
                pass
            debug_print("Client connection closed")

    async def handle_query(self, message):
        debug_print("Executing query handler")
        output = io.StringIO()
        with redirect_stdout(output):
            try:
                fetch_test_cdc_rows()
                return {
                    'jsonrpc': '2.0',
                    'id': message.get('id'),
                    'result': {
                        'output': output.getvalue()
                    }
                }
            except Exception as e:
                debug_print(f"Error in query handler: {e}")
                return {
                    'jsonrpc': '2.0',
                    'id': message.get('id'),
                    'error': {
                        'code': -32000,
                        'message': str(e)
                    }
                }

    async def handle_export(self, message):
        debug_print("Executing export handler")
        output = io.StringIO()
        with redirect_stdout(output):
            try:
                export_test_cdc_to_csv()
                return {
                    'jsonrpc': '2.0',
                    'id': message.get('id'),
                    'result': {
                        'output': output.getvalue()
                    }
                }
            except Exception as e:
                debug_print(f"Error in export handler: {e}")
                return {
                    'jsonrpc': '2.0',
                    'id': message.get('id'),
                    'error': {
                        'code': -32000,
                        'message': str(e)
                    }
                }

    async def start(self):
        try:
            server = await asyncio.start_server(
                self.handle_client,
                self.host,
                self.port
            )
            
            debug_print(f"MCP Server running on {self.host}:{self.port}")
            
            async with server:
                await server.serve_forever()
        except Exception as e:
            debug_print(f"Error starting server: {e}")
            raise

if __name__ == "__main__":
    debug_print("Starting MCP Server...")
    server = MCPServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        debug_print("\nServer shutdown requested")
    except Exception as e:
        debug_print(f"Server error: {e}")
    finally:
        debug_print("Server shutdown complete") 