
from .generic import AbstractService, AbstractServiceRequest, AbstractServiceResponse
from core.models import Round, PartyRound, PlayerGuess
from core.interfaces import PartyRoundInterface


class TeamGuessServiceRequest(AbstractServiceRequest):
    def __set_default(self):
        self.team_round = None


class TeamGuessServiceResponse(AbstractServiceResponse):
    def __set_default(self):
        self.team_guess = None
        self.is_team_guess_ready = False
        self.missing_guesses = []
        self.conflicting_guesses = []


class TeamGuessService(AbstractService):

    """
    Tries to create a Team Guess out of Player Guesses
    """
    @staticmethod
    def run(request: TeamGuessServiceRequest) -> TeamGuessServiceResponse:
        """
        Requires Round instance in Request and returns Response with Team Guess or None

        :param request: TeamGuessServiceRequest
        :return: TeamGuessServiceResponse
        """
        if not isinstance(request, TeamGuessServiceRequest):
            raise ValueError('`request` object is not instance of TeamGuessServiceRequest.')
        if not isinstance(request.team_round, PartyRound):
            raise ValueError('`round` is not instance of TeamRound.')
        response = TeamGuessServiceResponse()

        team_round = request.team_round  # type: PartyRound
        expected_guess_count = TeamGuessService.__get_expected_guess_count(team_round)
        valid_guess_count = TeamGuessService.__get_valid_guesses(team_round)

        if expected_guess_count > valid_guess_count:
            return response


        # TODO: Check for conflicting answers per target_word


        return TeamGuessServiceResponse()

    @staticmethod
    def __get_expected_guess_count(team_round: PartyRound):
        target_words_count = team_round.target_words.count()
        guesser_count = PartyRoundInterface(team_round).get_guessing_players().count()
        return guesser_count * target_words_count

    @staticmethod
    def __get_valid_guess_count(team_round: PartyRound):
        return TeamGuessService.__get_valid_guesses(team_round).count()

    @staticmethod
    def __get_valid_guesses(team_round: PartyRound):
        return PlayerGuess.objects.filter(
            target_word__team_round=team_round
        ).exclude(
            guess=None
        )

    @staticmethod
    def __get_target_words_missing_guesses(team_round: PartyRound):
        return PlayerGuess.objects.filter(
            target_word__team_round=team_round
        ).exclude(
            guess=None
        )
