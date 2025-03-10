package com.ssafy.glu.problem.domain.problem.repository;

import static org.assertj.core.api.Assertions.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.data.mongo.DataMongoTest;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.ActiveProfiles;

import com.ssafy.glu.problem.domain.problem.domain.Problem;
import com.ssafy.glu.problem.domain.problem.domain.ProblemMemo;
import com.ssafy.glu.problem.domain.problem.domain.UserProblemStatus;
import com.ssafy.glu.problem.domain.problem.dto.request.ProblemSearchCondition;
import com.ssafy.glu.problem.domain.problem.exception.status.UserProblemStatusNotFoundException;
import com.ssafy.glu.problem.util.MockFactory;

import lombok.extern.slf4j.Slf4j;

@DataMongoTest
@ActiveProfiles("test")
@DirtiesContext
@Slf4j
public class UserProblemStatusRepositoryTest {
	@Autowired
	private UserProblemStatusRepository userProblemStatusRepository;
	@Autowired
	private ProblemRepository problemRepository;

	private final int NUM_PROBLEMS = 3;
	private List<Problem> problemList;
	private final Long[] userIdList = {1L, 2L, 3L, 4L};

	@BeforeEach
	public void setUp() throws InterruptedException {
		problemRepository.deleteAll();
		userProblemStatusRepository.deleteAll();

		problemList = new ArrayList<>();
		for (int i = 0; i < NUM_PROBLEMS; i++) {
			problemList.add(problemRepository.save(MockFactory.createProblem()));
		}

		// 유저별 풀이 상태 등록
		for (Long userId : userIdList) {
			userProblemStatusRepository.save(
				MockFactory.createUserProblemStatus(userId, Problem.Status.CORRECT, problemList.get(0),
					Map.of(1L, "메모1", 2L, "메모2"), false));
			userProblemStatusRepository.save(
				MockFactory.createUserProblemStatus(userId, Problem.Status.WRONG, problemList.get(1), Map.of(1L, "메모1"),
					true));
			userProblemStatusRepository.save(
				MockFactory.createUserProblemStatus(userId, Problem.Status.WRONG, problemList.get(2), Map.of(), true));
		}
	}

	@Test
	void createMemo() {
		Long userId = userIdList[0];
		Problem problem = problemList.get(2);

		// UserProblemStatus를 userId와 problemId로 조회
		UserProblemStatus userProblemStatus = userProblemStatusRepository.findByUserIdAndProblem_ProblemId(userId,
			problem.getProblemId()).orElseThrow(UserProblemStatusNotFoundException::new);

		String content = "새로운 메모 내용";
		// 메모 추가
		ProblemMemo problemMemo = userProblemStatus.addMemo(content);

		assertThat(userProblemStatus.getMemoList().size()).isEqualTo(1);
		assertThat(problemMemo.getContent()).isEqualTo(content);
	}

	@Test
	void searchUserProblemStatusOfCorrectTest() {
		Long userId = userIdList[0];

		ProblemSearchCondition condition = ProblemSearchCondition.builder()
			.status(Problem.Status.CORRECT)
			.build();

		Page<UserProblemStatus> userProblemStatusList = userProblemStatusRepository.findAllProblemByCondition(userId,
			condition, Pageable.ofSize(10));

		assertThat(userProblemStatusList.getTotalElements()).isEqualTo(1);
	}

	@Test
	void searchUserProblemStatusOfWrongTest() {
		Long userId = userIdList[0];

		ProblemSearchCondition condition = ProblemSearchCondition.builder()
			.status(Problem.Status.WRONG)
			.build();

		Page<UserProblemStatus> userProblemStatusList = userProblemStatusRepository.findAllProblemByCondition(userId,
			condition, Pageable.ofSize(10));

		assertThat(userProblemStatusList.getTotalElements()).isEqualTo(2);
	}

	@Test
	void searchUserProblemStatusOfHasMemoTest() {
		Long userId = userIdList[0];

		ProblemSearchCondition condition = ProblemSearchCondition.builder()
			.hasMemo(true)
			.build();

		Page<UserProblemStatus> userProblemStatusList = userProblemStatusRepository.findAllProblemByCondition(userId,
			condition, Pageable.ofSize(10));

		assertThat(userProblemStatusList.getTotalElements()).isEqualTo(2);
	}

	@Test
	void searchUserProblemStatusOfIsFavoriteTest() {
		Long userId = userIdList[0];

		ProblemSearchCondition condition = ProblemSearchCondition.builder()
			.isFavorite(true)
			.build();

		Page<UserProblemStatus> userProblemStatusList = userProblemStatusRepository.findAllProblemByCondition(userId,
			condition, Pageable.ofSize(10));

		assertThat(userProblemStatusList.getTotalElements()).isEqualTo(2);
	}

	@Test
	void searchUserProblemStatusOfAllCondition() {
		Long userId = userIdList[0];

		ProblemSearchCondition condition = ProblemSearchCondition.builder()
			.status(Problem.Status.WRONG)
			.hasMemo(true)
			.isFavorite(true)
			.build();

		Page<UserProblemStatus> userProblemStatusList = userProblemStatusRepository.findAllProblemByCondition(userId,
			condition, Pageable.ofSize(10));

		assertThat(userProblemStatusList.getTotalElements()).isEqualTo(1);
	}

	@Test
	void updateMemo() {
		Long userId = userIdList[0];
		Problem problem = problemList.get(0);

		// UserProblemStatus를 userId와 problemId로 조회
		UserProblemStatus userProblemStatus = userProblemStatusRepository.findByUserIdAndProblem_ProblemId(userId,
			problem.getProblemId()).orElseThrow(UserProblemStatusNotFoundException::new);

		String content = "새로운 메모 내용";

		int beforeCount = userProblemStatus.getMemoList().size();

		// 메모 추가
		ProblemMemo problemMemo = userProblemStatus.addMemo(content);

		assertThat(problemMemo.getContent()).isEqualTo(content);

		String newContent = "수정된 메모 내용";

		userProblemStatus.updateMemo(problemMemo.getMemoIndex(), newContent);
		userProblemStatusRepository.save(userProblemStatus);

		int afterCount = userProblemStatus.getMemoList().size();

		assertThat(userProblemStatus.getMemoList().size()).isEqualTo(afterCount);
		assertThat(problemMemo.getContent()).isEqualTo(newContent);
	}
}
