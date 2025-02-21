package com.ssafy.glu.problem.domain.test.dto.response;

import java.time.LocalDateTime;
import java.util.List;

import com.ssafy.glu.problem.domain.problem.domain.UserProblemLog;
import com.ssafy.glu.problem.domain.problem.dto.response.ProblemGradingResultResponse;
import com.ssafy.glu.problem.domain.problem.dto.response.TypeGradingResultResponse;
import com.ssafy.glu.problem.domain.test.domain.Test;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;

@Builder
@Schema(description = "테스트 채점 상세 응답 DTO")
public record TestGradingDetailResponse(
	@Schema(description = "테스트 ID", example = "test-123")
	String testId,

	@Schema(description = "전체 정답 수", example = "5")
	Integer totalCorrectCount,

	@Schema(description = "전체 풀이 시간", example = "600")
	Integer totalSolvedTime,

	@Schema(description = "생성 날짜")
	LocalDateTime createdDate,

	@Schema(description = "유형별 채점 결과 목록")
	List<TypeGradingResultResponse> gradingResultByTypeList,

	@Schema(description = "문제별 채점 결과 목록")
	List<ProblemGradingResultResponse> gradingResultByProblemList
) {
	public static TestGradingDetailResponse of(Test test, List<UserProblemLog> userProblemLogList) {
		if (test == null)
			return null;
		return TestGradingDetailResponse.builder()
			.testId(test.getTestId())
			.totalCorrectCount(test.getCorrectCount())
			.totalSolvedTime(test.getTotalSolveTime())
			.createdDate(test.getCreatedDate())
			.gradingResultByTypeList(TypeGradingResultResponse.createGradingResultByTypeList(userProblemLogList))
			.gradingResultByProblemList(
				ProblemGradingResultResponse.createGradingResultByProblemList(userProblemLogList))
			.build();
	}
}
