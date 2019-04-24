from django.db import models
from django.utils.translation import ugettext_lazy as _

from clusterbuster.mixins.models import TimeStamped

from games.models import Game, Condition

from ..basics import PatternDeckBuilder
from . import managers


class Word(TimeStamped):
    """
    Words that can be used for word based games.
    """
    class Meta:
        verbose_name = _("Word")
        verbose_name_plural = _("Words")
        ordering = ["text", "-created"]

    text = models.CharField(_("Text"), max_length=32, db_index=True)
    objects = managers.RandomWordManager()

    def __str__(self):
        return str(self.text)


class State(TimeStamped):
    """
    States define sections of the Game, like stages, rounds, and turns.
    """
    slug = models.SlugField(_("Slug"), max_length=32)
    name = models.CharField(_("Name"), max_length=64, blank=True)

    class Meta:
        verbose_name = _("State")
        verbose_name_plural = _("States")

    def __str__(self):
        return str(self.slug)


class StateMachine(models.Model):
    slug = models.SlugField(_("Slug"), max_length=32)
    root_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="+")

    class Meta:
        verbose_name = _("State Machine")
        verbose_name_plural = _("State Machines")

    def __str__(self):
        return str(self.slug)


class ClusterBuster(Game):
    WINNING_TOKENS_REQUIRED_TO_WIN = 2
    LOSING_TOKENS_REQUIRED_TO_LOSE = 2
    STARTING_WIN_TOKENS_PER_TEAM = 0
    STARTING_LOSE_TOKENS_PER_TEAM = 0
    SECRET_WORDS_PER_TEAM = 4
    CODE_CARD_SLOTS = 3
    LAST_ROUND_NUMBER = 8
    FIRST_ROUND_NUMBER = 1

    class Meta:
        verbose_name = _("Cluster Buster")
        verbose_name_plural = _("Cluster Busters")

    def set_state_machines(self):
        for state_machine in StateMachine.objects.all():
            parameter_key = state_machine.slug
            self.set_parameter_value(parameter_key, state_machine.root_state)

    def setup_state_parameters(self):
        for state in State.objects.all():
            parameter_key = state.slug + "_state"
            self.set_parameter_value(parameter_key, state)

    def transit_state_machine(self, key_args, state_slug: str):
        try:
            state = State.objects.get(slug=state_slug)
        except State.DoesNotExist:
            raise ValueError('state_slug must match the label of an existing State')
        self.set_parameter_value(key_args, state)

    def start_game(self):
        self.set_state_machines()
        self.setup_state_parameters()
        self.set_parameter_value('winning_tokens_required_to_win', ClusterBuster.WINNING_TOKENS_REQUIRED_TO_WIN)
        self.set_parameter_value('losing_tokens_required_to_lose', ClusterBuster.LOSING_TOKENS_REQUIRED_TO_LOSE)
        self.assign_team_win_tokens()
        self.assign_team_lose_tokens()
        self.set_win_condition()
        self.set_lose_condition()
        self.game_ready()
        self.transit_state_machine('fsm1', 'draw_words_stage')

    def assign_team_win_tokens(self):
        for team in self.teams.all():
            self.set_parameter_value(('team_winning_tokens', team), ClusterBuster.STARTING_WIN_TOKENS_PER_TEAM)

    def assign_team_lose_tokens(self):
        for team in self.teams.all():
            self.set_parameter_value(('team_losing_tokens', team), ClusterBuster.STARTING_LOSE_TOKENS_PER_TEAM)

    def set_win_condition(self):
        trigger = self.add_trigger('team_won')
        condition_group = trigger.condition_group
        for team in self.teams.all():
            condition_group.add_comparison_condition(
                ('team_winning_tokens', team),
                'winning_tokens_required_to_win',
                Condition.GREATER_THAN_OR_EQUAL
            )

    def set_lose_condition(self):
        trigger = self.add_trigger('team_lost')
        condition_group = trigger.condition_group
        for team in self.teams.all():
            condition_group.add_comparison_condition(
                ('team_losing_tokens', team),
                'losing_tokens_required_to_lose',
                Condition.GREATER_THAN_OR_EQUAL
            )

    def game_ready(self):

        # Draw Words Trigger
        trigger = self.add_trigger('draw_words')
        condition_group = trigger.condition_group
        condition_group.add_comparison_condition('fsm1', 'draw_words_stage_state')
        # Rounds Trigger
        trigger = self.add_trigger('start_first_round')
        condition_group = trigger.condition_group
        condition_group.add_comparison_condition('fsm1', 'rounds_stage_state')
        # Assign Team Leader Trigger
        trigger = self.add_trigger('assign_team_leader')
        trigger.repeats = True
        trigger.save()
        condition_group = trigger.condition_group
        condition_group.add_comparison_condition('fsm3', 'select_leader_stage_state')
        # Assign Team Leader Trigger
        trigger = self.add_trigger('leaders_draw_code_numbers')
        trigger.repeats = True
        trigger.save()
        condition_group = trigger.condition_group
        condition_group.add_comparison_condition('fsm3', 'draw_code_card_stage_state')
        # Game Ready Transition
        self.transit_state_machine('fsm0', 'game_play')

    def set_winning_team(self):
        winning_team = None
        losing_team = None
        team_1 = self.teams.all()[0]
        team_2 = self.teams.all()[1]
        team_1_winning_tokens = self.get_parameter_value(('team_winning_tokens', team_1))
        team_2_winning_tokens = self.get_parameter_value(('team_winning_tokens', team_2))
        if team_1_winning_tokens > team_2_winning_tokens:
            winning_team = team_1
            losing_team = team_2
        elif team_2_winning_tokens > team_1_winning_tokens:
            winning_team = team_2
            losing_team = team_1
        self.set_parameter_value('game_winning_team', winning_team)
        self.set_parameter_value('game_losing_team', losing_team)

    def set_losing_team(self):
        winning_team = None
        losing_team = None
        team_1 = self.teams.all()[0]
        team_2 = self.teams.all()[1]
        team_1_losing_tokens = self.get_parameter_value(('team_losing_tokens', team_1))
        team_2_losing_tokens = self.get_parameter_value(('team_losing_tokens', team_2))
        if team_1_losing_tokens > team_2_losing_tokens:
            losing_team = team_1
            winning_team = team_2
        elif team_2_losing_tokens > team_1_losing_tokens:
            losing_team = team_2
            winning_team = team_1
        self.set_parameter_value('game_winning_team', winning_team)
        self.set_parameter_value('game_losing_team', losing_team)

    def team_won(self):
        self.transit_state_machine('fsm1', 'final_scoring_stage')
        self.set_winning_team()
        self.transit_state_machine('fsm0', 'game_over')

    def team_lost(self):

        self.transit_state_machine('fsm1', 'final_scoring_stage')
        self.set_losing_team()
        self.transit_state_machine('fsm0', 'game_over')

    def last_round_over(self):
        self.transit_state_machine('fsm1', 'final_scoring_stage')
        self.set_winning_team()
        winning_team = self.get_parameter_value('game_winning_team')
        if winning_team is None:
            self.set_losing_team()
        self.transit_state_machine('fsm0', 'game_over')

    def draw_words(self):
        if not bool(self.get_parameter_value('word_cards_drawn')):
            teams_set = self.teams
            team_count = teams_set.count()
            total_words = ClusterBuster.SECRET_WORDS_PER_TEAM * team_count
            # Get Random Words
            random_word_set = Word.objects.order_by('?')
            random_words = random_word_set.all()[:total_words]
            for team_i, team in enumerate(teams_set.all()):
                start_word_i = ClusterBuster.SECRET_WORDS_PER_TEAM * team_i
                end_word_i = start_word_i + ClusterBuster.SECRET_WORDS_PER_TEAM
                for word_i, random_word in enumerate(random_words[start_word_i:end_word_i]):
                    self.set_parameter_value(('team', team, 'secret_word', word_i + 1), str(random_word))
            self.set_parameter_value('word_cards_drawn', True)
        self.transit_state_machine('fsm1', 'rounds_stage')

    def start_first_round(self):
        self.set_parameter_value('current_round_number', ClusterBuster.FIRST_ROUND_NUMBER)
        self.set_parameter_value('last_round_number', ClusterBuster.LAST_ROUND_NUMBER)
        self.transit_state_machine('fsm2', 'first_round')
        self.transit_state_machine('fsm3', 'select_leader_stage')

    def assign_team_leader(self):
        round_number = self.get_parameter_value('current_round_number')
        for team in self.teams.all():
            player_count = team.players.count()
            offset = (round_number - 1) % player_count
            round_leader = team.players.all()[offset]
            self.set_parameter_value(('round', round_number, 'team', team, 'leader'), round_leader)
        self.transit_state_machine('fsm3', 'draw_code_card_stage')

    def leaders_draw_code_numbers(self):
        round_number = self.get_parameter_value('current_round_number')
        for team in self.teams.all():
            deck = PatternDeckBuilder.build_deck()
            # drawn_cards = self.get_drawn_cards()
            # deck.reduce(drawn_cards)
            deck.shuffle()
            card = deck.draw()
            print(card, card.value)
            for card_i, value in enumerate(card.value):
                self.set_parameter_value(('round', round_number, 'team', team, 'code', card_i + 1), value)
        # Team Leader Made Hints Trigger
        trigger = self.add_trigger('leaders_made_hints')
        condition_group = trigger.condition_group
        condition_group.set_to_and_op()
        for team in self.teams.all():
            for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
                condition_group.add_has_value_condition(
                    ('round', round_number, 'team', team, 'hint', card_i + 1),
                )
        self.transit_state_machine('fsm3', 'leaders_make_hints_stage')

    def leaders_made_hints(self):
        self.transit_state_machine('fsm3', 'teams_guess_codes_stage')
        round_number = self.get_parameter_value('current_round_number')
        fsm2 = self.get_parameter_value('fsm2')  # type: State
        is_first_round = fsm2.slug == 'first_round'
        # Team Players Made Guesses Trigger
        trigger = self.add_trigger('teams_made_guesses')
        condition_group = trigger.condition_group
        condition_group.set_to_and_op()
        for guessing_team in self.teams.all():
            for hinting_team in self.teams.all():
                if guessing_team != hinting_team and is_first_round:
                    continue
                for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
                    condition_group.add_has_value_condition(
                        ('round', round_number, 'guessing_team', guessing_team, 'hinting_team', hinting_team, 'guess',
                         card_i + 1),
                    )

    def teams_made_guesses(self):
        self.transit_state_machine('fsm3', 'teams_share_guesses_stage')

    def score_teams(self):
        round_number = self.get_parameter_value('current_round_number')
        fsm2 = self.get_parameter_value('fsm2')  # type: State
        is_first_round = fsm2.slug == 'first_round'
        self.transit_state_machine('fsm3', 'score_teams_stage')
        for guessing_team in self.teams.all():
            for hinting_team in self.teams.all():
                if guessing_team != hinting_team and is_first_round:
                    continue
                correct_guesses = 0
                for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
                    card_slot = card_i + 1
                    guess = self.get_parameter_value(
                        ('round', round_number, 'guessing_team', guessing_team, 'hinting_team', hinting_team, 'guess',
                         card_slot),
                    )
                    actual = self.get_parameter_value(
                        ('round', round_number, 'team', hinting_team, 'code',
                         card_slot),
                    )
                    if int(guess) == int(actual):
                        correct_guesses += 1

                if correct_guesses == ClusterBuster.CODE_CARD_SLOTS and guessing_team != hinting_team:
                    # Guessed Opponent's Code Correctly
                    winning_tokens = self.get_parameter_value(('team_winning_tokens', guessing_team))
                    winning_tokens += 1
                    self.set_parameter_value(('team_winning_tokens', guessing_team), winning_tokens)
                if correct_guesses < ClusterBuster.CODE_CARD_SLOTS and guessing_team == hinting_team:
                    # Guessed Team's Code Incorrectly
                    losing_tokens = self.get_parameter_value(('team_losing_tokens', guessing_team))
                    losing_tokens += 1
                    self.set_parameter_value(('team_losing_tokens', guessing_team), losing_tokens)

    def start_next_round(self):
        fsm3 = self.get_parameter_value('fsm3')  # type: State
        fsm3_state = fsm3.slug
        if fsm3_state != 'score_teams_stage':
            return
        fsm2 = self.get_parameter_value('fsm2')  # type: State
        fsm2_state = fsm2.slug
        if fsm2_state == 'last_round':
            self.last_round_over()
            return
        round_number = self.get_parameter_value('current_round_number')
        round_number += 1
        self.set_parameter_value('current_round_number', round_number)
        if round_number == ClusterBuster.LAST_ROUND_NUMBER:
            self.transit_state_machine('fsm2', 'last_round')
        elif fsm2_state == 'first_round' and round_number > ClusterBuster.FIRST_ROUND_NUMBER:
            self.transit_state_machine('fsm2', 'middle_rounds')
        self.transit_state_machine('fsm3', 'select_leader_stage')
