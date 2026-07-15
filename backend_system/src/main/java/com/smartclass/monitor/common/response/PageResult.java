package com.smartclass.monitor.common.response;

import java.util.List;

/**
 * 统一分页响应结构。字段命名与接口文档一致：records / page / page_size / total。
 */
public class PageResult<T> {

    private List<T> records;
    private int page;
    private int pageSize;
    private long total;

    private PageResult(List<T> records, int page, int pageSize, long total) {
        this.records = records;
        this.page = page;
        this.pageSize = pageSize;
        this.total = total;
    }

    public static <T> PageResult<T> of(List<T> records, int page, int pageSize, long total) {
        return new PageResult<>(records, page, pageSize, total);
    }

    public List<T> getRecords() {
        return records;
    }

    public int getPage() {
        return page;
    }

    public int getPageSize() {
        return pageSize;
    }

    public long getTotal() {
        return total;
    }
}
