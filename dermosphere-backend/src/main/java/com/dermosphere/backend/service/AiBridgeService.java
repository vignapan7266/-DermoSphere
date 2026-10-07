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

@Service
public class AiBridgeService {

    @Value("${ai.microservice.url}")
    private String aiServiceUrl;

    private final WebClient webClient;

    public AiBridgeService(WebClient webClient) {
        this.webClient = webClient;
    }

    public Mono<AiResponseDto> processImageInferenceReactive(MultipartFile file) {
        return processImageInferenceReactive(file, "0.0", "0", "0");
    }

    public Mono<AiResponseDto> processImageInferenceReactive(
            MultipartFile file,
            String ageScaled,
            String sexEncoded,
            String anatomyEncoded
    ) {
        try {
            ByteArrayResource fileResource = new ByteArrayResource(file.getBytes()) {
                @Override
                public String getFilename() {
                    return file.getOriginalFilename();
                }
            };

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", fileResource);
            body.add("age_scaled", ageScaled != null ? ageScaled : "0.0");
            body.add("sex_encoded", sexEncoded != null ? sexEncoded : "0");
            body.add("anatomy_encoded", anatomyEncoded != null ? anatomyEncoded : "0");

            return webClient
                    .post()
                    .uri(aiServiceUrl)
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .bodyValue(body)
                    .exchangeToMono(response -> {
                        if (response.statusCode().is2xxSuccessful()) {
                            return response.bodyToMono(AiResponseDto.class);
                        }
                        return response
                                .bodyToMono(String.class)
                                .defaultIfEmpty("Unknown AI service error")
                                .flatMap(errorBody -> Mono.error(
                                        new RuntimeException("AI Service Error: " + errorBody)
                                ));
                    });
        } catch (Exception e) {
            return Mono.error(
                    new RuntimeException("Failed to prepare AI request: " + e.getMessage(), e)
            );
        }
    }
}