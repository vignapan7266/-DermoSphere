package com.dermosphere.backend.service;

import com.dermosphere.backend.dto.AiResponseDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.io.IOException;

@Service
public class AiBridgeService {

    @Value("${ai.microservice.url}")
    private String aiServiceUrl;

    private final WebClient webClient;

    public AiBridgeService(WebClient webClient) {
        this.webClient = webClient;
    }

    // ADVANCED: Returns a Reactive Mono, completely bypassing thread-blocking IO
    public Mono<AiResponseDto> processImageInferenceReactive(MultipartFile file) throws IOException {
        
        ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        };

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", fileResource);

        return webClient.post()
                .uri(aiServiceUrl)
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .bodyValue(body)
                .retrieve()
                .bodyToMono(AiResponseDto.class)
                .doOnError(e -> System.err.println("AI Microservice Connection Failed: " + e.getMessage()));
    }
}