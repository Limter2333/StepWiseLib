package com.github.Sheven.controller;

import lombok.extern.slf4j.Slf4j;
import com.github.Sheven.dto.ChatRequest;
import com.github.Sheven.dto.ChatResponse;
import com.github.Sheven.service.QwenService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

@Slf4j
@RestController
@RequestMapping("/chat")
public class QwenController {

    @Autowired
    private QwenService qwenService;


    @PostMapping("/")
    public ChatResponse chat(@RequestBody ChatRequest request) {
        return qwenService.chat(request);
    }

    @PostMapping("/skills")
    public ChatResponse chatWithSkills(@RequestBody ChatRequest request) {
        return qwenService.chatWithSkills(request);
    }

    @PostMapping(value = "/skills/stream", produces = "text/event-stream")
    public Flux<ChatResponse> streamChatWithSkills(@RequestBody ChatRequest request) {
        return qwenService.streamChatWithSkills(request);
    }
}
