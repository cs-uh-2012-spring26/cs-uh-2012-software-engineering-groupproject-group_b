# Case Specifications for each feature

---

## Feature 4: View Member/Guest List of a Class

**User story: As a class trainer or center admin, I want to view who booked a spot in my class.**

---

### UML Use Case Diagram

See `reports/feature4_usecase_diagram.puml` (render with PlantUML or the VS Code PlantUML extension).

```
+----------------------------------------------------------+
|              Fitness Class System                        |
|                                                          |
|   +------------------------------------------+          |
|   |      <<use case>>                        |          |
|   |   View Class Member List                 |          |
|   |   - - - <<include>> - - ->               |          |
|   |       Retrieve Member Details            |          |
|   |       (name, email, contact)             |          |
|   |                                          |          |
|   |   - - - <<extend>> - - ->                |          |
|   |       View Empty Member List             |          |
|   |       [no bookings found]                |          |
|   |                                          |          |
|   |   - - - <<extend>> - - ->                |          |
|   |       Handle Invalid Class ID            |          |
|   |       [blank/invalid class ID]           |          |
|   +------------------------------------------+          |
|                                                          |
+----------------------------------------------------------+
        ^                        ^
        |                        |
   [Trainer]                 [Admin]
```

**Actors:**
- **Trainer** — the instructor who created the class; wants to see who enrolled.
- **Admin** — center administrator; can view member lists for any class.

---

### Use Case Specifications

---

#### UC1 — View Class Member List

**Use case name**
View Class Member List

**Preconditions**
1. The user is authenticated as a Trainer or Admin.
2. At least one class has been created in the system (Feature 1).
3. The Trainer/Admin knows the class ID they want to inspect.

**Main success scenario**
1. The Trainer/Admin selects or provides the class ID for a specific class.
2. The system validates that the class ID is a non-blank string.
3. The system queries the bookings collection for all records matching that class ID.
4. The system retrieves each booked member's name, email address, and contact number.
5. The system returns the complete list of members to the Trainer/Admin.
6. The Trainer/Admin reviews the member information on the dashboard.

**Alternative flows / Extensions**

- **2a. Class ID is blank or whitespace:**
  1. The system rejects the request immediately.
  2. The system returns HTTP 406 with the message "Invalid class ID provided".
  3. The use case ends.

- **3a. No members have booked the class:**
  1. The system finds no matching booking records.
  2. The system returns HTTP 200 with an empty list.
  3. The dashboard displays "No members have booked this class yet."
  4. The use case ends successfully.

- **5a. An unexpected system/database error occurs:**
  1. The system catches the error.
  2. The system returns HTTP 500 with a descriptive error message.
  3. The Trainer/Admin is informed that the request could not be completed.
  4. The use case ends.

**Success guarantee / Postconditions**
1. The Trainer/Admin has viewed the name, email, and contact of every member who booked the class.
2. No data is modified — this is a read-only operation.
3. The booking records and class records remain unchanged.

---

#### UC2 — Retrieve Member Details *(included by UC1)*

**Use case name**
Retrieve Member Details

**Preconditions**
1. UC1 has been triggered and a valid class ID has been provided.
2. At least one booking record exists for the class.

**Main success scenario**
1. The system fetches all booking documents where `class_id` matches.
2. For each booking, the system extracts `user_name`, `user_email`, and `user_contact`.
3. The system serialises the records (converting internal IDs to strings) and returns them.

**Alternative flows / Extensions**
- None beyond those already handled by UC1.

**Success guarantee / Postconditions**
1. A list of member detail objects (name, email, contact) is returned to UC1 for display.

---

#### UC3 — View Empty Member List *(extends UC1)*

**Use case name**
View Empty Member List

**Preconditions**
1. UC1 has been triggered with a valid, non-blank class ID.
2. No bookings exist for the specified class.

**Main success scenario**
1. The system queries the bookings collection and finds zero records.
2. The system returns HTTP 200 with an empty list `[]`.
3. The Trainer/Admin sees a "no members yet" message on the dashboard.

**Alternative flows / Extensions**
- None.

**Success guarantee / Postconditions**
1. The Trainer/Admin is clearly informed that nobody has booked the class yet.
2. No error is raised — an empty class is a valid state.

---

#### UC4 — Handle Invalid Class ID *(extends UC1)*

**Use case name**
Handle Invalid Class ID

**Preconditions**
1. UC1 has been triggered.
2. The class ID provided is blank or consists only of whitespace.

**Main success scenario**
1. The system detects the invalid class ID before querying the database.
2. The system returns HTTP 406 with the message "Invalid class ID provided".
3. No database query is made.

**Alternative flows / Extensions**
- None.

**Success guarantee / Postconditions**
1. The Trainer/Admin receives a clear error message explaining the problem.
2. The database is not queried unnecessarily.

---

## Feature 2: View Class List

**User case story: As a guest/member, I want to see a list of upcoming fitness classes so I can decide what to book.**

**User case**

**Use case name**
Identifying available fitness classes for booking 

**Preconditions**
1) A guest should register on the site to become a member before booking and registering for a class

**Main success scenario**

1) A member/user succesfully finds a list of available fitness classes 
2) A member succesfully sees a list of classes they are already enrolled in.
3) A member/guest succesffuly sees class status which is open or full and closed
4) The system successfully updates list if any classes are added, removed or closed.

**Alternative flows/Extensions**
1) A member/user should come in person to the facility to check for availble classes if online checks fail.

**Success guarantee/Postconditions**
1) A member proceeds to book for a class of their choice that doesn't conflict with previous bookings.
2) A user sign-ups to be able to book available classes of their choice


## Feature 3: Book A Class

**Use Case Name** : Book a Fitness Class

**Preconditioins** 
1) The user is authenticated by the system. 
2) The fitness class exists in the system. 
3) The class has a defined and available capacity. 

**Main Success Scenario** 
1) User views available fitness classes and selects a class to book. 
2) User submits a booking request for the selected class. 
3) System verifies the user exists and the class exists. 
4) System checks that: 
a) The user is not already booked in the class, and 
b) the class is not full (booked count < capacity)
5) System records the booking by: 
a) adding the user to the class's list of booked users, and 
b) adding the class to the user's list of booked classes. 
6) System returns a confirmation that the booking was successful. 

**Alternative Flows/Extensions** 
A1: Class is full 
- At step 4, if booked count is greater than or equal to the capacity, the system rejects the booking and informs the user the class is full. 
A2: User already booked 
- At step 4, if the user is already enrolled, the system rejects the booking and infroms the user they are already booked. 
A3: User not found/ not identified 
- At step 3, if the user does not exist (or properly authenticated), the system rejects the request and informs the user. 
A4: Class not found 
- At step 3, if the class does not exist, the system rejects the request and infroms the user. 

**Success Guarantee / Postconditions** 
1) The user is enrolled in the selected class 
2) The class's booked user list includes the user 
3) The user's booked class list includes the class 
4) The class capacity is not exceeded 