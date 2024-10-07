package com.ssafy.glu.problem.global.dto;

import lombok.Getter;
import org.springframework.data.domain.Page;

import java.util.List;

@Getter
public class PageResponse<T> {
	private final List<T> content;
	private final int page;
	private final int size;
	private final int totalPages;
	private final long totalElements;

	public PageResponse(Page<T> page) {
		this.content = page.getContent();
		this.page = page.getNumber()+1;
		this.size = page.getSize();
		this.totalPages = page.getTotalPages();
		this.totalElements = page.getTotalElements();
	}
}
