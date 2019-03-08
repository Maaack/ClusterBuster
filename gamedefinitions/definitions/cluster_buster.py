from gamedefinitions.models import StateMachineInterface, GameInterface, RuleLibrary


class ClusterBuster(RuleLibrary):
    @staticmethod
    def evaluate(state_machine: StateMachineInterface, game: GameInterface):
        prefix = "cluster_buster_"
        prefix_length = len(prefix)
        current_rules = state_machine.get_current_rules()

        for current_rule in current_rules:
            if current_rule.startswith(prefix):
                current_rule = current_rule[prefix_length:]

            current_method = ClusterBuster.method_map(current_rule)
            current_method(state_machine, game)


    @staticmethod
    def start_game(state_machine: StateMachineInterface, game: GameInterface):
        pass

    @staticmethod
    def method_map(rule):
        return {
            'start_game': ClusterBuster.start_game
        }[rule]

