from multiprocessing import Process

class CustomProcess(Process):
    def __init__(self, target, args = (), kwargs = {}, name = str()):
        """
        Initialize CustomProcess

        Args:
            target: Function to execute
            args: Arguments to pass to function; defaults to ()
            kwargs: Keyword arguments to pass to function; defaults to {}
            name: Process name; defaults to empty string
        """
        Process.__init__(self, target = target, args = args, kwargs = kwargs, name = name)
        super(CustomProcess, self).__init__()
        self._target = target
        self._args = tuple(args)
        self._kwargs = dict(kwargs)
        self._name = name
        self._result = None

    @property
    def result(self):
        """
        Get result of process

        Returns:
            Any: Process result
        """
        return self._result

    @property
    def name(self) -> str:
        """
        String used for process identification

        Returns:
            str: Process name
        """
        return self._name

    @name.setter
    def name(self, name: str):
        """
        Set process name

        Args:
            name (str): Process name
        """
        self._name = name

    def is_alive(self) -> bool:
        """
        Checks if process is alive or not

        Returns:
            bool: True if process is alive, else False
        """
        return super().is_alive()