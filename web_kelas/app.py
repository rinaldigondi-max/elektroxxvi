import os
from datetime import datetime
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "kunci_rahasia_portal_elektro"

# Folder untuk menyimpan foto baju yang di-upload
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Pastikan folder uploads ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
  return (
      "." in filename
      and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
  )


# Data Mahasiswa & Admin (Role-Based Access)
DATA_MAHASISWA = {
    "21001": {"nama": "Budi Santoso", "role": "mahasiswa"},
    "21002": {"nama": "Siti Aminah", "role": "mahasiswa"},
    "21003": {"nama": "Ahmad Rizki", "role": "mahasiswa"},
    "030904": {"nama": "Admin Web", "role": "admin"},
    "99199": {"nama": "Developer Web", "role": "admin"},
}

# Data Pengumuman
pengumuman_list = [
    {
        "judul": "Selamat Datang di Portal Kelas Elektro",
        "isi": (
            "Gunakan website ini untuk memantau informasi, tugas, voting, dan"
            " pemilihan baju angkatan."
        ),
    },
]

# Data Info Tugas
tugas_list = [
    {
        "matkul": "Sistem Mikroprosesor",
        "judul": "Laporan Praktikum Modul 3",
        "deadline": "Jumat, pukul 23:59 WIB",
        "isi": (
            "Kumpul file laporan berformat PDF ke ketua kelompok masing-masing."
        ),
    },
]

# Data Voting Dinamis
voting_config = {
    "judul": "Pilih Waktu / Jadwal Kegiatan:",
    "deadline": "2026-12-31T23:59",
    "options": [
        "Pilihan A: Rabu, 13:00 WIB",
        "Pilihan B: Kamis, 15:00 WIB",
        "Pilihan C: Jumat, 10:00 WIB",
    ],
}
user_votes = {}

# Data Pemilihan Baju Angkatan + File Foto Upload
baju_config = {
    "judul": "Pemilihan Desain Baju Angkatan Elektro",
    "keterangan": (
        "Bahan: Cotton Combed 30s | Estimasi Harga: Rp 85.000 | Paket termasuk"
        " stiker angkatan."
    ),
    "deadline": "2026-12-31T23:59",
    "opsi_1": "Desain 1: Hitam Navy (Logo Dada Kiri)",
    "foto_1": "",  # Nama file foto yang tersimpan
    "opsi_2": "Desain 2: Hitam Solid (Minimalis Backprint)",
    "foto_2": "",
    "opsi_3": "Desain 3: Putih Oversize (Cyberpunk Style)",
    "foto_3": "",
}
user_baju_votes = {}


@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    npm_input = request.form.get("npm").strip()
    if npm_input in DATA_MAHASISWA:
      mhs = DATA_MAHASISWA[npm_input]
      session["user_npm"] = npm_input
      session["user_nama"] = mhs["nama"]
      session["user_role"] = mhs["role"]
      return redirect(url_for("index"))
    else:
      flash("NPM tidak terdaftar! Silakan periksa kembali.")
  return render_template("login.html")


@app.route("/logout")
def logout():
  session.clear()
  return redirect(url_for("login"))


@app.route("/")
def index():
  if "user_npm" not in session:
    return redirect(url_for("login"))
  return render_template("index.html", pengumuman=pengumuman_list)


@app.route("/tugas")
def tugas():
  if "user_npm" not in session:
    return redirect(url_for("login"))
  return render_template("tugas.html", tugas_list=tugas_list)


@app.route("/voting", methods=["GET", "POST"])
def voting():
  if "user_npm" not in session:
    return redirect(url_for("login"))

  current_npm = session["user_npm"]
  waktu_habis = False
  if voting_config["deadline"]:
    try:
      deadline_dt = datetime.strptime(
          voting_config["deadline"], "%Y-%m-%dT%H:%M"
      )
      if datetime.now() > deadline_dt:
        waktu_habis = True
    except ValueError:
      pass

  if request.method == "POST":
    if waktu_habis:
      flash("Maaf, waktu voting telah berakhir!")
    elif current_npm in user_votes:
      flash("Anda sudah pernah melakukan voting!")
    else:
      pilihan = request.form.get("pilihan")
      if pilihan in voting_config["options"]:
        user_votes[current_npm] = pilihan
    return redirect(url_for("voting"))

  hasil_voting = {opsi: 0 for opsi in voting_config["options"]}
  for npm, pilihan in user_votes.items():
    if pilihan in hasil_voting:
      hasil_voting[pilihan] += 1

  sudah_voting = current_npm in user_votes
  pilihan_saya = user_votes.get(current_npm, "")

  deadline_str = "-"
  if voting_config["deadline"]:
    try:
      dt = datetime.strptime(voting_config["deadline"], "%Y-%m-%dT%H:%M")
      bulan_indo = [
          "",
          "Januari",
          "Februari",
          "Maret",
          "April",
          "Mei",
          "Juni",
          "Juli",
          "Agustus",
          "September",
          "Oktober",
          "November",
          "Desember",
      ]
      deadline_str = f"{dt.day} {bulan_indo[dt.month]} {dt.year}, pukul {dt.strftime('%H:%M')} WIB"
    except ValueError:
      deadline_str = voting_config["deadline"]

  return render_template(
      "voting.html",
      voting=hasil_voting,
      sudah_voting=sudah_voting,
      pilihan_saya=pilihan_saya,
      user_votes=user_votes,
      data_mhs=DATA_MAHASISWA,
      voting_config=voting_config,
      waktu_habis=waktu_habis,
      deadline_str=deadline_str,
  )


@app.route("/update-voting", methods=["POST"])
def update_voting():
  if session.get("user_role") == "admin":
    judul_baru = request.form.get("judul")
    deadline_baru = request.form.get("deadline")
    options_raw = request.form.get("options")

    if judul_baru and options_raw:
      list_opsi = [
          opt.strip() for opt in options_raw.split("\n") if opt.strip()
      ]
      if list_opsi:
        voting_config["judul"] = judul_baru
        voting_config["deadline"] = deadline_baru
        voting_config["options"] = list_opsi
        user_votes.clear()
        flash("Topik dan batas waktu voting berhasil diperbarui!")
  return redirect(url_for("voting"))


@app.route("/hapus-voting", methods=["POST"])
def hapus_voting():
  if session.get("user_role") == "admin":
    voting_config["judul"] = ""
    voting_config["deadline"] = ""
    voting_config["options"] = []
    user_votes.clear()
    flash("Polling berhasil dihapus!")
  return redirect(url_for("voting"))


# --- ROUTE PEMILIHAN BAJU ANGKATAN (DENGAN UPLOAD FOTO) ---
@app.route("/baju-angkatan", methods=["GET", "POST"])
def baju_angkatan():
  if "user_npm" not in session:
    return redirect(url_for("login"))

  current_npm = session["user_npm"]
  waktu_habis = False
  if baju_config["deadline"]:
    try:
      deadline_dt = datetime.strptime(baju_config["deadline"], "%Y-%m-%dT%H:%M")
      if datetime.now() > deadline_dt:
        waktu_habis = True
    except ValueError:
      pass

  opsi_detail = []
  if baju_config.get("opsi_1"):
    opsi_detail.append({
        "nama": baju_config["opsi_1"],
        "foto": baju_config.get("foto_1", ""),
    })
  if baju_config.get("opsi_2"):
    opsi_detail.append({
        "nama": baju_config["opsi_2"],
        "foto": baju_config.get("foto_2", ""),
    })
  if baju_config.get("opsi_3"):
    opsi_detail.append({
        "nama": baju_config["opsi_3"],
        "foto": baju_config.get("foto_3", ""),
    })

  opsi_nama_list = [item["nama"] for item in opsi_detail]

  if request.method == "POST":
    if waktu_habis:
      flash("Maaf, batas waktu pemilihan baju angkatan telah berakhir!")
    elif current_npm in user_baju_votes:
      flash("Anda sudah memilih baju angkatan!")
    else:
      pilihan = request.form.get("pilihan")
      if pilihan in opsi_nama_list:
        user_baju_votes[current_npm] = pilihan
    return redirect(url_for("baju_angkatan"))

  hasil_baju = {nama: 0 for nama in opsi_nama_list}
  for npm, pilihan in user_baju_votes.items():
    if pilihan in hasil_baju:
      hasil_baju[pilihan] += 1

  sudah_pilih = current_npm in user_baju_votes
  pilihan_saya = user_baju_votes.get(current_npm, "")

  deadline_str = "-"
  if baju_config["deadline"]:
    try:
      dt = datetime.strptime(baju_config["deadline"], "%Y-%m-%dT%H:%M")
      bulan_indo = [
          "",
          "Januari",
          "Februari",
          "Maret",
          "April",
          "Mei",
          "Juni",
          "Juli",
          "Agustus",
          "September",
          "Oktober",
          "November",
          "Desember",
      ]
      deadline_str = f"{dt.day} {bulan_indo[dt.month]} {dt.year}, pukul {dt.strftime('%H:%M')} WIB"
    except ValueError:
      deadline_str = baju_config["deadline"]

  return render_template(
      "pemilihan_baju_angkatan.html",
      baju_config=baju_config,
      hasil_baju=hasil_baju,
      sudah_pilih=sudah_pilih,
      pilihan_saya=pilihan_saya,
      waktu_habis=waktu_habis,
      deadline_str=deadline_str,
      opsi_detail=opsi_detail,
  )


@app.route("/update-baju-angkatan", methods=["POST"])
def update_baju_angkatan():
  if session.get("user_role") == "admin":
    baju_config["judul"] = request.form.get("judul")
    baju_config["keterangan"] = request.form.get("keterangan")
    baju_config["deadline"] = request.form.get("deadline")
    baju_config["opsi_1"] = request.form.get("opsi_1")
    baju_config["opsi_2"] = request.form.get("opsi_2")
    baju_config["opsi_3"] = request.form.get("opsi_3")

    # Proses Upload Foto 1
    file_1 = request.files.get("file_1")
    if file_1 and allowed_file(file_1.filename):
      filename = secure_filename(file_1.filename)
      file_path = os.path.join(app.config["UPLOAD_FOLDER"], "baju_1_" + filename)
      file_1.save(file_path)
      baju_config["foto_1"] = "/" + file_path

    # Proses Upload Foto 2
    file_2 = request.files.get("file_2")
    if file_2 and allowed_file(file_2.filename):
      filename = secure_filename(file_2.filename)
      file_path = os.path.join(app.config["UPLOAD_FOLDER"], "baju_2_" + filename)
      file_2.save(file_path)
      baju_config["foto_2"] = "/" + file_path

    # Proses Upload Foto 3
    file_3 = request.files.get("file_3")
    if file_3 and allowed_file(file_3.filename):
      filename = secure_filename(file_3.filename)
      file_path = os.path.join(app.config["UPLOAD_FOLDER"], "baju_3_" + filename)
      file_3.save(file_path)
      baju_config["foto_3"] = "/" + file_path

    user_baju_votes.clear()
    flash("Pemilihan baju angkatan dan foto berhasil diperbarui!")
  return redirect(url_for("baju_angkatan"))


@app.route("/hapus-baju-angkatan", methods=["POST"])
def hapus_baju_angkatan():
  if session.get("user_role") == "admin":
    baju_config["judul"] = ""
    baju_config["keterangan"] = ""
    baju_config["deadline"] = ""
    baju_config["opsi_1"] = ""
    baju_config["foto_1"] = ""
    baju_config["opsi_2"] = ""
    baju_config["foto_2"] = ""
    baju_config["opsi_3"] = ""
    baju_config["foto_3"] = ""
    user_baju_votes.clear()
    flash("Pemilihan baju angkatan berhasil dihapus!")
  return redirect(url_for("baju_angkatan"))


@app.route("/tentang")
def tentang():
  if "user_npm" not in session:
    return redirect(url_for("login"))
  return render_template("tentang.html")


# --- MANAJEMEN PENGUMUMAN ---
@app.route("/tambah-pengumuman", methods=["POST"])
def tambah_pengumuman():
  if session.get("user_role") == "admin":
    judul = request.form.get("judul")
    isi = request.form.get("isi")
    if judul and isi:
      pengumuman_list.append({"judul": judul, "isi": isi})
  return redirect(url_for("index"))


@app.route("/hapus-pengumuman/<int:index>", methods=["POST"])
def hapus_pengumuman(index):
  if session.get("user_role") == "admin":
    if 0 <= index < len(pengumuman_list):
      pengumuman_list.pop(index)
  return redirect(url_for("index"))


@app.route("/edit-pengumuman/<int:index>", methods=["GET", "POST"])
def edit_pengumuman(index):
  if session.get("user_role") != "admin":
    return redirect(url_for("index"))
  if not (0 <= index < len(pengumuman_list)):
    return redirect(url_for("index"))

  if request.method == "POST":
    judul = request.form.get("judul")
    isi = request.form.get("isi")
    if judul and isi:
      pengumuman_list[index] = {"judul": judul, "isi": isi}
      return redirect(url_for("index"))

  pengumuman = pengumuman_list[index]
  return render_template(
      "edit_pengumuman.html", pengumuman=pengumuman, index=index
  )


# --- MANAJEMEN TUGAS ---
@app.route("/tambah-tugas", methods=["POST"])
def tambah_tugas():
  if session.get("user_role") == "admin":
    matkul = request.form.get("matkul")
    judul = request.form.get("judul")
    deadline = request.form.get("deadline")
    isi = request.form.get("isi")
    if matkul and judul:
      tugas_list.append(
          {
              "matkul": matkul,
              "judul": judul,
              "deadline": deadline,
              "isi": isi,
          }
      )
  return redirect(url_for("tugas"))


@app.route("/hapus-tugas/<int:index>", methods=["POST"])
def hapus_tugas(index):
  if session.get("user_role") == "admin":
    if 0 <= index < len(tugas_list):
      tugas_list.pop(index)
  return redirect(url_for("tugas"))


@app.route("/edit-tugas/<int:index>", methods=["GET", "POST"])
def edit_tugas(index):
  if session.get("user_role") != "admin":
    return redirect(url_for("tugas"))
  if not (0 <= index < len(tugas_list)):
    return redirect(url_for("tugas"))

  if request.method == "POST":
    matkul = request.form.get("matkul")
    judul = request.form.get("judul")
    deadline = request.form.get("deadline")
    isi = request.form.get("isi")
    if matkul and judul:
      tugas_list[index] = {
          "matkul": matkul,
          "judul": judul,
          "deadline": deadline,
          "isi": isi,
      }
      return redirect(url_for("tugas"))

  tugas = tugas_list[index]
  return render_template("edit_tugas.html", tugas=tugas, index=index)


if __name__ == "__main__":
  app.run(debug=True)