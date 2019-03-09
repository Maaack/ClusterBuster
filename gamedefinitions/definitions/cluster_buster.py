from gamedefinitions.interfaces import StateMachineInterface, GameInterface, RuleLibrary


class ClusterBuster(RuleLibrary):
    @staticmethod
    def evaluate(state_machine: StateMachineInterface, game: GameInterface):
        prefix = "cluster_buster_"
        prefix_length = len(prefix)
        current_rules = state_machine.get_rules()

        for current_rule in current_rules:
            if current_rule.startswith(prefix):
                current_rule = current_rule[prefix_length:]

            current_method = ClusterBuster.method_map(current_rule)
            current_method(state_machine, game)

    @staticmethod
    def start_game(state_machine: StateMachineInterface, game: GameInterface):
        """

        :param state_machine:
        :param game:
        :return:
        """
        game.add_parameter(("tokens_required_to_win",), 2)
        game.add_parameter(("tokens_required_to_lose",), 2)

    @staticmethod
    def method_map(rule):
        return {
            'start_game': ClusterBuster.start_game
        }[rule]

