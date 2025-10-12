# Learnings

This document captures important lessons learned during development to avoid repeating mistakes and to share knowledge.

---

## 2025-10-10: Django URL Trailing Slash and POST Redirects

### Problem
Form submission with POST method resulted in a 405 (Method Not Allowed) error, even though the view was decorated with `@require_POST`.

### Root Cause
Django's `APPEND_SLASH` setting (enabled by default) causes the following behavior:
1. POST request sent to URL without trailing slash: `/link-duplicate-bank-transactions`
2. Django's CommonMiddleware performs a **301 redirect** to add the trailing slash: `/link-duplicate-bank-transactions/`
3. The redirect changes the HTTP method from POST to GET
4. The GET request hits the `@require_POST` decorated view
5. Result: 405 Method Not Allowed

### Solution
Ensure URL patterns match the form action URLs by adding trailing slashes consistently:

```python
# ❌ Wrong - no trailing slash
path('flows/pair-transactions/link-duplicate-bank-transactions', view, name='...'),

# ✅ Correct - with trailing slash
path('flows/pair-transactions/link-duplicate-bank-transactions/', view, name='...'),
```

### Additional Issues Found
1. **Parameter mismatch**: Template and view must use matching POST parameter names
2. **Wrong request dict**: POST views should use `request.POST.get()`, not `request.GET.get()`

### Takeaway
- Always add trailing slashes to URL patterns for consistency with Django's default behavior
- Use the `{% url %}` template tag to generate URLs - it will automatically add the trailing slash
- Test form submissions early to catch these routing issues

---

## 2025-10-12: Django QuerySet Performance - Avoiding Duplicate Query Execution

### Problem
A Django QuerySet was being executed twice: once in an `.exclude(id__in=queryset)` clause and again when iterating over the same QuerySet in a template. This resulted in redundant database queries.

### Root Cause
Django QuerySets are lazy-evaluated and don't cache their results automatically. When a QuerySet is used in multiple contexts:
1. First use in `.exclude(id__in=same_amount_suggestions)` triggers database execution to get IDs for the subquery
2. Second use in template iteration `{% for transaction in same_amount_suggestions %}` triggers another database execution
3. Django doesn't recognize that the same QuerySet was already evaluated, leading to duplicate queries

### Solution
Evaluate the QuerySet once into a list, then reuse that list for both purposes:

```python
# Before: QuerySet used twice (2 database queries)
same_amount_suggestions = YnabTransaction.objects.filter(
    deleted=False,
    amount=first_unpaired_bank_transaction.amount,
    cleared=YnabTransaction.ClearedStatuses.UNCLEARED,
    budget_id=budget_id,
)
similar_date_suggestions = YnabTransaction.objects.filter(...).exclude(
    id__in=same_amount_suggestions  # Query #1
)
# Template: {% for transaction in same_amount_suggestions %}  # Query #2

# After: Evaluate once, reuse list (1 database query)
same_amount_suggestions = list(YnabTransaction.objects.filter(
    deleted=False,
    amount=first_unpaired_bank_transaction.amount,
    cleared=YnabTransaction.ClearedStatuses.UNCLEARED,
    budget_id=budget_id,
))
similar_date_suggestions = YnabTransaction.objects.filter(...).exclude(
    id__in=[s.id for s in same_amount_suggestions]  # Uses in-memory list
)
# Template gets the already-evaluated list (no additional query)
```

### Takeaway
- Be aware of Django's lazy QuerySet evaluation when the same QuerySet is used multiple times
- For small result sets, converting to `list()` can improve performance by avoiding duplicate queries
- Use `list(queryset)` when you need to reuse the same data in multiple places
- This pattern is most beneficial when result sets are small (dozens of records, not thousands)
- Monitor query counts during development to identify these optimization opportunities

---

## Template for Future Learnings

```markdown
## YYYY-MM-DD: Brief Title

### Problem
[What went wrong or what issue was encountered]

### Root Cause
[Why it happened - technical explanation]

### Solution
[How it was fixed]

### Takeaway
[Key lessons to remember]
```
