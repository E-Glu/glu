from collections import defaultdict
from typing import Optional

import random

import httpx
import numpy as np
from fastapi import APIRouter, Header

from repositories import get_wrong_sevendays, get_correct_sevendays
from repositories.problem_repositories import (
    get_problem_by_id,
    get_problem_by_ids,
    get_similar, get_random_problems_by_log)
from repositories.problem_repositories import get_random_problems_by_code_and_level
from models import ProblemResponse

from fastapi import HTTPException

router = APIRouter(prefix="/api/recommend", tags=["recommend"])

classifications = [
    "의사소통", "예술경험", "신체운동_건강", "자연탐구",
    "사회관계", "시사", "과학", "문화",
    "사설", "교육", "경제", "nie"
]
story_classifications = [0, 1, 2, 3, 4]
news_classifications = [5, 6, 7, 8, 9, 10, 11]

code_classifications = {
    "PT0211": story_classifications,
    "PT0221": news_classifications,
    "PT0222": news_classifications,
    "PT0311": story_classifications,
    "PT0312": story_classifications,
    "PT0321": news_classifications
}

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


async def get_user_info(user_id: str) -> dict:
    headers = {"X-User-Id": user_id}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://glu-user:8082/api/users",
            headers=headers
        )

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to call other service", "status_code": response.status_code}


@router.get(
    path="/test/level",
    summary="레벨 테스트 생성",
    description="사용자 나이를 기반으로 레벨 테스트 문제집을 생성합니다."
)
async def get_level_test(user_id: Optional[str] = Header(None, alias="X-User-Id")):
    try:
        # 사용자 정보 API 호출
        user_info = await get_user_info(user_id)
        birth_date = user_info['birth']

        if not birth_date:
            raise HTTPException(status_code=400, detail="사용자 출생일 정보가 없습니다.")
        # 출생일을 기준으로 나이 계산
        age = calculate_age(birth_date)
        # 나이를 기반으로 사용자 레벨 계산
        user_level = calculate_user_level(age)

    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"사용자 정보를 불러오는 중 오류가 발생했습니다: {exc}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    selected_problems = []
    user_levels = get_user_levels(user_level)

    # 각 대유형별로 문제 선택
    for pt_type, detail_codes in detail_codes_dict.items():
        # 세부유형 순서를 랜덤하게 섞어 어떤 세부유형에서 문제를 가져올지 결정
        shuffled_detail_codes = detail_codes.copy()
        random.shuffle(shuffled_detail_codes)

        # 첫 두 세부유형에서 2개씩, 마지막 세부유형에서 1개를 가져옴
        problem_counts = [2, 2, 1]

        for i, count in enumerate(problem_counts):
            detail_code = shuffled_detail_codes[i]  # 랜덤으로 섞인 세부유형에서 가져오기
            fetched_problems = get_random_problems_by_code_and_level(
                detail_code=detail_code,
                levels=user_levels,
                limit=count
            )

            # fetched_problems가 MongoDB에서 가져온 경우 ObjectId를 문자열로 변환
            for problem in fetched_problems:
                response = ProblemResponse.from_problem(problem)
                selected_problems.append(response)

    # 총 15문제가 선택되었는지 확인
    if len(selected_problems) != 15:
        raise HTTPException(
            status_code=500,
            detail="문제 선택 과정에서 예상치 못한 오류가 발생했습니다."
        )

    return selected_problems


@router.get(
    path="/test/general",
    summary="종합 테스트 생성",
    description="사용자의 유형별 등급과 사용자의 문제 풀이 기록을 기반으로 추천된 종합 테스트 문제집을 생성합니다."
)
async def get_general_test(user_id: Optional[str] = Header(None, alias="X-User-Id")):
    user_problemtype_level = {}

    try:
        # 사용자 정보 API 호출
        user_info = await get_user_info(user_id)

        for problemType in user_info['problemTypeList']:
            user_problemtype_level[problemType['type']['code']] = problemType['level']


    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"사용자 정보를 불러오는 중 오류가 발생했습니다: {exc}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    selected_problems = []
    problem_id_list = []
    type_index = [0, 1, 2]

    # 3개 PT01 PT02 PT03
    for pt_type, detail_codes in detail_codes_dict.items():

        user_level = user_problemtype_level.get(pt_type)
        user_levels = get_user_levels(user_level)

        detail_types = [0, 1, 2]
        detail_types.extend(random.choices(type_index, k=2))

        # 인덱스와 레벨 배열 매칭
        indices = list(range(len(detail_types)))

        # 5개
        idx = 0
        for i in indices:
            detail_code = detail_codes_dict[pt_type][detail_types[i]]  # PT01 대유형에서 detail_code 선택
            fetched_problems = None

            if idx < 3:
                fetched_problems = get_random_problems_by_code_and_level(
                    detail_code=detail_code,
                    levels=user_levels,
                    limit=1,
                    problem_id_list=problem_id_list
                )
                idx = idx + 1
            else:
                if pt_type == "PT01":
                    # 문제 가져오기
                    fetched_problems = get_random_problems_by_code_and_level(
                        detail_code=detail_code,
                        levels=user_levels,
                        limit=1,
                        problem_id_list=problem_id_list
                    )
                else:
                    wrong_status = get_wrong_status(int(user_id))

                    if wrong_status != {}:

                        top_classifications = top_n_classification(2, wrong_status)
                        for classification in top_classifications:
                            correct_ids = get_correct_ids(int(user_id))
                            wrong_ids = get_wrong_ids(int(user_id))

                            fetched_problems = get_random_problems_by_log(
                                detail_code=detail_code,
                                levels=user_levels,
                                correct_ids=correct_ids,
                                wrong_ids=wrong_ids,
                                vector=classification[3],
                                num=1,
                                problem_id_list=problem_id_list
                            )
                    else:

                        # 틀린 문제 없을때
                        if fetched_problems == None:
                            fetched_problems = get_random_problems_by_code_and_level(
                                detail_code=detail_code,
                                levels=user_levels,
                                limit=1,
                                problem_id_list = problem_id_list
                            )

            if fetched_problems:
                response = ProblemResponse.from_problem(fetched_problems[0])
                selected_problems.append(response)
                problem_id_list.append(fetched_problems[0].id)

            print(f"pt_type {pt_type} len selected_problems: {len(selected_problems)}")
            print("fetched_problems:", fetched_problems)
    # 총 15문제가 선택되었는지 확인
    if len(selected_problems) != 15:
        raise HTTPException(
            status_code=500,
            detail="문제 선택 과정에서 예상치 못한 오류가 발생했습니다."
        )

    return selected_problems


# 10개 가져오기
@router.get(
    path="/type",
    summary="유형별 학습 문제 리스트 생성",
    description="사용자의 유형별 등급과 사용자의 문제 풀이 기록을 기반으로 추천된 유형별 학습 문제집을 생성합니다."
)
async def get_type_problem_set(user_id: Optional[str] = Header(None, alias="X-User-Id")):
    user_problemtype_level = {}

    try:
        # 사용자 정보 API 호출
        user_info = await get_user_info(user_id)

        for problemType in user_info['problemTypeList']:
            user_problemtype_level[problemType['type']['code']] = problemType['level']


    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"사용자 정보를 불러오는 중 오류가 발생했습니다: {exc}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    selected_problems = make_type_problems(user_id, user_problemtype_level)

    return selected_problems


def make_type_problems(user_id, user_problemtype_level):
    selected_problems = []

    i = 0
    for pt_type, detail_codes in detail_codes_dict.items():

        user_level = user_problemtype_level[pt_type]
        user_levels = get_user_levels(user_level)
        type_counts = [3, 3, 4]  # 각 항목의 개수를 지정, 총합이 10

        idx = 0
        for detail_code in detail_codes:
            if idx >= len(type_counts):
                break

            current_count = type_counts[idx]

            # 10개
            if pt_type == "PT01":
                # 문제 가져오기
                fetched_problems = get_random_problems_by_code_and_level(
                    detail_code=detail_code,
                    levels=user_levels,
                    limit=current_count
                )
            # 20개
            else:
                wrong_status = get_wrong_status(int(user_id))
                top_classifications = top_n_classification(type_counts[i], wrong_status)

                pt_detail_classifications = [item for item in top_classifications if item[1].startswith(detail_code)]

                #빈 배열일때
                if not pt_detail_classifications :
                    fetched_problems = get_random_problems_by_code_and_level(
                        detail_code=detail_code,
                        levels=user_levels,
                        limit=current_count
                    )
                #빈 배열 아닐때
                else :
                    correct_ids = get_correct_ids(int(user_id))
                    wrong_ids = get_wrong_ids(int(user_id))

                    fetched_problems = get_random_problems_by_log(
                        detail_code=detail_code,
                        levels=user_levels,
                        correct_ids=correct_ids,
                        wrong_ids=wrong_ids,
                        vector=pt_detail_classifications[0][3],
                        num=type_counts[idx]
                    )

            for fetched_problem in fetched_problems:
                response = ProblemResponse.from_problem(fetched_problem)
                selected_problems.append(response)

            idx = idx + 1
    return selected_problems


def get_user_levels(user_level):
    user_levels = []
    levels = [-1,0,1]
    if user_level == 1:
        levels = [0, 1]
    elif user_level == 7:
        levels = [-1, 0]
    for level in levels:
        user_levels.append(f"PL0{user_level + level}")
    return user_levels


@router.get(
    path="/similar/{problem_id}",
    summary="유사한 문제 추천",
    description="현재 문제와 유사한 특성을 갖는 문제 3개를 추천해줍니다."
)
async def get_similar_problem_set(problem_id: str, user_id: Optional[str] = Header(None, alias="X-User-Id")):

    if not user_id:
        raise HTTPException(status_code=400, detail="유저ID가 없습니다.")

    find_problem = get_problem_by_id(problem_id)
    selected_problems = []

    if (find_problem.problemTypeCode == "PT01"):
        fetched_problems = get_random_problems_by_code_and_level(levels=[find_problem.problemLevelCode],
                                                      detail_code=find_problem.problemTypeDetailCode,
                                                      problem_id=problem_id)

        for fetched_problem in fetched_problems:
            response = ProblemResponse.from_problem(fetched_problem)
            selected_problems.append(response)

    else:
        fetched_problems = get_similar(find_problem.problemLevelCode, find_problem.problemTypeDetailCode,
                              find_problem.metadata.vector, problem_id)
        for fetched_problem in fetched_problems:
            response = ProblemResponse.from_problem(fetched_problem)
            selected_problems.append(response)

    return selected_problems


def get_correct_ids(user_id: int):
    return status_to_problem_ids(get_correct_sevendays(user_id))


def get_wrong_ids(user_id: int):
    return status_to_problem_ids(get_wrong_sevendays(user_id))

def status_to_problem_ids(status_list):
    problem_ids = []

    for status in status_list:
        if 'problem' in status and status['problem'] is not None:
            if '_id' in status['problem']:
                # ObjectId를 문자열로 변환
                problem_id = str(status['problem']['_id'])
                problem_ids.append(problem_id)  # 문제 ID 추가

    return problem_ids




def get_wrong_status(user_id: int):
    wrong_problem_ids = get_wrong_ids(user_id)

    problems = get_problem_by_ids(wrong_problem_ids)
    if not problems:
        return {}

    # classification_vectors를 중첩 defaultdict로 정의
    classification_vectors = defaultdict(lambda: defaultdict(list))

    for problem in problems:

        if (problem.problemTypeCode == "PT01"): continue

        # classification_vectors에 추가
        classification_vectors[problem.metadata.classification][problem.problemTypeDetailCode].append(problem.metadata.vector)

    # 각 classification에 대해 detailcode별 평균 벡터와 횟수 계산
    classification_avg_vectors = {}
    for classification, detail_codes in classification_vectors.items():
        classification_avg_vectors[classification] = {}
        for detailcode, vectors in detail_codes.items():
            # numpy를 사용하여 각 벡터 요소별 평균 계산
            avg_vector = np.mean(vectors, axis=0).tolist()
            count = len(vectors)  # 벡터의 개수 (횟수) 계산

            # 평균 벡터와 횟수를 함께 저장
            classification_avg_vectors[classification][detailcode] = {
                "average_vector": avg_vector,
                "count": count
            }

    return classification_avg_vectors


def top_n_classification(n, map):
    result = []
    for ckey in map.keys():
        detail_code_map = map.get(ckey)
        for dkey in detail_code_map.keys():
            value = detail_code_map.get(dkey)
            count = value.get('count')
            avg_vector = value.get('average_vector')

            result.append((ckey, dkey, count, avg_vector))

    result_sorted = sorted(result, key=lambda x: x[2], reverse=True)
    final_result = []

    if not result_sorted:
        try:
            random_problems = get_random_problems_by_code_and_level()
            final_result.extend(random_problems)
        except Exception as e:
            return final_result  # 빈 리스트 반환
    else:
        if len(result_sorted) >= n:
            final_result = result_sorted[:n]
        else:
            index = 0
            while len(final_result) < n:
                final_result.append(result_sorted[index % len(result_sorted)])
                index += 1

    return final_result
