# PharmApp Reminder Config & Runner

Bộ công cụ nhắc việc gọn nhẹ, đa nền tảng, chỉ dùng thư viện chuẩn Python:

- **`remind_config_gui.py`**: **GUI Tkinter** theo theme PharmApp để tạo/sửa file cấu hình `reminders.toml`.
- **`remind_runner.py`**: **runner chạy nền** (hot-reload) đọc `reminders.toml` và kích hoạt nhắc việc (và chạy lệnh nếu cần) theo thời gian.

Mục tiêu: đơn giản, không phụ thuộc thư viện ngoài, chạy tốt trên Windows/macOS/Linux.

---

## Tính năng

### 1) GUI cấu hình (Tkinter)
- Sửa **timezone**, **sound file** toàn cục, và danh sách **task**
- Trường của task: `time`, `type` (`notify` / `command` / `both`), `message`, `command`, `days`, `enabled`, `sound`
- Preset nhanh cho ngày: **Every day**, **Weekdays**, **Weekend**, **Clear**
- Quản lý task: **Add / Duplicate / Delete / Reorder**
- Chọn file âm thanh, test âm thanh, chọn file/lệnh để chạy
- Phím tắt:
  - **Ctrl+O** Open
  - **Ctrl+S** Save
  - **Ctrl+Shift+S** Save As
  - **F2** Add task
  - **Ctrl+D** Duplicate task
  - **Delete** Remove task
  - **Alt+Up / Alt+Down** Reorder

### 2) Runner (CLI)
- Đọc `reminders.toml` và chạy liên tục
- **Hot reload**: tự reload khi file TOML thay đổi
- Lọc theo ngày: hỗ trợ **Mon–Sun** và cả viết tắt tiếng Việt **T2–CN**
- Phát âm thanh khi nhắc việc (có fallback theo OS)
- Chạy command để tự động hóa

---

## Yêu cầu

- **Python 3.11+** (dùng `tomllib` của thư viện chuẩn)

Không cần cài thêm package nào.

---

## Bắt đầu nhanh

### 1) Clone repo
```bash
git clone <YOUR_REPO_URL>
cd <YOUR_REPO_FOLDER>
```

### 2) Tạo file cấu hình: `reminders.toml`
Tạo file `reminders.toml` cùng thư mục với script (hoặc đặt tên khác).

Ví dụ:

```toml
timezone = "Asia/Ho_Chi_Minh"
sound_file = "C:/Windows/Media/notify.wav"

[[task]]
time = "07:30"
type = "both"
message = "Chạy script buổi sáng"
command = "python C:/path/to/script.py"
days = ["Mon","Tue","Wed","Thu","Fri"]
enabled = true
sound = true

[[task]]
time = "15:00"
type = "notify"
message = "Ghi báo cáo hằng ngày"
enabled = true
sound = true
```

Ghi chú:
- Nếu `days` không có hoặc để trống thì task chạy **mỗi ngày**.
- `time` phải theo định dạng **24h `HH:MM`**.
- `type`:
  - `notify`: chỉ thông báo (in ra console)
  - `command`: chỉ chạy lệnh
  - `both`: vừa thông báo vừa chạy lệnh

---

## Cách chạy

### Cách A — Dùng GUI để sửa TOML
```bash
python remind_config_gui.py --config reminders.toml
```

### Cách B — Chạy runner nhắc việc
```bash
python remind_runner.py --config reminders.toml
```

Tùy chọn khoảng thời gian polling (giây):
```bash
python remind_runner.py --config reminders.toml --tick 5
```

---

## Tham chiếu cấu trúc TOML

Cấu hình global:

```toml
timezone = "Asia/Ho_Chi_Minh"
sound_file = "/path/to/sound.wav"   # tùy chọn
```

Mỗi task:

```toml
[[task]]
time = "08:00"                      # bắt buộc
type = "notify"                     # notify | command | both
message = "Reminder"                # nội dung thông báo (console)
command = "python /path/to/job.py"  # tùy chọn
days = ["Mon","Tue"]                # tùy chọn (Mon..Sun hoặc T2..CN)
enabled = true                      # tùy chọn (mặc định true)
sound = true                        # tùy chọn (mặc định true)
```

Giá trị ngày hỗ trợ trong runner:
- English: `Mon Tue Wed Thu Fri Sat Sun`
- Viết tắt: `T2 T3 T4 T5 T6 T7 CN`

---

## Ghi chú theo hệ điều hành

### Âm thanh
- **Windows**: dùng `winsound` (khuyến nghị `.wav`). Nếu không có file thì sẽ beep.
- **macOS**: dùng `afplay` nếu có.
- **Linux**: thử `paplay` hoặc `aplay` với file âm thanh hệ thống.
- Nếu không có backend audio, sẽ fallback sang bell của terminal.

### Chạy command
Runner chạy command theo dạng:
- `subprocess.Popen(cmd, shell=True)`

Khuyến nghị:
- Dùng đường dẫn tuyệt đối.
- Đường dẫn có khoảng trắng nên đặt trong dấu nháy.
- Không dùng TOML không rõ nguồn gốc.

---

## Xử lý lỗi thường gặp

- **Không nhắc**: đảm bảo runner đang chạy liên tục và timezone hệ thống đúng.
- **Sai định dạng giờ**: `time` phải là `HH:MM` (24h).
- **Không có âm thanh**:
  - kiểm tra `sound_file` có tồn tại
  - trên Windows nên dùng `.wav`
- **Sai ngày**: kiểm tra `days` (Mon–Sun hoặc T2–CN).

---

## Cấu trúc repo

```
.
├─ remind_config_gui.py   # GUI Tkinter chỉnh reminders.toml
├─ remind_runner.py       # Runner nhắc việc + chạy lệnh
└─ reminders.toml         # File cấu hình (tự tạo)
```

---

## License

Bạn thêm license phù hợp (MIT/Apache-2.0/GPL-3.0, …) vào repo GitHub.
