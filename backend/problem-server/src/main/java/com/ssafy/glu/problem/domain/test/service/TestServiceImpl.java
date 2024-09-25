package com.ssafy.glu.problem.domain.test.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.ssafy.glu.problem.domain.common.dto.CommonCodeResponse;
import com.ssafy.glu.problem.domain.problem.domain.Problem;
import com.ssafy.glu.problem.domain.problem.domain.ProblemTypeCode;
import com.ssafy.glu.problem.domain.problem.dto.grading.GradeResult;
import com.ssafy.glu.problem.domain.problem.dto.request.ProblemSolveRequest;
import com.ssafy.glu.problem.domain.problem.dto.response.ProblemGradingResultResponse;
import com.ssafy.glu.problem.domain.problem.dto.response.TypeGradingResultResponse;
import com.ssafy.glu.problem.domain.problem.event.ProblemSolvedEventPublisher;
import com.ssafy.glu.problem.domain.problem.exception.problem.ProblemNotFoundException;
import com.ssafy.glu.problem.domain.problem.repository.ProblemRepository;
import com.ssafy.glu.problem.domain.problem.service.ProblemGradingServiceImpl;
import com.ssafy.glu.problem.domain.test.domain.Test;
import com.ssafy.glu.problem.domain.test.dto.request.TestSolveRequest;
import com.ssafy.glu.problem.domain.test.dto.response.TestGradingResponse;
import com.ssafy.glu.problem.domain.test.repository.TestRepository;
import com.ssafy.glu.problem.domain.user.service.UserService;
import com.ssafy.glu.problem.global.feign.dto.ExpUpdateResponse;
import com.ssafy.glu.problem.global.feign.dto.UserResponse;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class TestServiceImpl implements TestService {
	private final TestRepository testRepository;
	private final ProblemRepository problemRepository;
	private final UserService userService;
	private final ProblemGradingServiceImpl problemGradingServiceImpl;
	private final ProblemSolvedEventPublisher problemSolvedEventPublisher;

	@Override
	public TestGradingResponse gradeTest(Long userId, TestSolveRequest request) {
		UserResponse user = userService.getUser(userId);

		// 문제별 채점 수행 및 결과 리스트 생성
		List<GradeResult> gradeResultList = new ArrayList<>();
		List<ProblemGradingResultResponse> gradingResultByProblemList = gradeProblems(userId, user, request,
			gradeResultList);

		// 경험치 업데이트 및 응답 처리
		ExpUpdateResponse expUpdateResponse = userService.updateUserExp(user, userId, gradeResultList);

		// 유형별 채점 결과 생성
		List<TypeGradingResultResponse> gradingResultByTypeList = createTypeGradingResultList(gradeResultList);

		// Test 객체 생성 및 저장
		Test test = createAndSaveTest(userId, request, gradeResultList);

		// 최종 응답 생성
		return createTestGradingResponse(test, gradingResultByTypeList, gradingResultByProblemList, expUpdateResponse);
	}

	private List<ProblemGradingResultResponse> gradeProblems(Long userId, UserResponse user, TestSolveRequest request,
		List<GradeResult> gradeResultList) {
		List<ProblemGradingResultResponse> gradingResultByProblemList = new ArrayList<>();
		for (ProblemSolveRequest problemSolveRequest : request.problemSolveRequestList()) {
			Problem problem = getProblemOrThrow(problemSolveRequest.problemId());

			GradeResult gradeResult = problemGradingServiceImpl.gradeProblem(user, problem, problemSolveRequest);
			gradeResultList.add(gradeResult);

			gradingResultByProblemList.add(
				ProblemGradingResultResponse.of(problem, gradeResult.isCorrect(), problemSolveRequest)
			);

			problemSolvedEventPublisher.publish(userId, problem, gradeResult, problemSolveRequest);
		}
		return gradingResultByProblemList;
	}

	private List<TypeGradingResultResponse> createTypeGradingResultList(List<GradeResult> gradeResultList) {
		Map<ProblemTypeCode, List<GradeResult>> resultsByType = gradeResultList.stream()
			.collect(Collectors.groupingBy(GradeResult::problemTypeCode));

		return resultsByType.entrySet().stream()
			.map(entry -> {
				ProblemTypeCode problemTypeCode = entry.getKey();
				List<GradeResult> typeGradeResults = entry.getValue();

				int correctCount = (int)typeGradeResults.stream().filter(GradeResult::isCorrect).count();
				int totalAcquiredScore = typeGradeResults.stream().mapToInt(GradeResult::acquiredScore).sum();
				int totalScore = typeGradeResults.stream().mapToInt(GradeResult::totalUserScore).sum();

				return TypeGradingResultResponse.builder()
					.correctCount(correctCount)
					.problemTypeCode(CommonCodeResponse.of(problemTypeCode))
					.acquiredScore(totalAcquiredScore)
					.totalScore(totalScore)
					.build();
			}).collect(Collectors.toList());
	}

	private Test createAndSaveTest(Long userId, TestSolveRequest request, List<GradeResult> gradeResultList) {
		Test test = Test.builder()
			.correctCount((int)gradeResultList.stream().filter(GradeResult::isCorrect).count())
			.totalSolveTime(request.totalSolvedTime())
			.userId(userId)
			.userProblemLogIdList(gradeResultList.stream()
				.map(GradeResult::problemTypeCode)
				.map(ProblemTypeCode::name)
				.collect(Collectors.toList()))
			.build();

		return testRepository.save(test);
	}

	private TestGradingResponse createTestGradingResponse(
		Test test,
		List<TypeGradingResultResponse> gradingResultByTypeList,
		List<ProblemGradingResultResponse> gradingResultByProblemList,
		ExpUpdateResponse expUpdateResponse) {

		return TestGradingResponse.builder()
			.testId(test.getTestId())
			.totalCorrectCount(test.getCorrectCount())
			.totalSolvedTime(test.getTotalSolveTime())
			.gradingResultByTypeList(gradingResultByTypeList)
			.gradingResultByProblemList(gradingResultByProblemList)
			.totalAcquiredScore(gradingResultByTypeList.stream().mapToInt(TypeGradingResultResponse::totalScore).sum())
			.isStageUp(expUpdateResponse.isStageUp())
			.stageUpUrl(expUpdateResponse.stageUpUrl())
			.build();
	}

	// 문제 ID로 문제 가져오기
	private Problem getProblemOrThrow(String problemId) {
		return problemRepository.findById(problemId).orElseThrow(ProblemNotFoundException::new);
	}
}
