#!/bin/bash

# Check for Apple Silicon
if [[ $(uname -m) != 'arm64' ]]; then
    echo "⚠️  Warning: This script is optimized for Apple Silicon (ARM64). You appear to be running on a different architecture." >&2
fi

# Set up paths for Oracle Client
ORACLE_CLIENT_PATH="/opt/oracle"

if [ ! -d "$ORACLE_CLIENT_PATH" ]; then
    echo "❌ Oracle Instant Client not found at $ORACLE_CLIENT_PATH" >&2
    echo "Please install Oracle Instant Client for ARM64:" >&2
    echo "1. Download from: https://www.oracle.com/database/technologies/instant-client/macos-arm64-intel-x86-downloads.html" >&2
    echo "2. Run these commands:" >&2
    echo "   sudo mkdir -p /opt/oracle" >&2
    echo "   cd /opt/oracle" >&2
    echo "   sudo unzip ~/Downloads/instantclient-basic-macos.arm64-19.8.0.0.0dbru.zip" >&2
    exit 1
fi

# Export the necessary environment variables
export ORACLE_HOME=$ORACLE_CLIENT_PATH
export DYLD_LIBRARY_PATH=$ORACLE_CLIENT_PATH
export LD_LIBRARY_PATH=$ORACLE_CLIENT_PATH
export PATH=$ORACLE_CLIENT_PATH:$PATH

echo "Oracle environment variables have been set:" >&2
echo "ORACLE_HOME=$ORACLE_HOME" >&2
echo "DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH" >&2
echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH" >&2

# Verify the existence of the library files
echo "" >&2
echo "Checking for Oracle Client libraries..." >&2
if [ -f "$ORACLE_CLIENT_PATH/libclntsh.dylib" ]; then
    echo "✅ Found main library: $ORACLE_CLIENT_PATH/libclntsh.dylib" >&2
else
    # Check for version-specific library name
    DYLIB_FILES=$(ls $ORACLE_CLIENT_PATH/libclntsh.dylib.* 2>/dev/null)
    if [ -n "$DYLIB_FILES" ]; then
        echo "Found Oracle library files:" >&2
        echo "$DYLIB_FILES" >&2
        echo "" >&2
        echo "Creating symbolic link..." >&2
        cd "$ORACLE_CLIENT_PATH"
        LATEST_LIB=$(ls libclntsh.dylib.* | sort -V | tail -n 1)
        ln -sf "$LATEST_LIB" libclntsh.dylib
        echo "✅ Created symbolic link: $LATEST_LIB -> libclntsh.dylib" >&2
    else
        echo "❌ No Oracle Client libraries found in $ORACLE_CLIENT_PATH" >&2
        echo "Please verify your installation" >&2
        exit 1
    fi
fi

echo "" >&2
echo "✅ Oracle environment setup complete." >&2

# Create the tools directory
mkdir -p ~/Library/Application\ Support/Claude/tools

# Copy the tool configuration
cp claude_tool.json ~/Library/Application\ Support/Claude/tools/oracle_db_query.json 