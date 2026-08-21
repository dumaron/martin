---
name: pr-review
description: Critically review the current branch's changes and post the findings as individual inline comments on its GitHub PR. Use when asked to review a branch/PR and leave comments on GitHub.
---

# PR review

Review the current branch critically, then publish each finding as its **own inline comment** on the PR, anchored to the exact line it concerns. No essay, no summary dump.

## 1. Get the diff

```bash
git fetch origin main --quiet
git diff origin/main...HEAD                 # changes introduced by this branch
gh pr view --json number,title,body,headRefOid,url
```

If no PR exists, stop and say so — do not open one.

Read the **full files** around non-trivial hunks, not just the diff context: most real problems live in the interaction between new code and code that didn't change.

## 2. Review critically

Be a demanding reviewer, not a cheerleader. Look for, in rough priority order:

- **Correctness** — wrong logic, off-by-one, unhandled `None`/empty case, wrong timezone/date handling, mutation of shared state.
- **Django-specific** — N+1 queries (missing `select_related`/`prefetch_related`), missing/duplicate migration, `null=True` on a `CharField`, queries in templates, unindexed lookups, transactions missing around multi-write flows, forms/views trusting unvalidated input.
- **Regressions** — call sites, templates, and tests that the change silently breaks.
- **Design** — logic in the wrong layer (business logic in views/templates instead of models/services), duplicated code, an abstraction that doesn't pay for itself.
- **Project conventions** (`CLAUDE.md`) — `lmap` & friends from `core.utils.fp` over comprehensions/loops when mapping, template partials named `partial_*.html`, no gratuitous comments, `ruff format` clean.
- **Tests** — behaviour changed but no existing test covers it.

Rules for what you post:

- One comment = one concrete, actionable point. Never batch unrelated points into one comment.
- Say what is wrong, why it matters, and what to do instead. Two or three sentences.
- Include a ` ```suggestion ` block whenever the fix is a small, mechanical edit — it makes the comment one-click applicable.
- Skip pure style nits that `ruff` already enforces, and skip praise.
- If you are not sure something is a real problem, phrase it as a question rather than dropping it or asserting it.
- Verify each finding against the actual file before posting. A confidently wrong comment costs more than a missed one.

## 3. Post the comments

Batch every finding into a single review request — each entry still renders as an individual inline comment, and the author gets one notification instead of twenty.

```bash
PR=$(gh pr view --json number -q .number)
SHA=$(gh pr view --json headRefOid -q .headRefOid)
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

REVIEW=$(mktemp -t pr-review)
cat > "$REVIEW" <<'JSON'
{
  "commit_id": "SHA_PLACEHOLDER",
  "event": "COMMENT",
  "comments": [
    {
      "path": "core/models/bank_transaction.py",
      "line": 42,
      "side": "RIGHT",
      "body": "`amount` can be `None` here when the CSV column is blank, so this raises `TypeError`. Guard before the arithmetic.\n\n```suggestion\n    amount = row.get(\"amount\") or Decimal(0)\n```"
    },
    {
      "path": "apps/website/pages/some_page.py",
      "start_line": 10,
      "line": 14,
      "side": "RIGHT",
      "body": "This loops the queryset and hits the DB per row — add `select_related(\"account\")` to the base queryset."
    }
  ]
}
JSON
sed -i.bak "s/SHA_PLACEHOLDER/$SHA/" "$REVIEW"

gh api "repos/$REPO/pulls/$PR/reviews" -X POST --input "$REVIEW"
```

- `event` must be `COMMENT`. Never use `APPROVE` or `REQUEST_CHANGES` unless the user explicitly asks for it.
- `line` is the line number **in the file's new version**; use `start_line` + `line` for a range, and `"side": "LEFT"` with the old line number to comment on a deleted line.
- **A commented line must appear in the PR diff** (a changed line, or within GitHub's few lines of surrounding context). Anchoring outside the diff returns `422 Unprocessable Entity`. If a finding is about untouched code, anchor it to the nearest changed line and name the real location in the body.
- Write the body via the JSON file, not `-f body=...` — that mangles newlines and backticks.
- A one-off standalone comment (outside a review) is `gh api "repos/$REPO/pulls/$PR/comments" --input file.json` with `commit_id`, `path`, `line`, `side`, `body`.

If a finding genuinely belongs to no line — a missing migration, an architectural objection to the whole PR — post it as a single top-level comment with `gh pr comment $PR --body-file`, and keep it to one.

## 4. Report back

Tell the user, in a few lines: how many comments were posted, the PR URL, and anything you deliberately did not post (uncertain, out of diff range, or rejected as a nit).
