package com.smartclass.monitor.common.exception;

/**
 * 业务异常，携带 HTTP 状态码和错误信息。
 * GlobalExceptionHandler 会根据 code 映射对应的 HTTP 响应码。
 */
public class BusinessException extends RuntimeException {

    private final int code;
    private final String message;

    public BusinessException(int code, String message) {
        super(message);
        this.code = code;
        this.message = message;
    }

    public BusinessException(int code, String message, Throwable cause) {
        super(message, cause);
        this.code = code;
        this.message = message;
    }

    public int getCode() {
        return code;
    }

    @Override
    public String getMessage() {
        return message;
    }
}
