import random
from django.db import models
from django.db.models import Count


class RandomWordManager(models.Manager):
    def random(self):
        count = self.aggregate(count=Count('id'))['count']
        if count == 0:
            raise ValueError
        random_index = random.randint(0, count - 1)
        return self.all()[random_index]