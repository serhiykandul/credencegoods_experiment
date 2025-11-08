  
I will run an interactive experiment in the lab with human participants. Below you will find the draft of the experimental instructions for the baseline condition. These instructions highlight all essential components of the experiment, such as the matching table of the participants across rounds, the decisions they make and the resulting payoffs they get.

I have the Otree 5\>0  package in Python installed (Windows). I have located the project and all the relevant files init\_py,  here C:\\Users\\Serhiy\\credencegoods\\credencegoodsBJS. Please write the code for init\_py and make all necessary changes in the auxiliary files to program this experiment. Generate a version for 16 participants (2 matching groups of eight) which I should be able to test locally with the devserver environment.  
I need an ID for each participant/client, an ID for a matching group, a groupID for each pair of players A in B in that particular round (you can use the in-built oTree variables for these purposes for that, no need to overwrite).  
Importantly pay attention to the waiting process.  
Participants' roles are assigned only when everyone arrives, and at every stage participants wait for all players within their matching group to submit their respective choices, before they can move forward.  
Importantly, a matching group refers to the group of eight participants. The two players within this matching group are then further paired in their Group (Otree variable) every round.

Include a welcome screen “Welcome to the experiment\! Please read the instructions carefully and click “Ready” when you are ready to proceed”, after this include a screen “You are player \<player.role\>” (you can use an in-built variable label for player role labels in Otree instead of “player.role” defined here) and the “next” button; afterwards put the main decision screens in every round (according to the instructions for the experiment), a role-specific feedback screen after every round with the information about participants’ choice and resulting payment.  
For player B: “This round is over. In this round, player A offered you price 1=\<price1\_offer\> and price2=\<price2\_offer\>. You have chosen \<”not to interact”\>\<input variable “interaction” (yes/no)\> with player A. Your payoff is \<outside\_option\> or “You have chosen  \<to interact\> with player A, player A paid you \<price\_paid\>. Your payoff is \<\>”;   
for player A \>: “ This round is over. You offered  price 1=\<price1\_offer\> and price2=\<price2\_offer\> to player B. Player B has chosen \<interaction(yes/no)\> with player B. Your payoff is \<outside\_option\> or You have chosen to interact with player B, player B paid you \<price\_paid\>. Your payoff is \<\>.”. To calculate the payoffs take into consideration the decisions of the players in the same pair for that round (GroupID or smth).  
Finally, add the final screen with the information about participants total payoffs at the end of the game.

**INSTRUCTIONS FOR THE EXPERIMENT**   
**(Adapted from Dulleck et al 2011\)**

Thank you for participating in this experiment.   
Please switch off your mobile phones and do not talk to any other participant until the experiment is over.   
For your participation in the experiment you will receive a fixed show-up fee of **XX EUR.**  
In the course of the experiment, you can earn additional money.  
Your earnings depend on your decisions, the decisions of other participants, and on chance.  
The detailed explanations on  how your earnings will be determined will be provided in these instructions below.

**Flow of the experiment**  
**2 Roles and 16 Rounds** 

This experiment consists of 16 rounds, each of which consists of the same sequence of decisions. This sequence of decisions is explained in detail below.   
There are 2 kinds of roles in this experiment: player A and player B. At the beginning of the experiment you will be randomly assigned to one of these two roles. On the first screen of the experiment you will see which role you are assigned to. Your role remains the same throughout the experiment.   
The participants will then be randomly matched in groups of eight and stay within the same group across all the rounds of the game. In your group there are 4 players A and 4 players B. The players of each role get an ID number: player A1, A2, A3 and A4; and players B1, B2, B3, B4. The ID numbers of all players A and B are fixed, i.e. players keep their ID numbers throughout the experiment. The ID number is private information, i.e. participants will not learn the ID numbers of each other. Every round each player A will be matched with another player B; the matching protocol is implemented such that each over 16 rounds, each player A will be matched exactly four times with each of the players B in some pre-defined order; this order will not be shown to participants, i.e. in any given round participants will not know whether and in which rounds they played with each other before.

\[**Matching protocol.** Not shown to participants, for programming in Otree: Repeat this matching table in at the background of every four rounds: 

| Rounds 1,5,9,13 | Rounds 2,6,10,14 | Rounds 3,7,11,15 | Rounds 4,8,12,16 |
| :---- | :---- | :---- | :---- |
| A1-B1 | A1-B4 | A1-B3 | A1-B2 |
| A2-B2 | A1-B1 | A1-B4 | A1-B3 |
| A3-B3 | A1-B2 | A1-B1 | A1-B4 |
| A4-B4 | A1-B3 | A1-B2 | A1-B1 |

All participants get the same information on the rules of the game, including the costs and payoffs of both players. 

**Overview of the Sequence of Decisions in a Round**

**Each round consists of a maximum of five consequent stages:** 

**Stage 1\.** *"Definition of player B type".* Player B is randomly assigned a type (type 1 or type 2\) with equal probability. At this stage, neither player B nor player A learn which type has been assigned to player B. 

**Stage 2\.** *"Price offering by player A".* Player A offers Player B two prices: price 1 and price 2\. Both prices must be in the range from 2 to 10 units (only integers are allowed). 

**Stage 3\.** *"Decision to interact by player B"***.** Player B gets to know the two prices offered by Player A. Then player B decides whether he/she wants to interact with one of the players A. If not, this round ends and both players receive 1 point; if player B decides to interact, the round proceeds to the next stage. 

**Stage 4\.** "Choice of action by player A". Player A is informed about the type of player B who decided to interact with him/her (Remember, there are two possible types of player B: he/she is of either type 1 or type 2 which are defined at stage 1). Player A has to choose an action: action 1 or action 2\. Action 1 costs player A **0 points**, action 2 costs player A **6 points**. 

Depending on the type of Player B and the chosen action, player A either receives **Revenue 1 \= 10 points** or **Revenue 2 \= 15 points.**   
If player B is of type 1 and player A chooses action 1, player A receives Revenue 1;   
If player B is of type 1 and player A chooses action 2, player A receives Revenue 2;   
If player B is of type 2, and player A chooses action 1 or action 2, player A receives Revenue 2**.** 

**Stage 5\.** *"Price paid to Player B".* Player A chooses which of the two prices, price 1 or price 2, eventually to pay to player B. Here, player A can choose to pay one of the two prices she/he set at the price offer stage.

The final payoffs for the players are defined: Player A gets price 1 or price 2 ; Player B gets Revenue 1 or Revenue 2 minus the costs of the chosen action minus the price he/she pays to player B. 

**Detailed Illustration of the Decisions and Their Consequences Regarding Payoffs**

**Overview of the Sequence of Decisions in a Round**

*Decision 1*  
At decision 1 each Player A has to set the prices. Only   
(strictly) positive integer numbers are possible, i.e., only  2, 3, 4, 5, 6, 7, 8, 9, 10 are   
valid prices. Note that the price 1 must not exceed the price 2\. 

*Decision 2*   
Player B gets to know the prices set by player A at   
decision 1\. Then player B decides whether he/she wants to interact with one of the players A.  
If he/she wants to do so, player A can choose an action at decision 3, which defines her respective revenue.   
If he/she doesn’t want to interact, this round ends both players get a payoff   
of 1 point for this round.

*Decision 3*  
player A chooses an action which (together with the type of player B) defines his/her revenue.

Before decision 3 is made  a type is randomly   
assigned to player B. Player B can be one of the two types: type 1 or type 2\. This type is   
determined for each player B in each new round. The determination is random and   
independent of the other players’ types. With a probability of 50% player B is of type 1,   
and with a probability of 50% he/she is of type 2\. Imagine that a coin is tossed for each   
player B in each round. If the result is e.g. “heads”, player B is of type 1, if the result is “tails”   
he/she is of type 2\.   
Player A gets to know the types of all players B who interact with him/her before he   
makes his decision 3\. Then player A chooses an action for each player B, either action 1 or   
action 2\.   
The action chosen by player A together with player B's type defines the revenue of player A.  
The amount of Revenue, player A receives depends on the type of player B. There are two possibilities a player A can have during choosing his action:   
a) In case player B is a type 1 player, player A has to choose action 2 to get  **a higher Revenue 2 \= 15 points** (otherwise he/she gets a lower **Revenue 1 \= 10 points)**  
b) In case player B is a type 2 player, player A can choose any of the actions, action 1 or action 2 to get a higher Revenue 2 (player A always receives **a higher Revenue 2 of 15 points** regardless of the action he/she chooses)

**At no time player B will be informed whether he/she is of type 1 or a type 2 player.**

*Decision 4*  
Player A pays the price (which he determined at decision 1). 

**Payoffs**

**No Interaction:**

If player B chose not to interact with the player A,  
he/she gets 1 point for this particular round.     
Otherwise the payoffs are as follows: 

**Interaction:**

Player A receives Revenue 1 or Revenue 2, respectively, less the costs for the action chosen at decision 3,  
less the price he/she eventually pays to participant B (decision 4).

Player B gets the price eventually chosen by player A.

To calculate the final payoff the initial endowment and the profits of all rounds are added up.   
This sum is then converted into cash using the following exchange rate: 

**1 point \= 25 Euro-cents**   
**(i.e. 4 points \= 1 Euro)**

