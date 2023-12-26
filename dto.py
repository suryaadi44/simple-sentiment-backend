from datetime import datetime
from pydantic import BaseModel
from fastapi.security import HTTPBasicCredentials
from typing import Dict

class Prediction(BaseModel):
    prediction: int
    predictionStr: str
    text: str
    time: datetime
    score: list[float]
    batchId: int | None = None


class BaseResponse:
    message: str
    status: int


class PredictionRequest(BaseModel):
    time: datetime
    text: str


class PredictionsRequest(BaseModel):
    texts: list[PredictionRequest]


class PredictionsMeta(BaseModel):
    total: int
    positive: int
    negative: int


class DataResponse(BaseModel):
    predictions: list[Prediction]
    meta: PredictionsMeta


class PredictionsResponse(BaseModel, BaseResponse):
    data: DataResponse


class BatchDataResponse(BaseModel):
    filename: str
    timestamp: datetime
    predictions: list[Prediction]
    meta: PredictionsMeta


class PredictionsBatchFileResponse(BaseModel, BaseResponse):
    data: BatchDataResponse


class PredictionResponse(BaseModel, BaseResponse):
    data: Prediction


class PredictionRequest(BaseModel):
    time: datetime
    text: str

class UserLoginRequest(HTTPBasicCredentials):
    pass


class UserSignInRequest(HTTPBasicCredentials):
    name: str

class UserLoginResponse(BaseModel, BaseResponse):
    data: Dict[str, str]

class SignInData (BaseModel):
    id : str
    name : str
    username : str

class UserSignInResponse(BaseModel, BaseResponse):
    data : SignInData

