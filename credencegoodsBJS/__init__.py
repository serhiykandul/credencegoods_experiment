from otree.api import *
import random


doc = """
Credence Goods Experiment - Baseline Condition
Adapted from Dulleck et al 2011
"""


class C(BaseConstants):
    NAME_IN_URL = 'credencegoodsBJS'
    PLAYERS_PER_GROUP = 2  # Pairs of A and B
    NUM_ROUNDS = 4  # for testing.

    MARKET_SIZE = 8  # players per matching group (“market”)

    # Payoff parameters
    OUTSIDE_OPTION = 1
    REVENUE_1 = 10
    REVENUE_2 = 16
    ACTION_2_COST = 6
    ACTION_1_COST = 1

    # Price limits
    MIN_PRICE = 2
    MAX_PRICE = 10


class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # Role and identification
    player_role = models.StringField()
    player_id_in_role = models.StringField()
    matching_group_id = models.IntegerField()

    # Decision variables - Player A
    price1_offer = models.IntegerField(
        min=C.MIN_PRICE,
        max=C.MAX_PRICE,
        label="Price 1 (must be ≤ Price 2)"
    )
    price2_offer = models.IntegerField(
        min=C.MIN_PRICE,
        max=C.MAX_PRICE,
        label="Price 2"
    )
    action_chosen = models.IntegerField(
        choices=[[1, 'Action 1'], [2, 'Action 2']],
        label="Choose an action",
        blank=True
    )
    price_paid = models.IntegerField(
        label="Which price to pay to Player B?",
        blank=True
    )

    # Decision variables - Player B
    interaction = models.BooleanField(
        choices=[[True, 'Yes'], [False, 'No']],
        label="Do you want to interact with Player A?"
    )

    # Game state variables
    player_b_type = models.IntegerField()  # 1 or 2, randomly assigned
    revenue = models.IntegerField()  # Revenue received by Player A
    round_payoff = models.CurrencyField()  # Payoff for this round

    # For feedback display
    partner_price1 = models.IntegerField()
    partner_price2 = models.IntegerField()
    partner_interaction = models.BooleanField()
    partner_action = models.IntegerField()
    partner_price_paid = models.IntegerField()

    def set_partner(self):
        """Get the partner player in this group"""
        return [p for p in self.group.get_players() if p != self][0]

    def calculate_payoff(self):
        """Calculate payoff for this round"""
        partner = self.set_partner()
        role = self.field_maybe_none('player_role')

        if role is None:
            raise RuntimeError(
                f"Player {self.id_in_subsession} is missing a role in round {self.round_number}."
            )

        if role == 'A':
            partner_interaction = partner.field_maybe_none('interaction')
            if partner_interaction is None:
                raise RuntimeError(
                    f"Partner interaction decision missing for player {self.id_in_subsession} in round {self.round_number}."
                )
            if not partner_interaction:
                # No interaction
                self.round_payoff = C.OUTSIDE_OPTION
                self.revenue = 0
            else:
                # Calculate revenue based on type and action
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
                    if action_chosen == 1:
                        revenue = C.REVENUE_1
                    else:  # action_chosen == 2
                        revenue = C.REVENUE_2
                else:  # player_b_type == 2
                    revenue = C.REVENUE_2

                # Calculate costs
                if action_chosen == 1:
                    cost = C.ACTION_1_COST
                elif action_chosen == 2:
                    cost = C.ACTION_2_COST
                else:
                    raise RuntimeError(
                        f"Invalid action choice {action_chosen} for player {self.id_in_subsession}."
                    )

                # Final payoff
                self.revenue = revenue
                price_paid = self.field_maybe_none('price_paid')
                if price_paid is None:
                    raise RuntimeError(
                        f"Price paid missing for player {self.id_in_subsession} in round {self.round_number}."
                    )
                self.round_payoff = revenue - cost - price_paid
        else:  # Player B
            interaction = self.field_maybe_none('interaction')
            if interaction is None:
                raise RuntimeError(
                    f"Interaction decision missing for player {self.id_in_subsession} in round {self.round_number}."
                )
            if not interaction:
                self.round_payoff = C.OUTSIDE_OPTION
            else:
                partner_price_paid = partner.field_maybe_none('price_paid')
                if partner_price_paid is None:
                    raise RuntimeError(
                        f"Partner price paid missing for player {self.id_in_subsession} in round {self.round_number}."
                    )
                if partner_price_paid:
                    self.round_payoff = partner_price_paid
                else:
                    self.round_payoff = 0

    def validate_price1_offer(self, value):
        role = self.field_maybe_none('player_role')
        price2 = self.field_maybe_none('price2_offer')
        if role == 'A' and price2 is not None and value > price2:
                return 'Price 1 must be less than or equal to Price 2'
        return None

    def role(self):
        return self.player_role or 'A'


def creating_session(subsession: Subsession):
    players = sorted(subsession.get_players(), key=lambda p: p.id_in_subsession)
    market_size = C.MARKET_SIZE
    total_players = len(players)

    if total_players % market_size != 0:
        raise RuntimeError(
            f"Session size {total_players} is not divisible by market size {market_size}."
        )

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
                    raise RuntimeError(
                        f"Market {market_id}: {len(buyers)} buyers vs {len(sellers)} sellers."
                    )

                rng = random.Random(f"{session.code}-{market_id}-{round_no}")
                rng.shuffle(buyers)
                rng.shuffle(sellers)

                for buyer_id, seller_id in zip(buyers, sellers):
                    round_pairs.append([buyer_id, seller_id])

            round_matrices[round_no] = round_pairs

        session.vars['round_matrices'] = round_matrices

    round_matrices = session.vars.get('round_matrices')
    if not round_matrices:
        raise RuntimeError("Round matrices missing in session vars.")

    for player in players:
        stored_market = player.participant.vars.get('matching_group_id')
        stored_role = player.participant.vars.get('player_role')
        stored_label = player.participant.vars.get('player_id_in_role')

        if stored_market is None or stored_role is None or stored_label is None:
            raise RuntimeError(
                f"Participant {player.participant.code} is missing stored assignments."
            )

        player.matching_group_id = stored_market
        player.player_role = stored_role
        player.player_id_in_role = stored_label

    subsession.set_group_matrix(round_matrices[subsession.round_number])

# PAGES
class Welcome(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1
    
class WaitForAllPlayers(WaitPage):
    """Wait for all players to arrive before assigning roles"""
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
        return {
            'player_role': player.player_role
        }


class PriceOffer(Page):
    form_model = 'player'
    form_fields = ['price1_offer', 'price2_offer']
    
    @staticmethod
    def is_displayed(player: Player):
        role = player.player_role
        if role is None:
            raise RuntimeError(f"Player {player.id_in_subsession} missing role at PriceOffer in round {player.round_number}.")
        return role == 'A'
    
    @staticmethod
    def error_message(player: Player, values):
        if values['price1_offer'] > values['price2_offer']:
            return 'Price 1 must be less than or equal to Price 2'
    
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Store prices for partner to see
        partner = player.set_partner()
        price1 = player.field_maybe_none('price1_offer')
        price2 = player.field_maybe_none('price2_offer')
        if price1 is None or price2 is None:
            raise RuntimeError("Price offers must be submitted before leaving PriceOffer page.")
        partner.partner_price1 = price1
        partner.partner_price2 = price2


class WaitForPrices(WaitPage):
    title_text = "Waiting for prices"
    body_text = "Please wait while the price offers are submitted."
    wait_for_all_groups = False

    @staticmethod
    def after_all_players_arrive(group: Group, **kwargs):
        players = group.get_players()
        buyer = next((p for p in players if p.player_role == 'A'), None)
        if buyer is None:
            # fall back to id_in_group
            buyer = next((p for p in players if p.id_in_group == 1), None)
        if buyer is None:
            raise RuntimeError("No buyer found in group at WaitForPrices.")
        price1 = buyer.field_maybe_none('price1_offer')
        price2 = buyer.field_maybe_none('price2_offer')
        if price1 is None or price2 is None:
            raise RuntimeError(
                f"Buyer {buyer.id_in_subsession} missing price offers when releasing WaitForPrices."
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
        return {
            'price1': price1,
            'price2': price2
        }
    
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        partner = player.set_partner()
        interaction = player.field_maybe_none('interaction')
        if interaction is None:
            raise RuntimeError("Interaction decision must be submitted before leaving the page.")
        partner.partner_interaction = interaction


class WaitForInteraction(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group, **kwargs):
        # Assign player B type and check if interaction occurred
        players = group.get_players()
        players_b = [p for p in players if p.player_role == 'B']
        players_a = [p for p in players if p.player_role == 'A']

        if not players_b or not players_a:
            return

        player_b = players_b[0]
        player_a = players_a[0]
        
        interaction = player_b.field_maybe_none('interaction')
        if interaction is None:
            raise RuntimeError("Player B interaction decision missing when assigning type.")
        
        if interaction:
            # Randomly assign type 1 or 2
            player_b.player_b_type = random.randint(1, 2)
            player_a.player_b_type = player_b.player_b_type  # Player A sees the type
        else:
            # No interaction, assign default (won't be used)
            player_b.player_b_type = 0
            player_a.player_b_type = 0


class WaitForAction(WaitPage):
    title_text = "Waiting for action choice"
    body_text = "Please wait until your partner selects an action."
    wait_for_all_groups = False

    @staticmethod
    def is_displayed(player: Player):
        return True

    @staticmethod
    def after_all_players_arrive(group: Group, **kwargs):
        players = group.get_players()
        buyer = next((p for p in players if p.player_role == 'A'), None)
        seller = next((p for p in players if p.player_role == 'B'), None)
        if buyer is None or seller is None:
            raise RuntimeError("Both buyer and seller are required in WaitForAction.")
        interaction = seller.interaction
        if interaction is None:
            raise RuntimeError("Player B interaction decision missing before WaitForAction.")
        if interaction and buyer.player_b_type is None:
            raise RuntimeError("Player A missing player_b_type before WaitForAction.")

class ActionChoice(Page):
    form_model = 'player'
    form_fields = ['action_chosen']
    
    @staticmethod
    def is_displayed(player: Player):
        role = player.player_role
        if role is None:
            raise RuntimeError(f"Player {player.id_in_subsession} missing role at ActionChoice in round {player.round_number}.")
        if role == 'A':
            partner = player.set_partner()
            interaction = partner.interaction
            if interaction is None:
                raise RuntimeError(
                    f"Partner interaction decision missing before ActionChoice for player {player.id_in_subsession}."
                )
            return interaction
        return False
    
    @staticmethod
    def vars_for_template(player: Player):
        partner = player.set_partner()
        player_b_type = player.field_maybe_none('player_b_type')
        if player_b_type is None:
            raise RuntimeError("Player B type missing when rendering ActionChoice.")
        interaction = partner.field_maybe_none('interaction')
        if interaction is None:
            interaction = False
        return {
            'player_b_type': player_b_type,
            'interaction': interaction
        }


class WaitForPricePayment(WaitPage):
    title_text = "Waiting for payment decision"
    body_text = "Please wait while Player A chooses the price to pay."
    wait_for_all_groups = False

    @staticmethod
    def is_displayed(player: Player):
        return True

    @staticmethod
    def after_all_players_arrive(group: Group, **kwargs):
        players = group.get_players()
        buyer = next((p for p in players if p.player_role == 'A'), None)
        seller = next((p for p in players if p.player_role == 'B'), None)
        if buyer is None or seller is None:
            raise RuntimeError("Both buyer and seller are required in WaitForPricePayment.")
        interaction = seller.interaction
        if interaction is None:
            raise RuntimeError("Player B interaction decision missing before WaitForPricePayment.")
        if interaction and buyer.field_maybe_none('price_paid') is None:
            raise RuntimeError("Player A price payment missing before WaitForPricePayment.")


class PricePayment(Page):
    form_model = 'player'
    form_fields = ['price_paid']
    
    @staticmethod
    def is_displayed(player: Player):
        role = player.player_role
        if role is None:
            raise RuntimeError(f"Player {player.id_in_subsession} missing role at PricePayment in round {player.round_number}.")
        if role != 'A':
            return False
        partner = player.set_partner()
        interaction = partner.field_maybe_none('interaction')
        if interaction is None:
            raise RuntimeError(
                f"Partner interaction decision missing before PricePayment for player {player.id_in_subsession}."
            )
        return interaction
    
    @staticmethod
    def vars_for_template(player: Player):
        price1 = player.field_maybe_none('price1_offer')
        price2 = player.field_maybe_none('price2_offer')
        if price1 is None or price2 is None:
            raise RuntimeError("Price offers missing when displaying PricePayment.")
        return {
            'price1': price1,
            'price2': price2
        }
    
    @staticmethod
    def error_message(player: Player, values):
        price1 = player.field_maybe_none('price1_offer')
        price2 = player.field_maybe_none('price2_offer')
        if values['price_paid'] not in [price1, price2]:
            return f'You must choose either Price 1 ({price1} points) or Price 2 ({price2} points)'
    
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Store for partner feedback
        partner = player.set_partner()
        price_paid = player.field_maybe_none('price_paid')
        if price_paid is None:
            raise RuntimeError("Price paid must be selected before leaving PricePayment.")
        partner.partner_price_paid = price_paid
        partner.partner_action = player.field_maybe_none('action_chosen')


class RoundResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return True

    @staticmethod
    def vars_for_template(player: Player):
        partner = player.set_partner()
        role = player.field_maybe_none('player_role')
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
        
        # Calculate payoffs
        player.calculate_payoff()
        partner.calculate_payoff()
        
        if role is None:
            return {
                'player_role': None,
                'interaction': partner_interaction,
                'payoff': player.round_payoff,
                'outside_option': C.OUTSIDE_OPTION
            }
        
        if role == 'A':
            action_cost = None
            if partner_interaction and action_chosen:
                action_cost = C.ACTION_2_COST if action_chosen == 2 else C.ACTION_1_COST
            
            return {
                'player_role': 'A',
                'price1_offer': player_price1,
                'price2_offer': player_price2,
                'interaction': partner_interaction,
                'interaction_text': 'to interact' if partner_interaction else 'not to interact',
                'price_paid': player_price_paid if (partner_interaction and player_price_paid) else None,
                'payoff': player.round_payoff,
                'outside_option': C.OUTSIDE_OPTION,
                'revenue': player_revenue if (partner_interaction and player_revenue) else None,
                'action_cost': action_cost,
                'action_chosen': action_chosen if partner_interaction else None
            }
        else:  # Player B
            return {
                'player_role': 'B',
                'price1_offer': partner_price1,
                'price2_offer': partner_price2,
                'interaction': player_interaction,
                'interaction_text': 'to interact' if player_interaction else 'not to interact',
                'price_paid': partner_price_paid if (player_interaction and partner_price_paid) else None,
                'payoff': player.round_payoff,
                'outside_option': C.OUTSIDE_OPTION
            }

class WaitForRoundResults(WaitPage):
    wait_for_all_groups = True
    title_text = 'Waiting'
    body_text = 'Please wait until all participants have reviewed their round results.'

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number < C.NUM_ROUNDS


class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.round_number == C.NUM_ROUNDS and player.player_role is None:
            raise RuntimeError(
                f"Player {player.id_in_subsession} missing role at FinalResults."
            )
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
        total_euros = total_payoff * 0.25  # 1 point = 25 Euro-cents = 0.25 EUR
        
        return {
            'total_payoff': total_payoff,
            'total_euros': total_euros,
            'total_euros_rounded': f"{total_euros:.2f}",
            'rounds': player.in_all_rounds()
        }


page_sequence = [
    Welcome,
    WaitForAllPlayers,
    RoleAssignment,
    PriceOffer,
    WaitForPrices,
    InteractionDecision,
    WaitForInteraction,
    ActionChoice,
    WaitForAction,
    PricePayment,
    WaitForPricePayment,
    RoundResults,
    WaitForRoundResults,
    FinalResults
]
