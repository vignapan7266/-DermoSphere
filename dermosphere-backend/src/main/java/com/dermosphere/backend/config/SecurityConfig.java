package com.dermosphere.backend.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable()) // Disabled for local Capstone development
            .authorizeHttpRequests(auth -> auth
                // 1. PERMIT ALL STATIC FRONTEND FILES (HTML, CSS, JS, Assets)
                .requestMatchers("/", "/*.html", "/css/**", "/js/**", "/assets/**").permitAll()
                
                // 2. PERMIT PUBLIC API ENDPOINTS
                .requestMatchers("/api/v1/auth/**").permitAll()
                
                // 3. SECURE PROTECTED API ENDPOINTS (RBAC)
                .requestMatchers("/api/v1/triage/upload").hasRole("PATIENT")
                .requestMatchers("/api/v1/triage/queue", "/api/v1/triage/feedback/**").hasRole("DOCTOR")
                .requestMatchers("/api/v1/admin/**").hasRole("ADMIN")
                
                .anyRequest().authenticated()
            )
            .httpBasic(basic -> {}); 
            
        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOrigins(List.of("*")); 
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(Arrays.asList("authorization", "content-type", "x-auth-token"));
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}