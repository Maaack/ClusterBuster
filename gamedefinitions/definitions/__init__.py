from gamedefinitions.interfaces import StateMachineAbstract, GameAbstract, RuleLibrary
from gamedefinitions.models import State


class ClusterBuster(RuleLibrary):
    @staticmethod
    def evaluate(game: GameAbstract):
        for state_machine in game.get_state_machines().all():
            prefix = "cluster_buster_"
            prefix_length = len(prefix)
            current_rules = state_machine.get_rules()

            for current_rule in current_rules.all():
                current_rule_slug = current_rule.slug
                if current_rule_slug.startswith(prefix):
                    current_rule_slug = current_rule_slug[prefix_length:]
                try:
                    current_method = ClusterBuster.method_map(current_rule_slug)
                    current_method(game, state_machine)
                except KeyError:
                    print("%s didn't exist" % (current_rule_slug,))

    @staticmethod
    def start_game(game: GameAbstract, state_machine: StateMachineAbstract):
        """
        :param game:
        :param state_machine:
        :return:
        """
        game.add_parameter({'key': "winning_tokens_required_to_win"}, 2)
        game.add_parameter({'key': "losing_tokens_required_to_lose"}, 2)
        game.add_state_machine('draw_words_stage')
        state = State.objects.get(label='game_play')
        state_machine.transit(state, 'game is ready')

    @staticmethod
    def win_tokens(game: GameAbstract, state_machine: StateMachineAbstract):
        for team in game.get_teams().all():
            game.add_parameter({'key': "team_winning_tokens", 'team': team}, 0)

    @staticmethod
    def lose_tokens(game: GameAbstract, state_machine: StateMachineAbstract):
        for team in game.get_teams().all():
            game.add_parameter({'key': "team_losing_tokens", 'team': team}, 0)

    @staticmethod
    def win_condition(game: GameAbstract, state_machine: StateMachineAbstract):
        print('Win Condition')

    @staticmethod
    def lose_condition(game: GameAbstract, state_machine: StateMachineAbstract):
        print('Lose Condition')

    @staticmethod
    def draw_cards(game: GameAbstract, state_machine: StateMachineAbstract):
        pass

    @staticmethod
    def method_map(rule):
        return {
            'start_game': ClusterBuster.start_game,
            'win_tokens': ClusterBuster.win_tokens,
            'lose_tokens': ClusterBuster.lose_tokens,
            'win_condition': ClusterBuster.win_condition,
            'lose_condition': ClusterBuster.lose_condition,

        }[rule]

