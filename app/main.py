from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.wallet import wallet_router

app = FastAPI()

app.include_router(wallet_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        content={"message": f"ValidationError: {exc.errors()[0]["msg"]}"},
        status_code=422
    )
