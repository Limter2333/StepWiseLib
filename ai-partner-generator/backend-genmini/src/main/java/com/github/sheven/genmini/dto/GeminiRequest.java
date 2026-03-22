package com.github.sheven.genmini.dto;

import java.util.List;

public class GeminiRequest {

    public List<Content> contents;
    public GenerationConfig generationConfig;

    public static class Content {
        public String role = "user";
        public List<Part> parts;

        public Content(String text) {
            this.parts = List.of(new Part(text));
        }
    }

    public static class Part {
        public String text;
        public Part(String text) { this.text = text; }
    }

    public static class GenerationConfig {
        public List<String> responseModalities = List.of("IMAGE");
        public ImageConfig imageConfig = new ImageConfig();
    }

    public static class ImageConfig {
        public String imageSize = "4K";
        public String aspectRatio = "9:16";
    }
}
