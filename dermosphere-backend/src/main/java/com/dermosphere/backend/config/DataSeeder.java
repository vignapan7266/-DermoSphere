package com.dermosphere.backend.config;

import com.dermosphere.backend.entity.Role;
import com.dermosphere.backend.entity.User;
import com.dermosphere.backend.repository.RoleRepository;
import com.dermosphere.backend.repository.UserRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.Set;

@Configuration
public class DataSeeder {

    @Bean
    public CommandLineRunner initDatabase(
            UserRepository userRepository, 
            RoleRepository roleRepository, 
            PasswordEncoder passwordEncoder) {
        
        return args -> {
            // 1. Safely initialize Roles (Fail-safe in case schema.sql was skipped)
            Role adminRole = roleRepository.findByName("ROLE_ADMIN").orElseGet(() -> {
                Role r = new Role();
                r.setName("ROLE_ADMIN");
                return roleRepository.save(r);
            });

            Role doctorRole = roleRepository.findByName("ROLE_DOCTOR").orElseGet(() -> {
                Role r = new Role();
                r.setName("ROLE_DOCTOR");
                return roleRepository.save(r);
            });

            Role patientRole = roleRepository.findByName("ROLE_PATIENT").orElseGet(() -> {
                Role r = new Role();
                r.setName("ROLE_PATIENT");
                return roleRepository.save(r);
            });

            // 2. Create the Default "God-Mode" Admin User
            if (userRepository.findByUsername("admin").isEmpty()) {
                User admin = new User();
                admin.setUsername("admin");
                // The password must be hashed before saving to the database
                admin.setPassword(passwordEncoder.encode("admin123")); 
                admin.setEmail("admin@dermosphere.com");
                admin.setRoles(Set.of(adminRole));
                
                userRepository.save(admin);
                System.out.println("[SYSTEM BOOTSTRAP] Default Admin created successfully.");
            }

            // 3. Create a Default Non-Admin User (Clinician)
            if (userRepository.findByUsername("doctor1").isEmpty()) {
                User doctor = new User();
                doctor.setUsername("doctor1");
                doctor.setPassword(passwordEncoder.encode("doctor123"));
                doctor.setEmail("doctor1@dermosphere.com");
                doctor.setRoles(Set.of(doctorRole));
                
                userRepository.save(doctor);
                System.out.println("[SYSTEM BOOTSTRAP] Default Doctor created successfully.");
            }
            
            // 4. Create a Default Patient
            if (userRepository.findByUsername("patient1").isEmpty()) {
                User patient = new User();
                patient.setUsername("patient1");
                patient.setPassword(passwordEncoder.encode("patient123"));
                patient.setEmail("patient1@dermosphere.com");
                patient.setRoles(Set.of(patientRole));
                
                userRepository.save(patient);
                System.out.println("[SYSTEM BOOTSTRAP] Default Patient created successfully.");
            }
        };
    }
}