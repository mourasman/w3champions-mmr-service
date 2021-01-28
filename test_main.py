from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def run_test(mmr0, rd0, winning_team, number_of_teams, mmr1, rd1):
    response = client.post(
        "/mmr/update",
        json={
            "ratings_list": mmr0,
            "rds_list": rd0,
            "winning_team": winning_team,
            "number_of_teams": number_of_teams
        },
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
        [1400, 1600, 1340, 1700],
        [350, 350, 350, 350],
        0,
        2,
        [1467, 1658, 1269, 1645],
        [323, 327, 328, 337]
    )


def test_1x1():
    run_test(
        [2000, 1500],
        [90, 350],
        0,
        2,
        [2002, 1467],
        [89, 316]
    )
    run_test(
        [2000, 1500],
        [90, 350],
        1,
        2,
        [1986, 1732],
        [90, 336]
    )


def test_4x4():
    run_test(
        [1400, 1600, 1340, 1700, 1563, 1490, 1520, 1590],
        [350, 350, 350, 350, 278, 290, 310, 302],
        0,
        2,
        [1455, 1649, 1397, 1746, 1532, 1454, 1479, 1553],
        [327, 331, 326, 333, 276, 286, 306, 299]
    )


def test_ffa():
    run_test(
        [1400, 1600, 1340, 1700],
        [350, 350, 350, 350],
        2,
        4,
        [1370, 1555, 1473, 1646],
        [330, 329, 354, 330]
    )