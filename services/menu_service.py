from services.firebase_service import (
    malzemeleri_getir, kullanicilari_getir, db
)
from firebase_admin import firestore
from utils.helpers import bugun_tarih
from config import OYLAMA_KAPANIS_SAATI


def gunun_menusunu_olustur_ai():
    """AI ile menü oluşturur. Kişi sayısını evde olanlara göre ayarlar."""
    from services.gemini_service import tarif_onerisi_al

    malzemeler = malzemeleri_getir()
    malzeme_isimleri = [m["name"] for m in malzemeler]

    if not malzeme_isimleri:
        return {"success": False, "error": "Dolabınızda malzeme yok! Önce malzeme ekleyin."}

    kullanicilar = kullanicilari_getir()

    # Evde olan kişi sayısı
    evde_olanlar = [k for k in kullanicilar if k.get("isHome", True)]
    kisi_sayisi = len(evde_olanlar) if len(evde_olanlar) > 0 else 1

    # Sevmedikleri topla
    sevmedikler = []
    for k in kullanicilar:
        if k.get("dislikedFoods"):
            sevmedikler.extend(k["dislikedFoods"])
    sevmedikler = list(set(sevmedikler))

    son_yemekler = son_yemekleri_getir()

    sonuc = tarif_onerisi_al(malzeme_isimleri, sevmedikler, son_yemekler, kisi_sayisi)

    if not sonuc["success"]:
        return sonuc

    tarih = bugun_tarih()
    menu_ref = db.collection("dailyMenu").document(tarih)

    menu_ref.set({
        "date": tarih,
        "status": "voting",
        "menus": sonuc["menus"],
        "votes": {},
        "winner": None,
        "kisiSayisi": kisi_sayisi,
        "createdAt": firestore.SERVER_TIMESTAMP
    })

    return {"success": True, "menus": sonuc["menus"]}


def gunun_menusunu_olustur_manuel(tarifler):
    """Elle menü oluşturur."""
    tarih = bugun_tarih()
    menu_ref = db.collection("dailyMenu").document(tarih)

    menus = []
    for tarif in tarifler:
        menus.append({
            "name": tarif.get("name", "İsimsiz Yemek"),
            "description": tarif.get("description", ""),
            "cookTime": tarif.get("cookTime", "30 dk"),
            "prepTime": "",
            "totalTime": "",
            "calories": tarif.get("calories", 0),
            "servings": tarif.get("servings", 4),
            "difficulty": "Orta",
            "ingredients": [],
            "steps": [],
            "tips": [],
            "nutrition": {"protein": 0, "carb": 0, "fat": 0, "fiber": 0}
        })

    menu_ref.set({
        "date": tarih,
        "status": "voting",
        "menus": menus,
        "votes": {},
        "winner": None,
        "createdAt": firestore.SERVER_TIMESTAMP
    })

    return {"success": True, "menus": menus}


def gunun_menusunu_getir():
    tarih = bugun_tarih()
    doc = db.collection("dailyMenu").document(tarih).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None


def oy_ver(user_id, menu_index):
    tarih = bugun_tarih()
    db.collection("dailyMenu").document(tarih).update({
        f"votes.{user_id}": menu_index
    })


def oy_geri_al(user_id):
    tarih = bugun_tarih()
    db.collection("dailyMenu").document(tarih).update({
        f"votes.{user_id}": firestore.DELETE_FIELD
    })


def oylama_sonucunu_getir():
    menu_data = gunun_menusunu_getir()
    if not menu_data:
        return None

    votes = menu_data.get("votes", {})
    menus = menu_data.get("menus", [])

    sonuclar = {}
    for i in range(len(menus)):
        sonuclar[i] = {"name": menus[i]["name"], "count": 0, "voters": []}

    kullanicilar = kullanicilari_getir()
    kullanici_map = {k["id"]: k["name"] for k in kullanicilar}

    for user_id, menu_idx in votes.items():
        if menu_idx in sonuclar:
            sonuclar[menu_idx]["count"] += 1
            isim = kullanici_map.get(user_id, "Bilinmeyen")
            sonuclar[menu_idx]["voters"].append(isim)

    return sonuclar


def kazanani_belirle():
    sonuclar = oylama_sonucunu_getir()
    if not sonuclar:
        return None

    max_oy = 0
    kazananlar = []

    for idx, data in sonuclar.items():
        if data["count"] > max_oy:
            max_oy = data["count"]
            kazananlar = [idx]
        elif data["count"] == max_oy and data["count"] > 0:
            kazananlar.append(idx)

    return kazananlar


def kazanani_kaydet(menu_index):
    tarih = bugun_tarih()
    db.collection("dailyMenu").document(tarih).update({
        "winner": menu_index,
        "status": "closed"
    })


def oy_vermeyenleri_getir():
    menu_data = gunun_menusunu_getir()
    kullanicilar = kullanicilari_getir()

    if not menu_data:
        return []

    votes = menu_data.get("votes", {})
    evde_olanlar = [k for k in kullanicilar if k.get("isHome", True)]

    vermeyenler = []
    for k in evde_olanlar:
        if k["id"] not in votes:
            vermeyenler.append(k)

    return vermeyenler


def son_yemekleri_getir(gun_sayisi=7):
    from datetime import datetime, timedelta

    yemekler = []
    for i in range(1, gun_sayisi + 1):
        tarih = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        doc = db.collection("dailyMenu").document(tarih).get()
        if doc.exists:
            data = doc.to_dict()
            winner = data.get("winner")
            menus = data.get("menus", [])
            if winner is not None and winner < len(menus):
                yemekler.append(menus[winner]["name"])

    return yemekler


def gecmis_getir(gun_sayisi=7):
    from datetime import datetime, timedelta

    gecmis = []
    for i in range(0, gun_sayisi):
        tarih = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        doc = db.collection("dailyMenu").document(tarih).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            gecmis.append(data)

    return gecmis


def menu_sil():
    tarih = bugun_tarih()
    db.collection("dailyMenu").document(tarih).delete()


# ============ ALIŞVERİŞ LİSTESİ ============

def alisveris_listesi_getir():
    """Günün menüsündeki eksik malzemeleri alışveriş listesi olarak döner."""
    menu_data = gunun_menusunu_getir()
    if not menu_data:
        return []

    eksikler = []
    gorulenler = set()

    for tarif in menu_data.get("menus", []):
        for malzeme in tarif.get("ingredients", []):
            if not malzeme.get("available", True):
                isim = malzeme.get("name", "")
                if isim.lower() not in gorulenler:
                    gorulenler.add(isim.lower())
                    eksikler.append({
                        "name": isim,
                        "amount": malzeme.get("amount", ""),
                        "yemek": tarif.get("name", ""),
                        "note": malzeme.get("note", "")
                    })

    return eksikler


def alisveris_listesi_kaydet(items):
    """Alışveriş listesini Firebase'e kaydeder."""
    tarih = bugun_tarih()
    doc_ref = db.collection("shoppingList").document(tarih)

    doc_ref.set({
        "date": tarih,
        "items": items,
        "createdAt": firestore.SERVER_TIMESTAMP
    })


def alisveris_listesi_db_getir():
    """Firebase'den alışveriş listesini getirir."""
    tarih = bugun_tarih()
    doc = db.collection("shoppingList").document(tarih).get()
    if doc.exists:
        return doc.to_dict()
    return None