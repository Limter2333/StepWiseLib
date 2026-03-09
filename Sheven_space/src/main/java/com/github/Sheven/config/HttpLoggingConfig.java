package com.github.Sheven.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.web.client.RestClientCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpRequest;
import org.springframework.http.client.*;
import org.springframework.util.StreamUtils;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.stream.Collectors;

@Slf4j
@Configuration
public class HttpLoggingConfig {

    /**
     * 配置 RestClient 添加日志拦截器
     */
    @Bean
    public RestClientCustomizer restClientCustomizer() {
        return builder -> {
            // 使用 BufferingClientHttpRequestFactory 允许重复读取 Body
            BufferingClientHttpRequestFactory factory = new BufferingClientHttpRequestFactory(
                    new SimpleClientHttpRequestFactory()
            );

            builder.requestFactory(factory)
                    .requestInterceptor(new LoggingInterceptor());
        };
    }

    /**
     * HTTP 日志拦截器
     */
    public static class LoggingInterceptor implements ClientHttpRequestInterceptor {

        @Override
        public ClientHttpResponse intercept(HttpRequest request, byte[] body, ClientHttpRequestExecution execution) throws IOException {
            // 1. 记录请求信息
            logRequest(request, body);

            // 2. 执行请求
            ClientHttpResponse response = execution.execute(request, body);

            // 3. 记录响应信息（包装响应以支持重复读取）
            return logResponse(response);
        }

        private void logRequest(HttpRequest request, byte[] body) {
            log.info("========== DashScope HTTP Request ==========");
            log.info("URI         : {}", request.getURI());
            log.info("Method      : {}", request.getMethod());
            log.info("Headers     : {}", request.getHeaders());

            // 脱敏处理：隐藏 Authorization 中的完整 API Key
            if (request.getHeaders().containsKey("Authorization")) {
                String auth = request.getHeaders().getFirst("Authorization");
                if (auth != null && auth.length() > 20) {
                    log.info("Authorization: {}...", auth.substring(0, 20));
                }
            }

            // 打印请求体（JSON）
            if (body != null && body.length > 0) {
                String requestBody = new String(body, StandardCharsets.UTF_8);
                // 可以格式化 JSON（可选）
                log.info("Request Body: {}", requestBody);
            }
            log.info("===========================================");
        }

        private ClientHttpResponse logResponse(ClientHttpResponse response) throws IOException {
            // 读取响应体
            String body = new BufferedReader(
                    new InputStreamReader(response.getBody(), StandardCharsets.UTF_8))
                    .lines()
                    .collect(Collectors.joining("\n"));

            log.info("========== DashScope HTTP Response ==========");
            log.info("Status Code  : {}", response.getStatusCode());
            log.info("Status Text  : {}", response.getStatusText());
            log.info("Headers      : {}", response.getHeaders());
            log.info("Response Body: {}", body);
            log.info("============================================");

            // 返回包装后的响应，因为 Body 只能读取一次
            return new BufferedClientHttpResponseWrapper(response, body.getBytes(StandardCharsets.UTF_8));
        }
    }

    /**
     * 响应包装类 - 允许 Body 被多次读取
     */
    public static class BufferedClientHttpResponseWrapper implements ClientHttpResponse {
        private final ClientHttpResponse response;
        private final byte[] body;

        public BufferedClientHttpResponseWrapper(ClientHttpResponse response, byte[] body) {
            this.response = response;
            this.body = body;
        }

        @Override
        public org.springframework.http.HttpStatusCode getStatusCode() throws IOException {
            return response.getStatusCode();
        }

        @Override
        public String getStatusText() throws IOException {
            return response.getStatusText();
        }

        @Override
        public void close() {
            response.close();
        }

        @Override
        public java.io.InputStream getBody() throws IOException {
            return new java.io.ByteArrayInputStream(body);
        }

        @Override
        public org.springframework.http.HttpHeaders getHeaders() {
            return response.getHeaders();
        }
    }
}