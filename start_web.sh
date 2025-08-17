#!/bin/bash

# Crossplane Agentic Automation Web Interface Startup Script

echo "🌐 Starting Crossplane Agentic Automation Web Interface..."
echo "=" * 60

# Check if required environment variables are set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY not set"
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  Warning: GITHUB_TOKEN not set"
fi

if [ -z "$GITHUB_REPO_OWNER" ]; then
    echo "⚠️  Warning: GITHUB_REPO_OWNER not set"
fi

if [ -z "$GITHUB_REPO_NAME" ]; then
    echo "⚠️  Warning: GITHUB_REPO_NAME not set"
fi

echo ""
echo "🔧 Configuration Status:"
echo "   OpenAI API Key: ${OPENAI_API_KEY:+✅ Set}${OPENAI_API_KEY:-❌ Not Set}"
echo "   GitHub Token: ${GITHUB_TOKEN:+✅ Set}${GITHUB_TOKEN:-❌ Not Set}"
echo "   GitHub Repo Owner: ${GITHUB_REPO_OWNER:+✅ Set}${GITHUB_REPO_OWNER:-❌ Not Set}"
echo "   GitHub Repo Name: ${GITHUB_REPO_NAME:+✅ Set}${GITHUB_REPO_NAME:-❌ Not Set}"
echo ""

if [ -z "$OPENAI_API_KEY" ] || [ -z "$GITHUB_TOKEN" ] || [ -z "$GITHUB_REPO_OWNER" ] || [ -z "$GITHUB_REPO_NAME" ]; then
    echo "💡 To set up your API keys, run:"
    echo "   export OPENAI_API_KEY=\"your-openai-api-key\""
    echo "   export GITHUB_TOKEN=\"your-github-token\""
    echo "   export GITHUB_REPO_OWNER=\"your-github-username\""
    echo "   export GITHUB_REPO_NAME=\"your-repo-name\""
    echo ""
fi

echo "🚀 Starting web server..."
echo "📱 Open your browser to: http://localhost:5001"
echo "=" * 60

# Set default repository configuration if not already set
export GITHUB_REPO_OWNER="${GITHUB_REPO_OWNER:-krkatti-testing}"
export GITHUB_REPO_NAME="${GITHUB_REPO_NAME:-cross-plane-agentic-ai-automation}"

# Note: Set your API keys as environment variables before running this script:
# export OPENAI_API_KEY="your-openai-api-key"
# export GITHUB_TOKEN="your-github-token"

# Start the Flask application
python web_app.py
