from django.db import models

from gamedefinitions.interfaces import (StateMachineAbstract, GameAbstract,
                                        ConditionAbstractBase, ConditionalTransitionAbstract,
                                        ComparisonConditionAbstract,
                                        RuleLibrary)
from rooms.models import Player, Team
from core.models import Word


class ClusterBuster(RuleLibrary):
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
        game.add_parameter({'key': "winning_tokens_required_to_win"}, 2)
        game.add_parameter({'key': "losing_tokens_required_to_lose"}, 2)
        game.add_parameter({'key': "teams_start_tokens"}, 0)
        game.add_state_machine('draw_words_stage')
        conditional_transition = state_machine.add_conditional_transition('game_is_ready', 'game_play')
        conditional_transition.set_to_and_op()
        for team in game.get_teams().all():  # type: Team
            conditional_transition.add_comparison_condition(
                {'key': "teams_start_tokens"},
                {'key': "team_losing_tokens", 'team': team},
                ComparisonConditionAbstract.EQUAL
            )
            conditional_transition.add_comparison_condition(
                {'key': "teams_start_tokens"},
                {'key': "team_winning_tokens", 'team': team},
                ComparisonConditionAbstract.EQUAL
            )

    @staticmethod
    def win_tokens(game: GameAbstract, state_machine: StateMachineAbstract):
        for team in game.get_teams().all():  # type: Team
            game.add_parameter({'key': "team_winning_tokens", 'team': team}, 0)

    @staticmethod
    def lose_tokens(game: GameAbstract, state_machine: StateMachineAbstract):
        for team in game.get_teams().all():  # type: Team
            game.add_parameter({'key': "team_losing_tokens", 'team': team}, 0)

    @staticmethod
    def win_condition(game: GameAbstract, state_machine: StateMachineAbstract):
        conditional_transition = state_machine.add_conditional_transition('team_won', 'game_over')
        for team in game.get_teams().all():  # type: Team
            conditional_transition.add_comparison_condition(
                {'key': "team_winning_tokens", 'team': team},
                {'key': "winning_tokens_required_to_win"},
                ComparisonConditionAbstract.GREATER_THAN_OR_EQUAL
            )

    @staticmethod
    def lose_condition(game: GameAbstract, state_machine: StateMachineAbstract):
        conditional_transition = state_machine.add_conditional_transition('team_lost', 'game_over')
        for team in game.get_teams().all():
            conditional_transition.add_comparison_condition(
                {'key': "team_losing_tokens", 'team': team},
                {'key': "losing_tokens_required_to_lose"},
                ComparisonConditionAbstract.GREATER_THAN_OR_EQUAL
            )

    @staticmethod
    def draw_words(game: GameAbstract, state_machine: StateMachineAbstract):
        words_per_team = 4
        teams_set = game.get_teams()
        team_count = teams_set.count()
        total_words = words_per_team * team_count

        random_word_set = Word.objects.order_by('?')
        random_words = random_word_set.all()[:total_words]

        parameter = game.get_parameter(key="word_cards_drawn")
        if not bool(parameter.value):
            parameter.value.set(False)
            for team_i, team in enumerate(teams_set.all()):
                start_word_i = words_per_team * team_i
                end_word_i = start_word_i + words_per_team
                for word_i, random_word in enumerate(random_words[start_word_i:end_word_i]):
                    word_parameter = game.get_parameter(key="secret_word", counter=word_i+1, team=team)
                    word_parameter.value.set(str(random_word))
            parameter.value.set(True)

    @staticmethod
    def method_map(rule):
        return {
            'start_game': ClusterBuster.start_game,
            'win_tokens': ClusterBuster.win_tokens,
            'lose_tokens': ClusterBuster.lose_tokens,
            'win_condition': ClusterBuster.win_condition,
            'lose_condition': ClusterBuster.lose_condition,
            'draw_words': ClusterBuster.draw_words,

        }[rule]
