from typing import Optional

from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins import TimeStamped
from core.basics.utils import CodeGenerator

from .mixins import SessionOptional
from .managers import ActiveRoomManager


class Player(TimeStamped, SessionOptional):
    """
    Players are named individuals logging into the platform.
    """
    name = models.CharField(_("Name"), max_length=64)

    class Meta:
        verbose_name = _("Player")
        verbose_name_plural = _("Players")
        ordering = ["name", "-created"]

    def __str__(self):
        return str(self.name)


class Group(TimeStamped, SessionOptional):
    """
    Groups are a named collection of players.
    """
    name = models.CharField(_('Team Name'), max_length=64, default="")
    players = models.ManyToManyField(Player, blank=True)

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        ordering = ["name", "-created"]

    def __str__(self):
        return str(self.name)

    def has_player(self, player: Player) -> bool:
        """
        Returns `True` if the player is in the group.
        :param player: Player
        :return: bool
        """
        return self.players.filter(pk=player.pk).exists()

    def has(self, model_object) -> bool:
        """
        Returns `True` if the player is in the group.
        :param model_object: Player
        :return:
        """
        if isinstance(model_object, Player):
            return self.has_player(player=model_object)
        return False

    def is_leader(self, player: Player) -> bool:
        """
        Returns `True` if the player is the group leader.
        :param player: Player
        :return: bool
        """
        return bool(self.session == player.session)

    def can_join(self, player: Player) -> bool:
        """
        Returns `True` if the player can join the group.
        :return: bool
        """
        return not self.has_player(player)

    def join(self, player: Player):
        """
        Attempts to join the player to the group.
        :return: None
        """
        if not self.can_join(player):
            raise Exception('Player can not join this Group')
        self.players.add(player)
        self.save()


class Room(TimeStamped, SessionOptional):
    """
    Rooms are for players and groups to join together.
    """
    DEFAULT_GROUP_COUNT = 2
    DEFAULT_GROUP_NAMES = ['RED', 'BLUE', 'GREEN', 'CYAN', 'MAGENTA', 'YELLOW']

    code = models.SlugField(_("Code"), max_length=16)
    players = models.ManyToManyField(Player, blank=True)
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

    def __get_groups_with_player_count(self):
        return self.groups.annotate(num_players=models.Count('players')).order_by('num_players')

    def save(self, *args, **kwargs):
        self.__setup_code()
        super(Room, self).save(*args, **kwargs)

    def has_player(self, player: Player) -> bool:
        """
        Returns `True` if the player is in the room.
        :param player: Player
        :return: bool
        """
        return self.players.filter(pk=player.pk).exists()

    def has_group(self, group: Group) -> bool:
        """
        Returns `True` if the group is in the room.
        :param group: Group
        :return: bool
        """
        return self.groups.filter(pk=group.pk).exists()

    def has(self, model_object) -> bool:
        """
        Returns `True` if the room has the player or group in it.
        :param model_object: Player or Group
        :return:
        """
        if isinstance(model_object, Player):
            return self.has_player(player=model_object)
        elif isinstance(model_object, Group):
            return self.has_group(group=model_object)
        return False

    def is_leader(self, player: Player) -> bool:
        """
        Returns `True` if the player is the room leader.
        :param player: Player
        :return: bool
        """
        return bool(self.session == player.session)

    def can_join(self, player: Player) -> bool:
        """
        Returns `True` if the player can join the room.
        :return: bool
        """
        return not self.has_player(player)

    def get_group_with_fewest_players(self) -> Optional[Group]:
        """
        Returns the group with the fewest players.
        :return: Optional[Group]
        """
        return self.__get_groups_with_player_count().first()

    def get_fewest_players_per_group(self) -> int:
        """
        Returns the number of the fewest players in a group.
        :return: int
        """
        group = self.get_group_with_fewest_players()
        if group is None:
            return 0
        return group.players.count()

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
        return self.get_group_with_fewest_players()

    def join_group(self, player: Player, group: Group):
        """
        Attempts to join the player to a specific group in the room.
        Raises an exception if it fails.
        :param player: Player
        :param group: Group
        :raise: Exception
        :return:
        """
        if not self.has_group(group):
            raise Exception('Group does not exist in this Room.')
        group.join(player)

    def join(self, player: Player, group=None):
        """
        Attempts to join the player to the room.
        Raises an exception if it fails.
        :param player: Player
        :param group: Group or None
        :raise: Exception
        :return: None
        """
        if not self.can_join(player):
            raise Exception('Player can not join room.')
        self.players.add(player)
        if group is None:
            group = self.get_default_group()
        group.join(player)
        self.save()
