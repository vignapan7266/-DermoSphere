package com.dermosphere.backend.config;

import com.github.benmanes.caffeine.cache.Caffeine;
import org.springframework.cache.CacheManager;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.cache.caffeine.CaffeineCacheManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.web.reactive.function.client.WebClient;

import java.util.concurrent.Executor;
import java.util.concurrent.TimeUnit;

@Configuration
@EnableCaching
@EnableAsync
public class AppConfig {

    // 1. Reactive HTTP Client for zero-blocking AI network calls
    @Bean
    public WebClient webClient() {
        return WebClient.builder().build();
    }

    // 2. Custom Async Thread Pool (Prevents HTTP thread exhaustion during heavy AI loads)
    @Bean(name = "asyncTaskExecutor")
    public Executor asyncTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(50);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("AsyncThread-");
        executor.initialize();
        return executor;
    }

    // 3. Caffeine RAM Cache for the Triage Queue
    @Bean
    public CacheManager cacheManager() {
        CaffeineCacheManager cacheManager = new CaffeineCacheManager("triageQueue");
        cacheManager.setCaffeine(Caffeine.newBuilder()
                .expireAfterWrite(5, TimeUnit.MINUTES) // Auto-refresh cache every 5 mins
                .maximumSize(1000));
        return cacheManager;
    }
}