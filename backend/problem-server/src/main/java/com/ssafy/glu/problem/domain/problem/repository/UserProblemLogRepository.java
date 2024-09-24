package com.ssafy.glu.problem.domain.problem.repository;

import java.util.Optional;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import com.ssafy.glu.problem.domain.problem.domain.Problem;
import com.ssafy.glu.problem.domain.problem.domain.UserProblemLog;

@Repository
public interface UserProblemLogRepository extends MongoRepository<UserProblemLog,String> {
}
