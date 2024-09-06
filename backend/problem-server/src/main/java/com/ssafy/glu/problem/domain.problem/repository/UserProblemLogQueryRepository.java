package com.ssafy.glu.problem.domain.problem.repository;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import com.ssafy.glu.problem.domain.problem.domain.Problem;
import com.ssafy.glu.problem.domain.problem.dto.request.UserProblemLogSearchCondition;

public interface UserProblemLogQueryRepository {
    Page<Problem> findAllProblemInLogByCondition(Long userId, UserProblemLogSearchCondition condition, Pageable pageable);
}