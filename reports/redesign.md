
## Class Diagram

The following class diagram reflects the refactored system for Sprint 3B.

```mermaid
classDiagram


class Resource {
    <<external>>
}

%% API Layer 
class Register {
    -registration_template: StandardRegistration
    +__init__(api)
    +post() tuple
}

class Login {
    +post() tuple
}

class ClassBooking {
    +post(class_id) tuple
}

class UserEnrolledClasses {
    +get() tuple
}

class MemberNotificationPrefs {
    +put() tuple
}

class ClassList {
    -class_template: StandardClassCreation
    -recurring_template: RecurringClassCreation
    +__init__(api)
    +post() tuple
    +get() tuple
}

class ClassDetail {
    -class_template: StandardMemberAccess
    +__init__(api)
    +get(class_id) tuple
}

class SendClassReminder {
    -member_access: StandardMemberAccess
    +__init__(api)
    +post(class_id) tuple
}

Resource <|-- Register : inherits
Resource <|-- Login : inherits
Resource <|-- ClassBooking : inherits
Resource <|-- UserEnrolledClasses : inherits
Resource <|-- MemberNotificationPrefs : inherits
Resource <|-- ClassList : inherits
Resource <|-- ClassDetail : inherits
Resource <|-- SendClassReminder : inherits

%% Registration Template Pattern
class RegistrationTemplate {
    <<abstract>>
    +register(request_data) tuple
    +extract_input(data) tuple
    +validate_required(name, email, password, role) str
    +validate_role(role) str
    +email_exists(email) bool
    +after_registration(user_id, name, email, role) None
    +validate_password(password)* str
    +create_user(name, email, password, role)* str
}

class StandardRegistration {
    +validate_password(password) str
    +create_user(name, email, password, role) str
    +after_registration(user_id, name, email, role) None
}

RegistrationTemplate <|-- StandardRegistration : inherits

%%Class Creation Template  
class ClassCreationTemplate {
    <<abstract>>
    +create_class(data, trainer_id) tuple
    +validate_capacity(data) str
    +validate_time(data) str
    +validate_date(data) str
    +parse_datetime(data) tuple
    +class_document(data, trainer_id, start_dt, end_dt)* dict
    +save_class(class_doc)* str
}

class StandardClassCreation {
    +class_document(data, trainer_id, start_dt, end_dt) dict
    +save_class(class_doc) str
}

class RecurringClassCreation {
    +MAX_OCCURRENCES: int
    +class_document(data, trainer_id, start_dt, end_dt) dict
    +save_class(class_doc) str
    +save_recurring_classes(class_doc, occurrence_dates) list
    +create_recurring_class(data, trainer_id) tuple
}

ClassCreationTemplate <|-- StandardClassCreation : inherits
ClassCreationTemplate <|-- RecurringClassCreation : inherits

%% Member Access Template 
class MemberAccessTemplate {
    <<abstract>>
    +get_enrolled_members(class_id) tuple
    +get_enrolled_members_with_class(class_id) tuple
    +format_members(members) list
    +find_class(class_id)* dict
    +extract_member_ids(fitness_class)* list
    +fetch_members(member_ids)* list
}

class StandardMemberAccess {
    +find_class(class_id) dict
    +extract_member_ids(fitness_class) list
    +fetch_members(member_ids) list
}

MemberAccessTemplate <|-- StandardMemberAccess : inherits

%%  Notification Strategy 
class NotificationService {
    <<abstract>>
    +_build_message(member_name, class_info) dict
    +send(member, class_info)* tuple
}

class EmailNotificationService {
    +send(member, class_info) tuple
}

class TelegramNotificationService {
    +send(member, class_info) tuple
}

class NotificationDispatcher {
    -_DEFAULT_PREFS: dict
    -_SERVICE_REGISTRY: dict
    +dispatch_to_member(member, class_info) tuple
}

NotificationService <|-- EmailNotificationService : inherits
NotificationService <|-- TelegramNotificationService : inherits
NotificationDispatcher --> EmailNotificationService : uses
NotificationDispatcher --> TelegramNotificationService : uses

%% Database Layer
class DB {
    <<singleton>>
    -_db: Database
    +init_app(app)$ None
    +get_collection(collection_name)$ Collection
}

class UserResource {
    -collection: Collection
    -classes_collection: Collection
    +get_user_by_id(user_id) dict
    +get_user_by_email(email) dict
    +get_users_by_ids(user_ids) list
    +register_user(name, email, password, role) tuple
    +authenticate_user(email, password) tuple
    +add_class_to_user(user_id, class_id) bool
    +get_classes_by_user_id(user_id) list
    +update_notification_prefs(user_id, update_fields) tuple
}

class ClassResource {
    -collection: Collection
    +create_class(class_data) ObjectId
    +create_recurring_classes(base_data, occurrence_dates) list
    +get_all_upcoming_classes() list
    +get_class_by_id(class_id) dict
    +add_user_to_class(class_id, user_id) str
}

UserResource --> DB : uses
ClassResource --> DB : uses

%% MongoDB Document Models
class User {
    <<document>>
    +_id: ObjectId
    +name: str
    +email: str
    +role: str
    +password_hash: str
    +class_ids: list
    +notification_prefs: dict
    +telegram_chat_id: str
}

class FitnessClass {
    <<document>>
    +_id: ObjectId
    +name: str
    +date: str
    +start_time: str
    +end_time: str
    +capacity: int
    +trainer_id: str
    +user_ids: list
    +recurrence_group_id: str
}

UserResource --> User : manages
ClassResource --> FitnessClass : manages
User "1" --> "*" FitnessClass : enrolled in

%%API to Service Dependencies
Register --> StandardRegistration : uses
Login --> UserResource : uses
ClassList --> StandardClassCreation : uses
ClassList --> RecurringClassCreation : uses
ClassDetail --> StandardMemberAccess : uses
SendClassReminder --> StandardMemberAccess : uses
SendClassReminder --> NotificationDispatcher : uses
ClassBooking --> UserResource : uses
ClassBooking --> ClassResource : uses
UserEnrolledClasses --> UserResource : uses
MemberNotificationPrefs --> UserResource : uses

%% Service to Data Access Object Dependencies 
StandardRegistration --> UserResource : uses
StandardClassCreation --> ClassResource : creates
RecurringClassCreation --> ClassResource : creates
StandardMemberAccess --> ClassResource : queries
StandardMemberAccess --> UserResource : queries
```

---

## Key Differences to Sprint 3A

### 1. Consolidation of Authentication Classes

In Sprint 3A there were four separate authentication classes: `MemberLogin`, `TrainerLogin`, `MemberRegister`, and `TrainerRegister`. In Sprint 3B these were consolidated into two classes: `Login` and `Register`.

- `MemberLogin` + `TrainerLogin` → single `Login` class
- `MemberRegister` + `TrainerRegister` → single `Register` class
- `CreateClass` → merged into `ClassList` (which now handles both POST and GET)

### 2. Introduction of a Service Layer (Template Method Pattern)

In Sprint 3A, API classes called `ClassResource` and `UserResource` directly — there was no layer between the HTTP handler and the database. In Sprint 3B, a service layer was added using the **Template Method pattern** with three abstract base classes: `RegistrationTemplate`, `ClassCreationTemplate`, and `MemberAccessTemplate`.

- `RegistrationTemplate` → `StandardRegistration`
- `ClassCreationTemplate` → `StandardClassCreation`, `RecurringClassCreation`
- `MemberAccessTemplate` → `StandardMemberAccess`

### 3. Recurring Class Support Added (Feature 6)

In Sprint 3A, `ClassResource` only had `create_class()`. In Sprint 3B, `RecurringClassCreation` was added as a new subclass of `ClassCreationTemplate`, and `ClassResource` gained `create_recurring_classes()`. `ClassList` now holds both `class_template` and `recurring_template`. The `FitnessClass` document also gained a new `recurrence_group_id` field to group recurring classes together. These were updates to support the addition of Feature 6.

### 4. Notification System Added (Feature 7)

In Sprint 3A there were no notification classes. In Sprint 3B a full notification system was added using the **Strategy pattern**. The following were added:

- `NotificationService` (abstract base)
- `EmailNotificationService` (email via AWS SES)
- `TelegramNotificationService` (Telegram bot)
- `NotificationDispatcher` (decides which channel to use based on the member's preferences)

The `User` document also gained two new fields: `notification_prefs` and `telegram_chat_id`. These were updates to support the addition of Feature 7.

### 5. Removal of the Enrollment Class

In Sprint 3A there was an `Enrollment` class with `booking_date`, `status`, `confirm()`, and `cancel()`. In Sprint 3B this is gone — enrollment is handled directly by storing `class_ids` in the `User` document and `user_ids` in the `FitnessClass` document. There is no longer a separate enrollment object.