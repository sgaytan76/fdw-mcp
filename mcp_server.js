#!/usr/bin/env node

const oracledb = require('oracledb');
require('dotenv').config();

// Initialize Oracle client
oracledb.initOracleClient({ libDir: process.env.ORACLE_HOME });

class MCPServer {
    constructor() {
        this.tools = [
            {
                name: "query_test_cdc",
                description: "Query the first 10 rows from FDW database TEST_CDC table",
                inputSchema: {
                    type: "object",
                    properties: {},
                    required: []
                }
            },
            {
                name: "export_to_csv",
                description: "Export TEST_CDC data from FDW database to CSV file",
                inputSchema: {
                    type: "object",
                    properties: {},
                    required: []
                }
            }
        ];
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

    async handleQuery() {
        try {
            const connection = await this.getOracleConnection();
            const result = await connection.execute(
                'SELECT * FROM TEST_CDC WHERE ROWNUM <= 10',
                [],
                { outFormat: oracledb.OUT_FORMAT_OBJECT }
            );
            await connection.close();

            return {
                content: [
                    {
                        type: "text",
                        text: `Query Results from FDW database TEST_CDC table:\n\n${JSON.stringify(result.rows, null, 2)}`
                    }
                ]
            };
        } catch (error) {
            this.debug(`Query error: ${error.message}`);
            return {
                content: [
                    {
                        type: "text",
                        text: `Error querying FDW database: ${error.message}`
                    }
                ],
                isError: true
            };
        }
    }

    async handleExport() {
        try {
            const connection = await this.getOracleConnection();
            const result = await connection.execute(
                'SELECT * FROM TEST_CDC WHERE ROWNUM <= 10',
                [],
                { outFormat: oracledb.OUT_FORMAT_OBJECT }
            );
            await connection.close();

            if (result.rows.length === 0) {
                return {
                    content: [
                        {
                            type: "text",
                            text: "No data found in FDW database TEST_CDC table to export."
                        }
                    ]
                };
            }

            const fs = require('fs');
            const filename = 'test_cdc_export.csv';
            
            // Convert to CSV
            const headers = Object.keys(result.rows[0]).join(',');
            const rows = result.rows.map(row => 
                Object.values(row).map(val => 
                    typeof val === 'string' ? `"${val.replace(/"/g, '""')}"` : val
                ).join(',')
            );
            
            fs.writeFileSync(filename, [headers, ...rows].join('\n'));

            return {
                content: [
                    {
                        type: "text",
                        text: `Data exported successfully from FDW database to ${filename}\n\nExported ${result.rows.length} rows with columns: ${headers}`
                    }
                ]
            };
        } catch (error) {
            this.debug(`Export error: ${error.message}`);
            return {
                content: [
                    {
                        type: "text",
                        text: `Error exporting data from FDW database: ${error.message}`
                    }
                ],
                isError: true
            };
        }
    }

    async handleRequest(request) {
        const { method, params } = request;

        switch (method) {
            case 'initialize':
                return {
                    protocolVersion: params.protocolVersion,
                    capabilities: {
                        tools: {},
                        resources: {}
                    },
                    serverInfo: {
                        name: "fdw-mcp-server",
                        version: "1.0.0"
                    }
                };

            case 'notifications/initialized':
                // This is a notification, no response needed
                return null;

            case 'tools/list':
                return {
                    tools: this.tools
                };

            case 'resources/list':
                return {
                    resources: []
                };

            case 'tools/call':
                const { name, arguments: args } = params;
                
                switch (name) {
                    case 'query_test_cdc':
                        return await this.handleQuery();
                    case 'export_to_csv':
                        return await this.handleExport();
                    default:
                        throw new Error(`Unknown tool: ${name}`);
                }

            default:
                throw new Error(`Unknown method: ${method}`);
        }
    }

    sendResponse(id, result) {
        if (result !== null) {
            const response = {
                jsonrpc: "2.0",
                id: id,
                result: result
            };
            console.log(JSON.stringify(response));
        }
    }

    sendError(id, error) {
        const response = {
            jsonrpc: "2.0",
            id: id,
            error: {
                code: -32000,
                message: error.message
            }
        };
        console.log(JSON.stringify(response));
    }

    start() {
        this.debug('FDW MCP Server starting...');

        process.stdin.setEncoding('utf8');
        
        let buffer = '';
        
        process.stdin.on('data', async (chunk) => {
            buffer += chunk;
            
            // Process complete lines
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer
            
            for (const line of lines) {
                if (line.trim()) {
                    let currentRequest = null;
                    try {
                        currentRequest = JSON.parse(line);
                        this.debug(`Received request: ${JSON.stringify(currentRequest)}`);
                        
                        const result = await this.handleRequest(currentRequest);
                        this.sendResponse(currentRequest.id, result);
                        
                    } catch (error) {
                        this.debug(`Error processing request: ${error.message}`);
                        this.sendError(currentRequest?.id || null, error);
                    }
                }
            }
        });

        process.stdin.on('end', () => {
            this.debug('FDW MCP Server shutting down...');
            process.exit(0);
        });

        this.debug('FDW MCP Server ready for requests');
    }
}

const server = new MCPServer();
server.start(); 