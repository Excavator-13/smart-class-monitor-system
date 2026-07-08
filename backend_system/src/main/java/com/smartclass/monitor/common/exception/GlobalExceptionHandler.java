package com.smartclass.monitor.common.exception;

import com.smartclass.monitor.common.response.ApiResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 全局异常处理，将各类异常映射为统一的 ApiResponse 响应。
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    /** 参数校验失败 → 400 */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidation(MethodArgumentNotValidException ex) {
        String msg = ex.getBindingResult().getFieldErrors().stream()
                .map(e -> e.getField() + ": " + e.getDefaultMessage())
                .reduce((a, b) -> a + "; " + b)
                .orElse("参数校验失败");
        return ResponseEntity.badRequest()
                .body(ApiResponse.error(400, msg));
    }

    /** 业务异常 → 按 code 映射 */
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiResponse<Void>> handleBusiness(BusinessException ex) {
        HttpStatus status = HttpStatus.resolve(ex.getCode());
        if (status == null) {
            status = HttpStatus.INTERNAL_SERVER_ERROR;
        }
        return ResponseEntity.status(status)
                .body(ApiResponse.error(ex.getCode(), ex.getMessage()));
    }

    /** 数据库唯一约束冲突 → 409 */
    @ExceptionHandler(DuplicateKeyException.class)
    public ResponseEntity<ApiResponse<Void>> handleDuplicateKey(DuplicateKeyException ex) {
        log.warn("Duplicate key: {}", ex.getMessage());
        return ResponseEntity.status(HttpStatus.CONFLICT)
                .body(ApiResponse.error(409, "数据已存在或字段重复"));
    }

    /** 未预期异常 → 500，不暴露堆栈 */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleUnknown(Exception ex) {
        log.error("Unexpected error", ex);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.error(500, "服务内部异常"));
    }
}
