# My Fixes — Where to Find Them in the Code
### Uditi's Violations & Code Smells: Before → After

> **How to use this:** Open each file in your editor as you read. The line numbers tell you exactly where to look. For the "before" code — that file (`app/apis/admin.py`, `tests/unit/test_admin.py`) **no longer exists** in Sprint 3B. That's intentional — it was deleted and replaced.

---

## FIX 1 — Violation 5: Open/Closed Principle (OCP)

### What was wrong (the "before")

**File that no longer exists:** `app/apis/admin.py`, `ClassMemberList.get()`, line ~166

The role check was hardcoded directly inside the method body:

```python
# BEFORE — inside ClassMemberList.get() in admin.py
claims = get_jwt()
role = claims.get("role")
if role not in ("trainer", "admin"):
    return {"message": "Only trainers can view member lists"}, 403
```

**Why it's a problem:** That `("trainer", "admin")` list is buried inside the function. Every endpoint in `admin.py` had its own copy of this check. To add a new role, you'd open this file and edit each one manually.

---

### What was fixed (the "after")

**Step 1 — A reusable decorator was created**

**File:** `app/services/auth.py` — open this file

```
Line 4:  def jwt_required_with_role(*allowed_roles):   ← the general-purpose inner function
Line 14:     if user_role not in allowed_roles:         ← the role check, defined ONCE
Line 15:         return {"message": "..."}, 403         ← returns 403 if wrong role
Line 22: def trainer_required(fn):                     ← trainer-only decorator
Line 23:     return jwt_required_with_role("trainer")(fn)
Line 25: def member_required(fn):                      ← trainers + members decorator
Line 26:     return jwt_required_with_role("trainer", "member")(fn)
```

Think of `trainer_required` like a lock you can put on any door. You define the lock once. You don't rebuild a new lock for each door.

**Step 2 — The decorator is used on every protected endpoint**

**File:** `app/apis/classes.py` — open this file

```
Line 166: @trainer_required          ← this runs FIRST before ClassList.post()
Line 215: @trainer_required          ← this runs FIRST before ClassDetail.get()
Line 248: @trainer_required          ← this runs FIRST before SendClassReminder.post()
```

**How to explain it in the exam:**

> "In Sprint 3A, I found an OCP violation in `admin.py` — the role check was hardcoded as `if role not in ('trainer', 'admin')` inside the method. In Sprint 3B, we extracted that into a `@trainer_required` decorator in `app/services/auth.py` at line 22. Now every endpoint that needs trainer access just puts `@trainer_required` on top — you can see it at line 166 in `classes.py`. To add a new role, you only change the decorator in one place — you never touch the endpoint methods. That satisfies OCP: the endpoints are closed for modification, the auth system is open for extension."

---

## FIX 2 — Violation 6: Modularity (Duplicate Mock Setup)

### What was wrong (the "before")

**File that no longer exists:** `tests/unit/test_admin.py`, lines 49, 81, 103, 138

The same mock setup code was copy-pasted into four different test functions:

```python
# BEFORE — this exact block appeared 4 separate times in test_admin.py
mocker.patch(
    "app.apis.admin.ClassResource",
    return_value=MagicMock(...)
)
```

**Why it's a problem:** This is low modularity — the same thing defined four times. If the import path of `ClassResource` changed, you'd have to hunt down all four copies and update each one.

---

### What was fixed (the "after")

**A shared fixture was created, defined once, used everywhere.**

**File:** `tests/unit/conftest.py` — open this file

```
Line 39-44:  def trainer_token(app):       ← creates a trainer JWT once, reused in any test
Line 47-53:  def member_token(app):        ← creates a member JWT once, reused in any test
Line 71-83:  def seeded_class(client, trainer_token):  ← creates a real class in the DB once
```

A **pytest fixture** is a function decorated with `@pytest.fixture`. Instead of copy-pasting setup code into every test, you declare the fixture once in `conftest.py`. Any test file in the same folder can use it just by listing it as a parameter in the test function.

**Example — how a test uses the fixture without any setup code:**

**File:** `tests/unit/test_view_member_list.py`, line 82

```python
# AFTER — no setup code needed, trainer_token fixture is injected automatically
def test_view_members_class_not_found(client, trainer_token):
    response = client.get(
        "/classes/random_class_id/members",
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
```

`trainer_token` is not defined in this test — it comes from `conftest.py` automatically. That's the fix. One definition, used in any test across the whole test suite.

**How to explain it in the exam:**

> "In Sprint 3A, I identified a Modularity violation in `test_admin.py` — the same `mocker.patch` setup for `ClassResource` was copy-pasted at lines 49, 81, 103, and 138. In Sprint 3B, we removed that duplication entirely. The test setup was moved to `conftest.py`, which you can see at line 39 for `trainer_token` and line 71 for `seeded_class`. Any test can now use these fixtures just by listing them as parameters — you can see that at line 82 in `test_view_member_list.py`. One definition, no duplication."

---

## FIX 3 — Code Smell 6: Magic Strings

### What was wrong (the "before")

**File that no longer exists:** `tests/unit/test_admin.py`, lines 60, 86, 121, 143

The URL was hardcoded as a raw string in four places:

```python
# BEFORE — appeared 4 separate times in test_admin.py
response = client.get("/admin/class-1/members", headers=...)
```

**Why it's a problem:** `"/admin/class-1/members"` and `"class-1"` are magic — there's no explanation of where they came from. If the URL structure changed (which it did — it's now `/classes/<id>/members`), you'd have to find and fix all four copies manually.

---

### What was fixed (the "after")

**Dynamic variables replace hardcoded strings.**

**File:** `tests/unit/test_view_member_list.py` — open this file

```
Line 72-78:  test_view_members_forbidden_for_member_role(client, member_token, seeded_members_class)
Line 73:         f"/classes/{seeded_members_class}/members"    ← dynamic, not hardcoded
```

```
Line 82-89:  test_view_members_class_not_found(client, trainer_token)
Line 84:         "/classes/random_class_id/members"           ← descriptive name, not "class-1"
```

```
Line 92-99:  test_view_members_empty(client, trainer_token, empty_members_class)
Line 94:         f"/classes/{empty_members_class}/members"    ← dynamic fixture ID
```

```
Line 102-117: test_view_members_returns_enrolled_members(client, trainer_token, seeded_members_class)
Line 104:         f"/classes/{seeded_members_class}/members"  ← dynamic fixture ID
```

**The key difference:**
- Before: `"/admin/class-1/members"` — a mystery string no one can trace
- After: `f"/classes/{seeded_members_class}/members"` — `seeded_members_class` is a fixture that creates a real class and returns its actual ID. The URL is built from that real ID.

The class ID is never hardcoded. The URL structure is never duplicated.

**How to explain it in the exam:**

> "In Sprint 3A, I identified a Magic Strings smell in `test_admin.py` — the URL `/admin/class-1/members` was hardcoded at lines 60, 86, 121, and 143. In Sprint 3B, the tests were rewritten to use dynamic fixture IDs. You can see in `test_view_member_list.py` at line 73, the URL is built as `f'/classes/{seeded_members_class}/members'` — where `seeded_members_class` is a fixture that creates a real class and returns its database ID. Nothing is hardcoded. If the URL structure changes, you only update the fixture, not every test."

---

## FIX 4 — Code Smell 7: Long Method

### What was wrong (the "before")

**File that no longer exists:** `app/apis/admin.py`, `ClassMemberList.get()`, lines 160–194 (34 lines)

The method did five completely separate jobs all in one place:

```python
# BEFORE — all of this was inside one get() method in admin.py
# Job 1: Check the role
claims = get_jwt()
role = claims.get("role")
if role not in ("trainer", "admin"):
    return ..., 403

# Job 2: Look up the class
fitness_class = class_resource.get_class_by_id(class_id)
if not fitness_class:
    return ..., 404

# Job 3: Extract user IDs from the class
user_oids = fitness_class.get("user_ids", [])

# Job 4: Fetch full user details for each ID
members = user_resource.get_users_by_ids(user_oids)

# Job 5: Format the response
result = [{"name": m["name"], "email": m["email"]} for m in members]
return result, 200
```

**Why it's a problem:** 34 lines, 5 different reasons to change the method. It's hard to read, hard to test, and dangerous to edit.

---

### What was fixed (the "after")

**The 5 jobs were split across 3 layers. Each layer has one job.**

---

#### Layer 1 — The Decorator handles the role check (Job 1)

**File:** `app/services/auth.py`, line 22–23

```python
def trainer_required(fn):
    return jwt_required_with_role("trainer")(fn)
```

The role is checked here before the endpoint even runs. The endpoint never touches JWT claims.

---

#### Layer 2 — The API endpoint is now 5 lines (was 34)

**File:** `app/apis/classes.py`, lines 205–230 — open this file

```
Line 205: @api.route("/<class_id>/members")
Line 207: class ClassDetail(Resource):
Line 211:     def __init__(self, api=None):
Line 212:         super().__init__(api)
Line 213:         self.class_template = StandardMemberAccess()   ← delegate to service
Line 215:     @trainer_required                                   ← role check handled here
Line 221:     def get(self, class_id):
Line 223:         members, error = self.class_template.get_enrolled_members(class_id)
Line 224:         if error:
Line 225:             return {MSG: error}, HTTPStatus.NOT_FOUND
Line 227:         if not members:
Line 228:             return []
Line 230:         return members
```

The endpoint now has ONE job: receive the request, call the service, return the result. It knows nothing about MongoDB, user IDs, or formatting.

---

#### Layer 3 — The service layer does the real work (Jobs 2, 3, 4, 5)

**File:** `app/services/templates/member_access_template.py`, lines 8–20

```
Line 8:  def get_enrolled_members(self, class_id):
Line 11:     fitness_class = self.find_class(class_id)   ← Job 2: look up the class
Line 12:     if not fitness_class:
Line 13:         return None, "Class not found"
Line 15:     member_ids = self.extract_member_ids(fitness_class)  ← Job 3: get IDs
Line 16:     if not member_ids:
Line 17:         return [], None
Line 19:     members = self.fetch_members(member_ids)     ← Job 4: fetch users
Line 20:     return self.format_members(members), None    ← Job 5: format response
```

**File:** `app/services/templates/standard_member_access.py`, lines 7–17

```
Line 8:  def find_class(self, class_id):       ← implements Job 2 with MongoDB
Line 12: def extract_member_ids(self, fitness_class):  ← implements Job 3
Line 15: def fetch_members(self, member_ids):   ← implements Job 4 with MongoDB
```

**How the layers connect:**

```
Request comes in
    → @trainer_required checks JWT role           (app/services/auth.py)
    → ClassDetail.get() calls get_enrolled_members (app/apis/classes.py)
    → MemberAccessTemplate runs the steps          (member_access_template.py)
    → StandardMemberAccess fills in the MongoDB details (standard_member_access.py)
    → Response goes back
```

**How to explain it in the exam:**

> "In Sprint 3A, I identified a Long Method smell in `admin.py` — `ClassMemberList.get()` was 34 lines doing five different jobs: role checking, class lookup, ID extraction, user fetching, and formatting.

> In Sprint 3B, we split those five jobs across separate layers using the Template Method pattern. You can see in `classes.py` at line 223, the endpoint now just calls `self.class_template.get_enrolled_members(class_id)` — that's it, one line. The actual work is in `member_access_template.py` — look at lines 8 to 20, it defines the steps: find class, extract IDs, fetch members, format. The MongoDB-specific implementation is in `standard_member_access.py`. The role check is handled by `@trainer_required` at line 215. Each piece has exactly one job now."

---

## Quick Reference: Where Everything Moved

| What was wrong | Old location (deleted) | Fixed location |
|---|---|---|
| Hardcoded role check `if role not in (...)` | `app/apis/admin.py` line 166 | `app/services/auth.py` lines 22–23 + used via `@trainer_required` in `classes.py` |
| Duplicate mock setup × 4 | `tests/unit/test_admin.py` lines 49, 81, 103, 138 | `tests/unit/conftest.py` lines 39–44, 71–83 |
| Hardcoded URL `"/admin/class-1/members"` × 4 | `tests/unit/test_admin.py` lines 60, 86, 121, 143 | `tests/unit/test_view_member_list.py` lines 73, 84, 94, 104 (dynamic f-strings) |
| 34-line method doing 5 jobs | `app/apis/admin.py` lines 160–194 | Split: `classes.py` lines 205–230 + `member_access_template.py` lines 8–57 + `standard_member_access.py` lines 7–17 |
