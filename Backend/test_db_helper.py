from src.database import get_db, get_schema, execute_query, get_full_table_info

def test_get_db():
    print("=== Testing get_db() ===")
    db = get_db()
    print("Database object:", db)

def test_get_schema():
    print("=== Testing get_schema() ===")
    schema = get_schema()
    print("Schema info (original get_schema()):")
    print(schema)

def test_full_table_info():
    print("=== Testing get_full_table_info() ===")
    schema = get_full_table_info()  # no arguments needed
    print(schema)

def test_execute_query():
    print("=== Testing execute_query() ===")
    db = get_db()
    
    # Pick a safe test query
    test_query = "SELECT * FROM clients;"
    
    result = execute_query(test_query)
    print("Query result:")
    print(result)

if __name__ == "__main__":
    test_get_db()
    test_get_schema()
    test_full_table_info()  # new test
    test_execute_query()
