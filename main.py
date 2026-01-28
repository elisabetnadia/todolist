import json
import os
import time
import threading
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from tabulate import tabulate

# File untuk menyimpan data
DATA_FILE = "tasks.json"
# Aktifkan/Non-aktifkan bunyi alarm
SOUND_ENABLED = True
 

def load_tasks():
    """Memuat data tugas dari file JSON dan normalisasi fields."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
        except Exception:
            return []

        # normalize
        for i, t in enumerate(tasks, 1):
            t.setdefault('id', i)
            if 'nama' not in t and 'judul' in t:
                t['nama'] = t['judul']
            t.setdefault('nama', '(tanpa nama)')
            if 'status' not in t:
                t['status'] = 'SELESAI' if t.get('completed', False) else 'BELUM'
            t.setdefault('completed', t['status'] == 'SELESAI')
            t.setdefault('notified_1d', False)
            t.setdefault('notified_1h', False)
            t.setdefault('priority', 'MEDIUM')
        return tasks
    return []


def save_tasks(tasks):
    """Simpan daftar tugas ke file JSON."""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def log_event(message: str):
    """Tambahkan entri ke LOG.txt dengan timestamp."""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with open('LOG.txt', 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {message}\n")
    except Exception:
        pass
def display_tasks(tasks):
    """Menampilkan semua tugas"""
    if not tasks:
        print("\n❌ Tidak ada tugas.\n")
        return

    # Tampilkan ringkasan tugas TERLAMBAT
    late = [t for t in tasks if t.get('status') == 'TERLAMBAT']
    if late:
        print(f"\n[!] {len(late)} tugas TERLAMBAT:")
        for t in late:
            print(f" - {t.get('nama')} (deadline: {t.get('deadline')})")
        print()

    # Urutkan semua tugas berdasarkan deadline terdekat
    def _deadline_key(t):
        try:
            return parse_deadline_string(t.get('deadline',''))
        except Exception:
            return datetime.max

    sorted_tasks = sorted(tasks, key=_deadline_key)

    table_data = []
    for i, task in enumerate(sorted_tasks, 1):
        st = task.get("status", "BELUM")
        if st == "TERLAMBAT":
            status = "❗ TERLAMBAT"
        elif st == "SELESAI":
            status = "✓ SELESAI"
        else:
            status = "⏳ BELUM"
        table_data.append([
            i,
            task.get('nama', '(tanpa nama)'),
            task.get('mata_pelajaran', ''),
            task.get('deadline', ''),
            task.get('priority', 'MEDIUM'),
            status
        ])

    headers = ["NO", "TUGAS", "MATA PELAJARAN", "DEADLINE", "PRIORITY", "STATUS"]
    print("\n" + tabulate(table_data, headers=headers, tablefmt="grid", stralign="left"))
    print()

def add_task(tasks):
    """Menambah tugas baru"""
    print("\n\033[1m--- TAMBAH TUGAS BARU ---\033[0m")
    
    nama = input("Nama tugas: ").strip()
    if not nama:
        print("❌ Nama tugas tidak boleh kosong!\n")
        return
    
    mata_pelajaran = input("Mata pelajaran: ").strip()
    if not mata_pelajaran:
        print("❌ Mata pelajaran tidak boleh kosong!\n")
        return
    
    deadline_date = input("Deadline (format: DD-MM-YYYY): ").strip()
    if not deadline_date:
        print("❌ Deadline tidak boleh kosong!\n")
        return

    waktu = input("Waktu (format: HH:MM atau HH:MM:SS, kosong = 23:59:59): ").strip()
    if waktu:
        deadline = f"{deadline_date} {waktu}"
    else:
        deadline = deadline_date
    if not deadline:
        print("❌ Deadline tidak boleh kosong!\n")
        return
    
    # Validasi format deadline (mendukung waktu opsional)
    try:
        _ = parse_deadline_string(deadline)
    except ValueError:
        print("❌ Format deadline tidak valid! Gunakan DD-MM-YYYY dan waktu HH:MM[:SS]\n")
        return
    
    # Priority input
    pri = input("Priority (LOW/MEDIUM/HIGH) [MEDIUM]: ").strip().upper() or "MEDIUM"
    if pri not in ("LOW", "MEDIUM", "HIGH"):
        print("⚠️ Priority tidak valid, diset ke MEDIUM")
        pri = "MEDIUM"

    task = {
        "id": len(tasks) + 1,
        "nama": nama,
        "mata_pelajaran": mata_pelajaran,
        "deadline": deadline,
        "completed": False,
        "status": "BELUM",
        "priority": pri,
        "notified_1d": False,
        "notified_1h": False,
        "created_at": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }
    
    tasks.append(task)
    save_tasks(tasks)
    log_event(f"Tambah tugas: {nama} (deadline: {deadline})")
    print(f"✅ Tugas '{nama}' berhasil ditambahkan!\n")
    # Jika user menyertakan waktu, mulai hitung mundur otomatis di background
    if waktu:
        start_countdown_for_task(task)

def delete_task(tasks):
    """Menghapus tugas"""
    if not tasks:
        print("\n❌ Tidak ada tugas untuk dihapus.\n")
        return
    
    display_tasks(tasks)
    
    try:
        nomor = int(input("Masukkan nomor tugas yang ingin dihapus: "))
        if 1 <= nomor <= len(tasks):
            nama_tugas = tasks[nomor - 1]["nama"]
            tasks.pop(nomor - 1)
            save_tasks(tasks)
            log_event(f"Hapus tugas: {nama_tugas}")
            print(f"✅ Tugas '{nama_tugas}' berhasil dihapus!\n")
        else:
            print("❌ Nomor tidak valid!\n")
    except ValueError:
        print("❌ Masukkan angka yang valid!\n")

def mark_completed(tasks):
    """Menandai tugas sebagai selesai"""
    if not tasks:
        print("\n❌ Tidak ada tugas.\n")
        return
    
    display_tasks(tasks)
    
    try:
        nomor = int(input("Masukkan nomor tugas yang sudah selesai: "))
        if 1 <= nomor <= len(tasks):
            t = tasks[nomor - 1]
            # toggle
            if t.get("status") == "SELESAI":
                t["status"] = "BELUM"
                t["completed"] = False
                status = "belum selesai"
            else:
                t["status"] = "SELESAI"
                t["completed"] = True
                status = "selesai"

            save_tasks(tasks)
            log_event(f"Tandai {status}: {t.get('nama')}")
            print(f"✅ Tugas ditandai sebagai {status}!\n")
        else:
            print("❌ Nomor tidak valid!\n")
    except ValueError:
        print("❌ Masukkan angka yang valid!\n")

def edit_task(tasks):
    """Mengedit tugas yang sudah ada"""
    if not tasks:
        print("\n❌ Tidak ada tugas untuk diedit.\n")
        return
    
    display_tasks(tasks)
    
    try:
        nomor = int(input("Masukkan nomor tugas yang ingin diedit: "))
        if not (1 <= nomor <= len(tasks)):
            print("❌ Nomor tidak valid!\n")
            return
        
        task = tasks[nomor - 1]
        
        print("\n\033[1m--- EDIT TUGAS ---\033[0m")
        print(f"Nama tugas saat ini: {task['nama']}")
        nama_baru = input("Nama tugas baru (kosongkan jika tidak ingin diubah): ").strip()
        if nama_baru:
            task['nama'] = nama_baru
        
        print(f"Mata pelajaran saat ini: {task['mata_pelajaran']}")
        mp_baru = input("Mata pelajaran baru (kosongkan jika tidak ingin diubah): ").strip()
        if mp_baru:
            task['mata_pelajaran'] = mp_baru
        
        print(f"Deadline saat ini: {task['deadline']}")
        deadline_baru = input("Deadline baru dalam format DD-MM-YYYY (kosongkan jika tidak ingin diubah): ").strip()
        if deadline_baru:
            try:
                datetime.strptime(deadline_baru, "%d-%m-%Y")
                task['deadline'] = deadline_baru
            except ValueError:
                print("❌ Format deadline tidak valid!\n")
                return
        
        save_tasks(tasks)
        log_event(f"Edit tugas: {task.get('nama')}")
        print(f"✅ Tugas berhasil diperbarui!\n")
    except ValueError:
        print("❌ Masukkan angka yang valid!\n")

def search_tasks(tasks):
    """Mencari tugas berdasarkan nama atau mata pelajaran"""
    if not tasks:
        print("\n❌ Tidak ada tugas.\n")
        return
    
    
    keyword = input("\nCari berdasarkan nama atau mata pelajaran: ").strip().lower()
    
    hasil = [task for task in tasks if keyword in task['nama'].lower() or keyword in task['mata_pelajaran'].lower()]
    
    if hasil:
        table_data = []
        for i, task in enumerate(hasil, 1):
            status = "✓ Selesai" if task.get("completed", False) else "⏳ Belum"
            table_data.append([
                i,
                task['nama'],
                task['mata_pelajaran'],
                task['deadline'],
                status
            ])
        
        headers = ["NO", "TUGAS", "MATA PELAJARAN", "DEADLINE", "STATUS"]
        print("\n" + tabulate(table_data, headers=headers, tablefmt="grid", stralign="left"))
        print()
    else:
        print(f"\n❌ Tugas dengan kata kunci '{keyword}' tidak ditemukan.\n")

def _parse_time_input(s: str) -> int:
    """Parsekan input durasi menjadi total detik.
    Diterima: SS, MM:SS, atau HH:MM:SS
    """
    parts = s.split(":")
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        raise ValueError("Format waktu tidak valid")

    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    raise ValueError("Format waktu tidak valid")


def parse_deadline_string(s: str) -> datetime:
    """Parse deadline string yang bisa berupa:
    - DD-MM-YYYY HH:MM:SS
    - DD-MM-YYYY HH:MM
    - DD-MM-YYYY
    Mengembalikan datetime objek. Untuk format tanpa waktu, mengembalikan tanggal pada 23:59:59.
    """
    formats = ["%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y"]
    for fmt in formats:
        try:
            d = datetime.strptime(s, fmt)
            if fmt == "%d-%m-%Y":
                return datetime(d.year, d.month, d.day, 23, 59, 59)
            if fmt == "%d-%m-%Y %H:%M":
                return datetime(d.year, d.month, d.day, d.hour, d.minute, 0)
            return d
        except ValueError:
            continue
    raise ValueError("Format deadline tidak dikenali")


def start_countdown_for_task(task):
    """Mulai thread hitung mundur untuk `task` jika deadline memiliki waktu spesifik.

    Thread akan menunggu sampai waktu deadline, lalu memanggil `_alarm_notify`.
    """
    try:
        dl_dt = parse_deadline_string(task.get("deadline", ""))
    except Exception:
        return

    # Jika deadline ditentukan hanya tanggal (23:59:59) kita masih bisa
    # memulai countdown, tapi ini mungkin panjang — tetap diizinkan.
    secs = (dl_dt - datetime.now()).total_seconds()
    if secs <= 0:
        return

    def worker(name, seconds, task_id):
        try:
            time.sleep(seconds)
            # reload tasks to check status
            tasks = load_tasks()
            # find task by id and ensure not completed
            for t in tasks:
                if t.get("id") == task_id:
                    if not t.get("completed", False):
                        _alarm_notify(f"⏰ ALARM! '{name}' deadline tercapai")
                        t["status"] = "TERLAMBAT"
                        save_tasks(tasks)
                    break
        except Exception:
            pass

    th = threading.Thread(target=worker, args=(task.get("nama"), secs, task.get("id")), daemon=True)
    th.start()


def start_countdowns_for_all_tasks(tasks):
    """Mulai countdown background untuk semua tugas yang memiliki waktu spesifik pada deadline."""
    for task in tasks:
        try:
            dl_dt = parse_deadline_string(task.get('deadline', ''))
            # jika waktu bukan 23:59:59, anggap user memberikan waktu spesifik
            if dl_dt.hour != 23 or dl_dt.minute != 59 or dl_dt.second != 59:
                secs = (dl_dt - datetime.now()).total_seconds()
                if secs > 0:
                    start_countdown_for_task(task)
        except Exception:
            continue


def _alarm_notify(message: str):
    """Coba kirim notifikasi desktop dan bunyikan alarm terminal/OS."""
    # Desktop notification (Linux `notify-send` jika tersedia)
    try:
        if shutil.which("notify-send"):
            subprocess.Popen(["notify-send", "Alarm", message])
    except Exception:
        pass
    # Bunyi alarm: hanya jika SOUND_ENABLED True
    try:
        if SOUND_ENABLED:
            if sys.platform.startswith("win"):
                import winsound
                for _ in range(3):
                    winsound.Beep(1000, 500)
                    time.sleep(0.1)
            else:
                for _ in range(6):
                    print('\a', end='', flush=True)
                    time.sleep(0.25)
    except Exception:
        pass

    # Selalu tampilkan pesan teks (meskipun bunyi dimatikan)
    print(f"\n🔔 {message}\n")


def countdown_alarm(tasks=None):
    """Fitur hitung mundur dengan alarm peringatan."""
    print("\n\033[1m--- ALARM HITUNG MUNDUR ---\033[0m")
    durasi = input("Masukkan durasi (SS, MM:SS, atau HH:MM:SS): ").strip()
    if not durasi:
        print("❌ Durasi tidak boleh kosong!\n")
        return

    try:
        total = _parse_time_input(durasi)
    except ValueError:
        print("❌ Format durasi tidak valid! Gunakan SS, MM:SS, atau HH:MM:SS\n")
        return

    pesan = input("Pesan alarm (kosong = 'Waktu telah habis!'): ").strip() or "Waktu telah habis!"

    print(f"Memulai hitung mundur selama {durasi} (hh:mm:ss). Tekan Ctrl+C untuk batal.")
    try:
        while total > 0:
            hrs = total // 3600
            mins = (total % 3600) // 60
            secs = total % 60
            print(f"\rSisa waktu: {hrs:02}:{mins:02}:{secs:02}", end="", flush=True)
            time.sleep(1)
            total -= 1

        print("\rSisa waktu: 00:00:00                                ")
        _alarm_notify(pesan)
    except KeyboardInterrupt:
        print("\n⏸️ Penghitungan mundur dibatalkan.\n")
        return


def check_upcoming_deadlines(tasks, threshold_days: float = 1.0):
    """Tampilkan peringatan untuk tugas yang mendekati deadline.

    - `threshold_days` dapat berupa pecahan (contoh 0.5 = 12 jam).
    - Deadline tugas disimpan sebagai DD-MM-YYYY; dianggap berakhir pada 23:59:59 hari itu.
    """
    if not tasks:
        return

    now = datetime.now()
    threshold = timedelta(days=threshold_days)
    alerts = []

    for task in tasks:
        dl = task.get("deadline")
        if not dl:
            continue
        try:
            d = datetime.strptime(dl, "%d-%m-%Y")
            deadline_dt = datetime(d.year, d.month, d.day, 23, 59, 59)
            delta = deadline_dt - now
            if delta.total_seconds() > 0 and delta <= threshold:
                secs = int(delta.total_seconds())
                days = secs // 86400
                rem = secs % 86400
                hours = rem // 3600
                rem = rem % 3600
                minutes = rem // 60
                seconds = rem % 60

                if days > 0:
                    rem_str = f"{days}d {hours:02}:{minutes:02}:{seconds:02}"
                else:
                    rem_str = f"{hours:02}:{minutes:02}:{seconds:02}"

                alerts.append((task.get("nama", "(tanpa nama)"), rem_str))
        except Exception:
            continue

    if alerts:
        # Trigger a short alarm/notification
        _alarm_notify("⏰ ALARM! Kerjakan, deadline sudah mendekat")

        print("\n\033[1m🕒 PERINGATAN: Tugas Mendekati Deadline\033[0m")
        for name, rem_str in alerts:
            print(f"🕒 PERINGATAN: \"{name}\" deadline dalam {rem_str}")
        print()


def update_overdue_statuses(tasks):
    """Tandai tugas yang lewat deadline sebagai TERLAMBAT dan simpan perubahan."""
    changed = False
    now = datetime.now()
    for task in tasks:
        try:
            dl = task.get("deadline")
            if not dl:
                continue
            d = datetime.strptime(dl, "%d-%m-%Y")
            deadline_dt = datetime(d.year, d.month, d.day, 23, 59, 59)
            if now > deadline_dt and not task.get("completed", False) and task.get("status") != "TERLAMBAT":
                task["status"] = "TERLAMBAT"
                changed = True
                msg = f"Tugas \"{task.get('nama', '(tanpa nama)')}\" TERLAMBAT"
                print(f"[!] {msg}")
                log_event(msg)
        except Exception:
            continue

    if changed:
        save_tasks(tasks)


def notify_time_based(tasks):
    """Kirim notifikasi 1 hari dan 1 jam sebelum deadline (satu kali per task).

    Menandai `notified_1d` dan `notified_1h` agar tidak mengulang.
    """
    now = datetime.now()
    changed = False
    for task in tasks:
        if task.get("completed", False):
            continue
        try:
            dl = task.get("deadline")
            if not dl:
                continue
            d = datetime.strptime(dl, "%d-%m-%Y")
            deadline_dt = datetime(d.year, d.month, d.day, 23, 59, 59)
            delta = (deadline_dt - now).total_seconds()
            # 1 day = 86400 seconds, 1 hour = 3600 seconds
            if 0 < delta <= 86400 and not task.get("notified_1d", False):
                msg = f"🔔 Reminder: Tugas \"{task.get('nama')}\" 1 hari lagi"
                _alarm_notify(msg)
                task["notified_1d"] = True
                changed = True
                log_event(f"Reminder 1 hari: {task.get('nama')} (deadline: {task.get('deadline')})")
            if 0 < delta <= 3600 and not task.get("notified_1h", False):
                msg = f"🔔 Reminder: Tugas \"{task.get('nama')}\" 1 jam lagi"
                _alarm_notify(msg)
                task["notified_1h"] = True
                changed = True
                log_event(f"Reminder 1 jam: {task.get('nama')} (deadline: {task.get('deadline')})")
        except Exception:
            continue

    if changed:
        save_tasks(tasks)


def show_stats(tasks):
    """Tampilkan statistik sederhana: total, selesai, persentase, dan progress bar."""
    total = len(tasks)
    done = sum(1 for t in tasks if t.get('status') == 'SELESAI')
    pct = int((done / total) * 100) if total > 0 else 0
    # bigger ASCII bar (20 blocks)
    filled = int(pct / 5)
    bar = '█' * filled + '░' * (20 - filled)
    print(f"\nProgress: {bar} {pct}%")
    print(f"Selesai: {done} / {total} tugas\n")

    # breakdown by priority
    pri_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for t in tasks:
        p = t.get('priority', 'MEDIUM')
        pri_counts[p] = pri_counts.get(p, 0) + 1

    print("By Priority:")
    for p in ("HIGH", "MEDIUM", "LOW"):
        print(f" - {p}: {pri_counts.get(p,0)}")

    # export simple CSV for plotting
    try:
        with open('progress.csv', 'w', encoding='utf-8') as f:
            f.write('id,nama,status,priority,deadline\n')
            for t in tasks:
                line = f"{t.get('id')},{t.get('nama')},{t.get('status')},{t.get('priority','MEDIUM')},{t.get('deadline')}\n"
                f.write(line)
    except Exception:
        pass


def view_log(lines: int = 50):
    """Tampilkan log aktivitas terakhir (default 50 baris)."""
    if not os.path.exists('LOG.txt'):
        print("\nBelum ada log aktivitas.\n")
        return
    try:
        with open('LOG.txt', 'r', encoding='utf-8') as f:
            all_lines = f.read().strip().splitlines()
            for line in all_lines[-lines:]:
                print(line)
            print()
    except Exception:
        print("Gagal membaca LOG.txt\n")


def filter_sort_tasks(tasks):
    """Filter dan sort tugas berdasarkan priority / deadline / status."""
    if not tasks:
        print("\nTidak ada tugas.\n")
        return

    print("\nFilter by priority: (ALL/LOW/MEDIUM/HIGH)")
    f = input("Pilih filter [ALL]: ").strip().upper() or "ALL"
    if f not in ("ALL", "LOW", "MEDIUM", "HIGH"):
        print("⚠️ Filter tidak valid, menggunakan ALL")
        f = "ALL"

    print("Sort by: (deadline/status/priority)")
    s = input("Pilih sort [deadline]: ").strip().lower() or "deadline"
    if s not in ("deadline", "status", "priority"):
        print("⚠️ Sort tidak valid, menggunakan deadline")
        s = "deadline"

    filtered = [t for t in tasks if f == "ALL" or t.get('priority','MEDIUM') == f]

    if s == "deadline":
        def _key(t):
            try:
                return parse_deadline_string(t.get('deadline',''))
            except Exception:
                return datetime.max
        filtered.sort(key=_key)
    else:
        filtered.sort(key=lambda x: x.get(s, ""))

    display_tasks(filtered)

def main():
    """Fungsi utama aplikasi"""
    print("\n" + "="*80)
    print("\033[1m" + " "*20 + "APLIKASI TO-DO LIST SEDERHANA" + "\033[0m")
    print("="*80)
    
    while True:
        tasks = load_tasks()
        # Perbarui status TERLAMBAT otomatis dan kirim notifikasi time-based
        update_overdue_statuses(tasks)
        notify_time_based(tasks)
        # Tampilkan peringatan tugas yang mendekati deadline (default 1 hari)
        check_upcoming_deadlines(tasks, threshold_days=1.0)
        
        print("\n\033[1m📋 MENU UTAMA\033[0m")
        print("1. Tampilkan semua tugas")
        print("2. Tambah tugas baru")
        print("3. Hapus tugas")
        print("4. Tandai tugas selesai/belum")
        print("5. Edit tugas")
        print("6. Cari tugas")
        print("7. Alarm hitung mundur")
        print("8. Mode fokus (Pomodoro)")
        print("9. Toggle bunyi (Saat ini: {'ON' if SOUND_ENABLED else 'OFF'})")
        print("10. Filter/Sort tugas")
        print("11. Statistik tugas")
        print("12. Lihat log aktivitas")
        print("13. Keluar")

        pilihan = input("\nPilih menu (1-13): ").strip()
        
        if pilihan == "1":
            display_tasks(tasks)
        elif pilihan == "2":
            add_task(tasks)
        elif pilihan == "3":
            delete_task(tasks)
        elif pilihan == "4":
            mark_completed(tasks)
        elif pilihan == "5":
            edit_task(tasks)
        elif pilihan == "6":
            search_tasks(tasks)
        elif pilihan == "7":
            countdown_alarm(tasks)
        elif pilihan == "8":
            # Mode fokus (pomodoro)
            try:
                cycles = int(input("Jumlah siklus (default 1): ").strip() or "1")
            except ValueError:
                cycles = 1
            try:
                focus_min = int(input("Durasi fokus (menit, default 25): ").strip() or "25")
                break_min = int(input("Durasi istirahat (menit, default 5): ").strip() or "5")
            except ValueError:
                focus_min, break_min = 25, 5

            for c in range(cycles):
                print(f"\nMulai fokus: siklus {c+1} dari {cycles} ({focus_min} menit)")
                _alarm_notify(f"Mulai fokus {focus_min} menit")
                try:
                    time.sleep(focus_min * 60)
                except KeyboardInterrupt:
                    print("\nMode fokus dibatalkan.\n")
                    break
                _alarm_notify("Selesai fokus. Saatnya istirahat")
                if c < cycles:
                    try:
                        time.sleep(break_min * 60)
                    except KeyboardInterrupt:
                        print("\nMode fokus dibatalkan.\n")
                        break
            print("\nSelesai mode fokus.\n")
        elif pilihan == "9":
            # Toggle sound without creating a local binding
            new = not globals().get('SOUND_ENABLED', True)
            globals()['SOUND_ENABLED'] = new
            print(f"\n🔊 Bunyi sekarang {'aktif' if new else 'dinonaktifkan'}\n")
        elif pilihan == "10":
            filter_sort_tasks(tasks)
        elif pilihan == "11":
            show_stats(tasks)
        elif pilihan == "12":
            view_log()
        elif pilihan == "13":
            print("\n👋 Terima kasih telah menggunakan aplikasi To-Do List!\n")
            break
        else:
            print("\n❌ Pilihan tidak valid! Silakan pilih menu 1-13.\n")

if __name__ == "__main__":
    main()
