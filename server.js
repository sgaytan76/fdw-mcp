const net = require('net');
const oracledb = require('oracledb');
require('dotenv').config();

// Initialize Oracle client
oracledb.initOracleClient({ libDir: process.env.ORACLE_HOME });

class MCPServer {
    constructor(port = 1337) {
        this.port = port;
        this.handlers = {
            'query_test_cdc': this.handleQuery.bind(this),
            'export_to_csv': this.handleExport.bind(this)
        };
    }

    debug(msg) {
        console.error(`[DEBUG] ${msg}`);
    }

    async getOracleConnection() {
        return await oracledb.getConnection({
            user: process.env.ORACLE_USER,
            password: process.env.ORACLE_PASSWORD,
            connectString: process.env.ORACLE_DSN
        });
    }

    async handleQuery(message) {
        try {
            const connection = await this.getOracleConnection();
            const result = await connection.execute(
                'SELECT * FROM TEST_CDC WHERE ROWNUM <= 10',
                [],
                { outFormat: oracledb.OUT_FORMAT_OBJECT }
            );
            await connection.close();

            return {
                jsonrpc: '2.0',
                id: message.id,
                result: {
                    output: JSON.stringify(result.rows, null, 2)
                }
            };
        } catch (error) {
            this.debug(`Query error: ${error.message}`);
            return {
                jsonrpc: '2.0',
                id: message.id,
                error: {
                    code: -32000,
                    message: error.message
                }
            };
        }
    }

    async handleExport(message) {
        try {
            const connection = await this.getOracleConnection();
            const result = await connection.execute(
                'SELECT * FROM TEST_CDC WHERE ROWNUM <= 10',
                [],
                { outFormat: oracledb.OUT_FORMAT_OBJECT }
            );
            await connection.close();

            const fs = require('fs');
            const filename = 'test_cdc_export.csv';
            
            // Convert to CSV
            const headers = Object.keys(result.rows[0]).join(',');
            const rows = result.rows.map(row => 
                Object.values(row).map(val => 
                    typeof val === 'string' ? `"${val}"` : val
                ).join(',')
            );
            
            fs.writeFileSync(filename, [headers, ...rows].join('\n'));

            return {
                jsonrpc: '2.0',
                id: message.id,
                result: {
                    output: `Data exported successfully to ${filename}`
                }
            };
        } catch (error) {
            this.debug(`Export error: ${error.message}`);
            return {
                jsonrpc: '2.0',
                id: message.id,
                error: {
                    code: -32000,
                    message: error.message
                }
            };
        }
    }

    async handleMessage(message) {
        this.debug(`Received message: ${JSON.stringify(message)}`);

        if (message.method === 'initialize') {
            return {
                jsonrpc: '2.0',
                id: message.id,
                result: {
                    protocolVersion: message.params.protocolVersion,
                    capabilities: {}
                }
            };
        }

        const handler = this.handlers[message.command];
        if (!handler) {
            return {
                jsonrpc: '2.0',
                id: message.id,
                error: {
                    code: -32601,
                    message: `Unknown command: ${message.command}`
                }
            };
        }

        return await handler(message);
    }

    async handleConnection(socket) {
        this.debug('New client connected');
        
        let buffer = Buffer.alloc(0);
        
        socket.on('data', async (data) => {
            buffer = Buffer.concat([buffer, data]);
            
            while (buffer.length >= 4) {
                const messageLength = buffer.readUInt32BE(0);
                if (buffer.length < 4 + messageLength) break;
                
                const messageData = buffer.slice(4, 4 + messageLength);
                buffer = buffer.slice(4 + messageLength);
                
                try {
                    const message = JSON.parse(messageData.toString());
                    const response = await this.handleMessage(message);
                    
                    if (response) {
                        const responseData = Buffer.from(JSON.stringify(response));
                        const lengthPrefix = Buffer.alloc(4);
                        lengthPrefix.writeUInt32BE(responseData.length);
                        socket.write(Buffer.concat([lengthPrefix, responseData]));
                        
                        // Send ready notification after initialization
                        if (message.method === 'initialize') {
                            const readyNotification = {
                                jsonrpc: '2.0',
                                method: 'server/ready',
                                params: {}
                            };
                            const notificationData = Buffer.from(JSON.stringify(readyNotification));
                            const notificationPrefix = Buffer.alloc(4);
                            notificationPrefix.writeUInt32BE(notificationData.length);
                            socket.write(Buffer.concat([notificationPrefix, notificationData]));
                        }
                    }
                } catch (error) {
                    this.debug(`Error processing message: ${error.message}`);
                    const errorResponse = {
                        jsonrpc: '2.0',
                        id: null,
                        error: {
                            code: -32000,
                            message: error.message
                        }
                    };
                    const responseData = Buffer.from(JSON.stringify(errorResponse));
                    const lengthPrefix = Buffer.alloc(4);
                    lengthPrefix.writeUInt32BE(responseData.length);
                    socket.write(Buffer.concat([lengthPrefix, responseData]));
                }
            }
        });

        socket.on('error', (error) => {
            this.debug(`Socket error: ${error.message}`);
        });

        socket.on('close', () => {
            this.debug('Client disconnected');
        });
    }

    start() {
        const server = net.createServer((socket) => {
            this.handleConnection(socket);
        });

        server.listen(this.port, () => {
            this.debug(`MCP Server running on localhost:${this.port}`);
        });

        server.on('error', (error) => {
            this.debug(`Server error: ${error.message}`);
        });
    }
}

const server = new MCPServer();
server.start(); 