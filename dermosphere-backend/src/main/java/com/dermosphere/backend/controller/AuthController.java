package com.dermosphere.backend.controller;

import com.dermosphere.backend.entity.Role;
import com.dermosphere.backend.entity.User;
import com.dermosphere.backend.repository.RoleRepository;
import com.dermosphere.backend.repository.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;

    public AuthController(UserRepository userRepository, RoleRepository roleRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @PostMapping("/register")
    public ResponseEntity<?> registerUser(@RequestBody Map<String, String> request) {
        if (userRepository.findByUsername(request.get("username")).isPresent()) {
            return ResponseEntity.badRequest().body("Username explicitly taken.");
        }

        User user = new User();
        user.setUsername(request.get("username"));
        user.setPassword(passwordEncoder.encode(request.get("password")));
        user.setEmail(request.get("email"));
        
        String assignedRole = request.getOrDefault("role", "PATIENT");
        Role role = roleRepository.findByName("ROLE_" + assignedRole.toUpperCase())
                .orElseThrow(() -> new RuntimeException("Role asset target unrecognized in application system mappings."));
        
        user.setRoles(Set.of(role));
        userRepository.save(user);

        return ResponseEntity.ok("User registration recorded successfully.");
    }
}