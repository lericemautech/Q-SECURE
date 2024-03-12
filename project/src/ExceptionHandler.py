from socket import error
from logging import shutdown

def handle_exceptions(log):
    def decorator(func):
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except BrokenPipeError as exception:
                exception_msg = "Unable to write to shutdown socket"
                log.exception(exception_msg)
                raise BrokenPipeError(exception_msg) from exception

            except ConnectionRefusedError as exception:
                exception_msg = "Connection refused"
                log.exception(exception_msg)
                raise ConnectionRefusedError(exception_msg) from exception

            except ConnectionAbortedError as exception:
                exception_msg = "Connection aborted"
                log.exception(exception_msg)
                raise ConnectionAbortedError(exception_msg) from exception

            except ConnectionResetError as exception:
                exception_msg = "Connection reset"
                log.exception(exception_msg)
                raise ConnectionResetError(exception_msg) from exception

            except ConnectionError as exception:
                exception_msg = "Connection lost"
                log.exception(exception_msg)
                raise ConnectionError(exception_msg) from exception

            except TimeoutError as exception:
                exception_msg = "Connection timed out"
                log.exception(exception_msg)
                raise TimeoutError(exception_msg) from exception

            except error as exception:
                log.exception(exception)
                raise error from exception

            finally:
                shutdown()

        return inner

    return decorator