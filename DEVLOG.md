# Current Sprint: Core Infrastructure & Reliability

## 1. Containerization & Cleanup (Active)
- [x] Fix `Dockerfile` environment and path mapping issues.
- [x] Refactor internal storage file imports so the app runs correctly inside the container.
- [x] Fix celery_app.py, add autodiscovertasks, change the command in docker_compose.yml

## 2. Upload Reliability (Next Up)
- [x] Implement Idempotency for the `confirm-upload` endpoint.
- [x] Securing Docker containers by removing root privileges

## 3. Query Optimization
- [ ] Fix N+1 queries
- [ ] Add cursor pagination


  