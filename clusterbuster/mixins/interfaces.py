from abc import ABC, abstractmethod


class ModelInterface(ABC):
    model = None

    def __init__(self, model_object):
        if self.model is None:
            raise Exception('`model` must not be None in ModelInterface.')
        if not isinstance(model_object, self.model):
            raise Exception('`model_object` must be instance of %s.' % self.model)
        self.object = model_object


class Model2ModelInterface(ABC):
    model_a = None
    model_b = None

    def __init__(self, model_object_a, model_object_b):
        if self.model_a is None:
            raise Exception('`model_a` must not be None in Model2ModelInterface.')
        if self.model_b is None:
            raise Exception('`model_b` must not be None in Model2ModelInterface.')
        if not isinstance(model_object_a, self.model_a):
            raise Exception('`model_object_a` must be instance of %s.' % self.model_a)
        if not isinstance(model_object_b, self.model_b):
            raise Exception('`model_object_b` must be instance of %s.' % self.model_b)
        self.object_a = model_object_a
        self.object_b = model_object_b


class SetupInterface(ABC):
    @abstractmethod
    def setup(self):
        pass

    @abstractmethod
    def is_setup(self) -> bool:
        pass
