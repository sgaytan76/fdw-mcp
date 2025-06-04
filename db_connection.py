import cx_Oracle
import os
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_oracle_client_path():
    """
    Get the Oracle Client library path
    """
    # Check manual installation path
    manual_path = "/opt/oracle"
    if os.path.exists(manual_path):
        print(f"Found Oracle Client at: {manual_path}")
        return manual_path

    return None

def get_db_config():
    """
    Get database configuration from environment variables
    """
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please create a .env file with the required variables."
        )
    
    return {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT')),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }

# Configure Oracle Client library path
oracle_client_path = get_oracle_client_path()
if oracle_client_path:
    print(f"Initializing Oracle Client with library path: {oracle_client_path}")
    try:
        cx_Oracle.init_oracle_client(lib_dir=oracle_client_path)
        print("Successfully initialized Oracle Client")
    except Exception as e:
        print(f"Warning: Could not initialize Oracle Client: {e}")
else:
    print("Warning: Could not find Oracle Client library path")

def try_connection(dsn_str):
    """
    Attempts to connect using a specific DSN string
    """
    try:
        db_config = get_db_config()
        connection = cx_Oracle.connect(
            user=db_config['user'],
            password=db_config['password'],
            dsn=dsn_str
        )
        return connection, None
    except cx_Oracle.DatabaseError as e:
        return None, str(e)

def get_connection():
    """
    Creates and returns a connection to the Oracle database.
    """
    try:
        db_config = get_db_config()
        print("\nAttempting to connect to Oracle Database...")
        print(f"Host: {db_config['host']}")
        print(f"Port: {db_config['port']}")
        print(f"User: {db_config['user']}")
        print(f"Oracle Client Path: {oracle_client_path}")
        
        # Try different connection methods
        connection_attempts = [
            {
                'type': 'SID',
                'value': os.getenv('DB_SID', 'FDW'),
                'dsn': cx_Oracle.makedsn(
                    host=db_config['host'],
                    port=db_config['port'],
                    sid=os.getenv('DB_SID', 'FDW')
                )
            },
            {
                'type': 'Service Name',
                'value': os.getenv('DB_SID', 'FDW'),
                'dsn': cx_Oracle.makedsn(
                    host=db_config['host'],
                    port=db_config['port'],
                    service_name=os.getenv('DB_SID', 'FDW')
                )
            },
            {
                'type': 'SID (lowercase)',
                'value': os.getenv('DB_SID', 'FDW').lower(),
                'dsn': cx_Oracle.makedsn(
                    host=db_config['host'],
                    port=db_config['port'],
                    sid=os.getenv('DB_SID', 'FDW').lower()
                )
            }
        ]

        print("\nTrying different connection methods:")
        for attempt in connection_attempts:
            print(f"\nAttempting connection using {attempt['type']}: {attempt['value']}")
            print(f"DSN: {attempt['dsn']}")
            
            connection, error = try_connection(attempt['dsn'])
            if connection:
                print(f"✅ Successfully connected using {attempt['type']}: {attempt['value']}")
                return connection
            else:
                print(f"❌ Failed with error: {error}")

        print("\nAll connection attempts failed.")
        print("\nPossible issues:")
        print("1. The database identifier (SID/Service Name) might be incorrect")
        print("2. The database might not be accepting connections")
        print("3. Network/firewall issues might be preventing the connection")
        print("\nPlease verify:")
        print("- The correct SID with your database administrator")
        print("- That the database is running and accepting connections")
        print("- That there are no network/firewall issues")
        
        raise Exception("Could not establish connection with any method")
        
    except Exception as error:
        print(f"\nError connecting to Oracle Database:")
        print(f"Error Type: {type(error).__name__}")
        print(f"Error Details: {str(error)}")
        raise

def test_connection():
    """
    Tests the database connection by executing a simple query.
    """
    try:
        connection = get_connection()
        cursor = connection.cursor()
        
        # Execute a simple test query that works in Oracle 9i
        cursor.execute("SELECT 1 FROM DUAL")
        result = cursor.fetchone()
        
        print("\nSuccessfully connected to Oracle Database!")
        print(f"Test query result: {result[0]}")
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"\nFailed to connect to the database: {e}")
        return False

if __name__ == "__main__":
    # Test the connection when running this file directly
    test_connection() 