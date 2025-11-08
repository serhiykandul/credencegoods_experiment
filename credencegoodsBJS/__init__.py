from otree.api import *
import random


doc = """
Credence Goods Experiment - Baseline Condition
Adapted from Dulleck et al 2011
"""


class C(BaseConstants):
    NAME_IN_URL = 'credencegoodsBJS'
    PLAYERS_PER_GROUP = 2  # Pairs of A and B
    NUM_ROUNDS = 16
    
    # Payoff parameters
    OUTSIDE_OPTION = 1
    REVENUE_1 = 10
    REVENUE_2 = 15
    ACTION_2_COST = 6
    ACTION_1_COST = 0
    
    # Price limits
    MIN_PRICE = 2
    MAX_PRICE = 10
    
    # Matching pattern repeats every 4 rounds
    # Pattern within each matching group (4 As and 4 Bs):
    # Round mod 4 = 1: A1-B1, A2-B2, A3-B3, A4-B4
    # Round mod 4 = 2: A1-B2, A2-B3, A3-B4, A4-B1
    # Round mod 4 = 3: A1-B3, A2-B4, A3-B1, A4-B2
    # Round mod 4 = 0: A1-B4, A2-B1, A3-B2, A4-B3


class Subsession(BaseSubsession):
    def assign_roles(self):
        """Assign roles to players in matching groups of 8"""
        players = self.get_players()
        
        # Split into matching groups (groups of 8)
        num_matching_groups = len(players) // 8
        for mg in range(num_matching_groups):
            mg_players = players[mg * 8:(mg + 1) * 8]
            
            # Randomly assign roles: 4 As and 4 Bs
            roles = ['A'] * 4 + ['B'] * 4
            random.shuffle(roles)
            
            # Assign roles and player IDs within matching group
            a_count = 1
            b_count = 1
            for i, p in enumerate(mg_players):
                p.player_role = roles[i]
                if p.player_role == 'A':
                    p.player_id_in_role = f'A{a_count}'
                    a_count += 1
                else:
                    p.player_id_in_role = f'B{b_count}'
                    b_count += 1
                p.matching_group_id = mg + 1
    
    def creating_subsession(self):
        # For round 1, create temporary groups (will be reassigned after roles are assigned)
        # For other rounds, create pairs based on matching protocol
        if self.round_number == 1:
            # Create temporary random groups (pairs) - will be reassigned after role assignment
            players = self.get_players()
            shuffled_players = players[:]
            random.shuffle(shuffled_players)
            group_matrix = []
            for i in range(0, len(shuffled_players), 2):
                if i + 1 < len(shuffled_players):
                    group_matrix.append([shuffled_players[i], shuffled_players[i + 1]])
                else:
                    # If odd number of players, put last one in a group by themselves
                    group_matrix.append([shuffled_players[i]])
            self.set_group_matrix(group_matrix)
        else:
            self.create_pairs()
    
    def create_pairs(self):
        """Create pairs of A and B players according to matching protocol"""
        players = self.get_players()
        
        # Group players by matching group and role
        matching_groups = {}
        for p in players:
            # Only process players who have been assigned a role
            if p.player_role and p.matching_group_id:
                if p.matching_group_id not in matching_groups:
                    matching_groups[p.matching_group_id] = {'A': [], 'B': []}
                matching_groups[p.matching_group_id][p.player_role].append(p)
        
        # Build group matrix: list of lists, where each inner list is a group (pair)
        group_matrix = []
        
        # Determine matching pattern based on round number (mod 4)
        round_pattern = (self.round_number - 1) % 4
        
        # Matching patterns
        if round_pattern == 0:  # Rounds 1, 5, 9, 13
            matches = [(0, 0), (1, 1), (2, 2), (3, 3)]
        elif round_pattern == 1:  # Rounds 2, 6, 10, 14
            matches = [(0, 1), (1, 2), (2, 3), (3, 0)]
        elif round_pattern == 2:  # Rounds 3, 7, 11, 15
            matches = [(0, 2), (1, 3), (2, 0), (3, 1)]
        else:  # Rounds 4, 8, 12, 16
            matches = [(0, 3), (1, 0), (2, 1), (3, 2)]
        
        # Create pairs according to matching protocol
        for mg_id in sorted(matching_groups.keys()):
            roles = matching_groups[mg_id]
            as_players = sorted(roles['A'], key=lambda x: x.player_id_in_role)
            bs_players = sorted(roles['B'], key=lambda x: x.player_id_in_role)
            
            # Create groups (pairs) based on matching pattern
            for a_idx, b_idx in matches:
                if a_idx < len(as_players) and b_idx < len(bs_players):
                    # Add pair to group matrix
                    group_matrix.append([as_players[a_idx], bs_players[b_idx]])
        
        # Set the group matrix to create groups
        self.set_group_matrix(group_matrix)


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
        choices=[[True, 'Interact'], [False, 'Not interact']],
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
        
        if self.player_role == 'A':
            if not partner.interaction:
                # No interaction
                self.round_payoff = C.OUTSIDE_OPTION
                self.revenue = 0
            else:
                # Calculate revenue based on type and action
                if partner.player_b_type == 1:
                    if self.action_chosen == 1:
                        revenue = C.REVENUE_1
                    else:  # action_chosen == 2
                        revenue = C.REVENUE_2
                else:  # player_b_type == 2
                    revenue = C.REVENUE_2
                
                # Calculate costs
                if self.action_chosen == 1:
                    cost = C.ACTION_1_COST
                else:
                    cost = C.ACTION_2_COST
                
                # Final payoff
                self.revenue = revenue
                self.round_payoff = revenue - cost - self.price_paid
        else:  # Player B
            if not self.interaction:
                self.round_payoff = C.OUTSIDE_OPTION
            else:
                if partner.price_paid:
                    self.round_payoff = partner.price_paid
                else:
                    self.round_payoff = 0
    
    def validate_price1_offer(self, value):
        if self.player_role == 'A' and hasattr(self, 'price2_offer'):
            if self.price2_offer and value > self.price2_offer:
                return 'Price 1 must be less than or equal to Price 2'
        return None


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
    
    @staticmethod
    def after_all_players_arrive(subsession: Subsession):
        # Assign roles to all players
        subsession.assign_roles()
        # Create pairs for round 1
        subsession.create_pairs()


class RoleAssignment(Page):
    @staticmethod
    def is_displayed(player: Player):
        # Only display if we're in round 1 and role has been assigned
        return player.round_number == 1 and player.player_role is not None
    
    @staticmethod
    def vars_for_template(player: Player):
        return {
            'player_role': player.player_role,
            'player_id': player.player_id_in_role
        }


class PriceOffer(Page):
    form_model = 'player'
    form_fields = ['price1_offer', 'price2_offer']
    
    @staticmethod
    def is_displayed(player: Player):
        return player.player_role == 'A'
    
    @staticmethod
    def error_message(player: Player, values):
        if values['price1_offer'] > values['price2_offer']:
            return 'Price 1 must be less than or equal to Price 2'
    
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Store prices for partner to see
        partner = player.set_partner()
        partner.partner_price1 = player.price1_offer
        partner.partner_price2 = player.price2_offer


class WaitForPrices(WaitPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.player_role == 'B'


class InteractionDecision(Page):
    form_model = 'player'
    form_fields = ['interaction']
    
    @staticmethod
    def is_displayed(player: Player):
        return player.player_role == 'B'
    
    @staticmethod
    def vars_for_template(player: Player):
        partner = player.set_partner()
        return {
            'price1': partner.price1_offer,
            'price2': partner.price2_offer
        }
    
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        partner = player.set_partner()
        partner.partner_interaction = player.interaction


class WaitForInteraction(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        # Assign player B type and check if interaction occurred
        player_b = [p for p in group.get_players() if p.player_role == 'B'][0]
        player_a = [p for p in group.get_players() if p.player_role == 'A'][0]
        
        if player_b.interaction:
            # Randomly assign type 1 or 2
            player_b.player_b_type = random.randint(1, 2)
            player_a.player_b_type = player_b.player_b_type  # Player A sees the type
        else:
            # No interaction, assign default (won't be used)
            player_b.player_b_type = 0
            player_a.player_b_type = 0


class WaitForAction(WaitPage):
    @staticmethod
    def is_displayed(player: Player):
        if player.player_role == 'B':
            return player.interaction
        return False


class ActionChoice(Page):
    form_model = 'player'
    form_fields = ['action_chosen']
    
    @staticmethod
    def is_displayed(player: Player):
        if player.player_role == 'A':
            partner = player.set_partner()
            return partner.interaction
        return False
    
    @staticmethod
    def vars_for_template(player: Player):
        partner = player.set_partner()
        return {
            'player_b_type': player.player_b_type,
            'interaction': partner.interaction
        }


class WaitForPricePayment(WaitPage):
    @staticmethod
    def is_displayed(player: Player):
        if player.player_role == 'B':
            return player.interaction
        return False


class PricePayment(Page):
    form_model = 'player'
    form_fields = ['price_paid']
    
    @staticmethod
    def is_displayed(player: Player):
        if player.player_role == 'A':
            partner = player.set_partner()
            return partner.interaction
        return False
    
    @staticmethod
    def vars_for_template(player: Player):
        return {
            'price1': player.price1_offer,
            'price2': player.price2_offer
        }
    
    @staticmethod
    def error_message(player: Player, values):
        if values['price_paid'] not in [player.price1_offer, player.price2_offer]:
            return f'You must choose either Price 1 ({player.price1_offer} points) or Price 2 ({player.price2_offer} points)'
    
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Store for partner feedback
        partner = player.set_partner()
        partner.partner_price_paid = player.price_paid
        partner.partner_action = player.action_chosen


class RoundResults(Page):
    @staticmethod
    def vars_for_template(player: Player):
        partner = player.set_partner()
        
        # Calculate payoffs
        player.calculate_payoff()
        partner.calculate_payoff()
        
        if player.player_role == 'A':
            action_cost = None
            if partner.interaction and player.action_chosen:
                action_cost = C.ACTION_2_COST if player.action_chosen == 2 else C.ACTION_1_COST
            
            return {
                'player_role': 'A',
                'price1_offer': player.price1_offer,
                'price2_offer': player.price2_offer,
                'interaction': partner.interaction,
                'interaction_text': 'to interact' if partner.interaction else 'not to interact',
                'price_paid': player.price_paid if (partner.interaction and player.price_paid) else None,
                'payoff': player.round_payoff,
                'outside_option': C.OUTSIDE_OPTION,
                'revenue': player.revenue if (partner.interaction and player.revenue) else None,
                'action_cost': action_cost,
                'action_chosen': player.action_chosen if partner.interaction else None
            }
        else:  # Player B
            return {
                'player_role': 'B',
                'price1_offer': partner.price1_offer,
                'price2_offer': partner.price2_offer,
                'interaction': player.interaction,
                'interaction_text': 'to interact' if player.interaction else 'not to interact',
                'price_paid': partner.price_paid if (player.interaction and partner.price_paid) else None,
                'payoff': player.round_payoff,
                'outside_option': C.OUTSIDE_OPTION
            }


class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS
    
    @staticmethod
    def vars_for_template(player: Player):
        total_payoff = sum([p.round_payoff for p in player.in_all_rounds()])
        total_euros = total_payoff * 0.25  # 1 point = 25 Euro-cents = 0.25 EUR
        
        return {
            'total_payoff': total_payoff,
            'total_euros': total_euros,
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
    FinalResults
]
