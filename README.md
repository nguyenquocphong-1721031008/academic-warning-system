# Academic Warning Backend

Backend hệ thống cảnh báo học vụ dùng FastAPI + Clean Architecture + Machine Learning.

Mục tiêu: phân tích dữ liệu điểm, đánh giá theo rule-based, dự báo nguy cơ cảnh báo học vụ bằng ML và hỗ trợ can thiệp sớm.

## 1) Tính năng chính

- Xác thực JWT + refresh token.
- Import điểm từ Excel.
- Sinh cảnh báo học vụ theo bộ quy tắc cấu hình trong DB.
- Phân tích sinh viên theo MSSV (`/api/warnings/analysis/{student_code}`) kết hợp:
  - Rule-based warning
  - ML risk prediction
- Quản trị rule set / rules / người dùng / khoa.
- Train ML model và theo dõi trạng thái model qua API.

## 2) Kiến trúc dự án

Project theo Clean Architecture:

- `app/domain`: entities, value objects, repository interfaces.
- `app/application`: use-cases, services, DTOs, ports.
- `app/infrastructure`: DB session/models/repositories, config, security, ML artifacts/registry.
- `app/api`: routers, dependencies, schemas, response contract.
- `app/main.py`: composition root (middleware, lifespan, exception handlers, router wiring).

## 3) Yêu cầu môi trường

- Python 3.12+ (khuyến nghị 3.12 hoặc 3.13)
- PostgreSQL 14+
- Windows / Linux / macOS

## 3.1) Developer onboarding checklist (10-15 phút)

Checklist cho dev mới vào dự án:

- [ ] Clone repo và tạo virtualenv
- [ ] Cài dependencies từ `requirements.txt`
- [ ] Tạo file `.env` đúng `DATABASE_URL` local
- [ ] Khởi tạo DB (Cách A Alembic hoặc Cách B schema.sql)
- [ ] Chạy seed để có admin và default rules
- [ ] Chạy API (`uvicorn app.main:app --reload`)
- [ ] Mở Swagger `/docs` và test `/health`
- [ ] Login bằng tài khoản admin seed
- [ ] Kiểm tra `/api/ml/status` xem model artifacts đã load

Nếu checklist trên hoàn tất, môi trường local coi như sẵn sàng dev.

## 3.2) One-time setup commands (copy/paste)

### Windows PowerShell

```powershell
git clone <repo-url>
cd academic-warning-backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Linux/macOS

```bash
git clone <repo-url>
cd academic-warning-backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4) Cài đặt nhanh (local) - chạy được ngay

### Bước 1: Clone và tạo virtual environment

```bash
git clone <repo-url>
cd academic-warning-backend
python -m venv venv
```

Kích hoạt venv:

- Windows PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```

- Linux/macOS:
```bash
source venv/bin/activate
```

### Bước 2: Cài dependencies

```bash
pip install -r requirements.txt
```

### Bước 3: Tạo `.env`

Tạo file `.env` ở thư mục gốc:

```env
APP_ENV=dev
DATABASE_URL=postgresql://postgres:123456@localhost:5432/academic_warning_db
SECRET_KEY=change-me-very-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
SUPPORT_PHONE=0362629326

# Security / CORS
CORS_ALLOW_ORIGINS=["http://localhost:3000","http://localhost:5173"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["GET","POST","PUT","PATCH","DELETE","OPTIONS"]
CORS_ALLOW_HEADERS=["Authorization","Content-Type"]
TRUSTED_HOSTS=["localhost","127.0.0.1"]
MAX_UPLOAD_MB=15
ML_PREDICT_RATE_LIMIT_PER_MINUTE=60

# SMTP (optional)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
SMTP_USE_TLS=false
SMTP_FROM_EMAIL=no-reply@academic-warning-system.local

# ML artifacts
ML_ARTIFACTS_DIR=./ml_artifacts
```

### Cấu hình SMTP Gmail (để gửi mail thật)

Sử dụng cho endpoint `POST /api/admin/send-warning-email`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=your_gmail@gmail.com
SMTP_PASSWORD=your_16_char_app_password
SMTP_FROM_EMAIL=your_gmail@gmail.com
```

Checklist:
- Bật `2-Step Verification` cho Gmail.
- Tạo `App Password` (16 ký tự) và dùng cho `SMTP_PASSWORD`.
- Không dùng mật khẩu đăng nhập Gmail thường.

### Bước 4: Chạy API

```bash
uvicorn app.main:app --reload
```

Mặc định: `http://127.0.0.1:8000`

Swagger docs: `http://127.0.0.1:8000/docs`

## 5) Database-first: cách chạy cho người mới (khuyến nghị)

Chọn **1 trong 2 cách** sau:

### Cách A - Dùng Alembic (chuẩn triển khai)

1) Tạo DB rỗng:

```sql
CREATE DATABASE academic_warning_db;
```

2) Chạy migration:

```bash
alembic upgrade head
```

3) Seed dữ liệu mẫu:

```bash
python scripts/seed.py
```

### Cách B - Dùng `schema.sql` (backup/offline)

1) Tạo database:

```sql
CREATE DATABASE academic_warning_db;
```

2) Apply schema:

```bash
psql -U postgres -d academic_warning_db -f schema.sql
```

3) Seed dữ liệu tối thiểu (tạo admin + rule set mặc định):

```bash
python scripts/seed.py
```

Bạn có thể cấu hình tài khoản seed qua env:

- `SEED_ADMIN_USERNAME` (default: `admin`)
- `SEED_ADMIN_PASSWORD` (default: `admin123456`)

## 6) Alembic migration (bắt buộc cho team/deploy)

Các lệnh thường dùng:

```bash
alembic upgrade head      # apply migration mới nhất
alembic current           # xem revision hiện tại
alembic history           # xem lịch sử migration
```

Nếu DB đã có schema sẵn nhưng chưa có bảng version của Alembic:

```bash
alembic stamp head
```

## 7) Train ML model

### Train từ script

```bash
python -m app.infrastructure.ml.train_model
```

Artifacts được lưu tại:

- `ml_artifacts/<model>/pipeline.joblib`
- `ml_artifacts/<model>/threshold.json`
- `ml_artifacts/<model>/meta.json` (có metrics)

### Train qua API (Admin)

`POST /api/ml/train`

Body:

```json
{
  "model_type": "random_forest"
}
```

## 8) API quan trọng

### Auth

- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Warning

- `GET /api/warnings`
- `GET /api/warnings/{student_code}`
- `GET /api/warnings/analytics`
- `GET /api/warnings/export`
- `PATCH /api/warnings/{warning_id}/status`
- `GET /api/warnings/analysis/{student_code}?model=random_forest`

### ML

- `GET /api/ml/status`  
  Trả model đã load + threshold + metrics từ `meta.json`.
- `POST /api/ml/predict`  
  Predict trực tiếp theo `student_code` (nội bộ).
- `POST /api/ml/train` (Admin)

### Admin

- Quản lý users/faculties/rule-sets/rules
- `POST /api/admin/warnings/regenerate`
- `POST /api/admin/send-warning-email`

## 9) Contract response (chuẩn toàn hệ thống)

- Success: `violations: []`
- Validation fail: `violations` có dữ liệu
- Business fail: `violations` có dữ liệu
- Server error: `violations: []`

## 10) Lỗi thường gặp

- `403` khi gọi endpoint internal: thiếu token hoặc role không đủ.
- `503 Model artifact not found`: chưa train model hoặc thiếu file trong `ml_artifacts`.
- `400` khi import điểm: sai cột Excel hoặc file không phải `.xlsx`.
- `502 Gửi email thất bại: WinError 10061`: chưa có SMTP server ở host/port cấu hình (ví dụ đang để `localhost:1025` nhưng chưa chạy MailHog/Mailpit).
- `500` do DB schema chưa đúng: cần đồng bộ bảng trước khi chạy.

## 11) Quick check sau khi setup

1) Kiểm tra service:

```bash
curl http://127.0.0.1:8000/health
```

2) Đăng nhập lấy token:
- `POST /api/auth/login`

3) Kiểm tra ML artifacts:
- `GET /api/ml/status`

4) Phân tích một MSSV:
- `GET /api/warnings/analysis/{student_code}?model=random_forest`

## 11.1) Daily developer commands

### Chạy app

```bash
uvicorn app.main:app --reload
```

### Lint + format

```bash
ruff check app --fix
ruff format app
```

### Chạy migration

```bash
alembic upgrade head
```

### Seed lại dữ liệu mẫu

```bash
python scripts/seed.py
```

### Train lại ML

```bash
python -m app.infrastructure.ml.train_model
```

## 12) Gợi ý triển khai production

- Đổi `SECRET_KEY` mạnh, không dùng mặc định.
- Dùng reverse proxy + HTTPS.
- Dùng Redis cho rate limiting (thay in-memory).
- Thêm migration tool (Alembic) để quản lý schema.
- Thiết lập CI chạy lint + test + smoke checks.

## 13) System Architecture Diagram

```text
Client (Admin / Faculty Manager)
        |
        v
FastAPI API Layer (app/main.py + routers)
  - Auth (JWT + refresh token)
  - Validation + error handling
  - Rate limit (ML predict)
  - CORS + TrustedHosts + security headers
        |
        +-------------------------------+
        |                               |
        v                               v
PostgreSQL                          ML Artifacts
  - student_scores                  - pipeline.joblib
  - student_semester_stats          - threshold.json
  - academic_warnings               - meta.json
  - warning_rules, rule_sets
        |
        v
Application Layer
  - WarningRuleEngine (rule-based)
  - PredictionService (hybrid: rule + ML + policy)
```

## 14) ML Pipeline

### Training (offline)

1. Đọc dữ liệu từ DB (`student_semester_stats`, `academic_warnings`, `semesters`).
2. Tạo label dự báo kỳ sau (`next_warning_level`).
3. Tạo feature:
   - `semester_gpa`, `cumulative_gpa`, `gpa_diff`
   - `total_failed`, `total_subjects`, `fail_ratio`
   - `gpa_trend`, `fail_trend`, `was_warning`
4. Pipeline:
   - `StandardScaler`
   - `SMOTE` (xử lý mất cân bằng lớp)
   - Classifier (RandomForest / LogisticRegression / XGBoost)
5. Tune threshold theo F1, lưu artifacts.

### Inference (online)

- Model được preload khi app startup (lifespan).
- Predict dùng đúng feature schema như train.
- Quyết định `prediction` theo `risk_score >= threshold`.

## 15) Hybrid Approach (Rule-based + ML)

- **Rule-based**: xác định cảnh báo theo bộ quy tắc cấu hình trong DB.
- **ML**: dự báo nguy cơ bị cảnh báo kỳ sau từ dữ liệu điểm và xu hướng.
- Endpoint phân tích tổng hợp:
  - `GET /api/warnings/analysis/{student_code}?model=random_forest`
  - Trả về cả `warning` (rule) và `ml_prediction` (ML).

## 16) Interpretation (Giải thích output ML)

- `risk_score`: điểm rủi ro trong khoảng `[0, 1]`.
- `threshold`: ngưỡng quyết định từ quá trình tuning.
- `prediction`:
  - `1` nếu `risk_score >= threshold`
  - `0` nếu ngược lại
- `risk_level`:
  - `low`: < 0.4
  - `medium`: 0.4 - <0.7
  - `high`: >= 0.7
- `trend_analysis` và `recommendations`: diễn giải nghiệp vụ hỗ trợ can thiệp.

## 17) Design Decisions

- Dùng Clean Architecture để tách biệt domain/use-case/infrastructure/api.
- Model ML load một lần qua lifespan để giảm latency.
- Lưu artifacts tách bạch (`pipeline.joblib`, `threshold.json`, `meta.json`).
- DB-first: có `schema.sql` backup + Alembic migration cho quản lý thay đổi schema.
- Chuẩn hóa response contract với `violations` rõ ràng cho success/fail.

## 18) Security

- JWT access token + refresh token.
- RBAC theo role (`admin`, `faculty_manager`).
- CORS + Trusted Host middleware.
- Security headers (`X-Frame-Options`, `X-Content-Type-Options`, ...).
- Rate limiting cho endpoint ML predict.
- Validation input chặt với Pydantic.

## 19) Future Work

- Thay rate limit in-memory bằng Redis (hỗ trợ multi-instance).
- Thêm migration chi tiết theo từng feature.
- Thêm test tự động (unit + integration + smoke test API chính).
- Thêm monitoring (structured logging, metrics, tracing).
- Thêm model explainability (SHAP/feature importance) cho output ML.

## 20) Evaluation Strategy

Trong bài toán cảnh báo học vụ:

- Ưu tiên Recall (quan trọng nhất) để tránh bỏ sót sinh viên có nguy cơ.
- Chấp nhận tăng false positive (cảnh báo dư còn hơn thiếu).
- Precision và F1 dùng để cân bằng chất lượng mô hình.

Đây là bài toán hỗ trợ can thiệp sớm, không phải classification thông thường.

## 21) Data Flow (System Thinking)

Luồng dữ liệu end-to-end:

1. Import điểm (`/api/scores/import`) vào `student_scores`.
2. Tính `student_semester_stats` (semester_gpa, cumulative_gpa, fail_ratio...).
3. Rule engine sinh `academic_warnings` theo rule set active.
4. ML đọc dữ liệu thống kê + cảnh báo lịch sử để dự báo nguy cơ kỳ sau.
5. API `GET /api/warnings/analysis/{student_code}` trả kết quả hybrid:
   - rule-based warning
   - ML prediction + trend + recommendations

## 22) Quick Demo

Các lệnh tối thiểu để người chấm test nhanh:

```bash
# 1) Login (lấy access_token)
curl -X POST "http://127.0.0.1:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"admin123456\"}"

# 2) Check ML status (xem model + threshold + metrics)
curl "http://127.0.0.1:8000/api/ml/status"

# 3) Predict / analysis
curl -X GET "http://127.0.0.1:8000/api/warnings/analysis/151900126?model=random_forest" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## 23) Key Strengths

- Kết hợp rule-based + ML (hybrid system).
- Clean Architecture rõ ràng, dễ mở rộng.
- ML pipeline đầy đủ (train -> evaluate -> deploy artifacts).
- API-first, dễ tích hợp frontend.
- Có thể triển khai production với ít thay đổi.

## 24) Limitations

- Dataset còn hạn chế, ảnh hưởng độ tổng quát.
- Chưa có explainability chi tiết (ví dụ SHAP).
- Chưa tối ưu cho real-time large-scale.

## 25) Business Impact

Hệ thống không chỉ “dự đoán ML”, mà là **decision support system** cho nhà trường:

- Hỗ trợ cố vấn học tập **ưu tiên can thiệp đúng đối tượng** (SV có nguy cơ cao).
- Giảm công sức xử lý thủ công, chuẩn hóa quy trình cảnh báo theo rule set trong DB.
- Có thể tích hợp vào hệ thống quản lý đào tạo hiện có (API-first).
- Mục tiêu cuối: **giảm tỷ lệ SV bị cảnh báo học vụ/bỏ học** nhờ phát hiện sớm và can thiệp kịp thời.

## 26) Model Performance (Report)

Dataset cảnh báo thường **mất cân bằng** (ít SV bị cảnh báo), vì vậy mô hình được đánh giá bằng:
Recall, Precision, F1, ROC-AUC, PR-AUC và threshold tuning.

Để xem metrics ngay trên hệ thống (không cần terminal):

```bash
curl "http://127.0.0.1:8000/api/ml/status"
```

Endpoint này trả về `metrics` cho từng model (được lưu trong `ml_artifacts/<model>/meta.json`).

## 27) Why Accuracy is not used

Trong bài toán cảnh báo học vụ, accuracy có thể **đánh lừa** vì dữ liệu lệch lớp:

- Ví dụ: 90% SV không bị cảnh báo.
- Một model “đoán tất cả = không nguy cơ” có thể đạt accuracy ~90% nhưng **vô dụng** (Recall = 0).

Do đó hệ thống ưu tiên Recall và dùng threshold tuning để cân bằng Precision/F1.

## 28) Explainability (Preview)

Mục tiêu: biến hệ thống từ “black-box” thành **trustable**:

- SV biết yếu tố nào cần cải thiện.
- Giảng viên/cố vấn hiểu lý do cảnh báo và vì sao risk_score tăng.

Ví dụ diễn giải (rule/policy + trend):

- GPA giảm mạnh -> risk_score tăng.
- Số môn rớt cao -> rủi ro tăng.
- Từng bị warning kỳ trước (`was_warning=1`) -> tín hiệu quan trọng.

Planned (Future Work): SHAP/feature importance để giải thích trực tiếp theo model.

## 29) Scalability Design

Thiết kế có thể mở rộng cho hệ thống lớn:

- Stateless API -> dễ scale ngang (horizontal scaling).
- ML model preload (startup lifespan) -> giảm latency inference.

Planned:

- Redis cache (hot queries: student snapshot, analytics).
- Redis rate limiting (multi-instance).
- Batch jobs qua queue (Celery/RQ/Kafka) cho import/regenerate/training.
- Tách ML service riêng (microservice) khi tải tăng cao.

## 30) Advanced Security

Phù hợp hệ thống giáo dục có dữ liệu nhạy cảm:

Implemented:

- Input validation (Pydantic) giảm rủi ro injection và payload bất thường.
- Password hashing (bcrypt via passlib).
- JWT access token + refresh token (có revoke + rotation khi refresh).
- RBAC: admin / faculty_manager.
- Rate limit cho ML predict.
- CORS + Trusted Hosts + security headers.

Planned:

- Rate limit cho login/refresh để chống brute-force.
- Audit log “ai xem dữ liệu SV” (truy vết truy cập nhạy cảm).
- Masking/field-level access cho endpoint public (nếu mở cho phụ huynh).

## 31) Demo Scenario (End-to-End)

Mục tiêu demo: minh họa full pipeline “data -> warning -> risk -> recommendation”.

1) Import dữ liệu điểm (Admin):

- `POST /api/scores/import` (file Excel .xlsx)

2) Hệ thống tự tính thống kê học kỳ + sinh cảnh báo rule-based:

- cập nhật `student_semester_stats`
- sinh `academic_warnings` theo rule set active

3) Train model ML (Admin):

- `POST /api/ml/train` hoặc `python -m app.infrastructure.ml.train_model`

4) Gọi API phân tích cho 1 sinh viên (Internal):

- `GET /api/warnings/analysis/{student_code}?model=random_forest`

5) Hiển thị output (frontend/Swagger):

- Warning hiện tại (rule-based)
- Risk kỳ sau (ML)
- Recommendation (policy/recommendation service)

## 32) Deploy Render (Docker)

Repo đã có sẵn:

- `Dockerfile`
- `.dockerignore`
- `render.yaml`

### Chuẩn bị

1. Push code lên GitHub.
2. Tạo PostgreSQL trên Render (hoặc dùng DB ngoài).
3. Trong Render, tạo Web Service từ repo (Render sẽ đọc `render.yaml`).

### Environment variables bắt buộc

- `DATABASE_URL` (PostgreSQL URL)
- `SECRET_KEY` (chuỗi mạnh, không dùng mặc định)
- `APP_ENV=production`

Khuyến nghị thêm:

- `TRUSTED_HOSTS=["<your-render-domain>"]`
- `CORS_ALLOW_ORIGINS=["https://<your-frontend-domain>"]`
- SMTP (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`)

### Start command trong container

`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Health check

- Endpoint: `GET /health`
- Đã cấu hình trong `render.yaml` bằng `healthCheckPath: /health`

### Sau khi deploy

1. Kiểm tra `https://<your-render-domain>/health`
2. Kiểm tra Swagger: `https://<your-render-domain>/docs`
3. Chạy migration/seed (nếu DB mới):
   - `alembic upgrade head`
   - `python scripts/seed.py`
4. Train model:
   - `POST /api/ml/train` hoặc `POST /api/ml/train-all`

