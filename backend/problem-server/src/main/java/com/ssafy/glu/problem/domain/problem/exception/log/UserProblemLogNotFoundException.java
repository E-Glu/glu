package com.ssafy.glu.problem.domain.problem.exception.log;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

import com.ssafy.glu.problem.global.error.ErrorCode;
import com.ssafy.glu.problem.global.error.ServiceException;

@ResponseStatus(HttpStatus.NOT_FOUND)
public class UserProblemLogNotFoundException extends ServiceException {
	private static final ErrorCode errorCode = ErrorCode.USER_PROBLEM_LOG_NOT_FOUND;

	public UserProblemLogNotFoundException() {
		super(errorCode);
	}

	public UserProblemLogNotFoundException(Exception exception) {
		super(errorCode, exception);
	}
}
