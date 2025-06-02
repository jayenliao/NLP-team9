#!/bin/bash
# Quick test to ensure everything is working

echo "🧪 Running Quick System Test"
echo "==========================="

# Test 1: CLI help
echo -n "Test 1: CLI help... "
if python cli.py --help > /dev/null 2>&1; then
    echo "✅ Pass"
else
    echo "❌ Fail"
    exit 1
fi

# Test 2: Format tests
echo -n "Test 2: Format handlers... "
if python cli.py test --formats > /dev/null 2>&1; then
    echo "✅ Pass"
else
    echo "❌ Fail"
    exit 1
fi

# Test 3: Status command
echo -n "Test 3: Status command... "
if python cli.py status > /dev/null 2>&1; then
    echo "✅ Pass"
else
    echo "❌ Fail"
    exit 1
fi

# Test 4: Check if API keys are set
echo -n "Test 4: API keys... "
if grep -q "your-.*-api-key" .env 2>/dev/null; then
    echo "⚠️  Using template keys (update .env!)"
else
    echo "✅ Keys configured"
fi

echo ""
echo "✅ All basic tests passed!"
echo ""
echo "Ready to run experiments with:"
echo "  python cli.py run --subtask abstract_algebra --num-questions 1"