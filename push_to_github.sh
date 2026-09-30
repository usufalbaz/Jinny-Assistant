#!/usr/bin/env bash
# Jinny Core - One-Click Git Push Script
# Author: Eng. Yousuf Albaz (AI & Systems Engineer)

set -e

REPO_URL="https://github.com/usufalbaz/Jinny-Assistant.git"

echo "=========================================================="
echo " Jinny Assistant - Deployment Script"
echo " Author: Eng. Yousuf Albaz (AI & Systems Engineer)"
echo "=========================================================="

cd "$(dirname "$0")"

git init
git config user.name "Yousuf Albaz"
git config user.email "usufalbaz@users.noreply.github.com"
git branch -m main

git add -A
git commit -m "Jinny Core: Enterprise Production Release (Jarvis Architecture, IoT, Silent SMS & Persistent Memory)" || true

echo ""
echo "To push to your remote GitHub repository, provide your Personal Access Token:"
read -sp "Enter your GitHub Personal Access Token (or press Enter to use git credentials): " GITHUB_TOKEN
echo ""

if [ -n "$GITHUB_TOKEN" ]; then
    AUTH_URL="https://usufalbaz:${GITHUB_TOKEN}@github.com/usufalbaz/Jinny-Assistant.git"
    git push --force "$AUTH_URL" main
    echo " Successfully pushed to https://github.com/usufalbaz/Jinny-Assistant.git under Yousuf Albaz!"
else
    git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
    git push --force origin main
    echo " Successfully pushed to origin main!"
fi
