"""
Hand Evaluation Demo

This example demonstrates the hand evaluator capabilities.
"""

from pypokerengine.engine import Card, HandEvaluator


def evaluate_and_print(cards, description):
    """Evaluate and print a hand."""
    rank, tiebreakers, hand_name = HandEvaluator.evaluate_hand(cards)
    cards_str = " ".join(str(c) for c in cards)
    print(f"{description}")
    print(f"  Cards: {cards_str}")
    print(f"  Hand: {hand_name}")
    print(f"  Rank: {rank}, Tiebreakers: {tiebreakers}")
    print()


def main():
    """Demonstrate hand evaluation."""
    print("="*60)
    print("HAND EVALUATION DEMO")
    print("="*60)
    print()
    
    # Royal Flush
    cards = [
        Card.from_string("As"),
        Card.from_string("Ks"),
        Card.from_string("Qs"),
        Card.from_string("Js"),
        Card.from_string("Ts")
    ]
    evaluate_and_print(cards, "Royal Flush:")
    
    # Straight Flush
    cards = [
        Card.from_string("9h"),
        Card.from_string("8h"),
        Card.from_string("7h"),
        Card.from_string("6h"),
        Card.from_string("5h")
    ]
    evaluate_and_print(cards, "Straight Flush:")
    
    # Four of a Kind
    cards = [
        Card.from_string("Kd"),
        Card.from_string("Kh"),
        Card.from_string("Ks"),
        Card.from_string("Kc"),
        Card.from_string("2d")
    ]
    evaluate_and_print(cards, "Four of a Kind:")
    
    # Full House
    cards = [
        Card.from_string("Ah"),
        Card.from_string("Ad"),
        Card.from_string("As"),
        Card.from_string("Kh"),
        Card.from_string("Kd")
    ]
    evaluate_and_print(cards, "Full House:")
    
    # Flush
    cards = [
        Card.from_string("Ac"),
        Card.from_string("Jc"),
        Card.from_string("9c"),
        Card.from_string("5c"),
        Card.from_string("2c")
    ]
    evaluate_and_print(cards, "Flush:")
    
    # Straight
    cards = [
        Card.from_string("9d"),
        Card.from_string("8c"),
        Card.from_string("7h"),
        Card.from_string("6s"),
        Card.from_string("5d")
    ]
    evaluate_and_print(cards, "Straight:")
    
    # Three of a Kind
    cards = [
        Card.from_string("Qh"),
        Card.from_string("Qd"),
        Card.from_string("Qs"),
        Card.from_string("7c"),
        Card.from_string("4d")
    ]
    evaluate_and_print(cards, "Three of a Kind:")
    
    # Two Pair
    cards = [
        Card.from_string("Jh"),
        Card.from_string("Jd"),
        Card.from_string("8h"),
        Card.from_string("8c"),
        Card.from_string("3s")
    ]
    evaluate_and_print(cards, "Two Pair:")
    
    # One Pair
    cards = [
        Card.from_string("Th"),
        Card.from_string("Td"),
        Card.from_string("Ah"),
        Card.from_string("Kc"),
        Card.from_string("6s")
    ]
    evaluate_and_print(cards, "One Pair:")
    
    # High Card
    cards = [
        Card.from_string("Ah"),
        Card.from_string("Kd"),
        Card.from_string("Qh"),
        Card.from_string("8c"),
        Card.from_string("3s")
    ]
    evaluate_and_print(cards, "High Card:")
    
    # Test 7-card evaluation (Texas Hold'em)
    print("="*60)
    print("7-CARD EVALUATION (Texas Hold'em)")
    print("="*60)
    print()
    
    # Player has As Ah
    # Board is Ac Kh Kd 7s 2c
    cards = [
        Card.from_string("As"),  # Hole card
        Card.from_string("Ah"),  # Hole card
        Card.from_string("Ac"),  # Flop
        Card.from_string("Kh"),  # Flop
        Card.from_string("Kd"),  # Flop
        Card.from_string("7s"),  # Turn
        Card.from_string("2c")   # River
    ]
    evaluate_and_print(cards, "Player: As Ah | Board: Ac Kh Kd 7s 2c")
    
    # Compare two hands
    print("="*60)
    print("COMPARING HANDS")
    print("="*60)
    print()
    
    hand1 = [
        Card.from_string("As"),
        Card.from_string("Ad"),
        Card.from_string("Kh"),
        Card.from_string("Kd"),
        Card.from_string("Ks")
    ]
    
    hand2 = [
        Card.from_string("Qh"),
        Card.from_string("Qd"),
        Card.from_string("Qs"),
        Card.from_string("Qc"),
        Card.from_string("7h")
    ]
    
    result = HandEvaluator.compare_hands(hand1, hand2)
    
    rank1, _, name1 = HandEvaluator.evaluate_hand(hand1)
    rank2, _, name2 = HandEvaluator.evaluate_hand(hand2)
    
    print(f"Hand 1: {name1}")
    print(f"Hand 2: {name2}")
    
    if result == 1:
        print("Result: Hand 1 wins!")
    elif result == -1:
        print("Result: Hand 2 wins!")
    else:
        print("Result: Tie!")


if __name__ == "__main__":
    main()

