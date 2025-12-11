"""
Task Final: Safe Shutdown v1.0.0 - Claude Code & Terminal Cleanup
=================================================================
Pipeline sonunda guvenli kapatma:
1. Her terminalde /exit komutu gonderir (Claude Code kapatir)
2. Claude Code kapandiktan sonra terminali kapatir

Window ID ile kesin hedefleme - %100 guvenilir!
ULTRATHINK Edition
"""

import subprocess
import time
from datetime import datetime
from typing import Any, Dict
from pathlib import Path

from .base import BaseTask, TaskResult, TaskStatus


class TaskFinal(BaseTask):
    """
    Task Final - Safe Shutdown

    1. Her terminal penceresine odaklan (Window ID ile)
    2. /exit komutu gonder (Claude Code kapatir)
    3. Claude kapanmasi icin bekle
    4. Terminal penceresini kapat
    5. Temizlik tamamlandi
    """

    name = "task_final"
    description = "Claude Code ve terminalleri guvenli kapatir"
    version = "1.0.0"

    DEFAULT_CONFIG = {
        'wait_before_exit': 2,         # /exit gondermeden once bekle
        'wait_after_exit': 5,          # Claude kapanmasi icin bekle
        'wait_before_close': 2,        # Terminal kapatmadan once bekle
        'wait_between_terminals': 3,   # Terminaller arasi bekleme
        'close_terminal_after': True,  # Terminal penceresini de kapat
        'screenshot_before': False,    # Kapatmadan once screenshot
        'screenshot_dir': 'screenshots',
    }

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.settings = {**self.DEFAULT_CONFIG, **(config or {})}

    def execute(self, context: Dict[str, Any]) -> TaskResult:
        """Her terminalde Claude Code'u ve terminali guvenli kapat"""

        print("\n🛑 Task Final v1.0.0 (Safe Shutdown)...")

        # Onceki task'lardan bilgi al
        terminals = context.get('terminals', [])
        role_assignments = context.get('role_assignments', {})

        if not terminals:
            return TaskResult(
                task_name=self.name,
                status=TaskStatus.FAILED,
                error="No terminal information from previous tasks"
            )

        terminal_count = len(terminals)
        wait_before = self.settings['wait_before_exit']
        wait_after = self.settings['wait_after_exit']
        wait_close = self.settings['wait_before_close']
        wait_between = self.settings['wait_between_terminals']
        close_terminal = self.settings['close_terminal_after']

        print(f"   🖥️  Terminals to close: {terminal_count}")
        print(f"   ⏱️  Wait before /exit: {wait_before}s")
        print(f"   ⏱️  Wait after /exit: {wait_after}s")
        print(f"   ⏱️  Wait before close: {wait_close}s")
        print(f"   🚪 Close terminal after: {close_terminal}")

        # Kapatma sirasi goster
        print(f"\n   📋 KAPATMA SIRASI:")
        for term in terminals:
            title = term.get('title', 'Unknown')
            window_id = term.get('window_id', 'N/A')
            role = role_assignments.get(title, {}).get('role', title)
            print(f"      🔑 {title} (ID: {window_id}) - {role}")

        # Her terminali kapat
        results = []
        closed_count = 0

        for i, term in enumerate(terminals):
            terminal_title = term.get('title', f'Terminal {i+1}')
            window_id = term.get('window_id')

            print(f"\n   🛑 [{terminal_title}] Window ID: {window_id}")

            # 1. /exit gonder
            print(f"   ⏳ Waiting {wait_before}s before sending /exit...")
            time.sleep(wait_before)

            print(f"   📤 Sending /exit command...")
            exit_success = self._send_exit_command(window_id)

            if exit_success:
                print(f"   ✅ /exit sent to {terminal_title}")

                # 2. Claude kapanmasi icin bekle
                print(f"   ⏳ Waiting {wait_after}s for Claude Code to close...")
                time.sleep(wait_after)

                # 3. Terminal penceresini kapat
                if close_terminal:
                    print(f"   ⏳ Waiting {wait_close}s before closing terminal...")
                    time.sleep(wait_close)

                    print(f"   🚪 Closing terminal window...")
                    close_success = self._close_terminal_window(window_id)

                    if close_success:
                        print(f"   ✅ Terminal {terminal_title} closed")
                        closed_count += 1
                        results.append({
                            'terminal': terminal_title,
                            'window_id': window_id,
                            'exit_sent': True,
                            'terminal_closed': True,
                            'status': 'success'
                        })
                    else:
                        print(f"   ⚠️  Failed to close terminal {terminal_title}")
                        results.append({
                            'terminal': terminal_title,
                            'window_id': window_id,
                            'exit_sent': True,
                            'terminal_closed': False,
                            'status': 'partial'
                        })
                else:
                    closed_count += 1
                    results.append({
                        'terminal': terminal_title,
                        'window_id': window_id,
                        'exit_sent': True,
                        'terminal_closed': False,
                        'status': 'exit_only'
                    })
            else:
                print(f"   ⚠️  Failed to send /exit to {terminal_title}")
                results.append({
                    'terminal': terminal_title,
                    'window_id': window_id,
                    'exit_sent': False,
                    'terminal_closed': False,
                    'status': 'failed'
                })

            # Son terminal degilse bekle
            if i < terminal_count - 1:
                print(f"   ⏳ Waiting {wait_between}s before next terminal...")
                time.sleep(wait_between)

        # Ozet
        successful = sum(1 for r in results if r['status'] in ['success', 'exit_only'])

        print(f"\n   📋 KAPATMA ÖZETİ:")
        print(f"   ─────────────────────────────────────")
        print(f"   🎯 Basariyla kapatildi: {successful}/{terminal_count}")
        for r in results:
            status_icon = "✅" if r['status'] == 'success' else ("⚡" if r['status'] == 'exit_only' else "❌")
            wid = r.get('window_id', 'N/A')
            print(f"      {status_icon} {r['terminal']} (ID: {wid}) - {r['status']}")
        print(f"   ─────────────────────────────────────")

        return TaskResult(
            task_name=self.name,
            status=TaskStatus.SUCCESS if successful > 0 else TaskStatus.FAILED,
            data={
                'closed_count': successful,
                'total_terminals': terminal_count,
                'results': results,
                'shutdown_complete': successful == terminal_count
            }
        )

    def _send_exit_command(self, window_id: int) -> bool:
        """Window ID ile /exit komutu gonder - Claude Code kapatir"""

        applescript = f'''
tell application "Terminal"
    activate
    delay 0.3

    -- Window ID ile kesin hedefle
    try
        set targetWindow to window id {window_id}

        -- Pencereyi one getir
        set frontmost of targetWindow to true
        set index of targetWindow to 1
        delay 0.5

        -- /exit komutu gonder
        tell application "System Events"
            tell process "Terminal"
                keystroke "/exit"
                delay 0.3
                keystroke return
            end tell
        end tell

        return "OK: /exit sent to Window ID {window_id}"
    on error errMsg
        return "ERROR: " & errMsg
    end try
end tell
'''

        try:
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=15
            )

            if 'OK' in result.stdout:
                return True
            else:
                print(f"      ⚠️  AppleScript: {result.stdout.strip()} {result.stderr.strip()}")
                return False

        except Exception as e:
            print(f"      ❌ Error: {e}")
            return False

    def _close_terminal_window(self, window_id: int) -> bool:
        """Window ID ile terminal penceresini kapat"""

        applescript = f'''
tell application "Terminal"
    try
        set targetWindow to window id {window_id}

        -- Pencereyi kapat
        close targetWindow

        return "OK: Window ID {window_id} closed"
    on error errMsg
        -- Pencere zaten kapanmis olabilir
        return "OK: Window may already be closed"
    end try
end tell
'''

        try:
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=10
            )

            if 'OK' in result.stdout:
                return True
            else:
                print(f"      ⚠️  AppleScript: {result.stdout.strip()} {result.stderr.strip()}")
                return False

        except Exception as e:
            print(f"      ❌ Error: {e}")
            return False

    def _close_terminal_by_x_position(self, x_position: int) -> bool:
        """Fallback: X pozisyonu ile terminal kapat (Window ID yoksa)"""

        applescript = f'''
tell application "Terminal"
    set targetWindow to null
    set targetX to {x_position}

    repeat with w in windows
        set windowBounds to bounds of w
        set windowX to item 1 of windowBounds
        -- X pozisyonu ±50 pixel tolerans ile esles
        if windowX >= (targetX - 50) and windowX <= (targetX + 50) then
            set targetWindow to w
            exit repeat
        end if
    end repeat

    if targetWindow is not null then
        close targetWindow
        return "OK: Window at x={x_position} closed"
    else
        return "ERROR: Window at x={x_position} not found"
    end if
end tell
'''

        try:
            result = subprocess.run(
                ['osascript', '-e', applescript],
                capture_output=True,
                text=True,
                timeout=10
            )

            if 'OK' in result.stdout:
                return True
            else:
                return False

        except Exception as e:
            print(f"      ❌ Error: {e}")
            return False
