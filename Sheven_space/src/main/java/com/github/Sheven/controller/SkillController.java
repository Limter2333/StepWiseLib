package com.github.Sheven.controller;

import lombok.extern.slf4j.Slf4j;
import com.github.Sheven.dto.ChatRequest;
import com.github.Sheven.dto.ChatResponse;
import com.github.Sheven.service.SkillService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/chat")
public class SkillController {

    @Autowired
    private SkillService skillService;


    @PostMapping("/")
    public ChatResponse chat(@RequestBody ChatRequest request) {
        return skillService.chat(request);
    }

    @PostMapping("/skills")
    public ChatResponse chatWithSkills(@RequestBody ChatRequest request) {
        return skillService.chatWithSkills(request);
    }

    @PostMapping(value = "/skills/stream", produces = "text/event-stream")
    public Flux<ChatResponse> streamChatWithSkills(@RequestBody ChatRequest request) {
        return skillService.streamChatWithSkills(request);
    }

    /**
     * 健康检查
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        Map<String, String> result = new HashMap<>();
        result.put("status", "UP");
        result.put("service", "Skill Service");
        return ResponseEntity.ok(result);
    }
}
