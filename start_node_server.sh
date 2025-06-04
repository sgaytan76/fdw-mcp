#!/bin/bash

# Source Oracle environment
source ./setup_oracle_env.sh

# Install dependencies if needed
npm install

# Start the server
node server.js 