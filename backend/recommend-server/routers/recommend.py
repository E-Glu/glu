from collections import defaultdict
from typing import Optional

import numpy as np
from fastapi import APIRouter, HTTPException,  Header

from models import Problem
from repositories import get_all_problems, get_problems_not_solve, get_wrong_sevendays, get_correct_sevendays
from repositories.problem_repositories import get_one_problem

router = APIRouter(prefix="/api/recommend", tags=["recommend"])

classifications = [
    "의사소통", "예술경험", "신체운동_건강", "자연탐구",
    "사회관계", "시사", "과학", "문화",
    "사설", "교육", "경제", "nie"
]

detail_codes_list = [
    "PT0111", "PT0112", "PT0121",
    "PT0211", "PT0221", "PT0222",
    "PT0311", "PT0312", "PT0321"
]

@router.get("/test/level")
async def get_level_test(user_id: Optional[str] = Header(None, alias="X-User-Id")):
    # if not user_id:
    #     raise HTTPException(status_code=400, detail="유저ID가 없습니다.")

    # 더미 데이터 생성
    problem_data = get_one_problem()

    print("problem data", problem_data)

    # 날짜 형식 변환
    from datetime import datetime
    problem_data['createdDate'] = datetime.fromisoformat(problem_data['createdDate'])
    problem_data['modifiedDate'] = datetime.fromisoformat(problem_data['modifiedDate'])

    # Pydantic 모델을 사용해 데이터 변환
    problem = Problem(**problem_data)

    print("problem info" , problem)
    return problem


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

@router.get("/wrong")
async def get_wrong_status():
    status = get_wrong_sevendays(1)

    #초기화
    map_dict = {key: [] for key in detail_codes_list}

    # classification_vectors를 중첩 defaultdict로 정의
    classification_vectors = defaultdict(lambda: defaultdict(list))

    for document in status:
        # document에서 classification과 vector를 추출
        classification = document["problem"]["classification"]
        vector = document["problem"]["vector"]
        detailcode = document["problem"]["problemType"]["problemTypeCode"] + document["problem"]["problemTypeDetail"]["problemTypeDetailCode"]

        # classification_vectors에 추가
        classification_vectors[classification][detailcode].append(vector)

    print("classification_vector", classification_vectors)

    # 각 classification에 대해 detailcode별 평균 벡터 계산
    classification_avg_vectors = {}
    for classification, detail_codes in classification_vectors.items():
        classification_avg_vectors[classification] = {}
        for detailcode, vectors in detail_codes.items():
            # numpy를 사용하여 각 벡터 요소별 평균 계산
            avg_vector = np.mean(vectors, axis=0).tolist()
            classification_avg_vectors[classification][detailcode] = avg_vector

    print("classification_avg_vectors:", classification_avg_vectors)

    return "wrong call"


@router.get("/not_solve")
async def not_solve_problems():
    not_solve_problems = get_problems_not_solve(1)
    return not_solve_problems