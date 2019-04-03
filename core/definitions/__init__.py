from gamedefinitions.interfaces import ComparisonConditionAbstract, RuleLibrary
from games.models import Game, StateMachine
from core.models import Word
from core.basics import PatternDeckBuilder


class ClusterBuster(RuleLibrary):
    WINNING_TOKENS_REQUIRED_TO_WIN = 2
    LOSING_TOKENS_REQUIRED_TO_LOSE = 2
    STARTING_WIN_TOKENS_PER_TEAM = 0
    STARTING_LOSE_TOKENS_PER_TEAM = 0
    SECRET_WORDS_PER_TEAM = 4
    CODE_CARD_SLOTS = 3

    @staticmethod
    def start_game(game: Game):
        """
        :param game:
        :return:
        """
        game.set_parameter_value('winning_tokens_required_to_win', ClusterBuster.WINNING_TOKENS_REQUIRED_TO_WIN)
        game.set_parameter_value('losing_tokens_required_to_lose', ClusterBuster.LOSING_TOKENS_REQUIRED_TO_LOSE)
        game.set_parameter_value('teams_start_tokens', 0)
        game.add_state_machine('draw_words_stage', 'fsm1')
        ClusterBuster.assign_team_win_tokens(game)
        ClusterBuster.assign_team_lose_tokens(game)
        ClusterBuster.set_win_condition(game)
        ClusterBuster.set_lose_condition(game)
        # game.transit_state_machine('fsm0', 'game_play', 'game_ready')
        trigger = game.add_trigger('draw_words')
        condition_group = trigger.condition_group
        condition_group.set_to_and_op()
        for team in game.teams.all():
            condition_group.add_comparison_condition(
                'teams_start_tokens',
                ('team_losing_tokens', team),
                ComparisonConditionAbstract.EQUAL
            )
            condition_group.add_comparison_condition(
                'teams_start_tokens',
                ('team_winning_tokens', team),
                ComparisonConditionAbstract.EQUAL
            )

    @staticmethod
    def assign_team_win_tokens(game: Game):
        for team in game.teams.all():
            game.set_parameter_value(('team_winning_tokens', team), ClusterBuster.STARTING_WIN_TOKENS_PER_TEAM)

    @staticmethod
    def assign_team_lose_tokens(game: Game):
        for team in game.teams.all():
            game.set_parameter_value(('team_losing_tokens', team), ClusterBuster.STARTING_LOSE_TOKENS_PER_TEAM)

    @staticmethod
    def set_win_condition(game: Game):
        trigger = game.add_trigger('team_won')
        condition_group = trigger.condition_group
        for team in game.teams.all():
            condition_group.add_comparison_condition(
                ('team_winning_tokens', team),
                'winning_tokens_required_to_win',
                ComparisonConditionAbstract.GREATER_THAN_OR_EQUAL
            )

    @staticmethod
    def set_lose_condition(game: Game):
        trigger = game.add_trigger('team_lost')
        condition_group = trigger.condition_group
        for team in game.teams.all():
            condition_group.add_comparison_condition(
                ('team_losing_tokens', team),
                'losing_tokens_required_to_lose',
                ComparisonConditionAbstract.GREATER_THAN_OR_EQUAL
            )

    @staticmethod
    def game_ready(game: Game):
        """
        :param game:
        :return:
        """
        game.transit_state_machine('fsm0', 'game_play', 'game_ready')

    @staticmethod
    def team_won(game: Game):
        """
        :param game:
        :return:
        """
        game.transit_state_machine('fsm0', 'game_play', 'team_won')

    @staticmethod
    def team_lost(game: Game):
        """
        :param game:
        :return:
        """
        game.transit_state_machine('fsm0', 'game_over', 'team_lost')

    @staticmethod
    def draw_words(game: Game):
        teams_set = game.teams
        team_count = teams_set.count()
        total_words = ClusterBuster.SECRET_WORDS_PER_TEAM * team_count

        random_word_set = Word.objects.order_by('?')
        random_words = random_word_set.all()[:total_words]

        if not bool(game.get_parameter_value('word_cards_drawn')):
            for team_i, team in enumerate(teams_set.all()):
                start_word_i = ClusterBuster.SECRET_WORDS_PER_TEAM * team_i
                end_word_i = start_word_i + ClusterBuster.SECRET_WORDS_PER_TEAM
                for word_i, random_word in enumerate(random_words[start_word_i:end_word_i]):
                    game.set_parameter_value(('team', team, 'secret_word', word_i+1), str(random_word))
            game.set_parameter_value('word_cards_drawn', True)

    @staticmethod
    def secret_words_drawn(game: Game, state_machine: StateMachine):
        conditional_transition = state_machine.add_conditional_transition('secret_words_drawn', 'rounds_stage')
        conditional_transition.set_to_and_op()
        for team in game.teams.all():
            for i in range(ClusterBuster.SECRET_WORDS_PER_TEAM):
                conditional_transition.add_has_value_condition(
                    ('team', team, 'secret_word', i+1),
                )

    @staticmethod
    def rounds_stage(game: Game, state_machine: StateMachine):
        game.add_state_machine('first_round')
        game.add_state_machine('select_leader_stage')
        game.set_parameter_value('current_round_count', 1)
        game.set_parameter_value('last_round_count', 8)

    @staticmethod
    def assign_team_leader(game: Game, state_machine: StateMachine):
        round_number = game.get_parameter_value('current_round_count')
        for team in game.teams.all():
            player_count = team.players.count()
            offset = round_number % player_count
            round_leader = team.players.all()[offset]
            game.set_parameter_value(('round', round_number, 'team', team, 'leader'), round_leader)

    @staticmethod
    def team_leaders_assigned(game: Game, state_machine: StateMachine):
        round_number = game.get_parameter_value('current_round_count')
        conditional_transition = state_machine.add_conditional_transition('team_leader_assigned', 'draw_code_card_stage')
        conditional_transition.set_to_and_op()
        for team in game.teams.all():
            conditional_transition.add_has_value_condition(
                ('round', round_number, 'team', team, 'leader'),
            )

    @staticmethod
    def leaders_draw_code_numbers(game: Game, state_machine: StateMachine):
        round_number = game.get_parameter_value('current_round_count')
        for team in game.teams.all():
            deck = PatternDeckBuilder.build_deck()
            # drawn_cards = self.get_drawn_cards()
            # deck.reduce(drawn_cards)
            deck.shuffle()
            card = deck.draw()
            print(card, card.value)
            for card_i, value in enumerate(card.value):
                game.set_parameter_value(('round', round_number, 'team', team, 'code', card_i+1), value)

    @staticmethod
    def code_numbers_drawn(game: Game, state_machine: StateMachine):
        round_number = game.get_parameter_value('current_round_count')
        conditional_transition = state_machine.add_conditional_transition('code_numbers_drawn',
                                                                          'leaders_make_hints_stage')
        conditional_transition.set_to_and_op()
        for team in game.teams.all():
            for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
                conditional_transition.add_has_value_condition(
                    ('round', round_number, 'team', team, 'code', card_i + 1),
                )

    @staticmethod
    def leaders_made_hints(game: Game, state_machine: StateMachine):
        round_number = game.get_parameter_value('current_round_count')
        conditional_transition = state_machine.add_conditional_transition('hints_submitted',
                                                                          'teams_share_guesses_stage')
        conditional_transition.set_to_and_op()
        for team in game.teams.all():
            for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
                conditional_transition.add_has_value_condition(
                    ('round', round_number, 'team', team, 'hint', card_i + 1),
                )

    @staticmethod
    def teams_made_guesses(game: Game, state_machine: StateMachine):
        round_number = game.get_parameter_value('current_round_count')
        conditional_transition = state_machine.add_conditional_transition('guesses_submitted',
                                                                          'teams_share_guesses_stage')
        conditional_transition.set_to_and_op()
        for guessing_team in game.teams.all():
            for hinting_team in game.teams.all():
                for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
                    conditional_transition.add_has_value_condition(
                        ('round', round_number, 'guessing_team', guessing_team, 'hinting_team', hinting_team, 'guess', card_i + 1),
                    )

    @staticmethod
    def method_map(rule):
        return {
            'start_game': ClusterBuster.start_game,
            'win_tokens': ClusterBuster.assign_team_win_tokens,
            'lose_tokens': ClusterBuster.assign_team_lose_tokens,
            'win_condition': ClusterBuster.set_win_condition,
            'lose_condition': ClusterBuster.set_lose_condition,
            'draw_words': ClusterBuster.draw_words,
            'secret_words_drawn': ClusterBuster.secret_words_drawn,
            'rounds_stage': ClusterBuster.rounds_stage,
            'assign_team_leader': ClusterBuster.assign_team_leader,
            'team_leaders_assigned': ClusterBuster.team_leaders_assigned,
            'leaders_draw_code_numbers': ClusterBuster.leaders_draw_code_numbers,
            'code_numbers_drawn': ClusterBuster.code_numbers_drawn,
            'leaders_made_hints': ClusterBuster.leaders_made_hints,
            'teams_made_guesses': ClusterBuster.teams_made_guesses,
        }[rule]
