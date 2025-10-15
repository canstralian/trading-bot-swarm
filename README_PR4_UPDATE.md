# How to Apply PR #4 Updates

This document explains how to use the `PR4_UPDATE_PROPOSAL.md` file to update Pull Request #4.

## Overview

The `PR4_UPDATE_PROPOSAL.md` file contains the complete specifications for updating PR #4's title and body. Since direct programmatic updates to PR descriptions require elevated permissions, this proposal file serves as a reference for applying the updates.

## What's Included

The proposal document provides:

1. **Current State Analysis**: Documents PR #4's current title, status, and purpose
2. **Proposed Title**: The new title without the `[WIP]` tag
3. **Proposed Body**: A comprehensive, well-formatted PR description including:
   - Executive summary of the runbook implementation
   - Detailed deployment checklist covering all phases
   - What's included in each section
   - Benefits of the runbook
   - File changes summary
   - Links to related documentation

## How to Apply the Updates

### Option 1: Manual Update via GitHub UI

1. Navigate to PR #4: https://github.com/canstralian/trading-bot-swarm/pull/4
2. Click the "Edit" button next to the PR title
3. Copy the new title from `PR4_UPDATE_PROPOSAL.md` (line 11-13)
4. Click "Edit" next to the PR description
5. Copy the new body content from `PR4_UPDATE_PROPOSAL.md` (lines 18-132)
6. Save the changes

### Option 2: Using GitHub CLI (gh)

If you have the GitHub CLI installed with appropriate permissions:

```bash
# Update the title
gh pr edit 4 --title "Add production deployment runbook to docs directory"

# Update the body (using the content from the proposal file)
gh pr edit 4 --body "$(sed -n '/^## Production Deployment Runbook Implementation/,/^```$/p' PR4_UPDATE_PROPOSAL.md | sed '1d;$d')"
```

### Option 3: Using GitHub API

For automation via GitHub API (requires appropriate authentication):

```bash
# Set your GitHub token
GITHUB_TOKEN="your_token_here"

# Update PR title and body
curl -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/canstralian/trading-bot-swarm/pulls/4 \
  -d @- <<'EOF'
{
  "title": "Add production deployment runbook to docs directory",
  "body": "... [content from PR4_UPDATE_PROPOSAL.md] ..."
}
EOF
```

## Verification

After applying the updates, verify that:

1. ✅ The PR title no longer contains `[WIP]`
2. ✅ The PR body includes the comprehensive deployment checklist
3. ✅ All sections are properly formatted with Markdown
4. ✅ The checklist items are visible and properly marked as complete
5. ✅ The benefits and what's included sections are clear

## Benefits of the Updated PR Description

The new PR description provides:

- **Clear Context**: Explains what the runbook is and why it's valuable
- **Comprehensive Checklist**: Shows all deployment phases at a glance
- **Detailed Breakdown**: Describes each section of the runbook
- **Visual Indicators**: Uses emojis and formatting for better readability
- **Status Clarity**: Clearly indicates the work is complete and ready for review

## Questions or Issues?

If you encounter any issues applying the updates or have questions about the proposal:

1. Review the `PR4_UPDATE_PROPOSAL.md` file for the complete specifications
2. Check the original PR #4 to understand the context
3. Refer to the runbook file: `docs/PRODUCTION_DEPLOYMENT_RUNBOOK.md`

---

**Note**: This update proposal is part of PR #6, which was created to provide the updated content for PR #4. Once PR #4 is updated, PR #6 can be merged or closed as completed.
