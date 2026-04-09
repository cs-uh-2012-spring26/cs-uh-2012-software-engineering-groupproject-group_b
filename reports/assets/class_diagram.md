classDiagram
    direction TB
    
    %% Actors 
    class Trainer {
        <<actor>>
        +create_recurring_class()
        +send_reminder()
    }

    class Member {
        <<actor>>
        +view_class_list()
        +view_enrolled_classes()
        +book_class()
    }

    %% Flask_restx base
    class Resource {
        <<abstract>>
        +get()
        +post()
        +put()
        +delete()
    }

    %% API RESOURCES (app/apis/)
    class ClassList {
        +get() List~Class~
    }

    class EnrolledClasses {
        +get() List~Class~
    }

    class ClassBooking {
        +post(class_id) Response
    }

    class CreateClass {
        +post() Response
    }

    class ClassMemberList {
        +get(class_id) List~Member~
    }

    class SendClassReminder {
        +post(class_id) Response
    }

    class MemberLogin {
        +post() Token
    }

    class MemberRegister {
        +post() Response
    }

    class TrainerLogin {
        +post() Token
    }

    class TrainerRegister {
        +post() Response
    }

    %% DATABASE CLASSES (app/db/)
    class DB {
        -_db: MongoClient
        -_instance: DB
        +get_instance() DB
        +get_collection(name) Collection
        -_get() Connection
    }

    class ClassResource {
        +get_class_by_id(class_id) Class
        +add_user_to_class(class_id, user_id) str
        +create_class(class_data) Response
        +update_class(class_id, data) Response
        +delete_class(class_id) Response
    }

    class UserResource {
        +get_user_by_id(user_id) User
        +get_users_by_ids(user_ids) List~User~
        +add_class_to_user(user_id, class_id) bool
        +create_user(user_data) Response
        +update_user(user_id, data) Response
    }

    %% DATA ENTITIES
    class User {
        -user_id: ObjectId
        -name: str
        -email: str
        -password_hash: str
        -role: str
        -enrolled_class_ids: List~ObjectId~
        +to_dict() dict
    }

    class Class {
        -class_id: ObjectId
        -name: str
        -trainer_name: str
        -trainer_id: ObjectId
        -start_time: datetime
        -end_time: datetime
        -description: str
        -room_number: str
        -capacity: int
        -user_ids: List~ObjectId~
        +is_full() bool
        +get_status() str
        +to_dict() dict
    }

    class Enrollment {
        <<association>>
        -booking_date: datetime
        -status: str
        +confirm() void
        +cancel() void
    }

    class Config {
        -MONGO_URI: str
        -JWT_SECRET_KEY: str
        -AWS_SES_REGION: str
        -AWS_ACCESS_KEY_ID: str
        -AWS_SECRET_ACCESS_KEY: str
        +from_env() Config
    }

    %% INHERITANCE RELATIONSHIPS 
    Resource <|-- ClassList : inherits
    Resource <|-- EnrolledClasses : inherits
    Resource <|-- ClassBooking : inherits
    Resource <|-- CreateClass : inherits
    Resource <|-- ClassMemberList : inherits
    Resource <|-- SendClassReminder : inherits
    Resource <|-- MemberLogin : inherits
    Resource <|-- MemberRegister : inherits
    Resource <|-- TrainerLogin : inherits
    Resource <|-- TrainerRegister : inherits

    %% DEPENDENCY RELATIONSHIPS(uses)
    ClassList ..> DB : uses
    EnrolledClasses ..> DB : uses
    ClassBooking ..> UserResource : uses
    ClassBooking ..> ClassResource : uses
    CreateClass ..> ClassResource : uses
    ClassMemberList ..> ClassResource : uses
    SendClassReminder ..> ClassResource : uses
    SendClassReminder ..> UserResource : uses
    ClassResource ..> DB : uses
    UserResource ..> DB : uses
    DB ..> Config : uses

    %% ASSOCIATION RELATIONSHIPS 
    ClassResource --> Class : manages
    UserResource --> User : manages
    
    User "1..*" -- "1..*" Class : books >
    Enrollment -- User : records for
    Enrollment -- Class : records for

    %% ACTOR TO RESOURCE RELATIONSHIPS
    Member --> ClassList : views
    Member --> EnrolledClasses : views
    Member --> ClassBooking : books
    Trainer --> CreateClass : creates
    Trainer --> SendClassReminder : sends