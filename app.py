from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from config import SECRET_KEY, OYLAMA_KAPANIS_SAATI
from services.firebase_service import (
    kullanici_ekle, kullanicilari_getir, kullanici_getir, kullanici_sil,
    malzeme_ekle, malzemeleri_getir, malzeme_sil, malzeme_guncelle,
    evde_durumu_guncelle, sevmedigim_ekle, sevmedigim_kaldir
)
from services.menu_service import (
    gunun_menusunu_olustur_ai, gunun_menusunu_olustur_manuel,
    gunun_menusunu_getir, menu_sil,
    oy_ver, oy_geri_al, oylama_sonucunu_getir,
    kazanani_belirle, kazanani_kaydet,
    oy_vermeyenleri_getir, gecmis_getir
)
from utils.helpers import (
    bugun_tarih, bugun_tarih_gosterim, oylama_acik_mi,
    kalan_sure, KATEGORILER, AVATARLAR
)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ============ OTOMATİK ZAMANLAYICI ============

def otomatik_menu_olustur():
    """Her gece 00:05'te çalışır."""
    with app.app_context():
        from services.firebase_service import tum_evde_durumu_sifirla

        # 1. Evde durumlarını sıfırla
        tum_evde_durumu_sifirla()
        print("🏠 Tüm kullanıcılar 'evde' yapıldı.")

        # 2. Menü oluştur
        menu_data = gunun_menusunu_getir()
        if not menu_data:
            malzemeler = malzemeleri_getir()
            if len(malzemeler) > 0:
                sonuc = gunun_menusunu_olustur_ai()
                if sonuc["success"]:
                    print(f"✅ Otomatik menü oluşturuldu: {bugun_tarih()}")
                else:
                    print(f"❌ Otomatik menü hatası: {sonuc['error']}")
            else:
                print("⚠️ Dolap boş, menü oluşturulamadı.")
        else:
            print(f"ℹ️ Bugün zaten menü var: {bugun_tarih()}")


def otomatik_oylama_kapat():
    """Her gün 16:00'da çalışır, oylamayı kapatır."""
    with app.app_context():
        menu_data = gunun_menusunu_getir()
        if menu_data and menu_data.get("status") == "voting":
            kazananlar = kazanani_belirle()
            if kazananlar and len(kazananlar) == 1:
                kazanani_kaydet(kazananlar[0])
                print(f"✅ Oylama kapandı, kazanan belirlendi: {bugun_tarih()}")
            else:
                print(f"ℹ️ Oylama kapandı, berabere veya oy yok: {bugun_tarih()}")


def zamanlayici_baslat():
    """APScheduler ile zamanlanmış görevleri başlatır."""
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()

    # Her gece 00:05'te menü oluştur (00:00 yerine 00:05 daha güvenli)
    scheduler.add_job(
        func=otomatik_menu_olustur,
        trigger='cron',
        hour=0,
        minute=5,
        id='menu_olustur',
        replace_existing=True
    )

    # Her gün 16:00'da oylamayı kapat
    scheduler.add_job(
        func=otomatik_oylama_kapat,
        trigger='cron',
        hour=OYLAMA_KAPANIS_SAATI,
        minute=0,
        id='oylama_kapat',
        replace_existing=True
    )

    scheduler.start()
    print("⏰ Zamanlayıcı başlatıldı!")
    print(f"   📋 Menü oluşturma: Her gün 00:05")
    print(f"   🗳️ Oylama kapanış: Her gün {OYLAMA_KAPANIS_SAATI}:00")


# ============ GİRİŞ SAYFASI ============

@app.route("/")
def giris():
    kullanicilar = kullanicilari_getir()
    return render_template("login.html",
                         kullanicilar=kullanicilar,
                         avatarlar=AVATARLAR)

@app.route("/giris-yap/<user_id>")
def giris_yap(user_id):
    session["user_id"] = user_id
    user = kullanici_getir(user_id)
    if user:
        session["user_name"] = user["name"]
        session["user_avatar"] = user["avatar"]
    return redirect(url_for("dashboard"))

@app.route("/cikis")
def cikis():
    session.clear()
    return redirect(url_for("giris"))

@app.route("/kullanici-ekle", methods=["POST"])
def yeni_kullanici():
    isim = request.form.get("isim", "").strip()
    avatar = request.form.get("avatar", "👤")
    if isim:
        kullanici_ekle(isim, avatar)
    return redirect(url_for("giris"))

@app.route("/kullanici-sil/<user_id>")
def kullanici_kaldir(user_id):
    kullanici_sil(user_id)
    if session.get("user_id") == user_id:
        session.clear()
    return redirect(url_for("giris"))

# ============ DASHBOARD ============

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    kullanicilar = kullanicilari_getir()
    malzemeler = malzemeleri_getir()
    evde_olan = [k for k in kullanicilar if k.get("isHome", True)]

    menu_data = gunun_menusunu_getir()
    vermeyenler = oy_vermeyenleri_getir()

    sonuclar = None
    kazananlar = None
    if menu_data:
        sonuclar = oylama_sonucunu_getir()
        if not oylama_acik_mi():
            kazananlar = kazanani_belirle()

    return render_template("dashboard.html",
                         tarih=bugun_tarih_gosterim(),
                         kullanicilar=kullanicilar,
                         malzeme_sayisi=len(malzemeler),
                         evde_olan_sayisi=len(evde_olan),
                         oylama_acik=oylama_acik_mi(),
                         kalan=kalan_sure(),
                         menu_data=menu_data,
                         sonuclar=sonuclar,
                         kazananlar=kazananlar,
                         vermeyenler=vermeyenler)

# ============ DOLAP ============

@app.route("/dolap")
def dolap():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    malzemeler = malzemeleri_getir()
    kategori = request.args.get("kategori", "hepsi")

    if kategori != "hepsi":
        malzemeler = [m for m in malzemeler if m.get("category") == kategori]

    return render_template("dolap.html",
                         malzemeler=malzemeler,
                         kategoriler=KATEGORILER,
                         secili_kategori=kategori,
                         toplam=len(malzemeleri_getir()))

@app.route("/malzeme-ekle", methods=["POST"])
def yeni_malzeme():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    isim = request.form.get("isim", "").strip()
    kategori = request.form.get("kategori", "diger")

    if isim:
        malzeme_ekle(isim, kategori, session["user_id"])

    return redirect(url_for("dolap"))

@app.route("/malzeme-sil/<malzeme_id>")
def malzeme_kaldir(malzeme_id):
    if "user_id" not in session:
        return redirect(url_for("giris"))

    malzeme_sil(malzeme_id)
    return redirect(url_for("dolap"))

@app.route("/malzeme-duzenle/<malzeme_id>", methods=["POST"])
def malzeme_duzenle(malzeme_id):
    if "user_id" not in session:
        return redirect(url_for("giris"))

    yeni_isim = request.form.get("isim", "").strip()
    yeni_kategori = request.form.get("kategori", "diger")

    if yeni_isim:
        malzeme_guncelle(malzeme_id, yeni_isim, yeni_kategori)

    return redirect(url_for("dolap"))

# ============ GÜNÜN MENÜSÜ ============

@app.route("/menu")
def menu():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    menu_data = gunun_menusunu_getir()
    sonuclar = None
    kazananlar = None
    vermeyenler = []
    kullanici_oyu = None

    if menu_data:
        sonuclar = oylama_sonucunu_getir()
        vermeyenler = oy_vermeyenleri_getir()

        votes = menu_data.get("votes", {})
        kullanici_oyu = votes.get(session["user_id"])

        if not oylama_acik_mi():
            kazananlar = kazanani_belirle()

    return render_template("gunun_menusu.html",
                         menu_data=menu_data,
                         sonuclar=sonuclar,
                         kazananlar=kazananlar,
                         vermeyenler=vermeyenler,
                         kullanici_oyu=kullanici_oyu,
                         oylama_acik=oylama_acik_mi(),
                         kalan=kalan_sure())

@app.route("/menu-olustur-ai")
def menu_olustur_ai():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    sonuc = gunun_menusunu_olustur_ai()

    if sonuc["success"]:
        flash("AI menüyü oluşturdu! 🎉", "success")
    else:
        flash(sonuc["error"], "danger")

    return redirect(url_for("menu"))

@app.route("/menu-olustur-manuel", methods=["POST"])
def menu_olustur_manuel():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    yemek1 = request.form.get("yemek1", "").strip()
    yemek2 = request.form.get("yemek2", "").strip()
    yemek3 = request.form.get("yemek3", "").strip()

    if not yemek1 or not yemek2 or not yemek3:
        flash("3 yemek adı da girilmeli!", "warning")
        return redirect(url_for("menu"))

    tarifler = [
        {"name": yemek1, "description": "Elle eklenen yemek", "cookTime": "30 dk", "calories": 400, "servings": 4},
        {"name": yemek2, "description": "Elle eklenen yemek", "cookTime": "30 dk", "calories": 400, "servings": 4},
        {"name": yemek3, "description": "Elle eklenen yemek", "cookTime": "30 dk", "calories": 400, "servings": 4}
    ]

    sonuc = gunun_menusunu_olustur_manuel(tarifler)

    if sonuc["success"]:
        flash("Menü oluşturuldu! 🎉", "success")
    else:
        flash("Bir hata oluştu.", "danger")

    return redirect(url_for("menu"))

@app.route("/menu-sil")
def menu_kaldir():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    menu_sil()
    flash("Menü silindi.", "info")
    return redirect(url_for("menu"))

@app.route("/oy-ver/<int:menu_index>")
def oy_kullan(menu_index):
    if "user_id" not in session:
        return redirect(url_for("giris"))

    if not oylama_acik_mi():
        flash("Oylama süresi dolmuş!", "warning")
        return redirect(url_for("menu"))

    # Evde olmayan oy veremesin
    user = kullanici_getir(session["user_id"])
    if user and not user.get("isHome", True):
        flash("Evde olmadığın için oy veremezsin!", "warning")
        return redirect(url_for("menu"))

    oy_ver(session["user_id"], menu_index)
    flash("Oyun kaydedildi! ✅", "success")
    return redirect(url_for("menu"))

@app.route("/oy-geri-al")
def oy_iptal():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    oy_geri_al(session["user_id"])
    flash("Oyun geri alındı.", "info")
    return redirect(url_for("menu"))

@app.route("/kazanan-sec/<int:menu_index>")
def kazanan_sec(menu_index):
    if "user_id" not in session:
        return redirect(url_for("giris"))

    kazanani_kaydet(menu_index)
    flash("Kazanan yemek seçildi! 🏆", "success")
    return redirect(url_for("menu"))

# ============ TARİF DETAY ============

@app.route("/tarif/<int:menu_index>")
def tarif_detay(menu_index):
    if "user_id" not in session:
        return redirect(url_for("giris"))

    menu_data = gunun_menusunu_getir()
    if not menu_data:
        flash("Henüz menü oluşturulmadı.", "warning")
        return redirect(url_for("menu"))

    menus = menu_data.get("menus", [])
    if menu_index >= len(menus):
        flash("Tarif bulunamadı.", "danger")
        return redirect(url_for("menu"))

    tarif = menus[menu_index]
    return render_template("tarif_detay.html", tarif=tarif, menu_index=menu_index)

# ============ FOTOĞRAF İLE MALZEME ============

@app.route("/foto-ekle")
def foto_ekle():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    return render_template("foto_ekle.html")

@app.route("/foto-analiz", methods=["POST"])
def foto_analiz():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Giriş yapınız"})

    if 'foto' not in request.files:
        return jsonify({"success": False, "error": "Fotoğraf seçilmedi"})

    foto = request.files['foto']
    if foto.filename == '':
        return jsonify({"success": False, "error": "Fotoğraf seçilmedi"})

    try:
        from services.gemini_service import fotograf_malzeme_tani
        image_data = foto.read()
        sonuc = fotograf_malzeme_tani(image_data)
        return jsonify(sonuc)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/foto-toplu-ekle", methods=["POST"])
def foto_toplu_ekle():
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Giriş yapınız"})

    data = request.get_json()
    malzemeler = data.get("malzemeler", [])

    eklenen = 0
    for m in malzemeler:
        isim = m.get("isim", "").strip()
        kategori = m.get("kategori", "diger")
        if isim:
            malzeme_ekle(isim, kategori, session["user_id"])
            eklenen += 1

    return jsonify({"success": True, "eklenen": eklenen})

# ============ PROFİL ============

@app.route("/profil")
def profil():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    user = kullanici_getir(session["user_id"])
    return render_template("profil.html", user=user)

@app.route("/evde-durumu", methods=["POST"])
def evde_durumu():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    evde_mi = request.form.get("evde") == "true"
    evde_durumu_guncelle(session["user_id"], evde_mi)
    return redirect(url_for("profil"))

@app.route("/sevmedigim-ekle", methods=["POST"])
def sevmedik_ekle():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    yemek = request.form.get("yemek", "").strip()
    if yemek:
        sevmedigim_ekle(session["user_id"], yemek)
    return redirect(url_for("profil"))

@app.route("/sevmedigim-kaldir/<yemek>")
def sevmedik_kaldir(yemek):
    if "user_id" not in session:
        return redirect(url_for("giris"))

    sevmedigim_kaldir(session["user_id"], yemek)
    return redirect(url_for("profil"))

@app.route("/profil-duzenle", methods=["POST"])
def profil_duzenle():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    from services.firebase_service import kullanici_guncelle

    isim = request.form.get("isim", "").strip()
    avatar = request.form.get("avatar", "👤")

    if isim:
        kullanici_guncelle(session["user_id"], isim, avatar)
        session["user_name"] = isim
        session["user_avatar"] = avatar
        flash("Profil güncellendi! ✅", "success")

    return redirect(url_for("profil"))

# ============ ALIŞVERİŞ LİSTESİ ============

@app.route("/alisveris")
def alisveris():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    from services.menu_service import alisveris_listesi_getir
    
    eksikler = alisveris_listesi_getir()
    menu_data = gunun_menusunu_getir()

    return render_template("alisveris.html",
                         eksikler=eksikler,
                         menu_var=menu_data is not None)

# ============ GEÇMİŞ ============

@app.route("/gecmis")
def gecmis():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    gecmis_data = gecmis_getir()
    return render_template("gecmis.html", gecmis=gecmis_data)

# ============ API TEST ============

@app.route("/api-test")
def api_test():
    if "user_id" not in session:
        return redirect(url_for("giris"))

    from config import GROQ_API_KEY

    key_durumu = "❌ Key yok" if not GROQ_API_KEY else f"✅ Key var ({GROQ_API_KEY[:12]}...)"

    model_test_html = ""
    try:
        from groq import Groq
        test_client = Groq(api_key=GROQ_API_KEY)

        response = test_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Merhaba, 1+1 kaç?"}],
            max_tokens=20
        )

        yanit = response.choices[0].message.content
        model_test_html = f"<li>✅ <strong>llama-3.3-70b-versatile</strong> → Çalışıyor! Yanıt: {yanit}</li>"
    except Exception as e:
        model_test_html = f"<li>❌ Hata → {str(e)[:200]}</li>"

    return f"""
    <html>
    <head><title>API Test</title><meta charset="UTF-8"></head>
    <body style="font-family:Arial; padding:40px; max-width:700px; margin:auto;">
        <h2>🔧 API Test (Groq)</h2>
        <hr>
        <h4>API Key:</h4><p>{key_durumu}</p>
        <h4>Model Test:</h4><ul>{model_test_html}</ul>
        <hr>
        <a href="/dashboard">← Dashboard</a>
        &nbsp;&nbsp;
        <a href="/menu">🍽️ Menüye Git</a>
    </body></html>
    """

# ============ ÇALIŞTIR ============

if __name__ == "__main__":
    import os
    # Debug modda scheduler çift çalışmasın
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        zamanlayici_baslat()

    app.run(debug=True, port=5000)