from typing import Optional

from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins import TimeStamped
from core.basics.utils import CodeGenerator

from .mixins import SessionOptional
from .managers import ActiveRoomManager


class Person(TimeStamped, SessionOptional):
    """
    People are named individuals logging into the platform.
    """
    name = models.CharField(_("Name"), max_length=64)

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("People")
        ordering = ["name", "-created"]

    def __str__(self):
        return str(self.name)


class Group(TimeStamped, SessionOptional):
    """
    Groups are a named collection of people.
    """
    name = models.CharField(_('Team Name'), max_length=64, default="")
    people = models.ManyToManyField(Person, blank=True)

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        ordering = ["name", "-created"]

    def __str__(self):
        return str(self.name)

    def has_person(self, person: Person) -> bool:
        """
        Returns `True` if the person is in the group.
        :param person: Person
        :return: bool
        """
        return self.people.filter(pk=person.pk).exists()

    def can_join(self, person: Person) -> bool:
        """
        Returns `True` if the person can join the group.
        :return: bool
        """
        return not self.has_person(person)

    def join(self, person: Person):
        """
        Attempts to join the person to the group.
        :return: None
        """
        if not self.can_join(person):
            raise Exception('Person can not join this Group')
        self.people.add(person)
        self.save()


class Room(TimeStamped, SessionOptional):
    """
    Rooms are for people and groups to join together.
    """
    DEFAULT_GROUP_COUNT = 2
    DEFAULT_GROUP_NAMES = ['RED', 'BLUE', 'GREEN', 'CYAN', 'MAGENTA', 'YELLOW']

    code = models.SlugField(_("Code"), max_length=16)
    people = models.ManyToManyField(Person, blank=True)
    groups = models.ManyToManyField(Group, blank=True)

    objects = models.Manager()
    active_rooms = ActiveRoomManager()

    class Meta:
        verbose_name = _("Room")
        verbose_name_plural = _("Rooms")
        ordering = ["-created"]

    def __str__(self):
        return str(self.code)

    def __setup_code(self):
        if not self.code:
            self.code = CodeGenerator.room_code()

    def __get_groups_with_person_count(self):
        return self.groups.annotate(num_players=models.Count('people')).order_by('num_people')

    def save(self, *args, **kwargs):
        self.__setup_code()
        super(Room, self).save(*args, **kwargs)

    def has_person(self, person: Person) -> bool:
        """
        Returns `True` if the person is in the room.
        :param person: Person
        :return: bool
        """
        return self.people.filter(pk=person.pk).exists()

    def has_group(self, group: Group) -> bool:
        """
        Returns `True` if the group is in the room.
        :param group: Group
        :return: bool
        """
        return self.groups.filter(pk=group.pk).exists()

    def has(self, model_object) -> bool:
        """
        Returns `True` if the room has the person or group in it.
        :param model_object: Person or Group
        :return:
        """
        if isinstance(model_object, Person):
            return self.has_person(person=model_object)
        elif isinstance(model_object, Group):
            return self.has_group(group=model_object)
        return False

    def is_leader(self, person: Person) -> bool:
        """
        Returns `True` if the person is the room leader.
        :param person: Person
        :return: bool
        """
        return bool(self.session == person.session)

    def can_join(self, person: Person) -> bool:
        """
        Returns `True` if the person can join the room.
        :return: bool
        """
        return not self.has_person(person)

    def get_group_with_fewest_people(self) -> Optional[Group]:
        """
        Returns the group with the fewest people.
        :return: Optional[Group]
        """
        return self.__get_groups_with_person_count().first()

    def get_fewest_persons_per_group(self) -> int:
        """
        Returns the number of the fewest people in a group.
        :return: int
        """
        group = self.get_group_with_fewest_people()
        if group is None:
            return 0
        return group.people.count()

    def set_default_groups(self):
        """
        Sets the default groups.
        :return: None
        """
        group_count = self.groups.count()
        groups_remaining = self.DEFAULT_GROUP_COUNT - group_count
        for i in range(groups_remaining):
            new_group_i = group_count + i
            group = Group(name=self.DEFAULT_GROUP_NAMES[new_group_i])
            group.save()
            self.groups.add(group)
        self.save()

    def get_default_group(self) -> Group:
        """
        Returns the default group to join in the room.
        Will set default groups if there are none.
        :return: Team
        """
        if self.groups.count() <= self.DEFAULT_GROUP_COUNT:
            self.set_default_groups()
        return self.get_group_with_fewest_people()

    def join_group(self, person: Person, group: Group):
        """
        Attempts to join the person to a specific group in the room.
        Raises an exception if it fails.
        :param person: Person
        :param group: Group
        :raise: Exception
        :return:
        """
        if not self.has_group(group):
            raise Exception('Group does not exist in this Room.')
        group.join(person)

    def join(self, person: Person, group=None):
        """
        Attempts to join the person to the room.
        Raises an exception if it fails.
        :param person: Person
        :param group: Group or None
        :raise: Exception
        :return: None
        """
        if not self.can_join(person):
            raise Exception('Person can not join room.')
        self.people.add(person)
        if group is None:
            group = self.get_default_group()
        group.join(person)
        self.save()
