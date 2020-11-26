from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_basic_mmr1():
    response = client.post(
        "/mmr/update",
        json={
          "ratings_list":
            [ 1400, 1600, 1340, 1700 ],
          "rds_list":
            [ 350, 350, 350, 350 ],
          "t1_won": True},
    )
    assert response.status_code == 200

    result = response.json()

    ratings_list = result["ratings_list"]
    rds_list = result["rds_list"]

    rl = [round(num) for num in ratings_list]
    rd = [round(num) for num in rds_list]

    assert rl == [1530, 1714, 1203, 1592]
    assert rd == [278, 278, 278, 278]


def test_basic_mmr2():
    response = client.post(
        "/mmr/update",
        json={
            "ratings_list": [2000, 1500],
            "rds_list": [30, 350],
            "t1_won": True},
    )
    assert response.status_code == 200

    result = response.json()

    ratings_list = result["ratings_list"]
    rds_list = result["rds_list"]

    rl = [round(num) for num in ratings_list]
    rd = [round(num) for num in rds_list]

    assert rl == [2001, 1467]
    assert rd == [61, 319]
