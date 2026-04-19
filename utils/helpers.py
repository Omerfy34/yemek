from datetime import datetime

def bugun_tarih():
    """Bugünün tarihini YYYY-MM-DD formatında döner"""
    return datetime.now().strftime("%Y-%m-%d")

def bugun_tarih_gosterim():
    """Bugünün tarihini güzel formatta döner: 15 Ocak 2025"""
    aylar = {
        1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
        5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
        9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
    }
    now = datetime.now()
    return f"{now.day} {aylar[now.month]} {now.year}"

def saat_kontrol(saat):
    """Şu anki saat verilen saatten küçük mü kontrol eder"""
    return datetime.now().hour < saat

def oylama_acik_mi(kapanis_saati=16):
    """Oylama hala açık mı kontrol eder"""
    return datetime.now().hour < kapanis_saati

def kalan_sure(kapanis_saati=16):
    """Oylama kapanışına kalan süreyi döner"""
    now = datetime.now()
    if now.hour >= kapanis_saati:
        return "Oylama kapandı"
    kalan_saat = kapanis_saati - now.hour - 1
    kalan_dakika = 60 - now.minute
    if kalan_saat > 0:
        return f"{kalan_saat} saat {kalan_dakika} dk"
    else:
        return f"{kalan_dakika} dk"

# Malzeme kategorileri
KATEGORILER = {
    "et": "🥩 Et & Tavuk & Balık",
    "sebze": "🥬 Sebze",
    "meyve": "🍎 Meyve",
    "bakliyat": "🫘 Bakliyat & Tahıl",
    "sut": "🧀 Süt Ürünleri",
    "diger": "📦 Diğer"
}

# Avatar seçenekleri
AVATARLAR = ["👩", "👨", "👧", "👦", "👵", "👴", "🧑", "👶"]