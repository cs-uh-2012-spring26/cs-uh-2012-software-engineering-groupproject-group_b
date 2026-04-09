# Design Reflection

## Executive Summary:

### Tools Used:

Visual Studio PyreverseSequence Plugin was used to make an initial sequence diagram for the send class reminder endpoint. This was then edited to incorporate missing lifelines and actors.

## Task 1:

### Sequence Diagram — Send Class Reminder Endpoint

```mermaid
sequenceDiagram
    autonumber

    actor Trainer as Trainer
    participant JWT as flask_jwt_extended
    participant SCR as SendClassReminder
    participant CR as ClassResource
    participant DB as DB
    participant MongoDB as MongoDB
    participant Utils as utils
    participant UR as UserResource
    participant Email as send_class_reminder
    participant Env as OS Environment
    participant SES as AWS SES

    %% Step 1: HTTP Request
    Trainer->>JWT: POST /admin/class_id/remind - Authorization: Bearer token

    %% Step 2: JWT Validation
    JWT->>JWT: Validate JWT signature and expiry
    alt JWT invalid or missing
        JWT-->>Trainer: 401 Unauthorized
    end
    JWT->>SCR: Forward request with claims and identity

    %% Step 3: Role Check
    SCR->>SCR: get_jwt() - check claims role == trainer
    alt role is not trainer
        SCR-->>Trainer: 403 Forbidden - Only trainers can send reminder emails
    end

    %% Step 4: Look Up the Class
    SCR->>CR: get_class_by_id(class_id, str)
    CR->>CR: Convert class_id to ObjectId
    alt class_id is not a valid ObjectId
        CR-->>SCR: None
    end
    CR->>DB: get_collection(classes)
    DB-->>CR: classes Collection
    CR->>MongoDB: find_one by class ObjectId
    MongoDB-->>CR: class_doc or None
    CR->>Utils: serialize_item(class_doc)
    Utils-->>CR: class_doc with _id converted to string
    CR-->>SCR: fitness_class dict or None

    alt fitness_class is None
        SCR-->>Trainer: 404 Not Found - Class not found
    end

    %% Step 5: Trainer Ownership Check
    SCR->>SCR: get_jwt_identity() - get trainer_identity
    SCR->>SCR: check fitness_class trainer_id == trainer_identity
    alt trainer is not assigned to this class
        SCR-->>Trainer: 403 Forbidden - You are not the trainer assigned to this class
    end

    %% Step 6: Fetch Enrolled Members
    SCR->>SCR: Read user_oids from fitness_class user_ids
    alt user_oids is empty
        SCR-->>Trainer: 200 OK - No members enrolled
    end

    SCR->>UR: get_users_by_ids(user_oids)
    UR->>DB: get_collection(users)
    DB-->>UR: users Collection
    UR->>MongoDB: find users by ObjectId list
    MongoDB-->>UR: list of user docs
    UR->>Utils: serialize_items(user_docs)
    Utils-->>UR: list of user dicts with _id converted to string
    UR-->>SCR: members list

    %% Step 7: Send Reminder to Each Member
    loop for each member in members
        SCR->>Email: send_class_reminder(member_email, member_name, class_info)

        Email->>Env: _get_env(SES_SENDER_EMAIL)
        Env-->>Email: sender email string
        Email->>Env: _get_env(AWS_SES_REGION)
        Env-->>Email: AWS region string
        Email->>Env: _get_env(AWS_ACCESS_KEY_ID)
        Env-->>Email: access key string
        Email->>Env: _get_env(AWS_SECRET_ACCESS_KEY)
        Env-->>Email: secret key string

        alt any env var is missing or blank
            Email-->>SCR: raises EnvironmentError
        end

        Email->>SES: boto3.client(ses, region, key_id, secret_key)
        SES-->>Email: ses_client

        Email->>Email: Format date_str, start_str, end_str from class_info
        Email->>Email: Build subject and plain-text body

        Email->>SES: ses_client.send_email(Source, Destination, Message)

        alt email sent successfully
            SES-->>Email: success response
            Email-->>SCR: True, empty string
            SCR->>SCR: append email to successes list
        else SES ClientError
            SES-->>Email: ClientError exception
            Email-->>SCR: False, error_message
            SCR->>SCR: append email and error to failures list
        end
    end

    %% Step 8: Return Summary
    SCR-->>Trainer: 200 OK - Reminders processed: X sent, Y failed with sent_to and failed lists
```

---

## Task 2: Design Principle Violations

<<<<<<< HEAD

### Violation 1 — Open/Closed Principle (OCP)

**Principle:** Software entities should be open for extension but closed for modification.

**Location:**

- `app/email.py`, `send_class_reminder()`, lines 16–83
  ![send_class_reminder() — app/email.py lines 16–83](assets/violation_1.png)
- `app/apis/admin.py`, `SendClassReminder.post()`, line 21 (import) and lines 263–267 (call site)
  SendClassReminder.post() call site — app/apis/admin.py lines 263–267

**Explanation:**
The entire notification pipeline is hardwired to a single delivery mechanism: AWS SES email. There is no abstraction or extension point. If Feature 7 (Configure Notifications) requires adding SMS or Telegram, a developer would have to:

- Modify `send_class_reminder()` or write a parallel function
- Modify `SendClassReminder.post()` to conditionally call the right channel

This is a direct violation of OCP. A well-designed system would define a `NotificationService` abstraction (e.g., a protocol or abstract base class with a `send()` method), with `SESEmailNotifier` as one concrete implementation. The `SendClassReminder` handler would depend on the abstraction and new channels could be added without touching existing code.

---

## Task 3: Code Smells

### Code Smell 1 — Duplicate Code

**Location:** `app/db/users.py`, `register_member()` lines 140–169:

register_member() — app/db/users.py lines 140–169

`register_trainer()` lines 200–228

register_trainer() — app/db/users.py lines 200–228

**Explanation:**
The body of both methods is virtually identical line-for-line. This is a classic **Duplicate Code** smell. The duplicated block spans password validation, email uniqueness checking, password hashing, document construction, and database insertion. The shared logic should be extracted into a single private helper method parameterised by role, eliminating the duplication and making future changes to registration logic require a single edit.

---

## Task 4: Reflection on New Features

### Feature 7 — Configure Notifications

- As violation 1 in task 2 says, the OCP violation in `app/email.py` and `app/apis/admin.py` mean there is no abstraction to extend: the reminder endpoint is hardwired to call one concrete function that delivers one type of notification via one provider. Adding a second channel (SMS, for example) means either bloating `SendClassReminder.post()` with conditional dispatch logic or duplicating the entire endpoint. A `NotificationService` protocol with channel-specific implementations would need to be designed from scratch, and the existing code restructured around it before Feature 7 can be implemented in a maintainable way.
