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
