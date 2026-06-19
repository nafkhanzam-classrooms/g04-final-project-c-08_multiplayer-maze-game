[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/90Mprfp5)
# Network Programming - Final Project [G04]

## Anggota Kelompok
| Nama                  | NRP        | Kelas     |
|  Rhea Debora Sianturi | 5025241089 | C         | 


## Link Youtube (Unlisted)
Link ditaruh di bawah ini
```

```

## Penjelasan Program

# Multiplayer Maze Game

## Deskripsi Program

Multiplayer Maze Game adalah permainan labirin berbasis jaringan (network programming) yang memungkinkan hingga 4 pemain bermain secara bersamaan dalam satu labirin yang sama. Setiap pemain harus mencari jalan dari titik awal (Start) menuju titik akhir (Finish) secepat mungkin.

Program menggunakan arsitektur **Client-Server**, di mana server bertindak sebagai pengelola utama permainan (authoritative server) dan client digunakan oleh pemain untuk berinteraksi dengan permainan.

Setelah seluruh pemain siap (Ready), server akan membuat labirin secara otomatis dan permainan dimulai. Pemain pertama yang mencapai titik akhir akan dinyatakan sebagai pemenang.

---

# Fitur Program

### 1. Multiplayer 1–4 Pemain

* Mendukung hingga 4 pemain dalam satu permainan.
* Setiap pemain memiliki warna karakter yang berbeda.

### 2. Lobby System

* Pemain dapat masuk ke lobby sebelum permainan dimulai.
* Status Ready setiap pemain dapat dilihat oleh pemain lain.
* Permainan hanya dimulai ketika seluruh pemain sudah siap.

### 3. Maze Generation

* Labirin dibuat secara otomatis oleh server menggunakan algoritma recursive backtracking.
* Setiap permainan menghasilkan bentuk labirin yang berbeda.

### 4. Real-Time Movement

* Pergerakan pemain dikirim dari client ke server menggunakan socket TCP.
* Server melakukan validasi terhadap setiap pergerakan pemain untuk mencegah pelanggaran aturan permainan.

### 5. Ping Monitoring

* Client dan server melakukan pertukaran paket ping-pong secara berkala.
* Nilai latency (ping) ditampilkan kepada pemain.

### 6. Winner Detection

* Pemain pertama yang mencapai titik Finish akan menjadi pemenang.
* Permainan langsung berakhir ketika terdapat pemenang.

### 7. Replay System

* Server menyimpan posisi pemain selama permainan berlangsung.
* Setelah permainan selesai, pemain dapat menonton ulang perjalanan pemenang menuju garis akhir.

### 8. Spectator Server

* Server memiliki tampilan visual sendiri untuk memonitor jalannya permainan secara real-time.

---

# Arsitektur Sistem

## Server

Server memiliki tugas sebagai berikut:

* Menerima koneksi client.
* Mengelola data pemain.
* Membuat labirin.
* Memvalidasi pergerakan pemain.
* Menentukan pemenang.
* Menyimpan data replay.
* Mengirim pembaruan kondisi permainan ke seluruh client.

Server menggunakan:

* Socket Programming (TCP)
* Multithreading
* JSON Serialization
* Pygame

---

## Client

Client memiliki tugas sebagai berikut:

* Terhubung ke server.
* Mengirim input pemain.
* Menampilkan kondisi permainan.
* Menampilkan posisi pemain lain.
* Menampilkan replay setelah permainan selesai.

Client menggunakan:

* Socket Programming (TCP)
* Multithreading
* JSON Serialization
* Pygame

---

# Alur Program

## 1. Koneksi

Client terhubung ke server menggunakan alamat IP dan port yang telah ditentukan.

```
Client -> Server
```

Server kemudian memberikan ID unik kepada setiap pemain.

---

## 2. Lobby

Setelah terhubung:

* Pemain memilih mode permainan.
* Pemain menekan tombol Ready.
* Server menunggu hingga seluruh pemain siap.

---

## 3. Countdown

Server membuat labirin baru kemudian memulai hitung mundur sebelum permainan dimulai.

```
3...
2...
1...
START!
```

---

## 4. Gameplay

Pemain bergerak menggunakan tombol:

| Tombol | Fungsi            |
| ------ | ----------------- |
| ↑      | Bergerak ke atas  |
| ↓      | Bergerak ke bawah |
| ←      | Bergerak ke kiri  |
| →      | Bergerak ke kanan |

Server akan memeriksa apakah posisi tujuan merupakan jalan yang valid atau dinding.

---

## 5. Penentuan Pemenang

Ketika pemain mencapai sel Finish:

* Server menetapkan pemain tersebut sebagai pemenang.
* Status permainan berubah menjadi GAME_OVER.
* Semua client menerima informasi pemenang.

---

## 6. Replay

Server menyimpan posisi pemain setiap beberapa milidetik selama permainan berlangsung.

Data replay digunakan untuk:

* Menampilkan ulang perjalanan pemain yang menang.
* Memvisualisasikan langkah-langkah menuju Finish.

---

# Struktur Program

## FPServer.py

File utama server yang bertanggung jawab untuk:

* Membuat socket server
* Mengelola koneksi client
* Membuat labirin
* Menentukan pemenang
* Menyimpan replay
* Menampilkan spectator mode

### Class Utama

```
GameServer
```

---

## FPClient.py

File utama client yang bertanggung jawab untuk:

* Terhubung ke server
* Menampilkan permainan
* Mengirim input pemain
* Menampilkan replay

### Class Utama

```
MazeClient
```

---

# Teknologi yang Digunakan

* Python 3
* Socket Programming
* Multithreading
* JSON
* Pygame

---

# Cara Menjalankan Program

## 1. Install Dependency

```bash
pip install pygame
```

## 2. Jalankan Server

```bash
python FPServer.py
```

## 3. Jalankan Client

Buka terminal baru dan jalankan:

```bash
python FPClient.py
```

Jalankan hingga 4 client untuk simulasi multiplayer.

---

# Kesimpulan

Proyek Multiplayer Maze Game berhasil mengimplementasikan konsep Network Programming menggunakan arsitektur Client-Server. Program mampu menangani komunikasi real-time antar pemain, sinkronisasi posisi pemain, pembuatan labirin secara dinamis, penentuan pemenang, serta fitur replay untuk menampilkan perjalanan pemain yang berhasil mencapai tujuan terlebih dahulu.

## Screenshot Hasil

## 1. Server - 0 client
<img width="592" height="465" alt="image" src="https://github.com/user-attachments/assets/120f7541-c635-4fbe-b46a-85fea9283deb" />

## 2. Server - 2 Client
<img width="596" height="464" alt="image" src="https://github.com/user-attachments/assets/f3cda436-8ae4-4ede-a319-c084208452f3" />

## 3. Client - Not ready state
<img width="599" height="467" alt="image" src="https://github.com/user-attachments/assets/49eab334-f670-48db-9126-7676041f8761" />

## 4. Client - Ready state
<img width="591" height="467" alt="image" src="https://github.com/user-attachments/assets/4f0539fb-edf0-437c-9a1c-64780e427dff" />

## 5. Get-ready + Count down
<img width="590" height="464" alt="image" src="https://github.com/user-attachments/assets/a3ad29c3-57d0-4cb5-9d25-476e8b0ea7ab" />

## 6. Client - Game
<img width="589" height="461" alt="image" src="https://github.com/user-attachments/assets/b88029cc-e0e5-4247-9746-594436cb26e0" />

## 7. Game over screen
<img width="593" height="462" alt="image" src="https://github.com/user-attachments/assets/108c528a-8aaa-414a-92c5-4e7c333ae81e" />

## 8. Replay mode
<img width="586" height="459" alt="image" src="https://github.com/user-attachments/assets/70ffb802-1346-4e89-a56d-9524f2cb89e0" />
