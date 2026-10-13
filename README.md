# Driver-Drowsiness-and-Fatigue-Detection-System
A computer vision project that estimates visual indicators associated with driver drowsiness using facial landmarks, eye aspect ratio (EAR), mouth aspect ratio (MAR), and time based filtering.
The system uses Python, MediaPipe, FastAPI, and Streamlit to process image frames, calculate facial measurements, maintain detection state, and present alerts through a user interface.

Project Objectives
Estimate prolonged eye closure and sustained mouth opening.
Process image frames through REST and WebSocket interfaces.
Maintain isolated state for authorised client sessions.
Display detection metrics and session analytics.
Evaluate detection performance under different lighting, camera positions, and facial conditions.
Provide a foundation for controlled research and further development.
Safety and Limitations

This project is an experimental driver monitoring system. EAR and MAR measurements alone do not establish whether a person is fatigued or safe to drive. Detection performance depends on camera placement, image quality, individual differences, and the detection thresholds.

The system is not a certified automotive safety device and has not been established as suitable for sole reliance during driving. Evaluate its accuracy, failure modes, and alert behaviour under controlled conditions before considering any real world deployment.

Verification Status

Documented architecture and planned capabilities do not imply verified production readiness. Refer to the test results, performance benchmarks, security assessment, and deployment documentation for evidence of implementation and reliability.

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg?style = flat&logo = FastAPI&logoColor = white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg?style = flat&logo = Streamlit&logoColor = white)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg?style = flat&logo = docker&logoColor = white)](https://www.docker.com/)
[![CI/CD](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, real-time computer vision and MLOps platform for driver safety monitoring. Powered by **MediaPipe Face Mesh**, **FastAPI WebSocket streaming**, and an **isolated session-state architecture**, this system detects eye closure ($\text{EAR}$) and yawning ($\text{MAR}$) to prevent fatigue-induced accidents.

---

``
                                  ┌─────────────────────────────────────────┐
                                  │           Client Interfaces             │
                                  │   (Streamlit Dashboard / WebRTC App)    │
                                  └────────────────────┬────────────────────┘
                                                       │
                                            WebSocket / HTTP (X-Session-ID)
                                                       │
                                                       ▼
                                  ┌─────────────────────────────────────────┐
                                  │            Nginx Reverse Proxy          │
                                  └────────────────────┬────────────────────┘
                                                       │
                                                       ▼
                                  ┌─────────────────────────────────────────┐
                                  │             FastAPI Backend             │
                                  │          (ConnectionManager)            │
                                  └────────────────────┬────────────────────┘
                                                       │
                                 ┌─────────────────────┴─────────────────────┐
                                 ▼                                           ▼
                    ┌─────────────────────────┐                 ┌─────────────────────────┐
                    │ Isolated Session A      │                 │ Isolated Session B      │
                    │ DrowsinessDetector      │                 │ DrowsinessDetector      │
                    │  ├── MediaPipe Mesh     │                 │  ├── MediaPipe Mesh     │
                    │  ├── EAR/MAR Calculations│                 │  ├── EAR/MAR Calculations│
                    │  └── State Timers       │                 │  └── State Timers       │
                    └─────────────────────────┘                 └─────────────────────────┘
