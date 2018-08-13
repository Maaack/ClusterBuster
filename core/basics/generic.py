class ObjectList(list):
    def __init__(self, object_type):
        self.object_type = object_type
        super(ObjectList, self).__init__()

    def append(self, item):
        if not isinstance(item, self.object_type):
            raise TypeError('item is not of type %s' % self.object_type)
        super(ObjectList, self).append(item)

    def remove(self, item):
        if not isinstance(item, self.object_type):
            raise TypeError('item is not of type %s' % self.object_type)
        super(ObjectList, self).remove(item)

    def extend(self, iterable):
        if not isinstance(iterable, ObjectList):
            raise TypeError('iterable is not of type ObjectList')
        if self.object_type != iterable.object_type:
            raise TypeError('iterable must have equivalent object_type %s' % self.object_type)
        super(ObjectList, self).extend(iterable)

    def reduce(self, iterable):
        if not isinstance(iterable, ObjectList):
            raise TypeError('iterable is not of type ObjectList')
        if self.object_type != iterable.object_type:
            raise TypeError('iterable must have equivalent object_type %s' % self.object_type)
        for other_object in iterable:
            self.remove(other_object)

