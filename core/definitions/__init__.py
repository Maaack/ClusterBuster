from gamedefinitions.interfaces import ComparisonConditionAbstract, RuleLibrary
from games.models import Game, StateMachine, State
from core.models import Word
from core.basics import PatternDeckBuilder


class ClusterBuster(RuleLibrary):
    WINNING_TOKENS_REQUIRED_TO_WIN = 2
    LOSING_TOKENS_REQUIRED_TO_LOSE = 2
    STARTING_WIN_TOKENS_PER_TEAM = 0
    STARTING_LOSE_TOKENS_PER_TEAM = 0
    SECRET_WORDS_PER_TEAM = 4
    CODE_CARD_SLOTS = 3
    LAST_ROUND_NUMBER = 8
    FIRST_ROUND_NUMBER = 1

    @staticmethod
    def start_game(game: Game):
        """
        :param game:
        :return:
        """
        game.set_parameter_value('winning_tokens_required_to_win', ClusterBuster.WINNING_TOKENS_REQUIRED_TO_WIN)
        game.set_parameter_value('losing_tokens_required_to_lose', ClusterBuster.LOSING_TOKENS_REQUIRED_TO_LOSE)
        ClusterBuster.assign_team_win_tokens(game)
        ClusterBuster.assign_team_lose_tokens(game)
        ClusterBuster.set_win_condition(game)
        ClusterBuster.set_lose_condition(game)
        ClusterBuster.game_ready(game)
        game.transit_state_machine('fsm1', 'draw_words_stage', 'Game ready')

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
        # Draw Words Trigger
        trigger = game.add_trigger('draw_words')
        condition_group = trigger.condition_group
        condition_group.set_to_and_op()
        condition_group.add_fsm_state_condition('fsm0', 'game_play_state')
        condition_group.add_fsm_state_condition('fsm1', 'draw_words_stage_state')
        # Rounds Trigger
        trigger = game.add_trigger('start_first_round')
        condition_group = trigger.condition_group
        condition_group.add_fsm_state_condition('fsm1', 'rounds_stage_state')
        # Assign Team Leader Trigger
        trigger = game.add_trigger('assign_team_leader')
        trigger.repeats = True
        condition_group = trigger.condition_group
        condition_group.add_fsm_state_condition('fsm3', 'select_leader_stage_state')
        # Assign Team Leader Trigger
        trigger = game.add_trigger('leaders_draw_code_numbers')
        trigger.repeats = True
        condition_group = trigger.condition_group
        condition_group.add_fsm_state_condition('fsm3', 'draw_code_card_stage_state')
        # Game Ready Transition
        game.transit_state_machine('fsm0', 'game_play', 'game ready')

    @staticmethod
    def team_won(game: Game):
        """
        :param game:
        :return:
        """
        game.transit_state_machine('fsm0', 'game_play', 'Team won')

    @staticmethod
    def team_lost(game: Game):
        """
        :param game:
        :return:
        """
        game.transit_state_machine('fsm0', 'game_over', 'Team lost')

    @staticmethod
    def last_round_over(game: Game):
        """
        :param game:
        :return:
        """
        game.transit_state_machine('fsm0', 'game_over', 'Last round over')

    @staticmethod
    def draw_words(game: Game):
        if not bool(game.get_parameter_value('word_cards_drawn')):
            teams_set = game.teams
            team_count = teams_set.count()
            total_words = ClusterBuster.SECRET_WORDS_PER_TEAM * team_count
            # Get Random Words
            random_word_set = Word.objects.order_by('?')
            random_words = random_word_set.all()[:total_words]
            for team_i, team in enumerate(teams_set.all()):
                start_word_i = ClusterBuster.SECRET_WORDS_PER_TEAM * team_i
                end_word_i = start_word_i + ClusterBuster.SECRET_WORDS_PER_TEAM
                for word_i, random_word in enumerate(random_words[start_word_i:end_word_i]):
                    game.set_parameter_value(('team', team, 'secret_word', word_i + 1), str(random_word))
            game.set_parameter_value('word_cards_drawn', True)
        game.transit_state_machine('fsm1', 'rounds_stage', 'Secret words drawn')

    @staticmethod
    def start_first_round(game: Game):
        game.set_parameter_value('current_round_number', ClusterBuster.FIRST_ROUND_NUMBER)
        game.set_parameter_value('last_round_number', ClusterBuster.LAST_ROUND_NUMBER)
        game.transit_state_machine('fsm2', 'first_round', 'Starting first round')
        game.transit_state_machine('fsm3', 'select_leader_stage', 'Starting first round')

    @staticmethod
    def assign_team_leader(game: Game):
        round_number = game.get_parameter_value('current_round_number')
        for team in game.teams.all():
            player_count = team.players.count()
            offset = (round_number - 1) % player_count
            round_leader = team.players.all()[offset]
            game.set_parameter_value(('round', round_number, 'team', team, 'leader'), round_leader)
        game.transit_state_machine('fsm3', 'draw_code_card_stage', 'Team leaders assigned')

    @staticmethod
    def leaders_draw_code_numbers(game: Game):
        round_number = game.get_parameter_value('current_round_number')
        for team in game.teams.all():
            deck = PatternDeckBuilder.build_deck()
            # drawn_cards = self.get_drawn_cards()
            # deck.reduce(drawn_cards)
            deck.shuffle()
            card = deck.draw()
            print(card, card.value)
            for card_i, value in enumerate(card.value):
                game.set_parameter_value(('round', round_number, 'team', team, 'code', card_i + 1), value)
        # Team Leader Made Hints Trigger
        trigger = game.add_trigger('leaders_made_hints')
        condition_group = trigger.condition_group
        condition_group.set_to_and_op()
        for team in game.teams.all():
            for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
                condition_group.add_has_value_condition(
                    ('round', round_number, 'team', team, 'hint', card_i + 1),
                )
        game.transit_state_machine('fsm3', 'leaders_make_hints_stage', 'Code numbers drawn')

    @staticmethod
    def leaders_made_hints(game: Game):
        game.transit_state_machine('fsm3', 'teams_guess_codes_stage', 'Leaders made hints')
        round_number = game.get_parameter_value('current_round_number')
        fsm2 = game.get_parameter_value('fsm2')  # type: StateMachine
        is_first_round = fsm2.current_state.slug == 'first_round'
        # Team Players Made Guesses Trigger
        trigger = game.add_trigger('teams_made_guesses')
        condition_group = trigger.condition_group
        condition_group.set_to_and_op()
        for guessing_team in game.teams.all():
            for hinting_team in game.teams.all():
                if guessing_team != hinting_team and is_first_round:
                    continue
                for card_i in range(ClusterBuster.CODE_CARD_SLOTS):
                    condition_group.add_has_value_condition(
                        ('round', round_number, 'guessing_team', guessing_team, 'hinting_team', hinting_team, 'guess',
                         card_i + 1),
                    )

    @staticmethod
    def teams_made_guesses(game: Game):
        game.transit_state_machine('fsm3', 'teams_share_guesses_stage', 'Players made guesses')

    @staticmethod
    def teams_shared_guesses(game: Game):
        game.transit_state_machine('fsm3', 'score_teams_stage', 'Teams shared guesses')

    @staticmethod
    def start_next_round(game: Game):
        fsm3 = game.get_parameter_value('fsm3')  # type: StateMachine
        fsm3_state = fsm3.current_state.slug
        if fsm3_state != 'score_teams_stage':
            return
        fsm2 = game.get_parameter_value('fsm2')  # type: StateMachine
        fsm2_state = fsm2.current_state.slug
        if fsm2_state == 'last_round':
            ClusterBuster.last_round_over(game)
            return
        round_number = game.get_parameter_value('current_round_number')
        round_number += 1
        game.set_parameter_value('current_round_number', round_number)
        if round_number == ClusterBuster.LAST_ROUND_NUMBER:
            game.transit_state_machine('fsm2', 'last_round', 'round == last round')
        elif fsm2_state == 'first_round' and round_number > ClusterBuster.FIRST_ROUND_NUMBER:
            game.transit_state_machine('fsm2', 'middle_rounds', 'first round < round < last round')
        game.transit_state_machine('fsm3', 'select_leader_stage', 'Starting next round')

    @staticmethod
    def method_map(rule):
        return {
            'start_game': ClusterBuster.start_game,
            'win_tokens': ClusterBuster.assign_team_win_tokens,
            'lose_tokens': ClusterBuster.assign_team_lose_tokens,
            'win_condition': ClusterBuster.set_win_condition,
            'lose_condition': ClusterBuster.set_lose_condition,
            'draw_words': ClusterBuster.draw_words,
            'start_first_round': ClusterBuster.start_first_round,
            'assign_team_leader': ClusterBuster.assign_team_leader,
            'leaders_draw_code_numbers': ClusterBuster.leaders_draw_code_numbers,
            'leaders_made_hints': ClusterBuster.leaders_made_hints,
            'teams_made_guesses': ClusterBuster.teams_made_guesses,
            'teams_shared_guesses': ClusterBuster.teams_shared_guesses,
            'start_next_round': ClusterBuster.start_next_round,
        }[rule]
