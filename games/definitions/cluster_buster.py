from games.models import StateMachine, GameLibrary, Game, Parameter


class ClusterBuster(GameLibrary):
    @staticmethod
    def evaluate(state_machine: StateMachine, game: Game):
        prefix = "cluster_buster_"
        prefix_length = len(prefix)
        current_rules = state_machine.current_state.rules

        for current_rule in current_rules:
            if current_rule.startswith(prefix):
                current_rule = current_rule[prefix_length:]

            current_method = ClusterBuster.method_map(current_rule)
            current_method(state_machine, game)


    @staticmethod
    def start_game(state_machine: StateMachine, game: Game):
        pass

    @staticmethod
    def method_map(rule):
        return {
            'start_game': ClusterBuster.start_game
        }[rule]

