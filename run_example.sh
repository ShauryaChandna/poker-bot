#!/bin/bash
# Simple script to run examples with correct PYTHONPATH

export PYTHONPATH=/Users/shauryachandna/pokerbot:$PYTHONPATH

echo "🎯 POKER ENGINE - Available Examples"
echo "====================================="
echo ""
echo "Quick Demos:"
echo "  0) demo_interactive_test.py - Automated feature demo"
echo "  1) simple_game.py - AI vs AI game"
echo "  2) hand_evaluation_demo.py - Hand evaluation demo"  
echo "  3) api_usage.py - API usage examples"
echo "  4) interactive_cli.py - Play against AI"
echo ""
echo "Testing:"
echo "  5) interactive_test.py - Full interactive test suite"
echo "  6) test_pot_limit.py - Pot-limit calculation tests"
echo ""

if [ $# -eq 0 ]; then
    echo "Usage: ./run_example.sh <example_number>"
    echo "Example: ./run_example.sh 0"
    echo ""
    echo "Recommended: Start with 0 (demo) or 5 (interactive test)"
    exit 1
fi

case $1 in
    0)
        echo "Running automated feature demo..."
        python demo_interactive_test.py
        ;;
    1)
        echo "Running AI vs AI game..."
        python examples/simple_game.py
        ;;
    2)
        echo "Running hand evaluation demo..."
        python examples/hand_evaluation_demo.py
        ;;
    3)
        echo "Running API usage examples..."
        python examples/api_usage.py
        ;;
    4)
        echo "Starting interactive game..."
        python examples/interactive_cli.py
        ;;
    5)
        echo "Starting interactive test suite..."
        python interactive_test.py
        ;;
    6)
        echo "Running pot-limit calculation tests..."
        python test_pot_limit.py
        ;;
    *)
        echo "Invalid example number. Choose 0-6."
        exit 1
        ;;
esac

