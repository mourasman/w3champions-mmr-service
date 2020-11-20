import uvicorn
from fastapi import FastAPI

from mmr.update_mmr import UpdateMmrRequestBody, update_after_game

app = FastAPI()


@app.post("/mmr/update")
async def update_mmr(body: UpdateMmrRequestBody):
    return update_after_game(body.ratings_list, body.rds_list, 1 if body.t1_won else 0)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
