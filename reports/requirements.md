# Case Specifications for each feature

## Feature 1: Create Class

**Use Case Name: Create new class**
**Precondition**

- User must be logged in as an admin

**Main Success Scenario**

1. Admin/Trainer chooses "Create Class" option
2. System displays class creation form
3. Admin/Trainer fills in all required fields:
   - Name
   - Description
   - Start Time
   - End Time
   - Capacity
   - Room Number
4. Admin/Trainer submits form
5. System validates user input
6. System creates class with all fields entered
7. System displays success message

**Alternative Flows/Extensions**

**3a. Admin leaves required fields empty:**

- 3a1. System detects missing required fields
- 3a2. System displays error message indicating which fields are required
- 3a3. Return to step 3

**5a. Admin enters an invalid input:**

- 5a1. System detects invalid input
- 5a2. System displays error message about invalid input fields
- 5a3. Return to step 3

**6a. Admin cancels the operation at any time before submission:**

- 6a1. System discards entered information
- 6a2. Use case ends

**Success Guarantee / Postconditions**

- A new fitness class is successfully created and stored in the database
- A success message is displayed
- The class is available and visible for other users to view and join
- All required information (capacity, description, start time, end time, room number) is accurately recorded

---

## Feature 2: View Class List

**User case story: As a guest/member, I want to see a list of upcoming fitness classes so I can decide what to book.**

**User case**

**Use case name**
Identifying available fitness classes for booking

**Preconditions**

1. A guest should register on the site to become a member before booking and registering for a class

**Main success scenario**

1. A member/user succesfully finds a list of available fitness classes
2. A member succesfully sees a list of classes they are already enrolled in.
3. A member/guest succesffuly sees class status which is open or full and closed
4. The system successfully updates list if any classes are added, removed or closed.

**Alternative flows/Extensions**

1. A member/user should come in person to the facility to check for availble classes if online checks fail.

**Success guarantee/Postconditions**

1. A member proceeds to book for a class of their choice that doesn't conflict with previous bookings.
2. A user sign-ups to be able to book available classes of their choice

---

## Feature 3: Book A Class

**Use Case Name** : Book a Fitness Class

**Preconditioins**

1. The user is authenticated by the system.
2. The fitness class exists in the system.
3. The class has a defined and available capacity.

**Main Success Scenario**

1. User views available fitness classes and selects a class to book.
2. User submits a booking request for the selected class.
3. System verifies the user exists and the class exists.
4. System checks that:
   a) The user is not already booked in the class, and
   b) the class is not full (booked count < capacity)
5. System records the booking by:
   a) adding the user to the class's list of booked users, and
   b) adding the class to the user's list of booked classes.
6. System returns a confirmation that the booking was successful.

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

1. The user is enrolled in the selected class
2. The class's booked user list includes the user
3. The user's booked class list includes the class
4. The class capacity is not exceeded
