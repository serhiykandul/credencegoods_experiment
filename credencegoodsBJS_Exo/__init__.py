from otree.api import *
import random


doc = """
Credence Goods Experiment - Exogenous Prices Treatment
Adapted from Dulleck et al. (2011)
"""


class C(BaseConstants):
    NAME_IN_URL = 'credencegoodsBJS_Exo'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 16
    MARKET_SIZE = 8

    OUTSIDE_OPTION = 1
    REVENUE_1 = 10
    REVENUE_2 = 16
    ACTION_2_COST = 6
    ACTION_1_COST = 1

    PRICE_VECTORS = [
        dict(price1=2, price2=3, condition='unfair'),
        dict(price1=5, price2=7, condition='fair'),
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
    condition_price = models.StringField()

    # Exogenous prices (set by the experimenter)
    price1_offer = models.IntegerField()
    price2_offer = models.IntegerField()
    price_paid = models.IntegerField(blank=True)

    # Decision variables
    action_chosen = models.IntegerField(
        choices=[[1, 'Action 1'], [2, 'Action 2']],
        label="Choisissez une action",
        blank=True,
    )
    interaction = models.BooleanField(
        choices=[[True, 'Oui'], [False, 'Non']],
    )

    # Control quiz (updated text will be provided separately)
    cq_q1 = models.StringField(
        label="Question 1. Qu'est-ce qui est vrai concernant l'interaction entre les joueurs ?",
        choices=[
            ['A', 'Vous interagissez toujours avec la même personne'],
            ['B', 'Vous serez réappairé avec une autre personne à chaque tour'],
            ['C', 'Vous verrez l’identifiant unique de la personne avec laquelle vous interagissez'],
        ],
    )
    cq_q2 = models.StringField(label="Question 2. Quelle est la séquence correcte des décisions dans un tour ?",
    choices=[
        ['A', "1) Le Joueur A propose des prix, 2) Le Joueur B décide s'il interagit ou non, 3) Le Joueur A choisit une action, 4) Le Joueur A paye le prix proposé au Joueur B"],
        ['B', "1) Le Joueur B décide s'il interagit ou non, 2) Le Joueur A propose des prix, 3) Le Joueur A choisit une action, 4) Le Joueur B paye le Joueur A pour l'action choisie"],
        ['C', "1) Le Joueur A décide s'il interagit ou non, 2) Le Joueur A propose des prix, 3) Le Joueur B choisit une action, 4) Le Joueur B reçoit un revenu"],
    ])
    cq_q3 = models.StringField(
        label="Question 3. Qu’est-ce qui est vrai concernant les types du Joueur B ?",
        choices=[
            ['A', 'Le Joueur B est toujours de Type 1'],
            ['B', 'Le Joueur B est toujours de Type 2'],
            ['C', 'Le type du Joueur B, Type 1 ou Type 2, est défini aléatoirement à chaque tour'],
        ],
    )
    cq_q4 = models.StringField(
        label="Question 4. Qu’est-ce qui est FAUX concernant les gains des joueurs ?",
        choices=[
            ['A', 'Les deux joueurs reçoivent toujours le même nombre de points'],
            ['B', 'Les deux joueurs reçoivent le même gain, soit 1 point, si le Joueur B décide de ne pas interagir'],
            ['C', 'Le gain du Joueur A dépend du type du Joueur B et des actions du Joueur A'],
            ['D', 'Le gain du Joueur B dépend du prix payé par le Joueur A'],
        ],
    )

    # Game state variables
    player_b_type = models.IntegerField()
    revenue = models.IntegerField()
    round_payoff = models.CurrencyField()

    # Totals for payments
    total_payoff_points = models.FloatField(initial=0)
    total_payoff_euros = models.FloatField(initial=0)
    participation_fee = models.FloatField(initial=0)
    total_payment = models.FloatField(initial=0)

    def set_partner(self):
        partners = [p for p in self.group.get_players() if p.id_in_group != self.id_in_group]
        if len(partners) != 1:
            raise RuntimeError("Group configuration invalid: unable to identify partner.")
        return partners[0]

    def calculate_payoff(self):
        partner = self.set_partner()
        role = self.field_maybe_none('player_role')

        if role is None:
            raise RuntimeError(f"Player {self.id_in_subsession} is missing a role in round {self.round_number}.")

        if role == 'A':
            partner_interaction = partner.field_maybe_none('interaction')
            if partner_interaction is None:
                raise RuntimeError(
                    f"Partner interaction decision missing for player {self.id_in_subsession} in round {self.round_number}."
                )
            if not partner_interaction:
                self.round_payoff = C.OUTSIDE_OPTION
                self.revenue = 0
                self.payoff = cu(self.round_payoff)
                return

            partner_type = partner.field_maybe_none('player_b_type')
            if partner_type is None:
                raise RuntimeError(
                    f"Player B type missing for player {self.id_in_subsession} in round {self.round_number}."
                )
            action_chosen = self.field_maybe_none('action_chosen')
            if action_chosen is None:
                raise RuntimeError(
                    f"Action choice missing for player {self.id_in_subsession} in round {self.round_number}."
                )

            if partner_type == 1:
                revenue = C.REVENUE_1 if action_chosen == 1 else C.REVENUE_2
            else:
                revenue = C.REVENUE_2

            cost = C.ACTION_1_COST if action_chosen == 1 else C.ACTION_2_COST
            price_paid = self.field_maybe_none('price_paid')
            if price_paid is None:
                raise RuntimeError(
                    f"Price paid missing for player {self.id_in_subsession} in round {self.round_number}."
                )

            self.revenue = revenue
            self.round_payoff = revenue - cost - price_paid
            self.payoff = cu(self.round_payoff)
        else:
            interaction = self.field_maybe_none('interaction')
            if interaction is None:
                raise RuntimeError(
                    f"Interaction decision missing for player {self.id_in_subsession} in round {self.round_number}."
                )
            if not interaction:
                self.round_payoff = C.OUTSIDE_OPTION
                self.payoff = cu(self.round_payoff)
                return

            partner_price_paid = partner.field_maybe_none('price_paid')
            if partner_price_paid is None:
                raise RuntimeError(
                    f"Partner price paid missing for player {self.id_in_subsession} in round {self.round_number}."
                )

            self.round_payoff = partner_price_paid
            self.payoff = cu(self.round_payoff)

    def role(self):
        return self.player_role or 'A'


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
            role = 'A' if position < half_market else 'B'
            label_idx = position % half_market + 1
            label = f"{role}{label_idx}"

            player.matching_group_id = market_id
            player.player_role = role
            player.player_id_in_role = label

            player.participant.vars['matching_group_id'] = market_id
            player.participant.vars['player_role'] = role
            player.participant.vars['player_id_in_role'] = label

            markets.setdefault(market_id, []).append(player)

        round_matrices = {}
        for round_no in range(1, C.NUM_ROUNDS + 1):
            round_pairs = []
            for market_id, market_players in markets.items():
                buyers = [p.id_in_subsession for p in market_players if p.player_role == 'A']
                sellers = [p.id_in_subsession for p in market_players if p.player_role == 'B']

                if len(buyers) != len(sellers):
                    raise RuntimeError(f"Market {market_id}: {len(buyers)} buyers vs {len(sellers)} sellers.")

                rng = random.Random(f"{session.code}-{market_id}-{round_no}")
                rng.shuffle(buyers)
                rng.shuffle(sellers)

                for buyer_id, seller_id in zip(buyers, sellers):
                    round_pairs.append([buyer_id, seller_id])

            round_matrices[round_no] = round_pairs

        session.vars['round_matrices'] = round_matrices

        repeats, remainder = divmod(C.NUM_ROUNDS, len(C.PRICE_VECTORS))
        if remainder != 0:
            raise RuntimeError(
                f"NUM_ROUNDS ({C.NUM_ROUNDS}) must be a multiple of the number of price vectors ({len(C.PRICE_VECTORS)})."
            )
        price_schedule = C.PRICE_VECTORS * repeats
        rng_prices = random.Random(f"{session.code}-exo-prices")
        rng_prices.shuffle(price_schedule)
        session.vars['exo_price_schedule'] = price_schedule

    round_matrices = session.vars.get('round_matrices')
    if not round_matrices:
        raise RuntimeError("Round matrices missing in session vars.")

    for player in players:
        stored_market = player.participant.vars.get('matching_group_id')
        stored_role = player.participant.vars.get('player_role')
        stored_label = player.participant.vars.get('player_id_in_role')

        if stored_market is None or stored_role is None or stored_label is None:
            raise RuntimeError(f"Participant {player.participant.code} is missing stored assignments.")

        player.matching_group_id = stored_market
        player.player_role = stored_role
        player.player_id_in_role = stored_label

    subsession.set_group_matrix(round_matrices[subsession.round_number])

    price_schedule = session.vars.get('exo_price_schedule')
    if not price_schedule:
        raise RuntimeError("Price schedule missing in session vars.")

    current_prices = price_schedule[subsession.round_number - 1]
    condition = current_prices['condition']
    for player in subsession.get_players():
        player.price1_offer = current_prices['price1']
        player.price2_offer = current_prices['price2']
        player.price_paid = None
        player.condition_price = condition


class Welcome(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class ControlQuiz(Page):
    form_model = 'player'
    form_fields = ['cq_q1', 'cq_q2', 'cq_q3', 'cq_q4']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def error_message(player: Player, values):
        errors = {}
        if values['cq_q1'] != 'B':
            errors['cq_q1'] = 'Incorrect. Veuillez lire les instructions et réessayer.'
        if values['cq_q2'] != 'A':
            errors['cq_q2'] = 'Incorrect. Veuillez lire les instructions et réessayer.'
        if values['cq_q3'] != 'C':
            errors['cq_q3'] = 'Incorrect. Veuillez lire les instructions et réessayer.'
        if values['cq_q4'] != 'A':
            errors['cq_q4'] = 'Incorrect. Veuillez lire les instructions et réessayer.'

        if errors:
            return errors


class WaitForAllPlayers(WaitPage):
    title_text = "En attente"
    body_text = "Veuillez patienter jusqu'à ce que tous les participants aient lu les instructions."
    wait_for_all_groups = True

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class RoleAssignment(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.player_role is None:
            raise RuntimeError(f"Player {player.id_in_subsession} missing role at RoleAssignment.")
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return dict(player_role=player.player_role)


class PriceInfo(Page):
    @staticmethod
    def vars_for_template(player: Player):
        price1 = player.field_maybe_none('price1_offer')
        price2 = player.field_maybe_none('price2_offer')
        if price1 is None or price2 is None:
            raise RuntimeError("Les prix exogènes ne sont pas disponibles pour ce tour.")
        return dict(
            price1=price1,
            price2=price2,
            player_role=player.player_role,
        )


class InteractionDecision(Page):
    form_model = 'player'
    form_fields = ['interaction']

    @staticmethod
    def is_displayed(player: Player):
        role = player.player_role
        if role is None:
            raise RuntimeError(f"Player {player.id_in_subsession} missing role at InteractionDecision in round {player.round_number}.")
        if role != 'B':
            return False
        partner = player.set_partner()
        if partner.price1_offer is None or partner.price2_offer is None:
            raise RuntimeError(
                f"Partner price offers missing for player {player.id_in_subsession} entering InteractionDecision."
            )
        return True

    @staticmethod
    def vars_for_template(player: Player):
        partner = player.set_partner()
        price1 = partner.field_maybe_none('price1_offer')
        price2 = partner.field_maybe_none('price2_offer')
        if price1 is None or price2 is None:
            raise RuntimeError("Partner prices missing while rendering InteractionDecision.")
        return dict(price1=price1, price2=price2)

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        interaction = player.field_maybe_none('interaction')
        if interaction is None:
            raise RuntimeError("Interaction decision must be submitted before leaving the page.")


class WaitForInteraction(WaitPage):
    title_text = "En attente"
    body_text = "Merci de patienter pendant que le Joueur B fait son choix."
    wait_for_all_groups = False

    @staticmethod
    def after_all_players_arrive(group: Group, **kwargs):
        players = group.get_players()
        player_a = next((p for p in players if p.player_role == 'A'), None)
        player_b = next((p for p in players if p.player_role == 'B'), None)

        if player_a is None or player_b is None:
            raise RuntimeError("Group members missing when assigning types.")

        interaction = player_b.field_maybe_none('interaction')
        if interaction is None:
            raise RuntimeError("Player B interaction decision missing when assigning type.")

        if interaction:
            player_b.player_b_type = random.randint(1, 2)
            player_a.player_b_type = player_b.player_b_type
            price_to_pay = player_a.price1_offer if player_b.player_b_type == 1 else player_a.price2_offer
            player_a.price_paid = price_to_pay
        else:
            player_b.player_b_type = 0
            player_a.player_b_type = 0
            player_a.price_paid = None


class ActionChoice(Page):
    form_model = 'player'
    form_fields = ['action_chosen']

    @staticmethod
    def is_displayed(player: Player):
        role = player.player_role
        if role is None:
            raise RuntimeError(f"Player {player.id_in_subsession} missing role at ActionChoice in round {player.round_number}.")
        if role != 'A':
            return False
        partner = player.set_partner()
        interaction = partner.field_maybe_none('interaction')
        if interaction is None:
            raise RuntimeError(
                f"Partner interaction decision missing before ActionChoice for player {player.id_in_subsession}."
            )
        return interaction

    @staticmethod
    def error_message(player: Player, values):
        if values.get('action_chosen') is None:
            return 'Veuillez sélectionner une action avant de continuer.'

    @staticmethod
    def vars_for_template(player: Player):
        partner = player.set_partner()
        player_b_type = player.field_maybe_none('player_b_type')
        if player_b_type is None:
            raise RuntimeError("Player B type missing when rendering ActionChoice.")
        interaction = partner.field_maybe_none('interaction') or False

        if player_b_type == 1:
            revenue_action_1 = C.REVENUE_1
            revenue_action_2 = C.REVENUE_2
        else:
            revenue_action_1 = C.REVENUE_2
            revenue_action_2 = C.REVENUE_2

        action_info = [
            dict(
                label='Action 1',
                cost=C.ACTION_1_COST,
                revenue=revenue_action_1,
                net_gain=revenue_action_1 - C.ACTION_1_COST,
            ),
            dict(
                label='Action 2',
                cost=C.ACTION_2_COST,
                revenue=revenue_action_2,
                net_gain=revenue_action_2 - C.ACTION_2_COST,
            ),
        ]

        return dict(
            player_b_type=player_b_type,
            interaction=interaction,
            action_info=action_info,
        )


class WaitForAction(WaitPage):
    title_text = "En attente du choix d’action"
    body_text = "Veuillez patienter pendant que le Joueur A sélectionne une action."
    wait_for_all_groups = False

    @staticmethod
    def after_all_players_arrive(group: Group, **kwargs):
        players = group.get_players()
        buyer = next((p for p in players if p.player_role == 'A'), None)
        seller = next((p for p in players if p.player_role == 'B'), None)
        if buyer is None or seller is None:
            raise RuntimeError("Both players must be present in WaitForAction.")
        interaction = seller.field_maybe_none('interaction')
        if interaction is None:
            raise RuntimeError("Player B interaction decision missing before WaitForAction.")
        if interaction and buyer.field_maybe_none('action_chosen') is None:
            raise RuntimeError("Player A action choice missing before releasing WaitForAction.")


class RoundResults(Page):
    @staticmethod
    def vars_for_template(player: Player):
        partner = player.set_partner()
        player.calculate_payoff()
        partner.calculate_payoff()

        partner_interaction = partner.field_maybe_none('interaction')
        player_interaction = player.field_maybe_none('interaction')
        player_price_paid = player.field_maybe_none('price_paid')
        partner_price_paid = partner.field_maybe_none('price_paid')
        player_price1 = player.field_maybe_none('price1_offer')
        player_price2 = player.field_maybe_none('price2_offer')
        partner_price1 = partner.field_maybe_none('price1_offer')
        partner_price2 = partner.field_maybe_none('price2_offer')
        player_revenue = player.field_maybe_none('revenue')
        action_chosen = player.field_maybe_none('action_chosen')

        role = player.field_maybe_none('player_role')
        if role == 'A':
            action_cost = None
            if partner_interaction and action_chosen:
                action_cost = C.ACTION_2_COST if action_chosen == 2 else C.ACTION_1_COST

            return dict(
                player_role='A',
                price1_offer=player_price1,
                price2_offer=player_price2,
                interaction=partner_interaction,
                interaction_text="d'interagir" if partner_interaction else "de ne pas interagir",
                price_paid=player_price_paid if partner_interaction else None,
                has_price_paid=partner_interaction and player_price_paid is not None,
                payoff=player.round_payoff,
                outside_option=C.OUTSIDE_OPTION,
                revenue=player_revenue if partner_interaction else None,
                has_revenue=partner_interaction and player_revenue is not None,
                action_cost=action_cost,
                action_chosen=action_chosen if partner_interaction else None,
            )
        else:
            return dict(
                player_role='B',
                price1_offer=partner_price1,
                price2_offer=partner_price2,
                interaction=player_interaction,
                interaction_text="d'interagir" if player_interaction else "de ne pas interagir",
                price_paid=partner_price_paid if player_interaction else None,
                has_price_paid=player_interaction and partner_price_paid is not None,
                payoff=player.round_payoff,
                outside_option=C.OUTSIDE_OPTION,
            )


class WaitForRoundResults(WaitPage):
    wait_for_all_groups = True
    title_text = 'En attente'
    body_text = 'Veuillez patienter jusqu’à ce que tous les participants aient consulté les résultats de leur tour.'

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number < C.NUM_ROUNDS


class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.round_number == C.NUM_ROUNDS and player.player_role is None:
            raise RuntimeError(f"Player {player.id_in_subsession} missing role at FinalResults.")
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        round_payoffs = []
        for past_round in player.in_all_rounds():
            payoff = past_round.field_maybe_none('round_payoff')
            if payoff is None:
                raise RuntimeError(
                    f"Round payoff missing for player {player.id_in_subsession} in round {past_round.round_number}."
                )
            round_payoffs.append(payoff)

        total_payoff = sum(round_payoffs)
        total_euros = total_payoff.to_real_world_currency(player.session)
        participation_fee = player.session.config.get('participation_fee', 0)
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


class WaitForFinalResults(WaitPage):
    wait_for_all_groups = True
    title_text = "En attente"
    body_text = "Veuillez patienter pendant que tous les participants consultent les résultats finaux."

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


page_sequence = [
    Welcome,
    WaitForAllPlayers,
    ControlQuiz,
    RoleAssignment,
    PriceInfo,
    InteractionDecision,
    WaitForInteraction,
    ActionChoice,
    WaitForAction,
    RoundResults,
    WaitForRoundResults,
    WaitForFinalResults,
    FinalResults,
]
