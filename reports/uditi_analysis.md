# Uditi's Design Analysis — Sprint 3A
**Files analyzed:** `tests/unit/test_admin.py`, `app/apis/admin.py` (Feature 4 section, lines 134–194)

---

## Task 2: Design Principle Violations

### Violation 1 — Single Responsibility Principle (SRP)
**File:** `tests/unit/test_admin.py`, lines 39–68, method `test_view_members_success`

`test_view_members_success` checks 6 different things in a single test: the status code, the number of members, the first member's name, the first member's email, the second member's name, and the second member's email. SRP says a unit of code should have only one reason to change or one job. A test function should ideally verify one behavior. If any assertion fails, it's harder to tell exactly what broke. Each of these could be a separate focused test.

```python
# lines 62-68 — too many assertions in one test
assert response.status_code == HTTPStatus.OK
members = response.get_json()
assert len(members) == 2
assert members[0]["name"]  == "Alice"
assert members[0]["email"] == "alice@example.com"
assert members[1]["name"]  == "Bob"
assert members[1]["email"] == "bob@example.com"
```

---

### Violation 2 — Modularity Principle
**File:** `tests/unit/test_admin.py`, lines 49–52, 81–83, 103, 138–141

The same mock setup for `ClassResource` is copy-pasted across four different tests. Modularity means breaking code into reusable, independent pieces. Here, instead of writing a shared helper or pytest fixture for this repeated setup, the same block is duplicated four times. If the import path of `ClassResource` changes, every one of these four lines needs to be updated manually.

```python
# Repeated in 4 tests — lines 49, 81, 103, 138
mocker.patch("app.apis.admin.ClassResource").return_value.get_class_by_id.return_value = { ... }
```

---

### Violation 3 — Open/Closed Principle (OCP)
**File:** `app/apis/admin.py`, line 166, method `ClassMemberList.get`

The role check uses a hardcoded list: `if role not in ("trainer", "admin")`. OCP says code should be open for extension but closed for modification — meaning you should be able to add new behavior without editing existing code. If a new role (e.g. `"manager"`) needs access to this endpoint in the future, a developer must open this file and edit this line. A better design might store allowed roles in a config or use a decorator, so you could extend access without touching the method itself.

```python
# app/apis/admin.py line 166
if role not in ("trainer", "admin"):
    return {MSG: "Access restricted to trainers and admins"}, HTTPStatus.FORBIDDEN
```

---

## Task 3: Code Smells

### Smell 1 — Duplicate Code
**File:** `tests/unit/test_admin.py`, lines 49, 81, 103, 138

The `mocker.patch("app.apis.admin.ClassResource")` block is repeated identically across four test functions. This is a classic **Duplicate Code** smell. The fix would be a shared pytest fixture that sets up the mock once and passes it to each test that needs it. Duplicate code means more places to update when things change.

---

### Smell 2 — Magic Strings
**File:** `tests/unit/test_admin.py`, lines 55–58, 60, 86, 105, 121, 143

Hardcoded string literals like `"alice@example.com"`, `"class-1"`, `"555-0001"`, `"nonexistent-id"` are scattered throughout the test file with no named constants. These are **Magic Strings** — their meaning isn't immediately obvious from the value alone, and if the same string is used in multiple places it must be changed everywhere. Defining them as constants at the top of the file would make the tests clearer and easier to maintain.

```python
# examples of magic strings scattered in tests
response = client.get("/admin/class-1/members")       # line 60
response = client.get("/admin/nonexistent-id/members") # line 105
{"contact": "555-0001"}                                # line 57
```

---

### Smell 3 — Long Method
**File:** `app/apis/admin.py`, lines 160–194, method `ClassMemberList.get`

The `get` method is 34 lines long and does five distinct jobs: (1) checks the role, (2) looks up the class, (3) extracts user IDs, (4) fetches user details, (5) formats the response. This is a **Long Method** smell — it should be broken into smaller, named helper methods so each step is easier to read, test, and change independently.

---

### Smell 4 — Comments Explaining a Workaround
**File:** `tests/unit/test_admin.py`, lines 107–108 and 123–124

```python
# Note: @api.marshal_list_with on this endpoint strips response body fields,
# so we only assert the status code here — the 403 itself confirms the error.
```

This is a **Comment Smell** (specifically: a comment that explains why you *can't* do something you'd normally do). Comments like this signal a design problem — the framework behavior is forcing the tests to be less thorough. The comment is a band-aid over a deeper issue rather than a fix.

---

### Smell 5 — Inconsistent Abstraction Level
**File:** `tests/unit/test_admin.py`, lines 23–33 vs. lines 49–52

A helper function `mock_jwt` was created (good!) to avoid repeating the JWT mock setup. But the same pattern was *not* applied to `ClassResource` or `UserResource` mocking, even though those are repeated even more often. This inconsistency is an **Inconsistent Abstraction** smell — the same problem was solved with an abstraction in one case and ignored in another.

---

## Summary for Group Discussion

| # | Type | Principle/Smell | File | Lines |
|---|------|----------------|------|-------|
| 1 | Principle violation | Single Responsibility (SRP) | test_admin.py | 39–68 |
| 2 | Principle violation | Modularity | test_admin.py | 49, 81, 103, 138 |
| 3 | Principle violation | Open/Closed (OCP) | admin.py | 166 |
| 4 | Code smell | Duplicate Code | test_admin.py | 49, 81, 103, 138 |
| 5 | Code smell | Magic Strings | test_admin.py | 55–60, 86, 105 |
| 6 | Code smell | Long Method | admin.py | 160–194 |
| 7 | Code smell | Workaround Comment | test_admin.py | 107–108, 123–124 |
| 8 | Code smell | Inconsistent Abstraction | test_admin.py | 23–33 vs 49–52 |
