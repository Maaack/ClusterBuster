from gamedefinitions.interfaces import StateMachineAbstract, GameAbstract, RuleLibrary


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

                current_method = ClusterBuster.method_map(current_rule_slug)
                current_method(game, state_machine)

    @staticmethod
    def start_game(game: GameAbstract, state_machine: StateMachineAbstract):
        """

        :param game:
        :param state_machine:
        :return:
        """
        game.add_parameter(("winnin_tokens_required_to_win",), 2)
        game.add_parameter(("losing_tokens_required_to_lose",), 2)
        for team in game.get_teams().all():
            game.add_parameter(("team_winning_tokens", None, None, team), 0)
            game.add_parameter(("team_losing_tokens", None, None, team), 0)

    @staticmethod
    def method_map(rule):
        return {
            'start_game': ClusterBuster.start_game
        }[rule]

