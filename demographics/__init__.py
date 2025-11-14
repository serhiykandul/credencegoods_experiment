from otree.api import *


doc = """
A post-experimental questionnaire to collect demographics information from the participants.
"""


class C(BaseConstants):
    NAME_IN_URL = "demographics"
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    age = models.IntegerField(label="Quel âge avez-vous ?", min=18, max=99)
    gender = models.StringField(
        label="Quel est votre sexe ?",
        choices=[
            ["f", "Femme"],
            ["m", "Homme"],
            ["na", "Préfère ne pas répondre"],
        ],
        widget=widgets.RadioSelect,
    )
    field_of_study = models.StringField(label="Quel est votre domaine d'études ?")


class Demographics(Page):
    form_model = "player"
    form_fields = ["age", "gender", "field_of_study"]


class ThankYou(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict()


page_sequence = [Demographics, ThankYou]
