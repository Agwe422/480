import random
import time
import math
import itertools
import sys

# Constants
SUITS = ['heart', 'diamond', 'club', 'spade']
RANKS = list(range(1, 14))  # 1–10, 11=Jack, 12=Queen, 13=King

def create_deck() -> list[tuple[int, str]]:
    """
    Create a standard 52-card deck.
    Each card is a tuple: (rank, suit).
    """
    return [(rank, suit) for rank in RANKS for suit in SUITS]

def shuffle_deck(deck: list[tuple[int, str]]) -> None:
    """
    Shuffle the deck in place.
    """
    random.shuffle(deck)

def deal_cards(deck: list[tuple[int, str]], num: int) -> list[tuple[int, str]]:
    """
    Deal `num` cards from the top of the deck.
    Removes dealt cards from the deck.
    """
    if num > len(deck):
        raise ValueError("Not enough cards to deal")
    dealt = deck[:num]
    del deck[:num]
    return dealt


class Node:
    def __init__(self, hand=None, parent=None):
        self.hand = hand
        self.parent = parent
        self.children = []
        self.untried = []
        self.wins = 0.0
        self.visits = 0

def find_straight(ranks):
    ranks_set = set(ranks)
    if 1 in ranks_set:
        ranks_set.add(14)
    sorted_ranks = sorted(ranks_set)
    for i in range(len(sorted_ranks) - 4):
        window = sorted_ranks[i:i+5]
        if window[-1] - window[0] == 4 and len(window) == 5:
            return window[-1]
    return None

def evaluate_hand(cards):
    from collections import Counter
    ranks = [r for r, s in cards]
    suits = [s for r, s in cards]
    rank_counts = Counter(ranks)
    suit_counts = Counter(suits)
    # Flush?
    flush_suit = None
    for suit, count in suit_counts.items():
        if count >= 5:
            flush_suit = suit
            break
    # Straight flush
    if flush_suit:
        suited = [r for r, s in cards if s == flush_suit]
        top_sf = find_straight(suited)
        if top_sf:
            return (9, top_sf)
    # Four of a kind
    fours = [r for r, c in rank_counts.items() if c == 4]
    if fours:
        quad = fours[0]
        kickers = sorted([r for r in ranks if r != quad], reverse=True)
        return (8, quad, kickers[0])
    # Full house
    threes = sorted([r for r, c in rank_counts.items() if c >= 3], reverse=True)
    pairs = sorted([r for r, c in rank_counts.items() if c >= 2 and r not in threes], reverse=True)
    if threes and pairs:
        return (7, threes[0], pairs[0])
    if len(threes) >= 2:
        return (7, threes[0], threes[1])
    # Flush
    if flush_suit:
        flush_cards = sorted([r for r, s in cards if s == flush_suit], reverse=True)
        return (6, *flush_cards[:5])
    # Straight
    top_s = find_straight(ranks)
    if top_s:
        return (5, top_s)
    # Three of a kind
    if threes:
        trips = threes[0]
        kickers = sorted([r for r in ranks if r != trips], reverse=True)[:2]
        return (4, trips, *kickers)
    # Two pair
    if len(pairs) >= 2:
        top2 = pairs[:2]
        kicker = max([r for r in ranks if r not in top2])
        return (3, top2[0], top2[1], kicker)
    # One pair
    if pairs:
        pr = pairs[0]
        kickers = sorted([r for r in ranks if r != pr], reverse=True)[:3]
        return (2, pr, *kickers)
    # High card
    high = sorted(ranks, reverse=True)[:5]
    return (1, *high)

def mcts_decision(hole_cards, community_cards, deck, time_limit=10.0):
    """
    Use MCTS to choose stay (True) or fold (False) given hole cards,
    current community cards, remaining deck, within time_limit seconds.
    """
    start = time.time()
    root = Node(hand=None, parent=None)
    # Generate opponent hole combinations excluding my hole and community cards
    available = [c for c in deck if c not in hole_cards and c not in community_cards]
    root.untried = list(itertools.combinations(available, 2))
    while time.time() - start < time_limit:
        node = root
        # Selection / Expansion
        if node.untried:
            opp = node.untried.pop(random.randrange(len(node.untried)))
            child = Node(hand=opp, parent=node)
            node.children.append(child)
            node = child
        else:
            best, best_score = None, -float('inf')
            for c in node.children:
                score = (c.wins / c.visits) + math.sqrt(2 * math.log(node.visits) / c.visits)
                if score > best_score:
                    best_score, best = score, c
            node = best
        # Simulation
        sim_deck = [c for c in deck if c not in hole_cards and c not in community_cards]
        sim_deck.remove(node.hand[0])
        sim_deck.remove(node.hand[1])
        random.shuffle(sim_deck)
        needed = 5 - len(community_cards)
        sim_board = community_cards + [sim_deck.pop() for _ in range(needed)]
        bot_eval = evaluate_hand(hole_cards + sim_board)
        opp_eval = evaluate_hand(list(node.hand) + sim_board)
        outcome = 1.0 if bot_eval > opp_eval else (0.5 if bot_eval == opp_eval else 0.0)
        # Backpropagation
        temp = node
        while temp:
            temp.visits += 1
            temp.wins += outcome
            temp = temp.parent
    win_prob = root.wins / root.visits if root.visits else 0.0
    return win_prob

if __name__ == "__main__":
    deck = create_deck()
    shuffle_deck(deck)

    # Deal hole cards
    my_hole = deal_cards(deck, 2)
    

    # my_hole = [(1, 'diamond'), (1, 'diamond')] testing with set hand
    print("Hole cards:", my_hole)

    # Pre-Flop decision
    community = []
    win_prob = mcts_decision(my_hole, community, deck.copy(), time_limit=10.0)
    print(f"Win probability Pre-Flop: {win_prob:.2f}")
    decision = "Stay" if win_prob >= 0.5 else "Fold"
    print("Decision Pre-Flop:", decision)
    if decision == "Fold":
        print("Player folded. Game over.")
        sys.exit()

    # Flop: burn one, deal three cards
    _ = deal_cards(deck, 1)
    flop = deal_cards(deck, 3)
    community = flop.copy()
    print("Flop:", flop)
    win_prob = mcts_decision(my_hole, community, deck.copy(), time_limit=10.0)
    print(f"Win probability on Flop: {win_prob:.2f}")
    decision = "Stay" if win_prob >= 0.5 else "Fold"
    print("Decision on Flop:", decision)
    if decision == "Fold":
        print("Player folded. Game over.")
        sys.exit()

    # Turn: burn one, deal one card
    _ = deal_cards(deck, 1)
    turn_card = deal_cards(deck, 1)
    community.extend(turn_card)
    print("Turn:", turn_card)
    win_prob = mcts_decision(my_hole, community, deck.copy(), time_limit=10.0)
    print(f"Win probability on Turn: {win_prob:.2f}")
    decision = "Stay" if win_prob >= 0.5 else "Fold"
    print("Decision on Turn:", decision)
    if decision == "Fold":
        print("Player folded. Game over.")
        sys.exit()

    # River: burn one, deal one card
    _ = deal_cards(deck, 1)
    river_card = deal_cards(deck, 1)
    community.extend(river_card)
    print("River:", river_card)
    win_prob = mcts_decision(my_hole, community, deck.copy(), time_limit=10.0)
    print(f"Win probability on River: {win_prob:.2f}")
    decision = "Stay" if win_prob >= 0.5 else "Fold"
    print("Decision on River:", decision)
    if decision == "Fold":
        print("Player folded. Game over.")
        sys.exit()