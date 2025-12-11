# CLAUDE.md - System Inspector Demo v5.1.0

## FULL-AUTO INSTRUCTIONS FOR NEW CLAUDE SESSION

**Yeni bir Claude session açıldığında bu dosyayı oku ve aşağıdaki komutları çalıştır:**

### Başlatma (Task 1-5)
```bash
cd /Users/umitkacar/Documents/github-pluginagentmarketplace/claude-collective-intelligence/rabbitmq-agents/demos/demo-3-system-inspector && python3 orchestrator.py
```

### Kapatma (Task Final)
```bash
python3 orchestrator.py --task task_final --load-context
```

**Veya kısa yol:**
```bash
./run.sh           # Başlat
./run.sh shutdown  # Kapat (TODO: eklenecek)
```

---

## Bu Demo Ne Yapar?

Multi-agent terminal orchestration pipeline - Mac dual-monitor setup:

1. **Task 1 - Display Inspector:** Mac'teki tüm ekranları tespit eder
   - Ana ekran (main display) bilgilerini alır
   - Harici ekran (external display) bilgilerini alır
   - Çözünürlük, pozisyon, bağlantı türü gibi detayları toplar

2. **Task 2 - Terminal Setup:** Harici ekrana 3 terminal açar + Window ID capture
   - Harici ekran çözünürlüğünü dinamik olarak kullanır
   - 3 terminal yan yana açar (LEADER, WORKER-1, WORKER-2)
   - **KEY INNOVATION:** Her terminalin Window ID'sini yaratım anında yakalar
   - Window ID'ler değişmez - %100 güvenilir hedefleme!

3. **Task 3 - Screenshot Validator:** Doğrulama screenshot'ı alır
   - Harici ekranın ekran görüntüsünü kaydeder
   - Terminallerin doğru açıldığını doğrular

4. **Task 4 - Claude Launcher:** Her terminalde Claude Code başlatır
   - Window ID ile kesin hedefleme yapar
   - `claude --dangerously-skip-permissions` komutu çalıştırır
   - Her Claude instance için 7 saniye bekleme

5. **Task 5 - Role Prompter:** RabbitMQ rollerini atar
   - Window ID ile her terminale rol-spesifik mesaj gönderir
   - LEADER → Takım Lideri görevi
   - WORKER-1 → Agent görevi
   - WORKER-2 → Worker görevi

6. **Task Final - Safe Shutdown:** (NEW in v5.1.0)
   - `/exit` komutu gönderir (Claude Code kapatır)
   - 5 saniye bekler
   - Terminal penceresini kapatır
   - Window ID ile %100 güvenilir hedefleme

---

## Key Innovation: Window ID Tracking

### Problem
AppleScript ile 3 terminale mesaj gönderirken hangisinin hangisi olduğunu tespit edemiyorduk:
- Window index: Değişiyor (pencereler yeniden sıralandığında)
- Title-based: Claude Code terminal başlıklarını üzerine yazıyor
- X-position: Kırılgan (±50px tolerans)

### Solution: Window ID at Creation Time
```applescript
tell application "Terminal"
    do script ""
    set currentWindowID to id of window 1  -- HEMEN YAKALA!
    -- Bu ID terminal kapatılmadıkça değişmez
end tell
```

### Targeting with Window ID
```applescript
tell application "Terminal"
    set targetWindow to window id 25534  -- KESIN HEDEF!
    set frontmost of targetWindow to true
    -- keystroke message or /exit...
end tell
```

**Result:** %100 güvenilir terminal hedefleme!

---

## Pipeline Architecture

```
==========================================================================
                    SYSTEM INSPECTOR PIPELINE v5.1.0
==========================================================================

 TASK 1           TASK 2              TASK 3           TASK 4           TASK 5
 Display   -----> Terminal    -----> Screenshot -----> Claude   -----> Role
 Inspector        Setup              Validator         Launcher        Prompter
                     |
                     v
              Window ID Capture
              [25534, 25536, 25538]
                     |
                     +------------------+------------------+
                     |                  |                  |
                     v                  v                  v
                  LEADER             WORKER-1           WORKER-2
                  (25534)            (25536)            (25538)
                     |                  |                  |
                     v                  v                  v
              Takim Lideri          Agent              Worker
               gorevi               gorevi             gorevi
                     |                  |                  |
                     +------------------+------------------+
                                       |
                                       v
                                 TASK FINAL
                               Safe Shutdown
                                       |
                     +------------------+------------------+
                     |                  |                  |
                     v                  v                  v
                  /exit              /exit              /exit
                  close              close              close

==========================================================================
```

---

## Dosya Yapısı (v5.1.0)

```
demo-3-system-inspector/
│
├── 🚀 ENTRY POINTS (Giriş Noktaları)
│   ├── orchestrator.py      # ANA SCRIPT - python3 orchestrator.py
│   ├── run.sh               # Shell shortcut - ./run.sh
│   └── CLAUDE.md            # Bu dosya - Yeni session talimatları
│
├── ⚙️ CONFIGURATION (Yapılandırma)
│   └── config/
│       └── workflow.yaml    # Pipeline tanımı v5.1.0, 6 task
│
├── 🔧 TASKS (Pipeline Task'ları)
│   └── tasks/
│       ├── __init__.py              # Task exports
│       ├── base.py                  # BaseTask abstract class
│       ├── display_inspector.py     # Task 1: Ekran tespiti (v1.0.0)
│       ├── terminal_setup.py        # Task 2: Terminal + Window ID (v3.0.0)
│       ├── screenshot_validator.py  # Task 3: Screenshot (v1.0.0)
│       ├── claude_launcher.py       # Task 4: Claude başlatma (v2.0.0)
│       ├── role_prompter.py         # Task 5: Rol atama (v2.0.0)
│       └── task_final.py            # Task Final: Safe shutdown (v1.0.0) NEW!
│
├── 📜 SCRIPTS (Oluşturulan Scriptler)
│   └── scripts/
│       └── setup_terminals.scpt     # Auto-generated AppleScript
│
├── 📸 SCREENSHOTS (Doğrulama - IMMUTABLE)
│   └── screenshots/
│       ├── external_display_WORKED_2.jpg       # Task 2 doğrulama
│       ├── claude_verification_WORKED_2.jpg    # Task 4 doğrulama
│       ├── response_leader_WORKED_2.jpg        # Leader yanıtı
│       ├── response_worker-1_WORKED_2.jpg      # Agent yanıtı
│       ├── response_worker-2_WORKED_2.jpg      # Worker yanıtı
│       └── role_prompter_final_WORKED_2.jpg    # Final doğrulama
│
├── 📊 REPORTS (Raporlar - IMMUTABLE)
│   └── reports/
│       ├── pipeline_report_WORKED_2.json       # Task 1-5 raporu
│       └── shutdown_report_WORKED_2.json       # Task Final raporu
│
├── 📦 ARCHIVE (Önceki WORKED dosyaları)
│   └── archive/
│       ├── screenshots/
│       └── reports/
│
└── 📚 DOCUMENTATION (Dokümantasyon)
    ├── README.md            # Kullanım kılavuzu v5.1.0
    └── WORKFLOW.md          # Detaylı tasarım dokümanı v5.1.0
```

**Note:** `_WORKED_2` dosyaları `chflags uchg` ile immutable işaretlenmiştir.

---

## Role Assignment Messages

| Terminal | Role | Message |
|----------|------|---------|
| LEADER | Takım Lideri | "Sana Takim Lideri gorevi verecegim, RabbitMQ baglantisi yapip gorevini deklare edeceksin, hazir misin?" |
| WORKER-1 | Agent | "Sana Agent gorevi verecegim, RabbitMQ baglantisi yapip gorevini deklare edeceksin, hazir misin?" |
| WORKER-2 | Worker | "Sana Worker gorevi verecegim, RabbitMQ baglantisi yapip gorevini deklare edeceksin, hazir misin?" |

---

## Hızlı Komutlar

```bash
# Tüm pipeline'ı çalıştır (Task 1-5)
python3 orchestrator.py

# Güvenli kapatma (Task Final) - ÖNEMLİ: --load-context gerekli!
python3 orchestrator.py --task task_final --load-context

# Sadece belirli task'ı çalıştır
python3 orchestrator.py --task display_inspector
python3 orchestrator.py --task terminal_setup
python3 orchestrator.py --task screenshot_validator
python3 orchestrator.py --task claude_launcher
python3 orchestrator.py --task role_prompter

# Dry run (planı göster)
python3 orchestrator.py --dry-run

# Task listesi
python3 orchestrator.py --list
```

---

## Timing Configuration

| Parameter | Value | Purpose |
|-----------|-------|---------|
| wait_between_launches | 7s | Claude initialization |
| wait_after_all | 5s | All Claudes ready |
| wait_before_typing | 5s | Claude ready for input |
| wait_after_enter | 10s | Claude response time |
| wait_between_terminals | 7s | Context switch time |
| wait_before_exit | 2s | Before /exit command |
| wait_after_exit | 5s | Claude shutdown time |
| wait_before_close | 2s | Before terminal close |

**Total Pipeline Duration:** ~80 seconds (Task 1-5)
**Total Shutdown Duration:** ~37 seconds (Task Final)
**Total Combined:** ~117 seconds

---

## Context Flow

Tasks share data via context dictionary:

```python
context = {}

# Task 1 adds:
context['displays'] = [...]
context['external_display'] = {...}
context['main_display'] = {...}

# Task 2 adds:
context['terminals'] = [...with window_ids...]
context['window_ids'] = [25534, 25536, 25538]
context['x_offset'] = 1280

# Task 3 adds:
context['screenshot'] = 'external_display_WORKED_2.jpg'

# Task 4 adds:
context['launched_in'] = ['LEADER', 'WORKER-1', 'WORKER-2']

# Task 5 adds:
context['role_assignments'] = {...}

# Task Final adds (via --load-context):
context['closed_count'] = 3
context['shutdown_complete'] = True
```

---

## Verified Evidence

Immutable files (chflags uchg) - WORKED_2:

**Screenshots:**
- `external_display_WORKED_2.jpg` - 3 terminals on external display
- `claude_verification_WORKED_2.jpg` - Claude Code running in all 3
- `response_leader_WORKED_2.jpg` - Leader accepted role
- `response_worker-1_WORKED_2.jpg` - Agent accepted role
- `response_worker-2_WORKED_2.jpg` - Worker accepted role
- `role_prompter_final_WORKED_2.jpg` - Final verification

**Reports:**
- `pipeline_report_WORKED_2.json` - Task 1-5 execution log
- `shutdown_report_WORKED_2.json` - Task Final execution log

**Archive:**
- `archive/screenshots/*_WORKED.jpg` - Previous verified screenshots
- `archive/reports/pipeline_report_WORKED.json` - Previous verified report

---

## Yeni Task Ekleme (Scalability)

1. `tasks/` klasörüne yeni `.py` dosyası ekle
2. `BaseTask`'tan türet
3. `tasks/__init__.py`'a import ekle
4. `config/workflow.yaml`'a task'ı ekle

```python
# tasks/my_task.py
from .base import BaseTask, TaskResult, TaskStatus

class MyTask(BaseTask):
    name = "my_task"
    description = "Does something"

    def execute(self, context):
        # context'ten önceki task'ların çıktılarını al
        terminals = context.get('terminals', [])
        window_ids = context.get('window_ids', [])

        # Window ID ile işlem yap
        for terminal in terminals:
            window_id = terminal.get('window_id')
            # ...

        return TaskResult(
            task_name=self.name,
            status=TaskStatus.SUCCESS,
            data={'result': 'done'}
        )
```

---

**Version:** 5.1.0 (Window ID Tracking + RabbitMQ Role Assignment + Safe Shutdown)
**Status:** WORKING - VERIFIED (WORKED_2)
**Last Updated:** 2025-12-11
