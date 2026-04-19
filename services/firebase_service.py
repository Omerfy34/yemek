import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_KEY_PATH

cred = credentials.Certificate(FIREBASE_KEY_PATH)
firebase_admin.initialize_app(cred)

db = firestore.client()

# ============ KULLANICI İŞLEMLERİ ============

def kullanici_ekle(isim, avatar="👤"):
    doc_ref = db.collection("users").document()
    doc_ref.set({
        "name": isim,
        "avatar": avatar,
        "isHome": True,
        "dislikedFoods": [],
        "createdAt": firestore.SERVER_TIMESTAMP
    })
    return doc_ref.id

def kullanicilari_getir():
    users = db.collection("users").stream()
    kullanicilar = []
    for user in users:
        data = user.to_dict()
        data["id"] = user.id
        kullanicilar.append(data)
    return kullanicilar

def kullanici_getir(user_id):
    doc = db.collection("users").document(user_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None

def kullanici_sil(user_id):
    db.collection("users").document(user_id).delete()

def kullanici_guncelle(user_id, isim, avatar):
    db.collection("users").document(user_id).update({
        "name": isim,
        "avatar": avatar
    })

def evde_durumu_guncelle(user_id, evde_mi):
    db.collection("users").document(user_id).update({
        "isHome": evde_mi
    })

def tum_evde_durumu_sifirla():
    """Her gece tüm kullanıcıları 'evde' yapar."""
    users = db.collection("users").stream()
    for user in users:
        db.collection("users").document(user.id).update({
            "isHome": True
        })

def sevmedigim_ekle(user_id, yemek):
    db.collection("users").document(user_id).update({
        "dislikedFoods": firestore.ArrayUnion([yemek])
    })

def sevmedigim_kaldir(user_id, yemek):
    db.collection("users").document(user_id).update({
        "dislikedFoods": firestore.ArrayRemove([yemek])
    })

# ============ MALZEME İŞLEMLERİ ============

def malzeme_ekle(isim, kategori="diger", ekleyen_id=""):
    # Aynı isimde malzeme var mı kontrol et
    mevcut = db.collection("ingredients").where(
        "name", "==", isim
    ).limit(1).stream()

    if any(True for _ in mevcut):
        return None  # Zaten var, ekleme

    doc_ref = db.collection("ingredients").document()
    doc_ref.set({
        "name": isim,
        "category": kategori,
        "addedBy": ekleyen_id,
        "addedAt": firestore.SERVER_TIMESTAMP
    })
    return doc_ref.id

def malzemeleri_getir():
    items = db.collection("ingredients").stream()
    malzemeler = []
    for item in items:
        data = item.to_dict()
        data["id"] = item.id
        malzemeler.append(data)
    return malzemeler

def malzeme_guncelle(malzeme_id, yeni_isim, yeni_kategori):
    db.collection("ingredients").document(malzeme_id).update({
        "name": yeni_isim,
        "category": yeni_kategori
    })

def malzeme_sil(malzeme_id):
    db.collection("ingredients").document(malzeme_id).delete()

def kategoriye_gore_getir(kategori):
    items = db.collection("ingredients").where(
        "category", "==", kategori
    ).stream()
    malzemeler = []
    for item in items:
        data = item.to_dict()
        data["id"] = item.id
        malzemeler.append(data)
    return malzemeler
