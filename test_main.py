from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def run_test(mmr0, rd0, t1win, mmr1, rd1):
    response = client.post(
        "/mmr/update",
        json={
          "ratings_list": mmr0,
          "rds_list": rd0,
          "t1_won": t1win},
    )
    assert response.status_code == 200

    result = response.json()

    ratings_list = result["ratings_list"]
    rds_list = result["rds_list"]

    rl = [round(num) for num in ratings_list]
    rd = [round(num) for num in rds_list]

    assert rl == mmr1
    assert rd == rd1


def test_2x2():
    run_test(
      [ 1400, 1600, 1340, 1700 ],
      [ 350, 350, 350, 350 ],
      True,
      [1530, 1714, 1203, 1592],
      [278, 278, 278, 278]
    )


def test_1x1():
    run_test(
      [ 2000, 1500 ],
      [ 90, 350 ],
      True,
      [2002, 1465],
      [90, 318]
    )
    run_test(
      [ 2000, 1500 ],
      [ 90, 350 ],
      False,
      [1966, 2021],
      [90, 318]
    )

