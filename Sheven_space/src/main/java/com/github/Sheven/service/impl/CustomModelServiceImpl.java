package com.github.Sheven.service.impl;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.github.Sheven.service.CustomModelService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

/**
 * Implementation of CustomModelService for calling custom unknown model via HTTP POST
 */
@Service
public class CustomModelServiceImpl implements CustomModelService {

    private static final Logger logger = LoggerFactory.getLogger(CustomModelServiceImpl.class);

    private final WebClient webClient;
    private final ObjectMapper objectMapper;

    @Value("${custom.model.base-url:http://123.com/api}")
    private String baseUrl;

    @Value("${custom.model.code:aaaa}")
    private String code;

    @Value("${custom.model.api-key:your-api-key-here}")
    private String apiKey;

    public CustomModelServiceImpl(WebClient.Builder webClientBuilder, ObjectMapper objectMapper) {
        this.webClient = webClientBuilder.build();
        this.objectMapper = objectMapper;
    }

    @Override
    public String chat(String message) {
        try {
            ObjectNode requestBody = createRequestBody(message);

            String response = webClient.post()
                    .uri(baseUrl)
                    .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();

            return parseResponse(response);
        } catch (Exception e) {
            logger.error("Error calling custom model", e);
            throw new RuntimeException("Failed to call custom model: " + e.getMessage(), e);
        }
    }

    @Override
    public Mono<String> streamChat(String message) {
        try {
            ObjectNode requestBody = createRequestBody(message);

            return webClient.post()
                    .uri(baseUrl)
                    .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(String.class)
                    .map(this::parseResponseSafe);
        } catch (Exception e) {
            logger.error("Error calling custom model", e);
            return Mono.error(new RuntimeException("Failed to call custom model: " + e.getMessage(), e));
        }
    }

    @Override
    public String chatWithHistory(List<Map<String, String>> messages) {
        try {
            ObjectNode requestBody = objectMapper.createObjectNode();
            requestBody.put("Code", code);
            requestBody.put("Key", apiKey);
            
            // Convert messages to JSON array
            ArrayNode messagesArray = requestBody.putArray("messages");
            for (Map<String, String> msg : messages) {
                ObjectNode msgNode = messagesArray.addObject();
                msg.forEach(msgNode::put);
            }
            
            String response = webClient.post()
                    .uri(baseUrl)
                    .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();

            return parseResponse(response);
        } catch (Exception e) {
            logger.error("Error calling custom model with history", e);
            throw new RuntimeException("Failed to call custom model: " + e.getMessage(), e);
        }
    }

    /**
     * Create request body for the custom model API
     * Adjust this method based on the actual API requirements
     */
    private ObjectNode createRequestBody(String message) {
        ObjectNode root = objectMapper.createObjectNode();
        
        // Add Code and Key as per your specification
        root.put("Code", code);
        root.put("Key", apiKey);
        
        // Add messages array (common format for chat models)
        ArrayNode messages = root.putArray("messages");
        ObjectNode userMessage = messages.addObject();
        userMessage.put("role", "user");
        userMessage.put("content", message);
        
        return root;
    }

    /**
     * Parse response from the custom model API
     * Adjust this method based on the actual API response format
     * This version wraps IOException in RuntimeException for use in lambda expressions
     */
    private String parseResponse(String responseBody) {
        try {
            return parseResponseInternal(responseBody);
        } catch (Exception e) {
            logger.error("Error parsing response", e);
            throw new RuntimeException("Failed to parse response: " + e.getMessage(), e);
        }
    }

    /**
     * Safe version of parseResponse for use in lambda expressions
     * Catches IOException and wraps it in RuntimeException
     */
    private String parseResponseSafe(String responseBody) {
        try {
            return parseResponseInternal(responseBody);
        } catch (Exception e) {
            logger.error("Error parsing response in stream", e);
            throw new RuntimeException("Failed to parse response: " + e.getMessage(), e);
        }
    }

    /**
     * Internal method to parse response - may throw IOException
     */
    private String parseResponseInternal(String responseBody) throws Exception {
        JsonNode rootNode = objectMapper.readTree(responseBody);
        
        // Try common response formats
        // Format 1: { "content": "..." } or { "text": "..." }
        if (rootNode.has("content")) {
            return rootNode.get("content").asText();
        }
        if (rootNode.has("text")) {
            return rootNode.get("text").asText();
        }
        
        // Format 2: { "data": { "content": "..." } }
        if (rootNode.has("data") && rootNode.get("data").has("content")) {
            return rootNode.get("data").get("content").asText();
        }
        
        // Format 3: { "choices": [ { "message": { "content": "..." } } ] } (OpenAI-like)
        if (rootNode.has("choices") && rootNode.get("choices").isArray()) {
            JsonNode choices = rootNode.get("choices");
            if (choices.size() > 0 && choices.get(0).has("message")) {
                JsonNode messageNode = choices.get(0).get("message");
                if (messageNode.has("content")) {
                    return messageNode.get("content").asText();
                }
            }
        }
        
        // Format 4: { "response": "..." } or { "result": "..." }
        if (rootNode.has("response")) {
            return rootNode.get("response").asText();
        }
        if (rootNode.has("result")) {
            return rootNode.get("result").asText();
        }
        
        // Fallback: return the whole response as string
        logger.warn("Unknown response format, returning raw response: {}", responseBody);
        return responseBody;
    }
}
