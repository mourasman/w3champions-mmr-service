import uvicorn
from fastapi import FastAPI

from mmr.update_mmr import UpdateMmrRequestBody, update_after_game, UpdateMmrResponseBody

app = FastAPI()


@app.post("/mmr/update")
async def update_mmr(body: UpdateMmrRequestBody) -> UpdateMmrResponseBody:
    for i, rd in enumerate(body.rds_list):
        if rd < 60.25:
            body.rds_list[i] = 60.25

    for i, rating in enumerate(body.ratings_list):
        if rating < 0:
            body.ratings_list[i] = 0

    return update_after_game(body.ratings_list, body.rds_list, 1 if body.t1_won else 0)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
