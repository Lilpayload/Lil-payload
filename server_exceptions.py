class ServerError(Exception):
    """Base class for server exceptions"""
    pass

class ConnectionError(ServerError):
    """Raised when there's an error with the connection"""
    pass

class ProcessError(ServerError):
    """Raised when there's an error with the server process"""
    pass

class MonitorError(ServerError):
    """Raised when there's an error in the monitoring system"""
    pass