#!/usr/bin/env bash
set -euo pipefail

ISSUES=(4 5 6 7 8 9 10 11)

PROMPT_TEMPLATE='Implement GitHub issue #ISSUE_NUM from this repository.

Steps to follow:
1. Read the issue with: gh issue view ISSUE_NUM
2. Implement all requirements described in the issue. Use the existing codebase structure and conventions.
3. After implementation is complete and working, commit all changes with a descriptive commit message referencing the issue (e.g. "feat: ... closes #ISSUE_NUM").
4. Write a documentation file at Documentation/issue-ISSUE_NUM-<short-slug>.md that covers:
   - Feature description (what was built and why)
   - Architecture decisions (how it fits into the existing stack)
   - Stack / technologies used
   - Key files changed or created
5. Commit the documentation file as well.
6. Close the issue with: gh issue close ISSUE_NUM

Do not ask for confirmation at any step — complete all steps autonomously.'

for n in "${ISSUES[@]}"; do
  echo ""
  echo "============================================"
  echo "  Starting issue #$n"
  echo "============================================"

  PROMPT="${PROMPT_TEMPLATE//ISSUE_NUM/$n}"

  claude --dangerously-skip-permissions -p "$PROMPT"

  echo ""
  echo "  Issue #$n done."
done

echo ""
echo "All issues implemented."
