import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def generate_dashboard(csv_file="simulation_log.csv"):
    try:
        # Membaca data simulasi
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: File {csv_file} tidak ditemukan. Jalankan simulasi terlebih dahulu.")
        return

    # Jika data kosong
    if df.empty:
        print("Data simulasi kosong.")
        return

    # Menghitung persentase okupansi
    df['Occupancy_Rate'] = (df['Occupied_Slots'] / df['Total_Slots']) * 100

    # =========================================================================
    # MODIFIKASI: Ukuran disesuaikan untuk aspek rasio layar 1280 x 720 (12.5 x 6.8 inci)
    # =========================================================================
    fig, axs = plt.subplots(2, 2, figsize=(12.5, 6.8))
    fig.suptitle('Dashboard Analisis Simulasi Parkir Stasiun Bandung', fontsize=16, fontweight='bold')

    # ---------------------------------------------------------
    # 1. Grafik Validasi Input: Arrival Rate (Lambda) over Time
    # ---------------------------------------------------------
    axs[0, 0].plot(df['Time_Hours'], df['Lambda_Real'], color='tab:blue', linewidth=2)
    axs[0, 0].set_title('Distribusi Kedatangan (Arrival Rate / Lambda)', fontweight='bold', fontsize=11)
    axs[0, 0].set_xlabel('Jam (Waktu In-Game)', fontsize=9)
    axs[0, 0].set_ylabel('Kendaraan per Menit', fontsize=9)
    axs[0, 0].grid(True, linestyle='--', alpha=0.7)
    axs[0, 0].set_xlim(0, max(24, df['Time_Hours'].max()))
    axs[0, 0].tick_params(labelsize=8)

    # ---------------------------------------------------------
    # 2. Grafik Analisis Sistem: Parking Occupancy Rate
    # ---------------------------------------------------------
    axs[0, 1].fill_between(df['Time_Hours'], df['Occupancy_Rate'], color='tab:green', alpha=0.3)
    axs[0, 1].plot(df['Time_Hours'], df['Occupancy_Rate'], color='tab:green', linewidth=2)
    axs[0, 1].set_title('Tingkat Okupansi Parkir (%)', fontweight='bold', fontsize=11)
    axs[0, 1].set_xlabel('Jam (Waktu In-Game)', fontsize=9)
    axs[0, 1].set_ylabel('Kapasitas Terisi (%)', fontsize=9)
    axs[0, 1].set_ylim(0, 105)
    axs[0, 1].axhline(100, color='red', linestyle='--', linewidth=1, label='Kapasitas Maksimal')
    axs[0, 1].legend(fontsize=8)
    axs[0, 1].grid(True, linestyle='--', alpha=0.7)
    axs[0, 1].tick_params(labelsize=8)

    # ---------------------------------------------------------
    # 3. Grafik Bottleneck: Main Speed vs Gate Delays
    # ---------------------------------------------------------
    ax_speed = axs[1, 0]
    ax_gate = ax_speed.twinx() # Membuat sumbu Y kedua di kanan

    l1 = ax_speed.plot(df['Time_Hours'], df['Avg_Main_Speed'], color='tab:orange', linewidth=2, label='Kecepatan Jalan Raya')
    l2 = ax_gate.plot(df['Time_Hours'], df['Gate_Delay_Cars'], color='tab:red', linestyle=':', linewidth=2, label='Mobil Antre di Gerbang')

    ax_speed.set_title('Dampak Antrean Gerbang thd Kecepatan Jalan', fontweight='bold', fontsize=11)
    ax_speed.set_xlabel('Jam (Waktu In-Game)', fontsize=9)
    ax_speed.set_ylabel('Kecepatan (km/h)', color='tab:orange', fontsize=9)
    ax_gate.set_ylabel('Jumlah Mobil Antre', color='tab:red', fontsize=9)
    
    # Menggabungkan legend dari dua sumbu Y yang berbeda
    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax_speed.legend(lines, labels, loc='upper left', fontsize=8)
    ax_speed.grid(True, linestyle='--', alpha=0.7)
    ax_speed.tick_params(labelsize=8)
    ax_gate.tick_params(labelsize=8)

    # ---------------------------------------------------------
    # 4. Grafik Karakteristik Pengguna: Distribusi Intent
    # ---------------------------------------------------------
    # Ambil baris data terakhir untuk melihat total akhir akumulatif
    last_row = df.iloc[-1]
    intents = ['DROP_OFF', 'SHORT_VISIT', 'LONG_VISIT', 'DRIVE_BY']
    counts = [last_row['Intent_DropOff'], last_row['Intent_Short'], last_row['Intent_Long'], last_row['Intent_DriveBy']]
    
    # Filter warna dan label hanya untuk yang nilainya > 0 (menghindari error pie chart kosong)
    colors_map = {'DROP_OFF': '#9b59b6', 'SHORT_VISIT': '#e67e22', 'LONG_VISIT': '#f1c40f', 'DRIVE_BY': '#95a5a6'}
    filtered_intents = []
    filtered_counts = []
    filtered_colors = []
    
    for intent, count in zip(intents, counts):
        if count > 0:
            filtered_intents.append(intent)
            filtered_counts.append(count)
            filtered_colors.append(colors_map[intent])

    if sum(filtered_counts) > 0:
        axs[1, 1].pie(filtered_counts, labels=filtered_intents, colors=filtered_colors, autopct='%1.1f%%', startangle=90, explode=[0.05]*len(filtered_counts), textprops={'fontsize': 8})
        axs[1, 1].set_title('Proporsi Tujuan Pengendara (Kumulatif)', fontweight='bold', fontsize=11)
    else:
        axs[1, 1].text(0.5, 0.5, 'Belum ada data kendaraan', horizontalalignment='center', verticalalignment='center')
        axs[1, 1].axis('off')

    # =========================================================================
    # MODIFIKASI: Mengatur layout secara presisi agar tidak menabrak title utama
    # =========================================================================
    plt.tight_layout(rect=[0, 0, 1, 0.95]) 
    
    # Simpan grafik sebagai gambar resolusi tinggi (300 DPI)
    plt.savefig('simulation_analysis_dashboard.png', dpi=300)
    print("Grafik berhasil disimpan sebagai 'simulation_analysis_dashboard.png'")
    
    plt.show()

if __name__ == "__main__":
    generate_dashboard()