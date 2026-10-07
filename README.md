# DermoSphere

## AI-Based Skin Cancer Detection System

DermoSphere is an AI-powered skin lesion classification system developed using Deep Learning and modern web technologies. The system analyzes skin lesion images and classifies them into different categories using a trained deep learning model.

## Features

- Skin lesion image classification
- Deep Learning based prediction
- 7-class skin lesion classification
- Patient metadata integration
- Grad-CAM explainable AI
- FastAPI AI service
- Spring Boot backend
- MySQL database
- User authentication

## Technologies Used

- Python
- TensorFlow
- Keras
- FastAPI
- Java
- Spring Boot
- MySQL
- HTML
- CSS
- JavaScript
- Git & GitHub

## Skin Lesion Classes

1. Actinic Keratoses
2. Basal Cell Carcinoma
3. Benign Keratosis
4. Dermatofibroma
5. Melanoma
6. Melanocytic Nevi
7. Vascular Lesions

## System Architecture

User Interface  
↓  
Spring Boot Backend  
↓  
FastAPI AI Service  
↓  
Deep Learning Model  
↓  
Skin Lesion Prediction  
↓  
Grad-CAM Explanation

## How to Run

### AI Service

```bash
cd dermosphere-ai-service
venv\Scripts\activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
