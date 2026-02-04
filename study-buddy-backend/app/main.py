from fastapi import FastAPI, HTTPException,Query,Body
from core.database import user_collection as UserTable,feedback_collection as feedscoreTable, request_collection as requestTable , friends_collection as friendsTable
from services.match_service import find_best_matches
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware
from core.user import User,filter,update
from core.security import hash_password,verify_password,encode_response,decode_response
from core.feedback import Feedback
from core.request import Request

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return{"stduy finder is working"}


# return match profiles from the client
@app.get("/match/{profile_id}")
async def match_profiles(profile_id: str):
    profile_id = decode_response(profile_id)
    user_profile = await UserTable.find_one(
        {"_id": ObjectId(profile_id)}
    )

    if not user_profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    matches = await find_best_matches(user_profile, UserTable)

    return {
        "user_id": profile_id,
        "matches": matches
    }


# add new user
@app.post("/adduser")
async def create_user(user:User):
    user_dict = user.dict()
    user_dict["password"] = hash_password(user_dict["password"])
    user_dict["email"] = encode_response(user_dict["email"])
    user_dict["role"] = "student" 
    user_dict["feedscore"] = 0

    await UserTable.insert_one(user_dict)
    return {"message": "User added successfully"}

#login user
@app.post("/login")
async def loginuser(email_id: str, password: str):
    encoded_email_id = encode_response(email_id)
    
    
    user = await UserTable.find_one({"email": encoded_email_id})
    
    
    
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    
    if not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="invalid credentials")
    
    return {
        "user_id": encode_response(str(user["_id"])),
        "role": user["role"]
    }

#single user endpoint
@app.get("/singleuser/{user_id}")
async def singleuser(user_id:str):
    user_id = decode_response(user_id)
    if user_id is None:
        raise HTTPException(status_code=401 , detail="invalid id")
    
    user = await UserTable.find_one({"_id":ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404 , detail="user not found")
    
    # Get friend count
    friend_count = await friendsTable.count_documents({
        "$or": [
            {"user_id": user_id},
            {"friend_id": user_id}
        ]
    })
    
    # Get request count (pending friend requests for this user)
    request_count = await requestTable.count_documents({
        "reciver_id": user_id
    })
    
    if user["number_permission"]=="true":
       return({
        "user_name":user["name"],
        "intrusted_sub":user["subjects"],
        "study_time":user["study_time"],
        "year":user["year"],
        "study_mode":user["study_mode"],
        "course":user["course"],
        "interested_field":user["interested_field"],
        "email_id":decode_response(user["email"]),
        "gender":user["gender"],
        "number":"Can't show",
        "feed_score":user["feedscore"],
        "friend_count": friend_count,
        "request_count": request_count

       })
    else:
        return({
        "user_name":user["name"],
        "intrusted_sub":user["subjects"],
        "study_time":user["study_time"],
        "year":user["year"],
        "study_mode":user["study_mode"],
        "course":user["course"],
        "interested_field":user["interested_field"],
        "email_id":decode_response(user["email"]),
        "gender":user["gender"],
        "number":user["number"],
        "feed_score":user["feedscore"],
        "friend_count": friend_count,
        "request_count": request_count

       })




#filter students
@app.post("/filterstudents")
async def filter_students(filter_criteria: filter):
    query = {}
    
    # Filter by subjects (array match)
    if filter_criteria.subject is not None and len(filter_criteria.subject) > 0:
        query['subjects'] = {'$in': filter_criteria.subject}
    
    # Filter by study mode
    if filter_criteria.study_mode is not None:
        query['study_mode'] = {'$regex': f".*{filter_criteria.study_mode}.*", '$options': 'i'}
    
    # Filter by year
    if filter_criteria.year is not None and filter_criteria.year > 0:
        query['year'] = filter_criteria.year
    
    # Filter by course
    if filter_criteria.course is not None:
        query['course'] = {'$regex': f".*{filter_criteria.course}.*", '$options': 'i'}
    
    # Filter by interested field
    if filter_criteria.interested_field is not None:
        query['interested_field'] = {'$regex': f".*{filter_criteria.interested_field}.*", '$options': 'i'}
    
    students = []
    cursor = UserTable.find(query)
    
    async for student in cursor:
        students.append({
            "user_id": encode_response(str(student["_id"])),
            "name": student.get("name"),
            "subjects": student.get("subjects"),
            "study_time": student.get("study_time"),
            "year": student.get("year"),
            "study_mode": student.get("study_mode"),
            "course": student.get("course"),
            "interested_field": student.get("interested_field"),
            "email": decode_response(student.get("email")),
            
        })
    
    return students

#fetch student by subject
@app.post("/search/{subject}")
async def subject_search(subject: str):
    students = []
    cursor =  UserTable.find({"subjects": {"$in": [subject]}})
    
    async for student in cursor:
        students.append({
            "user_id": encode_response(str(student["_id"])),
            "name": student.get("name"),
            "subjects": student.get("subjects"),
            "study_time": student.get("study_time"),
            "year": student.get("year"),
            "study_mode": student.get("study_mode"),
            "course": student.get("course"),
            "interested_field": student.get("interested_field"),
            "email": decode_response(student.get("email")),
            
        })
    
    if not students:
        raise HTTPException(status_code=404, detail="No students found for this subject")
    
    return students
#update user
@app.put("/updateuser/{user_id}")
async def update_user(user_id: str, data: update=Body(...)):
    # Decode user id
    userid = decode_response(user_id)
    if userid is None:
        raise HTTPException(status_code=400, detail="Invalid user id")

    # Check user exists
    user = await UserTable.find_one({"_id": ObjectId(userid)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Convert Pydantic model to dict, exclude None for partial updates
    update_data = data.dict(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    # Perform MongoDB update
    result = await UserTable.update_one(
        {"_id": ObjectId(userid)},
        {"$set": update_data}
    )

    return {"message": "Updated successfully"}

#fetch all stidents
@app.get("/allstudents")
async def allstudents():
    students = []
    cursor = UserTable.find()
    
    async for student in cursor:
        students.append({
            "user_id": encode_response(str(student["_id"])),
            "name": student.get("name"),
            "subjects": student.get("subjects"),
            "study_time": student.get("study_time"),
            "year": student.get("year"),
            "study_mode": student.get("study_mode"),
            "course": student.get("course"),
            "interested_field": student.get("interested_field"),
            "email": decode_response(student.get("email")),
            "feed_score":student.get("feedscore")
        })
    
    return students

#feed back for students
@app.post("/feedback")
async def feedback(feedback: Feedback):
    feedback_dict = feedback.dict()
    
    feedback_dict["feed_giver"] = decode_response(feedback_dict["feed_giver"])
    feedback_dict["feed_reciver"] = decode_response(feedback_dict["feed_reciver"])
    reciver_id = feedback_dict["feed_reciver"]
    
    if reciver_id is None:
        raise HTTPException(status_code=401, detail="invalid receiver id")
    
    
    result = await feedscoreTable.insert_one(feedback_dict)
    
    
    reciver = await UserTable.find_one({"_id": ObjectId(reciver_id)})
    
    if not reciver:
        raise HTTPException(status_code=404, detail="receiver not found")
    
    # Update receiver's feed score
    reciverscore = reciver.get("feedscore", 0) + feedback_dict["feed_score"]
    data = {"feedscore": reciverscore}
    
    await UserTable.update_one(
        {"_id": ObjectId(reciver_id)},
        {"$set": data}
    )
    
    return {"message": "feedback added successfully", "updated_score": reciverscore}


#request handling
@app.post("/request")
async def handle_requests(request: Request):
    request_dict = request.dict()
    request_dict["sender_id"] = decode_response(request_dict["sender_id"])
    request_dict["reciver_id"] = decode_response(request_dict["reciver_id"])

    sender_id = request_dict["sender_id"]
    receiver_id = request_dict["reciver_id"]
    
    # Check if request already exists
    existing_request = await requestTable.find_one({
        "sender_id": sender_id,
        "reciver_id": receiver_id
    })
    
    if existing_request:
        raise HTTPException(status_code=400, detail="Request already sent")
    
    # Check if friendship already exists
    existing_friendship = await friendsTable.find_one({
        "$or": [
            {"user_id": sender_id, "friend_id": receiver_id},
            {"user_id": receiver_id, "friend_id": sender_id}
        ]
    })
    
    if existing_friendship:
        raise HTTPException(status_code=400, detail="Already friends with this user")

    sender_details = await UserTable.find_one({"_id":ObjectId(sender_id)})
    sender_name = sender_details["name"]
    sender_course = sender_details["course"]

    request_dict["sender_name"] = sender_name
    request_dict["sender_course"] = sender_course

    if receiver_id is None:
        raise HTTPException(status_code=401, detail="invalid receiver id")
    
    result = await requestTable.insert_one(request_dict)

    if result.inserted_id:
        return {"message": "request sent successfully"}
    else:
        return{"message":"please try again"}
    

#fetch all requests for a user
@app.get("/allrequests")
async def get_all_requests(user_id: str = Query(...)):
    try:
        user_id = decode_response(user_id)
        
        query = {
            "reciver_id": user_id
        }
        
        result = []
        requests = requestTable.find(query)
        
        # Get receiver details (the user making the request)
        receiver_details = await UserTable.find_one({"_id": ObjectId(user_id)})
        
        async for request in requests:
            sender_id = request.get("sender_id")
            
            # Get sender details from user table
            sender_details = await UserTable.find_one({"_id": ObjectId(sender_id)})
            request_count = await requestTable.count_documents({
            "reciver_id": user_id
               })
            
            request_data = {
               
                "request_id": encode_response(str(request["_id"])),
                "sender": {
                    "sender_id": encode_response(sender_id),
                    "sender_name": sender_details.get("name") if sender_details else request.get("sender_name"),
                    "sender_course": sender_details.get("course") if sender_details else request.get("sender_course")
                    
                }
            }
            result.append(request_data)
        
        if not result:
            return {"message": "No requests found", "result": []}
        
        return {"message": "Requests fetched successfully","count":request_count,"result": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching requests: {str(e)}")



# fetch requests using user_id and requestor_id
@app.post("/acceptrequest")
async def accept_friend(request_id: str = Query(...)):
    request_id = decode_response(request_id)
    if request_id is None:
        raise HTTPException(status_code=400, detail="invalid request id")
    
    request = await requestTable.find_one({"_id": ObjectId(request_id)})
    
    if not request:
        raise HTTPException(status_code=404, detail="request not found")
    
    sender_id = request["sender_id"]
    receiver_id = request["reciver_id"]
    
    # Check if friendship already exists to avoid duplication
    existing_friendship = await friendsTable.find_one({
        "$or": [
            {"user_id": sender_id, "friend_id": receiver_id},
            {"user_id": receiver_id, "friend_id": sender_id}
        ]
    })
    
    if existing_friendship:
        # Delete the request without adding to friends
        await requestTable.delete_one({"_id": ObjectId(request_id)})
        return {"message": "Friendship already exists"}
    
    # Add both users to friends collection
    friends_entry = {
        "friend_id": sender_id,
        "user_id": receiver_id,
        "friend_name": request["sender_name"],
        "friend_course": request["sender_course"]
    }
    await friendsTable.insert_one(friends_entry)
    
    # Delete the request
    await requestTable.delete_one({"_id": ObjectId(request_id)})
    
    return {"message": "Friend request accepted successfully"}


#reject request
@app.post("/rejectrequest")
async def reject_request(request_id: str = Query(...)):
    request_id = decode_response(request_id)
    if request_id is None:
        raise HTTPException(status_code=400, detail="invalid request id")
    
    reuslt = requestTable.delete_one({"_id":ObjectId(request_id)})

    if not reuslt:
        raise HTTPException(status_code=404 , detail ="reejection fails tray again")
    
    else:
        return({"message":"rejected request"})
    
@app.get("/get-friend/{user_id}")
async def get_friend(user_id: str):
    user_id = decode_response(user_id)
    if user_id is None:
        raise HTTPException(status_code=400, detail="invalid user id")

    friends = []
    cursor = friendsTable.find({
        "$or": [
            {"user_id": user_id},
            {"friend_id": user_id}
        ]
    })
    
    friend_count = await friendsTable.count_documents({
        "$or": [
            {"user_id": user_id},
            {"friend_id": user_id}
        ]
    })

    async for friend in cursor:
        # Determine which ID is the friend's
        if friend.get("user_id") == user_id:
            friend_id = friend.get("friend_id")
        else:
            friend_id = friend.get("user_id")
        
        # Find friend details in user table
        friend_details = await UserTable.find_one({"_id": ObjectId(friend_id)})
        
        if friend_details:
            friends.append({
                "_id": encode_response(str(friend.get("_id"))),
                "friend_id": encode_response(friend_id) if friend_id else None,
                "friend_name": friend_details.get("name"),
                "friend_course": friend_details.get("course")
            })
        else:
            friends.append({
                "_id": encode_response(str(friend.get("_id"))),
                "friend_id": encode_response(friend_id) if friend_id else None,
                "friend_name": friend.get("friend_name"),
                "friend_course": friend.get("friend_course")
            })

    if not friends:
        return {"message": "No friends found", "friends": []}

    return {"message": "Friends fetched successfully","count":friend_count, "friends": friends}


#remove friend
@app.delete("/removefriend/{_id}")
async def removeFriend(_id:str):
    id = decode_response(_id)
    if id is None:
        raise HTTPException(status_code=400, detail="invalid id")
    
    result = friendsTable.delete_one({"_id":ObjectId(id)})
    if not result:
        raise HTTPException(status_code=404 , detail="try again")
    
    else: 
        return({"message":"removed successfully"})
    

#remove stsudent 
@app.delete("/removestudent/{student_id}")
async def remove_user(student_id:str):
    student_id = decode_response(student_id)

    if student_id is None:
        raise HTTPException(status_code=400 , detail="invalid id")
    
    # Delete user from UserTable
    result = await UserTable.delete_one({"_id":ObjectId(student_id)})
    
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="user not found")
    
    
    
    # Delete all friend records associated with this user
    await friendsTable.delete_many({
        "$or": [
            {"user_id": student_id},
            {"friend_id": student_id}
        ]
    })
    
    return {"message": "User a removed successfully"}
    
#feed details
@app.get("/feeddetails/{user_id}")
async def student_feed_details(user_id: str):
    user_id = decode_response(user_id)

    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid ID")

    result = await feedscoreTable.find(
        {"feed_reciver": user_id}
    ).to_list(length=None)

    for doc in result:
        doc["_id"] = encode_response(str(doc["_id"]))

        if "feed_giver" in doc and doc["feed_giver"]:
            doc["feed_giver"] = encode_response(doc["feed_giver"])

        if "feed_reciver" in doc and doc["feed_reciver"]:
            doc["feed_reciver"] = encode_response(doc["feed_reciver"])

    return result



#admin all users count
@app.get("/admin")
async def admin_details():
    count = await UserTable.count_documents({})
    user_count =(count-1)
    return({"count":user_count})


@app.get("/review/{id}")
async def review(id: str):
    id = decode_response(id)
    
    if not id:
        raise HTTPException(status_code=400, detail="Invalid ID")

    cursor = feedscoreTable.find({"feed_reciver": id})

    data = []
    async for review in cursor:
        data.append({
            "id": encode_response(str(review["_id"])),
            "review": review.get("feed_content")
        })

    return data



@app.delete("/deletereview/{id}")
async def delete_review(id: str):
    decoded_id = decode_response(id)

    if not decoded_id:
        raise HTTPException(status_code=400, detail="Invalid ID")

    try:
        object_id = ObjectId(decoded_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    result = await feedscoreTable.delete_one({"_id": object_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Review not found")

    return {"message": "Review deleted successfully"}






@app.get("/suggestion/{user_id}")
async def suggest_home(user_id: str):
    user_id = decode_response(user_id)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user id")

    # current user ObjectId
    try:
        current_user_oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId")

    # 1. Find all friend relations where user is involved
    cursor = friendsTable.find(
        {
            "$or": [
                {"user_id": user_id},
                {"friend_id": user_id}
            ]
        }
    )

    friend_oids = []

    async for doc in cursor:
        try:
            if doc["user_id"] == user_id:
                # normal direction
                friend_oids.append(ObjectId(doc["friend_id"]))
            else:
                # reversed direction
                friend_oids.append(ObjectId(doc["user_id"]))
        except Exception:
            continue

    # 2. Exclude friends + self
    exclude_oids = friend_oids + [current_user_oid]
    
    
    # 3. Query users excluding friends
    users_cursor = UserTable.find(
        {"_id": {"$nin": exclude_oids}}
    )

    users = await users_cursor.to_list(length=None)

    # 4. Make response JSON-safe
    for u in users:
        u["_id"] = encode_response(str(u["_id"]))

    return users
 