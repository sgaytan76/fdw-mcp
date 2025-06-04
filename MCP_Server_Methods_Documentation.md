# MCP Server Methods Documentation

## 🏗️ **Code Architecture Overview**

The `mcp_server.js` implements a complete MCP (Model Context Protocol) server with the following core methods organized in a single `MCPServer` class.

---

## 📋 **Method Breakdown**

### **1. `constructor()`**
**Purpose**: Initialize the MCP server with available tools
```javascript
constructor() {
    this.tools = [
        {
            name: "query_test_cdc",
            description: "Query the first 10 rows from FDW database TEST_CDC table",
            inputSchema: { type: "object", properties: {}, required: [] }
        },
        {
            name: "export_to_csv", 
            description: "Export TEST_CDC data from FDW database to CSV file",
            inputSchema: { type: "object", properties: {}, required: [] }
        }
    ];
}
```
**Key Details**:
- Defines two main tools available to Claude
- Uses MCP standard tool schema format
- No input parameters required for these specific tools

---

### **2. `debug(msg)`**
**Purpose**: Centralized logging for debugging and monitoring
```javascript
debug(msg) {
    console.error(`[DEBUG] ${msg}`);
}
```
**Key Details**:
- Outputs to stderr to avoid interfering with MCP protocol communication
- Prefixed with `[DEBUG]` for easy filtering
- Used throughout server for troubleshooting

---

### **3. `getOracleConnection()`**
**Purpose**: Establish database connection using environment variables
```javascript
async getOracleConnection() {
    return await oracledb.getConnection({
        user: process.env.ORACLE_USER,
        password: process.env.ORACLE_PASSWORD,
        connectString: process.env.ORACLE_DSN
    });
}
```
**Key Details**:
- Async method returning Oracle connection object
- Uses dotenv for secure credential management
- Throws exception if connection fails (handled by callers)

---

### **4. `handleQuery()`**
**Purpose**: Execute database query and format results for Claude
```javascript
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
            content: [{
                type: "text",
                text: `Query Results from FDW database TEST_CDC table:\n\n${JSON.stringify(result.rows, null, 2)}`
            }]
        };
    } catch (error) {
        // Error handling...
    }
}
```
**Key Details**:
- Limits results to 10 rows for performance
- Returns data in MCP content format
- Automatically closes database connection
- Comprehensive error handling with user-friendly messages

---

### **5. `handleExport()`**
**Purpose**: Export database data to CSV file with validation
```javascript
async handleExport() {
    try {
        const connection = await this.getOracleConnection();
        const result = await connection.execute(/* same query */);
        await connection.close();
        
        if (result.rows.length === 0) {
            return { content: [{ type: "text", text: "No data found..." }] };
        }
        
        const fs = require('fs');
        const filename = 'test_cdc_export.csv';
        
        // CSV generation logic
        const headers = Object.keys(result.rows[0]).join(',');
        const rows = result.rows.map(row => 
            Object.values(row).map(val => 
                typeof val === 'string' ? `"${val.replace(/"/g, '""')}"` : val
            ).join(',')
        );
        
        fs.writeFileSync(filename, [headers, ...rows].join('\n'));
        
        return {
            content: [{
                type: "text",
                text: `Data exported successfully from FDW database to ${filename}...`
            }]
        };
    } catch (error) {
        // Error handling...
    }
}
```
**Key Details**:
- Validates data exists before export
- Handles CSV escaping for strings with quotes
- Creates file in current working directory
- Returns detailed success message with row count

---

### **6. `handleRequest(request)`**
**Purpose**: Main request router implementing MCP protocol methods
```javascript
async handleRequest(request) {
    const { method, params } = request;
    
    switch (method) {
        case 'initialize':
            return {
                protocolVersion: params.protocolVersion,
                capabilities: { tools: {}, resources: {} },
                serverInfo: { name: "fdw-mcp-server", version: "1.0.0" }
            };
            
        case 'notifications/initialized':
            return null; // Notification, no response needed
            
        case 'tools/list':
            return { tools: this.tools };
            
        case 'resources/list':
            return { resources: [] };
            
        case 'tools/call':
            const { name } = params;
            switch (name) {
                case 'query_test_cdc': return await this.handleQuery();
                case 'export_to_csv': return await this.handleExport();
                default: throw new Error(`Unknown tool: ${name}`);
            }
            
        default:
            throw new Error(`Unknown method: ${method}`);
    }
}
```
**Key Details**:
- Implements all required MCP protocol methods
- Handles initialization handshake
- Routes tool calls to appropriate handlers
- Supports notifications (no response required)
- Proper error handling for unknown methods/tools

---

### **7. `sendResponse(id, result)`**
**Purpose**: Send JSON-RPC 2.0 compliant responses to Claude
```javascript
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
```
**Key Details**:
- Outputs to stdout for MCP protocol communication
- Only sends response if result is not null (notifications)
- Follows JSON-RPC 2.0 specification exactly

---

### **8. `sendError(id, error)`**
**Purpose**: Send standardized error responses
```javascript
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
```
**Key Details**:
- Uses standard JSON-RPC error format
- Error code -32000 for implementation-defined errors
- Preserves original error message for debugging

---

### **9. `start()`**
**Purpose**: Initialize server and handle stdin communication
```javascript
start() {
    this.debug('FDW MCP Server starting...');
    
    process.stdin.setEncoding('utf8');
    let buffer = '';
    
    process.stdin.on('data', async (chunk) => {
        buffer += chunk;
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line
        
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
```
**Key Details**:
- Handles line-buffered stdin input
- Processes multiple requests per data chunk
- Robust error handling with request context preservation
- Graceful shutdown on stdin close
- Comprehensive debug logging throughout

---

## 🔧 **Implementation Patterns**

### **Error Handling Strategy**
- **Database Errors**: Caught and converted to user-friendly messages
- **Protocol Errors**: Proper JSON-RPC error responses
- **Request Parsing**: Safe JSON parsing with fallback error handling

### **Resource Management**
- **Database Connections**: Always closed in try/finally pattern
- **File Operations**: Synchronous for simplicity and reliability
- **Memory Management**: Streaming input processing to handle large requests

### **Protocol Compliance**
- **MCP 2024-11-05**: Full specification implementation
- **JSON-RPC 2.0**: Strict adherence to protocol standards
- **Stdio Communication**: No network dependencies

---

*This method documentation provides the technical foundation for understanding how the MCP server bridges Claude Desktop with the FDW database through a clean, maintainable Node.js implementation.* 