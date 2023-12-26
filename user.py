from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext
from dto import *
from auth import *
from mongo import users_collection

router = APIRouter()

hash_helper = CryptContext(schemes=["bcrypt"])


@router.post("/login")
async def login(request: UserLoginRequest):
    # find with same username
    user_exists = users_collection.find_one({"username": request.username})
    if user_exists:
        password = hash_helper.verify(request.password, user_exists["password"])
        if password:
            token = sign_jwt(request.username)
            return UserLoginResponse(message="Success", status=200, data=token)

        raise HTTPException(status_code=403, detail="Incorrect email or password")

    raise HTTPException(status_code=403, detail="Incorrect email or password")


@router.post("/signup")
async def signup(request: UserSignInRequest):
    user_exists = users_collection.find_one({"username": request.username})
    if user_exists is not None:
        raise HTTPException(
            status_code=409, detail="User with email supplied already exists"
        )

    request.password = hash_helper.encrypt(request.password)
    new_user = users_collection.insert_one(request.dict())
    return UserLoginResponse(
        message="Success",
        status=200,
        data=SignInData(
            id=new_user.inserted_id, name=request.username, username=request.username
        ),
    )
