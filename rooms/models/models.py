from typing import Optional

from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins import TimeStamped, CodeGenerator

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


class Team(TimeStamped, SessionOptional):
    """
    Teams are a named collection of players.
    """
    name = models.CharField(_('Team Name'), max_length=64, default="")
    players = models.ManyToManyField(Player, blank=True)

    class Meta:
        verbose_name = _("Team")
        verbose_name_plural = _("Teams")
        ordering = ["name", "-created"]

    def __str__(self):
        return str(self.name)

    def has_player(self, player: Player) -> bool:
        """
        Returns `True` if the player is in the team.
        :param player: Player
        :return: bool
        """
        return self.players.filter(pk=player.pk).exists()

    def has(self, model_object) -> bool:
        """
        Returns `True` if the player is in the team.
        :param model_object: Player
        :return:
        """
        if isinstance(model_object, Player):
            return self.has_player(player=model_object)
        return False

    def is_leader(self, player: Player) -> bool:
        """
        Returns `True` if the player is the team leader.
        :param player: Player
        :return: bool
        """
        return bool(self.session == player.session)

    def can_join(self, player: Player) -> bool:
        """
        Returns `True` if the player can join the team.
        :return: bool
        """
        return not self.has_player(player)

    def join(self, player: Player):
        """
        Attempts to join the player to the team.
        :return: None
        """
        if not self.can_join(player):
            raise Exception('Player can not join this Team')
        self.players.add(player)
        self.save()


class Room(TimeStamped, SessionOptional):
    """
    Rooms are for players and teams to join together.
    """
    DEFAULT_TEAM_COUNT = 2
    DEFAULT_TEAM_NAMES = ['RED', 'BLUE', 'GREEN', 'CYAN', 'MAGENTA', 'YELLOW']

    code = models.SlugField(_("Code"), max_length=16)
    players = models.ManyToManyField(Player, blank=True)
    teams = models.ManyToManyField(Team, blank=True)
    current_activity = models.ForeignKey("Activity", on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

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

    def __get_teams_with_player_count(self):
        return self.teams.annotate(num_players=models.Count('players')).order_by('num_players')

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

    def has_team(self, team: Team) -> bool:
        """
        Returns `True` if the team is in the room.
        :param team: Team
        :return: bool
        """
        return self.teams.filter(pk=team.pk).exists()

    def has(self, model_object) -> bool:
        """
        Returns `True` if the room has the player or team in it.
        :param model_object: Player or Team
        :return:
        """
        if isinstance(model_object, Player):
            return self.has_player(player=model_object)
        elif isinstance(model_object, Team):
            return self.has_team(team=model_object)
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

    def get_team_with_fewest_players(self) -> Optional[Team]:
        """
        Returns the team with the fewest players.
        :return: Optional[Team]
        """
        return self.__get_teams_with_player_count().first()

    def get_fewest_players_per_team(self) -> int:
        """
        Returns the number of the fewest players in a team.
        :return: int
        """
        team = self.get_team_with_fewest_players()
        if team is None:
            return 0
        return team.players.count()

    def set_default_teams(self):
        """
        Sets the default teams.
        :return: None
        """
        team_count = self.teams.count()
        teams_remaining = self.DEFAULT_TEAM_COUNT - team_count
        for i in range(teams_remaining):
            new_team_i = team_count + i
            team = Team(name=self.DEFAULT_TEAM_NAMES[new_team_i])
            team.save()
            self.teams.add(team)
        self.save()

    def get_default_team(self) -> Team:
        """
        Returns the default team to join in the room.
        Will set default teams if there are none.
        :return: Team
        """
        if self.teams.count() <= self.DEFAULT_TEAM_COUNT:
            self.set_default_teams()
        return self.get_team_with_fewest_players()

    def join_team(self, player: Player, team: Team):
        """
        Attempts to join the player to a specific team in the room.
        Raises an exception if it fails.
        :param player: Player
        :param team: Team
        :raise: Exception
        :return:
        """
        if not self.has_team(team):
            raise Exception('Team does not exist in this Room.')
        team.join(player)

    def join(self, player: Player, team=None):
        """
        Attempts to join the player to the room.
        Raises an exception if it fails.
        :param player: Player
        :param team: Team or None
        :raise: Exception
        :return: None
        """
        if not self.can_join(player):
            raise Exception('Player can not join room.')
        self.players.add(player)
        if team is None:
            team = self.get_default_team()
        team.join(player)
        self.save()

    def get_activity_options(self):
        player_count = self.players.count()
        team_count = self.teams.count()
        team_player_count = self.get_fewest_players_per_team()
        activity_options = ActivityOption.objects.filter(minimum_player__lte=player_count,
                                                         minimum_teams__lte=team_count,
                                                         minimum_players_per_team__lte=team_player_count).all()
        return activity_options

    def start_activity(self, name: str, link: str):
        activity = self.activities.create(name=name, link=link)
        self.current_activity = activity
        self.save()


class Activity(TimeStamped):
    """
    Activities tie Rooms to something else.
    """

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(_("Name"), max_length=64)
    link = models.URLField(_("Link"))

    class Meta:
        verbose_name = _("Activity")
        verbose_name_plural = _("Activities")
        ordering = ["-created"]

    def __str__(self):
        return str(self.name) + " (" + str(self.link) + ")"


class ActivityOption(TimeStamped):
    """
    Activities tie Rooms to something else.
    """

    slug = models.SlugField(_("Slug"))
    start_text = models.CharField(_("Text"), max_length=256)
    start_url = models.CharField(_("Relative Link"), max_length=64)
    minimum_player = models.PositiveSmallIntegerField(_("Minimum Players"), default=0)
    minimum_teams = models.PositiveSmallIntegerField(_("Minimum Teams"), default=0)
    minimum_players_per_team = models.PositiveSmallIntegerField(_("Minimum Players Per Team"), default=0)

    class Meta:
        verbose_name = _("Activity Option")
        verbose_name_plural = _("Activity Options")
        ordering = ["-created"]

    def __str__(self):
        return str(self.slug)

