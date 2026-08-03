# YouTube API — Production Checklist

## ✅ Infrastructure
- [x] PostgreSQL with Docker
- [x] MinIO for video storage
- [x] Redis broker (Celery) — separate instance, `allkeys-lru`
- [x] Redis blacklist (JWT) — separate instance, `noeviction`
- [x] Docker Compose with named volumes
- [x] `pool_pre_ping=True` on SQLAlchemy engine
- [x] Global DB exception handler (503)
- [x] FastAPI inside Docker (currently runs manually)
- [x] Celery worker inside Docker
- [ ] Environment-based secrets (no hardcoded credentials)

---

## ✅ Auth — `/auth`
- [x] `POST /auth/signup` — register + auto-create channel
- [x] `POST /auth/login` — return JWT
- [x] `POST /auth/logout` — blacklist token in Redis
- [x] `GET /auth/me` — current user profile
- [x] `PATCH /auth/me` — update username/email
- [ ] `PATCH /auth/me/password` — change password (verify old first)

---

## 🔲 Channels — `/channels`
- [ ] `GET /channels/{channel_id}` — public channel profile
- [ ] `PATCH /channels/me` — update name, description, avatar
- [ ] `GET /channels/{channel_id}/videos` — paginated video list
- [ ] `POST /channels/{channel_id}/subscribe` — subscribe/unsubscribe toggle
- [ ] `GET /channels/{channel_id}/subscribers` — count + list

---

## ✅ Videos — `/videos`
- [x] `POST /videos/request-upload` — get presigned URL from MinIO
- [x] `POST /videos/confirm-upload` — save to DB, trigger Celery
- [ ] `GET /videos` — paginated feed
- [ ] `GET /videos/{video_id}` — single video + increment view count
- [ ] `PATCH /videos/{video_id}` — update title/description (owner only)
- [ ] `DELETE /videos/{video_id}` — delete video + MinIO cleanup
- [ ] `GET /videos/search` — search by title/description

---

## ✅ Comments — `/comments`
- [x] `POST /videos/{video_id}/comments` — create top-level comment
- [x] `GET /videos/{video_id}/comments` — paginated + nested replies
- [x] `POST /comments/{comment_id}/replies` — reply to comment
- [ ] `PATCH /comments/{comment_id}` — edit comment (owner only)
- [ ] `DELETE /comments/{comment_id}` — delete + cascade replies

---

## 🔲 Reactions
- [ ] `POST /videos/{video_id}/react` — like/dislike toggle
- [ ] `POST /comments/{comment_id}/react` — like/dislike toggle
- [ ] `GET /videos/{video_id}/reactions` — like/dislike counts

---

## 🔲 Playlists — `/playlists`
- [ ] `POST /playlists` — create playlist
- [ ] `GET /playlists/{playlist_id}` — get playlist + videos
- [ ] `PATCH /playlists/{playlist_id}` — update name/privacy
- [ ] `DELETE /playlists/{playlist_id}` — delete playlist
- [ ] `POST /playlists/{playlist_id}/videos/{video_id}` — add video
- [ ] `DELETE /playlists/{playlist_id}/videos/{video_id}` — remove video

---

## 🔲 Watch History — `/history`
- [ ] `POST /videos/{video_id}/watch` — record watch event + progress
- [ ] `GET /history` — paginated watch history
- [ ] `DELETE /history` — clear history

---

## ✅ Background Tasks (Celery)
- [x] `generate_thumbnail` — FFmpeg frame extract on video upload
- [ ] `send_welcome_email` — triggered on signup
- [ ] `send_notification_email` — notify subscribers on new video
- [ ] `analyze_sentiment` — fill `sentiment` column via AI on comment create
- [x] Separate Celery queues (`thumbnails` / `emails`)

---

## 🔲 Code Quality
- [ ] Migrate to async SQLAlchemy (`AsyncSession` + `asyncpg`)
- [ ] Pagination on all list endpoints (skip/limit or cursor-based)
- [ ] Input validation on all endpoints (Pydantic schemas)
- [ ] Consistent error responses across all endpoints
- [ ] Remove `allow_origins=["*"]` — restrict CORS to actual frontend

---

## 🔲 Testing
- [x] Auth tests (signup, login, duplicate, token)
- [x] Video upload tests
- [ ] Channel tests
- [ ] Comment + reply tests
- [ ] Reaction tests
- [ ] Playlist tests
- [ ] Celery task tests

---

## 🔲 Deployment
- [ ] Add FastAPI + Celery worker to Docker Compose
- [ ] Add Nginx as reverse proxy
- [ ] Set up CI/CD (GitHub Actions)
- [ ] Choose cloud provider (Railway / Render / VPS)
- [ ] Configure production `.env` (strong secrets, real credentials)
- [ ] Set up domain + HTTPS (Let's Encrypt)
- [ ] Add Redis authentication (`--requirepass`)

---

## 📊 Summary
| Category | Done | Total |
|---|---|---|
| Infrastructure | 7 | 10 |
| Auth | 4 | 6 |
| Channels | 0 | 5 |
| Videos | 2 | 7 |
| Comments | 3 | 5 |
| Reactions | 0 | 3 |
| Playlists | 0 | 6 |
| Watch History | 0 | 3 |
| Background Tasks | 2 | 4 |
| Code Quality | 0 | 5 |
| Testing | 2 | 7 |
| Deployment | 0 | 7 |
| **Total** | **20** | **68** |