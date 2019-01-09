from abc import ABC, abstractmethod


class AbstractServiceResponse(ABC):
    def __init__(self):
        self.data = {}
        self.__set_default()

    def __getattr__(self, item):
        try:
            return self.data[item]
        except KeyError:
            pass
        raise AttributeError

    def __setattr__(self, key, value):
        self.data[key] = value

    @abstractmethod
    def __set_default(self):
        """
        Set the default response data.
        self.key = value
        :return:
        """
        pass


class AbstractServiceRequest(ABC):
    def __init__(self):
        self.parameters = {}
        self.__set_default()

    def __getattr__(self, item):
        try:
            return self.parameters[item]
        except KeyError:
            pass
        raise AttributeError

    def __setattr__(self, key, value):
        self.parameters[key] = value

    @abstractmethod
    def __set_default(self):
        """
        Set the default request parameters.
        self.key = value
        :return:
        """
        pass


class AbstractService(ABC):
    @staticmethod
    @abstractmethod
    def run(request: AbstractServiceRequest) -> AbstractServiceResponse:
        pass


class GenericServiceRequest(AbstractServiceRequest):
    def __set_default(self):
        self.generic = None


class GenericServiceResponse(AbstractServiceResponse):
    def __set_default(self):
        self.generic = None


class GenericService(AbstractService):
    @staticmethod
    def run(request: GenericServiceRequest) -> GenericServiceResponse:
        if not isinstance(request, GenericServiceRequest):
            raise ValueError('`request` object is not instance of GenericServiceRequest.')
        return GenericServiceResponse()

