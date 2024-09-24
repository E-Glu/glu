package com.ssafy.glu.problem.domain.problem.dto.response;

import com.ssafy.glu.problem.domain.problem.dto.grading.GradeResult;
import com.ssafy.glu.problem.global.feign.dto.ExpUpdateResponse;

import lombok.Builder;

@Builder
public record ProblemGradingResponse(
	boolean isCorrect,
	Integer acquiredScore,
	Integer totalScore,
	boolean isStageUp,
	String stageUpUrl
) {
	public static ProblemGradingResponse of(GradeResult gradeResult) {
		return ProblemGradingResponse.builder()
			.isCorrect(gradeResult.isCorrect())
			.acquiredScore(gradeResult.acquiredScore())
			.totalScore(gradeResult.updatedUserScore())
			.build();
	}

	public static ProblemGradingResponse of(GradeResult gradeResult, ExpUpdateResponse expUpdateResponse) {
		return ProblemGradingResponse.builder()
			.isCorrect(gradeResult.isCorrect())
			.acquiredScore(gradeResult.acquiredScore())
			.totalScore(gradeResult.updatedUserScore())
			.isStageUp(expUpdateResponse.isStageUp())
			.stageUpUrl(expUpdateResponse.stageUpUrl())
			.build();
	}
}
