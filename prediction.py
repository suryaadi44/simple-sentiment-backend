import csv
import logging
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from mongo import predictions_collection
from model import *
from dto import *
from snowflake import SnowflakeGenerator

logger = logging.getLogger(__name__)

router = APIRouter()
gen = SnowflakeGenerator(42)


@router.get("/stat")
async def get_stat():
    try:
        total = predictions_collection.count_documents({})
        positive = predictions_collection.count_documents({"prediction": 1})
        negative = total - positive

        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        pipeline = [
            {
                "$match": {
                    "time": {
                        "$gte": datetime(seven_days_ago.year, seven_days_ago.month, seven_days_ago.day),
                        "$lte": datetime.utcnow(),
                    },
                    "prediction": 1,
                }
            },
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$time"}},
                    "count": {"$sum": 1},
                }
            },
        ]

        res = predictions_collection.aggregate(pipeline)

        data = []
        for r in range(7):
            date = datetime.utcnow() - timedelta(days=7) + timedelta(days=r)
            date_str = date.strftime("%Y-%m-%d")
            data.append({"date": date_str, "count": 0})

        for r in res:
            for d in data:
                if d["date"] == r["_id"]:
                    d["count"] = r["count"]


        return JSONResponse(
            status_code=200,
            content={
                "message": "Success",
                "status": 200,
                "data": {
                    "total": total,
                    "positive": positive,
                    "negative": negative,
                    "daily": data,
                },
            },
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Failed to get predictions")


@router.post("")
async def predict(request: PredictionRequest):
    try:
        res = predict_service(request)

        predictions_collection.insert_one(res.model_dump())

        return PredictionResponse(
            message="Success",
            status=200,
            data=res,
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Failed to predict sentiment")


@router.get("")
async def get_predictions(
    page: int = 1,
    limit: int = 10,
    q: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
):
    try:
        skip = (page - 1) * limit
        args = {}

        if start is not None and end is not None:
            args["time"] = {"$gte": start, "$lte": end}

        if q is not None:
            args["text"] = {"$regex": q, "$options": "i"}

        logger.info(args)

        predictions = predictions_collection.find(args).skip(skip).limit(limit)

        res = []
        for prediction in predictions:
            res.append(Prediction(**prediction))

        return PredictionsResponse(
            message="Success",
            status=200,
            data=DataResponse(
                predictions=res,
                meta=PredictionsMeta(
                    total=predictions_collection.count_documents(args),
                    positive=len(
                        [prediction for prediction in res if prediction.prediction == 1]
                    ),
                    negative=len(
                        [prediction for prediction in res if prediction.prediction == 0]
                    ),
                ),
            ),
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Failed to get predictions")


@router.post("/batch/json")
async def predict_batch(request: PredictionsRequest):
    try:
        responses = []
        for req in request.texts:
            responses.append(predict_service(req))

        total = len(responses)
        positive = len([response for response in responses if response.prediction == 1])
        negative = total - positive

        res = DataResponse(
            predictions=responses,
            meta=PredictionsMeta(total=total, positive=positive, negative=negative),
        )

        # save to database
        batch_id = next(gen)
        res_entries = [response.model_dump() for response in responses]
        for entry in res_entries:
            entry["batchId"] = batch_id
        predictions_collection.insert_many(res_entries)

        return PredictionsResponse(message="Success", status=200, data=res)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Failed to predict sentiment")


@router.post("/batch/file")
async def predict_batch_file(file: UploadFile):
    try:
        contents = file.file.read()
        with open(file.filename, "wb") as f:
            f.write(contents)

        responses = []
        with open(file.filename, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                responses.append(
                    predict_service(
                        PredictionRequest(time=row["time"], text=row["data"])
                    )
                )

        total = len(responses)
        positive = len([response for response in responses if response.prediction == 1])
        negative = total - positive

        res = BatchDataResponse(
            filename=file.filename,
            timestamp=datetime.now(),
            predictions=responses,
            meta=PredictionsMeta(total=total, positive=positive, negative=negative),
        )

        # save to database
        batch_id = next(gen)
        res_entries = [response.model_dump() for response in responses]
        for entry in res_entries:
            entry["batchId"] = batch_id
        predictions_collection.insert_many(res_entries)

        return PredictionsBatchFileResponse(message="Success", status=200, data=res)
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Failed to predict sentiment")
    finally:
        file.file.close()
