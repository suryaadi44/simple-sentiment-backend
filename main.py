from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse

from prediction import router as prediction_router
from user import router as user_router
from auth import JWTBearer

token_listener = JWTBearer()

app = FastAPI()


@app.exception_handler(HTTPException)
async def http_exception_handler(request, e):
    return JSONResponse(
        status_code=e.status_code,
        content={
            "message": "Failed",
            "status": e.status_code,
            "error": e.detail,
        },
    )


app.include_router(
    prediction_router,
    tags=["prediction"],
    prefix="/predictions",
    dependencies=[Depends(token_listener)],
)
app.include_router(user_router, tags=["user"], prefix="/users")
