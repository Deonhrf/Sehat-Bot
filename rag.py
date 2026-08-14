import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import PyPDF2
from db import save_pdf 
from huggingface_hub import login 
from dotenv import load_dotenv


# ubah teks jadi angka
model = SentenceTransformer('all-MiniLM-L6-v2') # model ini lebih ringan dan cepat
DB_FOLDER = 'db_faiss' # folder utama untuk menyimpan file index 

load_dotenv() # load .env
login (token=os.getenv("HF_TOKENS")) # login ke huggingface hub pake token dari .env


# index = None # kotak pencarian
# chunks = [] # menyimpan potongan teks

# fungsi untuk membuat dan mengambilakn path folder
def get_user_db_path(user_id) :
  user_path = os.path.join(DB_FOLDER,f'user_{user_id}') # menggabungkan folder utama db dengan folder baru nantinya
  os.makedirs(user_path, exist_ok=True) # membuat folder tersebut apabila di sistem tidak ada
  return user_path


def load_index_and_chunks(user_id) :
  user_path = get_user_db_path(user_id) # ambil folder 
  index_path = os.path.join(user_path, "index.faiss") # buat path lengkap untuk file index
  chunks_path = os.path.join(user_path, "chunks.npy") # buat path lengkap untuk file chunks

  if os.path.exists(index_path) and os.path.exists(chunks_path) :
    index = faiss.read_index(index_path) # membaca file faiss 
    chunks = np.load(chunks_path, allow_pickle=True).tolist()
    return index, chunks
  else :
    # kalua belom ada, bikin kosong
    dimension = model.get_embedding_dimension()
    index = faiss.IndexFlatL2(dimension)
    chunks = []
    return index, chunks


def save_index_and_chunks(index, chunks, user_id) :
  user_path = get_user_db_path(user_id)

  # membuat file path index dan chunks 
  index_path = os.path.join(user_path, "index.faiss")
  chunks_path = os.path.join(user_path, "chunks.npy")

  # menyimpan
  faiss.write_index(index, index_path)
  np.save(chunks_path, np.array(chunks, dtype=object))



# fungsi membaca pdf
def process_pdf_for_user (file_path, user_id) :
    """Dipanggil dari ai.py. Baca PDF dan tambahkan ke DB milik user ini"""

    # 2.1 Load index lama milik user ini dulu
    index, chunks = load_index_and_chunks(user_id)

    # 2.2 Baca PDF
    reader = PyPDF2.PdfReader(file_path)
    text = ""
    for page in reader.pages:
        if page.extract_text(): # cek biar gak None
            text += page.extract_text()

    # 2.3 Pecah jadi potongan 800 karakter
    new_chunks = [text[i:i+800] for i in range(0, len(text), 600)]
    if not new_chunks:
        raise ValueError("PDF kosong atau gagal dibaca")

    # 2.4 Ubah potongan baru jadi vektor
    new_embeddings = model.encode(new_chunks)

    # 2.5 Gabungin sama chunks lama dan tambah ke index
    chunks.extend(new_chunks)
    index.add(np.array(new_embeddings))

    # 2.6 Simpan lagi ke file
    save_index_and_chunks(index, chunks, user_id)

    print(f"PDF diproses: {len(new_chunks)} potongan baru untuk user_{user_id}")

# fungsi membaca - jwaban dari user 
def search_user_docs(pertanyaan_user, user_id, k=3):
    """Dipanggil dari ai.py. Cari cuma di DB milik user ini"""

    # 3.1 Load index milik user ini
    index, chunks = load_index_and_chunks(user_id)

    # 3.2 Cek kalau user belum upload apa2
    if len(chunks) == 0:
        return ""

    # 3.3 Ubah pertanyaan jadi vektor dan cari
    question_embedding = model.encode([pertanyaan_user])
    D, I = index.search(np.array(question_embedding), k=k) # k=3 dokumen terdekat

    # 3.4 Gabungkan hasil
    context = "\n---\n".join([chunks[i] for i in I[0]])
    return context

  
