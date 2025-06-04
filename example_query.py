from db_connection import get_connection

def execute_sample_query():
    """
    Example function demonstrating how to execute a query and fetch results.
    """
    try:
        # Get database connection
        connection = get_connection()
        cursor = connection.cursor()

        # Example: Query to get current timestamp from Oracle
        cursor.execute("SELECT * FROM TEST_CDC")
        result = cursor.fetchone()
        print(f"Current database timestamp: {result[0]}")

       
        cursor.close()
        connection.close()

    except Exception as e:
        print(f"Error executing query: {e}")

if __name__ == "__main__":
    execute_sample_query() 