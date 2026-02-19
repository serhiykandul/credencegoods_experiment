from otree.api import *
import random


doc = """
Credence Goods Experiment - Verifiability treatment:
Player A chooses one price pair once; price paid is then fixed (auto-applied by type).
"""


class C(BaseConstants):
    NAME_IN_URL = "credencegoodsBJS_verifiability"
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 16
    MARKET_SIZE = 8

    # Payoff parameters
    OUTSIDE_OPTION = 1
    REVENUE_1 = 10
    REVENUE_2 = 16
    ACTION_2_COST = 6
    ACTION_1_COST = 1

    # Price vectors (chosen by A)
    MIN_PRICE = 2
    MAX_PRICE = 9
    PRICE_VECTORS = [
        (2, 3),
        (2, 7),
        (4, 7),
    ]


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Role and identification
    player_role = models.StringField()
    player_id_in_role = models.StringField()
    matching_group_id = models.IntegerField()

    # Price choice (only once by A)
    price_choice = models.StringField(
        choices=[
            ("2-3", "Prix 1 : 2 points, Prix 2 : 3 points"),
            ("2-7", "Prix 1 : 2 points, Prix 2 : 7 points"),
            ("4-7", "Prix 1 : 4 points, Prix 2 : 7 points"),
        ],
        widget=widgets.RadioSelect,
        label="Sélectionnez la paire de prix à proposer",
    )
    price1_offer = models.IntegerField()
    price2_offer = models.IntegerField()
    price_paid = models.IntegerField(blank=True)

    # Decisions
    action_chosen = models.IntegerField(choices=[[1, "Action 1"], [2, "Action 2"]], blank=True)
    interaction = models.BooleanField(choices=[[True, "Oui"], [False, "Non"]])

    # Control quiz
    cq_q1 = models.StringField(
        label="Question 1. Qu'est-ce qui est vrai concernant l'interaction entre les joueurs ?",
        choices=[
            ["A", "Vous interagissez toujours avec la même personne"],
            ["B", "Vous allez interagir avec une autre personne à chaque tour"],
            ["C", "Vous verrez l’identifiant unique de la personne avec qui vous allez interagir"],
        ],
    )
    cq_q2 = models.StringField(
        label="Question 2. Quelle est l’ordre correct des d´ecisions pendant un tour ?",
        choices=[
            [
                "A",
                "1) Le Joueur A propose deux prix, 2) Le Joueur B décide s'il interagit ou non, et 2) Le Joueur A choisit une Action",
            ],
            [
                "B",
                "1) Le Joueur B décide s'il interagit ou non, 2) Le Joueur A propose deux prix, 3) Le Joueur A choisit une Action",
            ],
            [
                "C",
                "1) Le Joueur A décide s'il interagit ou non, 2) Le Joueur A propose deux prix, 2) Le Joueur B choisit une Action",
            ],
        ],
    )
    cq_q3 = models.StringField(
        label="Question 3.Quelle est la bonne réponse concernant les types du Joueur B ?",
        choices=[
            ["A", "Le Joueur B est toujours de Type 1"],
            ["B", "Le Joueur B est toujours de Type 2"],
            ["C", "Le type du Joueur B, Type 1 ou Type 2, est attribué aléatoirement à chaque tour"],
        ],
    )
    cq_q4 = models.StringField(
        label="Question 4. Qu’est-ce qui est FAUX à propos du gain des joueurs",
        choices=[
            ["A", "Les deux joueurs reçoivent toujours le même nombre de points"],
            ["B", "Les deux joueurs reçoivent le même gain, c'est-à-dire 1 point, dans le cas où le Joueur B décide de ne pas interagir"],
            ["C", "Le gain du Joueur A dépend du type du Joueur B et des actions du Joueur A"],
            ["D", "Le gain du Joueur B dépend du prix payé par le Joueur A"],
        ],
    )

    # Game state
    player_b_type = models.IntegerField()
    revenue = models.IntegerField()
    round_payoff = models.CurrencyField()

    # Totals
    total_payoff_points = models.FloatField(initial=0)
    total_payoff_euros = models.FloatField(initial=0)
    participation_fee = models.FloatField(initial=0)
    total_payment = models.FloatField(initial=0)

    # For feedback
    partner_price1 = models.IntegerField()
    partner_price2 = models.IntegerField()
    partner_interaction = models.BooleanField()
    partner_action = models.IntegerField()
    partner_price_paid = models.IntegerField()

    def set_partner(self):
        return [p for p in self.group.get_players() if p != self][0]

    def calculate_payoff(self):
        partner = self.set_partner()
        role = self.player_role
        if role == "A":
            if not partner.interaction:
                self.round_payoff = C.OUTSIDE_OPTION
                self.revenue = 0
                self.payoff = cu(self.round_payoff)
                return
            partner_type = partner.field_maybe_none("player_b_type")
            if partner_type is None:
                raise RuntimeError(
                    f"Player B type missing for player {self.id_in_subsession} in round {self.round_number}."
                )
            action_chosen = self.field_maybe_none("action_chosen")
            if action_chosen is None:
                raise RuntimeError(
                    f"Action choice missing for player {self.id_in_subsession} in round {self.round_number}."
                )
            if partner_type == 1:
                revenue = C.REVENUE_1 if action_chosen == 1 else C.REVENUE_2
            else:
                revenue = C.REVENUE_2
            cost = C.ACTION_1_COST if action_chosen == 1 else C.ACTION_2_COST
            price_paid = self.field_maybe_none("price_paid")
            if price_paid is None:
                raise RuntimeError(
                    f"Price paid missing for player {self.id_in_subsession} in round {self.round_number}."
                )
            self.revenue = revenue
            self.round_payoff = revenue - cost - price_paid
            self.payoff = cu(self.round_payoff)
        else:
            interaction_val = self.field_maybe_none("interaction")
            if interaction_val is None:
                raise RuntimeError(
                    f"Interaction decision missing for player {self.id_in_subsession} in round {self.round_number}."
                )
            if not interaction_val:
                self.round_payoff = C.OUTSIDE_OPTION
                self.payoff = cu(self.round_payoff)
                return
            partner_price_paid = partner.field_maybe_none("price_paid")
            if partner_price_paid is None:
                raise RuntimeError(
                    f"Partner price paid missing for player {self.id_in_subsession} in round {self.round_number}."
                )
            self.round_payoff = partner_price_paid
            self.payoff = cu(self.round_payoff)


def creating_session(subsession: Subsession):
    players = sorted(subsession.get_players(), key=lambda p: p.id_in_subsession)
    market_size = C.MARKET_SIZE
    total_players = len(players)
    if total_players % market_size != 0:
        raise RuntimeError(f"Session size {total_players} is not divisible by market size {market_size}.")
    session = subsession.session
    if subsession.round_number == 1:
        markets = {}
        half_market = market_size // 2
        for idx, player in enumerate(players):
            market_id = idx // market_size + 1
            position = idx % market_size
            role = "A" if position < half_market else "B"
            label_idx = position % half_market + 1
            label = f"{role}{label_idx}"
            player.matching_group_id = market_id
            player.player_role = role
            player.player_id_in_role = label
            player.participant.vars["matching_group_id"] = market_id
            player.participant.vars["player_role"] = role
            player.participant.vars["player_id_in_role"] = label
            markets.setdefault(market_id, []).append(player)
        round_matrices = {}
        for round_no in range(1, C.NUM_ROUNDS + 1):
            round_pairs = []
            for market_id, market_players in markets.items():
                buyers = [p.id_in_subsession for p in market_players if p.player_role == "A"]
                sellers = [p.id_in_subsession for p in market_players if p.player_role == "B"]
                rng = random.Random(f"{session.code}-{market_id}-{round_no}")
                rng.shuffle(buyers)
                rng.shuffle(sellers)
                for buyer_id, seller_id in zip(buyers, sellers):
                    round_pairs.append([buyer_id, seller_id])
            round_matrices[round_no] = round_pairs
        session.vars["round_matrices"] = round_matrices
    round_matrices = session.vars.get("round_matrices")
    for player in players:
        player.matching_group_id = player.participant.vars["matching_group_id"]
        player.player_role = player.participant.vars["player_role"]
        player.player_id_in_role = player.participant.vars["player_id_in_role"]
    subsession.set_group_matrix(round_matrices[subsession.round_number])


class Welcome(Page):
    template_name = "credencegoodsBJS_verifiability/Welcome.html"
    @staticmethod
    def is_displayed(player): return player.round_number == 1


class ControlQuiz(Page):
    template_name = "credencegoodsBJS_verifiability/ControlQuiz.html"
    form_model = "player"
    form_fields = ["cq_q1", "cq_q2", "cq_q3", "cq_q4"]
    @staticmethod
    def is_displayed(player): return player.round_number == 1
    @staticmethod
    def error_message(player, values):
        errors = {}
        if values["cq_q1"] != "B": errors["cq_q1"] = "Incorrect."
        if values["cq_q2"] != "A": errors["cq_q2"] = "Incorrect."
        if values["cq_q3"] != "C": errors["cq_q3"] = "Incorrect."
        if values["cq_q4"] != "A": errors["cq_q4"] = "Incorrect."
        if errors: return errors


class WaitForAllPlayers(WaitPage):
    template_name = "credencegoodsBJS_verifiability/WaitForAllPlayers.html"
    wait_for_all_groups = True
    @staticmethod
    def is_displayed(player): return player.round_number == 1


class RoleAssignment(Page):
    template_name = "credencegoodsBJS_verifiability/RoleAssignment.html"
    @staticmethod
    def is_displayed(player): return player.round_number == 1
    @staticmethod
    def vars_for_template(player): return dict(player_role=player.player_role)


class PriceOffer(Page):
    template_name = "credencegoodsBJS_verifiability/PriceOffer.html"
    form_model = "player"
    form_fields = ["price_choice"]
    @staticmethod
    def is_displayed(player): return player.player_role == "A"
    @staticmethod
    def before_next_page(player, timeout_happened):
        mapping = {"2-3": (2, 3), "2-7": (2, 7), "4-7": (4, 7)}
        # If admin auto-advances without a selection, default to first pair to avoid crashes
        if not player.price_choice:
            player.price_choice = "2-3"
        if player.price_choice not in mapping:
            raise RuntimeError("Paire de prix inconnue.")
        p1, p2 = mapping[player.price_choice]
        player.price1_offer = p1
        player.price2_offer = p2
        partner = player.set_partner()
        partner.partner_price1 = p1
        partner.partner_price2 = p2


class WaitForPrices(WaitPage):
    template_name = "credencegoodsBJS_verifiability/WaitForPrices.html"
    wait_for_all_groups = False


class InteractionDecision(Page):
    template_name = "credencegoodsBJS_verifiability/InteractionDecision.html"
    form_model = "player"
    form_fields = ["interaction"]
    @staticmethod
    def is_displayed(player): return player.player_role == "B"
    @staticmethod
    def vars_for_template(player):
        partner = player.set_partner()
        return dict(price1=partner.price1_offer, price2=partner.price2_offer)
    @staticmethod
    def before_next_page(player, timeout_happened):
        partner = player.set_partner()
        partner.partner_interaction = player.interaction


class WaitForInteraction(WaitPage):
    template_name = "credencegoodsBJS_verifiability/WaitForInteraction.html"
    wait_for_all_groups = False
    @staticmethod
    def after_all_players_arrive(group: Group, **kwargs):
        players = group.get_players()
        player_a = next(p for p in players if p.player_role == "A")
        player_b = next(p for p in players if p.player_role == "B")
        interaction = player_b.interaction
        if interaction:
            player_b.player_b_type = random.randint(1, 2)
            player_a.player_b_type = player_b.player_b_type
            price_to_pay = player_a.price1_offer if player_b.player_b_type == 1 else player_a.price2_offer
            player_a.price_paid = price_to_pay
            player_b.partner_price_paid = price_to_pay
        else:
            player_b.player_b_type = 0
            player_a.player_b_type = 0
            player_a.price_paid = None
            player_b.partner_price_paid = None


class WaitForAction(WaitPage):
    template_name = "credencegoodsBJS_verifiability/WaitForAction.html"
    wait_for_all_groups = False


class ActionChoice(Page):
    template_name = "credencegoodsBJS_verifiability/ActionChoice.html"
    form_model = "player"
    form_fields = ["action_chosen"]
    @staticmethod
    def is_displayed(player):
        if player.player_role != "A":
            return False
        partner = player.set_partner()
        return bool(partner.interaction)
    @staticmethod
    def vars_for_template(player):
        player_b_type = player.player_b_type
        return dict(
            player_b_type=player_b_type,
            price1_offer=player.price1_offer,
            price2_offer=player.price2_offer,
        )
    @staticmethod
    def error_message(player, values):
        if values.get("action_chosen") is None:
            return "Veuillez choisir une action avant de continuer."


class RoundResults(Page):
    template_name = "credencegoodsBJS_verifiability/RoundResults.html"
    @staticmethod
    def vars_for_template(player):
        partner = player.set_partner()
        player.calculate_payoff()
        partner.calculate_payoff()
        role = player.player_role
        interaction = partner.interaction if role == "A" else player.interaction
        # Safe access with explicit guards (mirror Exo behavior)
        action_chosen_val = player.field_maybe_none("action_chosen") if role == "A" else partner.field_maybe_none("action_chosen")
        player_b_type_val = player.field_maybe_none("player_b_type") if role == "A" else partner.field_maybe_none("player_b_type")
        action_cost = None
        if role == "A" and interaction and action_chosen_val is not None:
            action_cost = C.ACTION_2_COST if action_chosen_val == 2 else C.ACTION_1_COST
        price_paid_a = player.field_maybe_none("price_paid")
        price_paid_partner = partner.field_maybe_none("price_paid")
        return dict(
            player_role=role,
            price1_offer=player.price1_offer if role == "A" else partner.price1_offer,
            price2_offer=player.price2_offer if role == "A" else partner.price2_offer,
            interaction=interaction,
            interaction_text="d'interagir" if interaction else "de ne pas interagir",
            price_paid=price_paid_a if role == "A" else price_paid_partner,
            has_price_paid=interaction and ((price_paid_a if role == "A" else price_paid_partner) is not None),
            payoff=player.round_payoff,
            player_b_type=player_b_type_val,
            outside_option=C.OUTSIDE_OPTION,
            revenue=player.revenue if role == "A" else None,
            has_revenue=interaction and role == "A" and player.revenue is not None,
            action_cost=action_cost,
            action_chosen=action_chosen_val if interaction else None,
        )


class WaitForRoundResults(WaitPage):
    template_name = "credencegoodsBJS_verifiability/WaitForRoundResults.html"
    wait_for_all_groups = True
    @staticmethod
    def is_displayed(player): return player.round_number < C.NUM_ROUNDS


class FinalResults(Page):
    template_name = "credencegoodsBJS_verifiability/FinalResults.html"
    @staticmethod
    def is_displayed(player): return player.round_number == C.NUM_ROUNDS
    @staticmethod
    def vars_for_template(player):
        round_payoffs = [pr.round_payoff for pr in player.in_all_rounds()]
        total_payoff = sum(round_payoffs)
        total_euros = total_payoff.to_real_world_currency(player.session)
        participation_fee = player.session.config.get("participation_fee", 0)
        total_payment = total_euros + participation_fee
        player.total_payoff_points = float(total_payoff)
        player.total_payoff_euros = float(total_euros)
        player.participation_fee = float(participation_fee)
        player.total_payment = float(total_payment)
        return dict(
            total_payoff=total_payoff,
            total_euros=total_euros,
            total_euros_rounded=f"{total_euros:.2f}",
            participation_fee=participation_fee,
            participation_fee_rounded=f"{participation_fee:.2f}",
            total_payment=total_payment,
            total_payment_rounded=f"{total_payment:.2f}",
            rounds=player.in_all_rounds(),
        )


page_sequence = [
    Welcome,
    WaitForAllPlayers,
    ControlQuiz,
    RoleAssignment,
    PriceOffer,
    WaitForPrices,
    InteractionDecision,
    WaitForInteraction,
    ActionChoice,
    WaitForAction,
    RoundResults,
    WaitForRoundResults,
    FinalResults,
]

