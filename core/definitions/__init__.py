from django.db import models

from gamedefinitions.interfaces import (StateMachineAbstract, GameAbstract,
                                        ConditionAbstractBase, ConditionalTransitionAbstract,
                                        ComparisonConditionAbstract,
                                        RuleLibrary)
from rooms.models import Player, Team
from core.models import Word


class ClusterBuster(RuleLibrary):
    SECRET_WORDS_PER_TEAM = 4

    @staticmethod
    def evaluate(game: GameAbstract):
        for state_machine in game.get_state_machines().all():  # type: StateMachineAbstract
            print("state_machine %s()" % (state_machine.current_state.label,))
            prefix = "cluster_buster_"
            prefix_length = len(prefix)
            current_rules = state_machine.get_rules()

            for current_rule in current_rules.all():
                current_rule_slug = current_rule.slug
                print("evaluating rule %s()" % (current_rule_slug,))
                if current_rule_slug.startswith(prefix):
                    current_rule_slug = current_rule_slug[prefix_length:]
                try:
                    current_method = ClusterBuster.method_map(current_rule_slug)
                    print("calling %s()" % (current_rule_slug,))
                    current_method(game, state_machine)
                except KeyError:
                    print("%s didn't exist" % (current_rule_slug,))
            state_machine.evaluate_conditions()

    @staticmethod
    def start_game(game: GameAbstract, state_machine: StateMachineAbstract):
        """
        :param game:
        :param state_machine:
        :return:
        """
        game.set_parameter_value(('winning_tokens_required_to_win',), 2)
        game.set_parameter_value(('losing_tokens_required_to_lose',), 2)
        game.set_parameter_value(('teams_start_tokens',), 0)
        game.add_state_machine('draw_words_stage')
        conditional_transition = state_machine.add_conditional_transition('game_is_ready', 'game_play')
        conditional_transition.set_to_and_op()
        for team in game.get_teams().all():  # type: Team
            conditional_transition.add_comparison_condition(
                ('teams_start_tokens',),
                ('team_losing_tokens', team),
                ComparisonConditionAbstract.EQUAL
            )
            conditional_transition.add_comparison_condition(
                ('teams_start_tokens',),
                ('team_winning_tokens', team),
                ComparisonConditionAbstract.EQUAL
            )

    @staticmethod
    def win_tokens(game: GameAbstract, state_machine: StateMachineAbstract):
        for team in game.get_teams().all():  # type: Team
            game.set_parameter_value(('team_winning_tokens', team), 0)

    @staticmethod
    def lose_tokens(game: GameAbstract, state_machine: StateMachineAbstract):
        for team in game.get_teams().all():  # type: Team
            game.set_parameter_value(('team_losing_tokens', team), 0)

    @staticmethod
    def win_condition(game: GameAbstract, state_machine: StateMachineAbstract):
        conditional_transition = state_machine.add_conditional_transition('team_won', 'game_over')
        for team in game.get_teams().all():  # type: Team
            conditional_transition.add_comparison_condition(
                ('team_winning_tokens', team),
                ('winning_tokens_required_to_win',),
                ComparisonConditionAbstract.GREATER_THAN_OR_EQUAL
            )

    @staticmethod
    def lose_condition(game: GameAbstract, state_machine: StateMachineAbstract):
        conditional_transition = state_machine.add_conditional_transition('team_lost', 'game_over')
        for team in game.get_teams().all():
            conditional_transition.add_comparison_condition(
                ('team_losing_tokens', team),
                ('losing_tokens_required_to_lose',),
                ComparisonConditionAbstract.GREATER_THAN_OR_EQUAL
            )

    @staticmethod
    def secret_words_drawn(game: GameAbstract, state_machine: StateMachineAbstract):
        conditional_transition = state_machine.add_conditional_transition('secret_words_drawn', 'rounds_stage')
        conditional_transition.set_to_and_op()
        for team in game.get_teams().all():
            for i in range(ClusterBuster.SECRET_WORDS_PER_TEAM):
                conditional_transition.add_has_value_condition(
                    ('secret_word', team, i+1),
                )

    @staticmethod
    def draw_words(game: GameAbstract, state_machine: StateMachineAbstract):
        teams_set = game.get_teams()
        team_count = teams_set.count()
        total_words = ClusterBuster.SECRET_WORDS_PER_TEAM * team_count

        random_word_set = Word.objects.order_by('?')
        random_words = random_word_set.all()[:total_words]

        if not bool(game.get_parameter_value('word_cards_drawn')):
            for team_i, team in enumerate(teams_set.all()):
                start_word_i = ClusterBuster.SECRET_WORDS_PER_TEAM * team_i
                end_word_i = start_word_i + ClusterBuster.SECRET_WORDS_PER_TEAM
                for word_i, random_word in enumerate(random_words[start_word_i:end_word_i]):
                    game.set_parameter_value(('secret_word', team, word_i+1), str(random_word))
            game.set_parameter_value('word_cards_drawn', True)

    @staticmethod
    def method_map(rule):
        return {
            'start_game': ClusterBuster.start_game,
            'win_tokens': ClusterBuster.win_tokens,
            'lose_tokens': ClusterBuster.lose_tokens,
            'win_condition': ClusterBuster.win_condition,
            'lose_condition': ClusterBuster.lose_condition,
            'draw_words': ClusterBuster.draw_words,
            'secret_words_drawn': ClusterBuster.secret_words_drawn,
        }[rule]
