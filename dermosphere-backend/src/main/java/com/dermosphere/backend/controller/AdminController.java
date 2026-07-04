package com.dermosphere.backend.controller;

import com.dermosphere.backend.repository.ScanRecordRepository;
import com.dermosphere.backend.repository.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/admin")
public class AdminController {

    private final UserRepository userRepository;
    private final ScanRecordRepository scanRecordRepository;
    
    // Absolute path to the AI microservice for Dev Mode live-editing
    private final String AI_SERVICE_DIR = "../dermosphere-ai-service/";

    public AdminController(UserRepository userRepository, ScanRecordRepository scanRecordRepository) {
        this.userRepository = userRepository;
        this.scanRecordRepository = scanRecordRepository;
    }

    // GOD MODE: System-Wide Statistics
    @GetMapping("/telemetry")
    public ResponseEntity<?> getSystemTelemetry() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("total_users", userRepository.count());
        stats.put("total_scans", scanRecordRepository.count());
        // In a real app, you would add more complex JPA aggregations here
        return ResponseEntity.ok(stats);
    }

    // DEV MODE: Read Source Code
    @GetMapping("/dev/read")
    public ResponseEntity<?> readSourceCode(@RequestParam String filename) {
        try {
            Path path = Paths.get(AI_SERVICE_DIR + filename);
            String content = Files.readString(path);
            return ResponseEntity.ok(Map.of("content", content));
        } catch (IOException e) {
            return ResponseEntity.badRequest().body("File not found or access denied.");
        }
    }

    // DEV MODE: Inject Source Code
    @PostMapping("/dev/write")
    public ResponseEntity<?> writeSourceCode(@RequestBody Map<String, String> payload) {
        try {
            String filename = payload.get("filename");
            String newContent = payload.get("content");
            Path path = Paths.get(AI_SERVICE_DIR + filename);
            Files.writeString(path, newContent);
            return ResponseEntity.ok("Code dynamically injected and saved to disk.");
        } catch (IOException e) {
            return ResponseEntity.internalServerError().body("Failed to write to file system.");
        }
    }
}