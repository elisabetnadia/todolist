import json
import os
from datetime import datetime
from tabulate import tabulate

# File untuk menyimpan data
DATA_FILE = "tasks.json"

def load_tasks():
    """Memuat data tugas dari file JSON"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return []
    return []

def save_tasks(tasks):
    """Menyimpan data tugas ke file JSON"""
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(tasks, file, indent=2, ensure_ascii=False)

def display_tasks(tasks):
    """Menampilkan semua tugas"""
    if not tasks:
        print("\n❌ Tidak ada tugas.\n")
        return
    
    table_data = []
    for i, task in enumerate(tasks, 1):
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
    
    deadline = input("Deadline (format: DD-MM-YYYY): ").strip()
    if not deadline:
        print("❌ Deadline tidak boleh kosong!\n")
        return
    
    # Validasi format deadline
    try:
        datetime.strptime(deadline, "%d-%m-%Y")
    except ValueError:
        print("❌ Format deadline tidak valid! Gunakan DD-MM-YYYY\n")
        return
    
    task = {
        "id": len(tasks) + 1,
        "nama": nama,
        "mata_pelajaran": mata_pelajaran,
        "deadline": deadline,
        "completed": False,
        "created_at": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }
    
    tasks.append(task)
    save_tasks(tasks)
    print(f"✅ Tugas '{nama}' berhasil ditambahkan!\n")

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
            tasks[nomor - 1]["completed"] = not tasks[nomor - 1]["completed"]
            status = "selesai" if tasks[nomor - 1]["completed"] else "belum selesai"
            save_tasks(tasks)
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

def main():
    """Fungsi utama aplikasi"""
    print("\n" + "="*80)
    print("\033[1m" + " "*20 + "APLIKASI TO-DO LIST SEDERHANA" + "\033[0m")
    print("="*80)
    
    while True:
        tasks = load_tasks()
        
        print("\n\033[1m📋 MENU UTAMA\033[0m")
        print("1. Tampilkan semua tugas")
        print("2. Tambah tugas baru")
        print("3. Hapus tugas")
        print("4. Tandai tugas selesai/belum")
        print("5. Edit tugas")
        print("6. Cari tugas")
        print("7. Keluar")
        
        pilihan = input("\nPilih menu (1-7): ").strip()
        
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
            print("\n👋 Terima kasih telah menggunakan aplikasi To-Do List!\n")
            break
        else:
            print("\n❌ Pilihan tidak valid! Silakan pilih menu 1-7.\n")

if __name__ == "__main__":
    main()
