from collections import defaultdict
from typing import Optional

import httpx
import random
import numpy as np
from fastapi import APIRouter, HTTPException,  Header

from models import Problem
from repositories import get_all_problems, get_problems_not_solve, get_wrong_sevendays, get_correct_sevendays
from repositories.problem_repositories import get_one_problem, get_random_problems_by_code_and_level

router = APIRouter(prefix="/api/recommend", tags=["recommend"])

classifications = [
    "의사소통", "예술경험", "신체운동_건강", "자연탐구",
    "사회관계", "시사", "과학", "문화",
    "사설", "교육", "경제", "nie"
]

detail_codes_dict = {
    "PT01": ["PT0111", "PT0112", "PT0121"],
    "PT02": ["PT0211", "PT0221", "PT0222"],
    "PT03": ["PT0311", "PT0312", "PT0321"]
}

def calculate_age(birth_date: str) -> int:
    from datetime import datetime
    birth_date = datetime.strptime(birth_date, "%Y-%m-%d")
    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

def calculate_user_level(age: int) -> int:
    if 6 <= age <= 12:
        return age - 5  # 만 6세 -> 1레벨, 만 12세 -> 7레벨
    elif age < 6:
        return 1
    else:
        return 7


@router.get("/test/level")
async def get_level_test(user_id: Optional[str] = Header(None, alias="X-User-Id")):
    if not user_id:
        raise HTTPException(status_code=400, detail="유저ID가 없습니다.")

    # try:
    #     # 사용자 정보 API 호출
    #     async with httpx.AsyncClient() as client:
    #         response = await client.get(f"http://j11a506.p.ssafy.io:8082/api/users/{user_id}")
    #
    #     print(response)
    #     if response.status_code != 200:
    #         raise HTTPException(status_code=response.status_code, detail="사용자 정보를 불러올 수 없습니다.")
    #
    #     user_data = response.json()
    #     birth_date = user_data.get("birth")
    #     print(birth_date)
    #
    #     if not birth_date:
    #         raise HTTPException(status_code=400, detail="사용자 출생일 정보가 없습니다.")
    #
    #     # 출생일을 기준으로 나이 계산
    #     age = calculate_age(birth_date)
    #     # 나이를 기반으로 사용자 레벨 계산
    #     user_level = calculate_user_level(age)
    #
    # except httpx.RequestError as exc:
    #     raise HTTPException(status_code=500, detail=f"사용자 정보를 불러오는 중 오류가 발생했습니다: {exc}")
    # except ValueError as e:
    #     raise HTTPException(status_code=400, detail=str(e))

    selected_problems = []

    # 각 대유형별로 문제 선택
    for pt_type, detail_codes in detail_codes_dict.items():
        # 세부유형 순서를 랜덤하게 섞어 어떤 세부유형에서 1개를 가져올지 결정
        shuffled_detail_codes = detail_codes.copy()
        random.shuffle(shuffled_detail_codes)

        print(shuffled_detail_codes)
        # 첫 두 세부유형에서 2개씩, 마지막 세부유형에서 1개를 가져옴
        problem_counts = [2, 2, 1]

        for i, count in enumerate(problem_counts):
            detail_code = detail_codes[i]  # 각 세부유형에서 순서대로 가져오기
            fetched_problems = get_random_problems_by_code_and_level(
                detail_code=detail_code,
                level=6,
                limit=count
            )

            selected_problems.extend(fetched_problems)

    # 총 15문제가 선택되었는지 확인
    if len(selected_problems) != 15:
        raise HTTPException(
            status_code=500,
            detail="문제 선택 과정에서 예상치 못한 오류가 발생했습니다."
        )

    return selected_problems


@router.get("/test/general")
async def get_level_test(user_id: Optional[str] = Header(None, alias="X-User-Id")):
    if not user_id:
        raise HTTPException(status_code=400, detail="유저ID가 없습니다.")
    # 더미 데이터 생성
    return get_all_problems()



@router.get("/type")
async def get_level_test(user_id: Optional[str] = Header(None, alias="X-User-Id")):
    if not user_id:
        raise HTTPException(status_code=400, detail="유저ID가 없습니다.")
    # 더미 데이터 생성
    return get_all_problems()


@router.get("/similar")
async def get_level_test(user_id: Optional[str] = Header(None, alias="X-User-Id")):
    if not user_id:
        raise HTTPException(status_code=400, detail="유저ID가 없습니다.")
    # 더미 데이터 생성
    return get_all_problems()


@router.get("/correct")
async def get_correct_status():
    status = get_correct_sevendays(1)
    print("correct status", status)
    return "correct call"

# @router.get("/wrong")
# async def get_wrong_status():
#     status = get_wrong_sevendays(1)
#
#     #초기화
#     map_dict = {key: [] for key in detail_codes_list}
#
#     # classification_vectors를 중첩 defaultdict로 정의
#     classification_vectors = defaultdict(lambda: defaultdict(list))
#
#     for document in status:
#         # document에서 classification과 vector를 추출
#         classification = document["problem"]["classification"]
#         vector = document["problem"]["vector"]
#         detailcode = document["problem"]["problemType"]["problemTypeCode"] + document["problem"]["problemTypeDetail"]["problemTypeDetailCode"]
#
#         # classification_vectors에 추가
#         classification_vectors[classification][detailcode].append(vector)
#
#     print("classification_vector", classification_vectors)
#
#     # 각 classification에 대해 detailcode별 평균 벡터 계산
#     classification_avg_vectors = {}
#     for classification, detail_codes in classification_vectors.items():
#         classification_avg_vectors[classification] = {}
#         for detailcode, vectors in detail_codes.items():
#             # numpy를 사용하여 각 벡터 요소별 평균 계산
#             avg_vector = np.mean(vectors, axis=0).tolist()
#             classification_avg_vectors[classification][detailcode] = avg_vector
#
#     print("classification_avg_vectors:", classification_avg_vectors)
#
#     return "wrong call"


@router.get("/not_solve")
async def not_solve_problems():
    not_solve_problems = get_problems_not_solve(1)
    return not_solve_problems