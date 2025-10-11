# Git Workflow for Spark MCP Server

## Quick Reference

### Before Starting Work
```bash
# Back up current state
./backup.sh
```

### After Successful Changes
```bash
# Commit with meaningful message
git add .
git commit -m "feat: Added X feature - description"
git push origin main

# Tag if it's a stable version
./tag-working.sh 1.5.3
```

### If Something Breaks
```bash
# See all working versions
./rollback.sh

# Roll back to specific version
./rollback.sh v1.5.2-working
```

## Branching Strategy

### For Experimental Features
```bash
git checkout -b feature/new-analytics-tool
# work on feature
git add . && git commit -m "feat: New analytics tool"

# If it works
git checkout main
git merge feature/new-analytics-tool
git branch -d feature/new-analytics-tool

# If it doesn't work
git checkout main
git branch -D feature/new-analytics-tool  # Delete branch
```

### For Bug Fixes
```bash
git checkout -b fix/team-members-endpoint
# fix the bug
git add . && git commit -m "fix: Team members endpoint now returns data"

# Test it thoroughly
# If working, merge to main
git checkout main
git merge fix/team-members-endpoint
```

## Git Aliases Available

- `git save` - Quick save current state with timestamp
- `git working` - List all working tagged versions
- `git branches` - Show all branches
- `git unstage` - Unstage files
- `git last` - Show last commit details

## Commit Message Format

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

Examples:
```bash
git commit -m "feat: Added pagination to search_contacts tool"
git commit -m "fix: Interaction type enrichment now works correctly"
git commit -m "docs: Updated API documentation for new endpoints"
```

## Never Lose Your Work

The three magic commands:
1. `./backup.sh` - Before starting anything risky
2. `./tag-working.sh X.Y.Z` - When everything works perfectly
3. `./rollback.sh vX.Y.Z-working` - When you need to go back

## Emergency Recovery

If you accidentally deleted something:
```bash
# See recent commits
git reflog

# Recover from any point in history
git reset --hard HEAD@{5}
```
