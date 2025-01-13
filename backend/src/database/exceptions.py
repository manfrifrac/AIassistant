class DatabaseError(Exception):
    """Base class for database-related exceptions."""
    pass

class ConnectionError(DatabaseError):
    """Exception raised for connection-related issues."""
    pass

class QueryError(DatabaseError):
    """Exception raised for query execution failures."""
    pass
