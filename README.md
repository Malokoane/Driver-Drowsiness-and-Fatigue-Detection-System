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
