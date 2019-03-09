from gamedefinitions.interfaces import StateMachineAbstract, GameAbstract, RuleLibrary


class ClusterBuster(RuleLibrary):
    @staticmethod
    def evaluate(state_machine: StateMachineAbstract, game: GameAbstract):
        prefix = "cluster_buster_"
        prefix_length = len(prefix)
        current_rules = state_machine.get_rules()

        for current_rule in current_rules:
            if current_rule.startswith(prefix):
                current_rule = current_rule[prefix_length:]

            current_method = ClusterBuster.method_map(current_rule)
            current_method(state_machine, game)

    @staticmethod
    def start_game(state_machine: StateMachineAbstract, game: GameAbstract):
        """

        :param state_machine:
        :param game:
        :return:
        """
        game.add_parameter(("winnin_tokens_required_to_win",), 2)
        game.add_parameter(("losing_tokens_required_to_lose",), 2)
        for team in game.teams.all():
            game.add_parameter(("team_winning_tokens"))

    @staticmethod
    def method_map(rule):
        return {
            'start_game': ClusterBuster.start_game
        }[rule]

