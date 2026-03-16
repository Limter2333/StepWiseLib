package com.github.Sheven.service;

import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

/**
 * Service for calling custom unknown model via HTTP POST
 */
public interface CustomModelService {

    /**
     * Call the custom model with a simple message
     * @param message user input message
     * @return model response content
     */
    String chat(String message);

    /**
     * Call the custom model with streaming response
     * @param message user input message
     * @return Mono of response content
     */
    Mono<String> streamChat(String message);

    /**
     * Call with conversation history
     * @param messages conversation history
     * @return model response content
     */
    String chatWithHistory(List<Map<String, String>> messages);
}
