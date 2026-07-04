package com.dermosphere.backend.controller;

import com.dermosphere.backend.entity.ScanRecord;
import com.dermosphere.backend.repository.ScanRecordRepository;
import com.dermosphere.backend.service.AiBridgeService;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Mono;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/triage")
public class TriageController {

    private final AiBridgeService aiBridgeService;
    private final ScanRecordRepository scanRecordRepository;
    private final String localUploadStorage = System.getProperty("user.home") + "/dermosphere_uploads/";

    public TriageController(AiBridgeService aiBridgeService, ScanRecordRepository scanRecordRepository) {
        this.aiBridgeService = aiBridgeService;
        this.scanRecordRepository = scanRecordRepository;
        File dir = new File(localUploadStorage);
        if (!dir.exists()) dir.mkdirs();
    }

    // CacheEvict ensures the Triage Queue cache is busted the moment a new scan is uploaded
    @PostMapping("/upload")
    @CacheEvict(value = "triageQueue", allEntries = true)
    public Mono<ResponseEntity<?>> uploadLesionImage(
            @RequestParam("file") MultipartFile file,
            @RequestParam("patient_id") Long patientId) {
        
        try {
            String destinationPath = localUploadStorage + System.currentTimeMillis() + "_" + file.getOriginalFilename();
            file.transferTo(new File(destinationPath));

            // Notice the <ResponseEntity<?>> type hint added directly before map()
            return aiBridgeService.processImageInferenceReactive(file)
                    .<ResponseEntity<?>>map(aiResult -> {
                        ScanRecord record = new ScanRecord();
                        record.setPatientId(patientId);
                        record.setOriginalFilename(file.getOriginalFilename());
                        record.setStoredFilePath(destinationPath);
                        record.setPredictedClass(aiResult.getPrediction());
                        record.setConfidenceScore(aiResult.getConfidence());
                        record.setTriageTier(aiResult.getTriage_tier());
                        record.setHeatmapPath(aiResult.getHeatmap_path());

                        scanRecordRepository.save(record);
                        return ResponseEntity.ok(record); // Returns the Object
                    })
                    // onErrorResume dynamically handles the exception and returns the String
                    .onErrorResume(e -> Mono.just(
                        ResponseEntity.internalServerError().body("System proxy exception: " + e.getMessage())
                    ));
                    
        } catch (IOException e) {
            return Mono.just(ResponseEntity.internalServerError().body("File persistence failed: " + e.getMessage()));
        }
    }

    // Cacheable intercepts the request and serves it from Caffeine RAM instantly
    @GetMapping("/queue")
    @Cacheable(value = "triageQueue")
    public ResponseEntity<List<ScanRecord>> getClinicalTriageQueue() {
        return ResponseEntity.ok(scanRecordRepository.findAllByOrderByTriageTierDescScannedAtDesc());
    }

    // Feedback loops (Upvotes/Downvotes) also bust the cache so the UI updates globally
    @PatchMapping("/feedback/{id}")
    @CacheEvict(value = "triageQueue", allEntries = true)
    public ResponseEntity<?> submitDoctorFeedback(
            @PathVariable Long id,
            @RequestBody Map<String, String> body) {
        
        ScanRecord record = scanRecordRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Target Scan Record missing."));
        
        String feedbackValue = body.get("feedback"); 
        
        // Handling the "YouTube-Like" Engagement Loop
        if (feedbackValue.equalsIgnoreCase("AGREE")) {
            record.setUpvotes(record.getUpvotes() + 1);
        } else if (feedbackValue.equalsIgnoreCase("DISAGREE")) {
            record.setDownvotes(record.getDownvotes() + 1);
        }
        
        record.setDoctorFeedback(feedbackValue.toUpperCase());
        scanRecordRepository.save(record);
        
        return ResponseEntity.ok("Engagement tracked. Feed updated.");
    }
}