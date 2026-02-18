# Case Specifications for each feature

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


## Feature 4: View Member/Guest List of a Class

**User story: As a class trainer or center admin, I want to view who has booked a spot in my class.**

**Use case name**
View Booked Member List for a Class

**Preconditions**
1) The requester (trainer or admin) is authenticated with a valid JWT token.
2) The requester's account has the role of trainer or admin.
3) The fitness class exists in the system and has a valid class ID.

**Main Success Scenario**
1) The trainer or admin sends a request to view the member list for a specific class, providing the class ID and their JWT token.
2) The system validates the JWT token and confirms the requester's role is trainer or admin.
3) The system looks up the class by the provided class ID and confirms it exists.
4) The system retrieves the list of user IDs stored in the class's booked users list.
5) For each user ID, the system fetches the corresponding user's details: name, email address, and contact number.
6) The system returns the full list of booked members with their details to the requester.

**Alternative Flows/Extensions**
A1: Missing or invalid JWT token
- At step 2, if no token is provided or the token is invalid/expired, the system rejects the request with a 401 Unauthorized response.

A2: Insufficient role
- At step 2, if the requester's role is member (not trainer or admin), the system rejects the request with a 403 Forbidden response.

A3: Class not found
- At step 3, if the provided class ID does not match any class in the system, the system rejects the request with a 404 Not Found response.

A4: Class has no bookings
- At step 4, if the class's booked users list is empty, the system returns a 200 OK response with an empty list.

**Success Guarantee / Postconditions**
1) The trainer or admin receives a list of all members who have booked a spot in the class.
2) Each entry in the list contains the member's name, email address, and contact number.
3) No user data is modified as a result of this request.
4) Only authenticated trainers and admins can access this information; members and unauthenticated users cannot.