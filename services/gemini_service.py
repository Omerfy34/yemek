import json
import base64
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

TEXT_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def tarif_onerisi_al(malzemeler, sevmedigler=None, son_yemekler=None, kisi_sayisi=4):
    """
    Malzemelere göre 3 farklı yemek tarifi önerir.
    Kişi sayısına göre ölçüler ayarlanır.
    """

    malzeme_listesi = ", ".join(malzemeler) if malzemeler else "Malzeme yok"

    sevmedik_text = ""
    if sevmedigler and len(sevmedigler) > 0:
        sevmedik_text = f"\n⛔ Şunları KESİNLİKLE önerme: {', '.join(sevmedigler)}"

    son_yemek_text = ""
    if son_yemekler and len(son_yemekler) > 0:
        son_yemek_text = f"\n📅 Son günlerde yediklerimiz (tekrarlama): {', '.join(son_yemekler)}"

    prompt = f"""Sen bir Türk mutfağı uzmanısın. Aile için akşam yemeği önereceksin.

📦 Elimdeki malzemeler: {malzeme_listesi}
👥 Evdeki kişi sayısı: {kisi_sayisi} kişi (ölçüleri buna göre ayarla)
{sevmedik_text}
{son_yemek_text}

📋 KURALLAR:
1. Tam olarak 3 farklı yemek öner
2. Orta zorlukta, evde yapılabilir olsun
3. En fazla 1-2 eksik malzeme olabilir
4. Tuz, karabiber, pul biber, sıvıyağ, zeytinyağı temel malzeme say, eksik sayma
5. Her yemek farklı ana malzeme olsun
6. Türk mutfağı ağırlıklı olsun
7. Malzeme miktarlarını {kisi_sayisi} kişilik olarak yaz
8. Yapılış adımlarını ÇOK DETAYLI yaz. Her adımı açıkla:
   - Ateş derecesi (kısık/orta/güçlü)
   - Pişirme süresi (kaç dakika)
   - Kıvam nasıl olmalı
   - Renk nasıl olmalı
   - İpuçları ve püf noktaları
9. Minimum 6-8 yapılış adımı olsun
10. Her adım en az 2 cümle olsun

Sadece JSON formatında yanıt ver, başka hiçbir şey yazma:

[
    {{
        "name": "Yemek Adı",
        "description": "Bu yemeğin kısa tanıtımı ve özelliği (2-3 cümle)",
        "cookTime": "45 dk",
        "prepTime": "15 dk",
        "totalTime": "60 dk",
        "calories": 450,
        "servings": {kisi_sayisi},
        "difficulty": "Orta",
        "ingredients": [
            {{"name": "Tavuk göğsü", "amount": "500g", "available": true, "note": "Kuşbaşı doğranmış"}},
            {{"name": "Eksik malzeme", "amount": "1 adet", "available": false, "note": ""}}
        ],
        "steps": [
            "1. Hazırlık: Tavuk göğsünü yıkayıp kuruladıktan sonra kuşbaşı doğrayın. Parçalar parmak ucu büyüklüğünde olmalı, böylece eşit pişer. Doğradıktan sonra bir kaseye alıp tuz ve karabiber ile marineleyin.",
            "2. Sebzeleri doğrayın: Soğanı ince ince piyaz doğrayın. Domatesleri küp küp kesin. Biberleri julyen (ince uzun şeritler halinde) doğrayın. Sarımsakları ince ince kıyın veya rendeleyin.",
            "3. Kavurma: Geniş bir tavayı orta ateşte ısıtın. 2 yemek kaşığı zeytinyağı ekleyin. Yağ kızdığında (hafif duman çıkmaya başladığında) tavukları ekleyin. 5-6 dakika ara ara karıştırarak her tarafını altın sarısı olana kadar kavurun.",
            "4. ...",
            "5. ...",
            "6. ...",
            "7. ...",
            "8. Servis: Yemeği derin bir tabağa alın. Üzerine taze maydanoz serpin. Yanında pilav veya sıcak ekmek ile servis edin. Afiyet olsun!"
        ],
        "tips": [
            "Tavuğu çok kısık ateşte pişirirseniz suyu çıkar ve kavurma yerine haşlama olur.",
            "Domatesleri eklemeden önce salçayı kavurmak lezzeti artırır."
        ],
        "nutrition": {{
            "protein": 35,
            "carb": 20,
            "fat": 15,
            "fiber": 3
        }}
    }},
    {{
        "name": "İkinci Yemek",
        "description": "Detaylı açıklama",
        "cookTime": "30 dk",
        "prepTime": "10 dk",
        "totalTime": "40 dk",
        "calories": 380,
        "servings": {kisi_sayisi},
        "difficulty": "Orta",
        "ingredients": [
            {{"name": "Malzeme", "amount": "{kisi_sayisi} kişilik ölçü", "available": true, "note": ""}}
        ],
        "steps": ["1. Detaylı adım...", "2. Detaylı adım...", "3. ...", "4. ...", "5. ...", "6. ..."],
        "tips": ["İpucu 1", "İpucu 2"],
        "nutrition": {{"protein": 20, "carb": 40, "fat": 10, "fiber": 5}}
    }},
    {{
        "name": "Üçüncü Yemek",
        "description": "Detaylı açıklama",
        "cookTime": "20 dk",
        "prepTime": "10 dk",
        "totalTime": "30 dk",
        "calories": 300,
        "servings": {kisi_sayisi},
        "difficulty": "Kolay",
        "ingredients": [
            {{"name": "Malzeme", "amount": "{kisi_sayisi} kişilik ölçü", "available": true, "note": ""}}
        ],
        "steps": ["1. Detaylı adım...", "2. Detaylı adım...", "3. ...", "4. ...", "5. ...", "6. ..."],
        "tips": ["İpucu 1", "İpucu 2"],
        "nutrition": {{"protein": 15, "carb": 30, "fat": 12, "fiber": 4}}
    }}
]"""

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Sen bir profesyonel Türk aşçısın. Tarifleri çok detaylı, adım adım anlatırsın. Her adımda ateş derecesi, süre, kıvam ve ipuçları verirsin. Sadece geçerli JSON formatında yanıt ver."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=4000
        )

        text = response.choices[0].message.content.strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        text = text.strip()

        tarifler = json.loads(text)

        if not isinstance(tarifler, list) or len(tarifler) < 3:
            return {"success": False, "error": "AI yeterli tarif üretemedi. Tekrar deneyin."}

        return {"success": True, "menus": tarifler[:3]}

    except json.JSONDecodeError as e:
        print(f"JSON Parse Hatası: {e}")
        print(f"Gelen yanıt: {text}")
        return {"success": False, "error": "AI yanıtı işlenemedi. Tekrar deneyin."}
    except Exception as e:
        print(f"Groq API Hatası: {e}")
        return {"success": False, "error": f"AI hatası: {str(e)[:150]}"}


def fotograf_malzeme_tani(image_data):
    """Fotoğraftaki malzemeleri tanır. Türkçe sonuç döner."""

    try:
        base64_image = base64.b64encode(image_data).decode('utf-8')

        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Sen bir yiyecek tanıma uzmanısın. Her zaman TÜRKÇE yanıt ver. Malzeme isimlerini kesinlikle Türkçe yaz."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Bu fotoğraftaki yiyecek malzemelerini tanı.

ÖNEMLİ: Malzeme isimlerini KESİNLİKLE TÜRKÇE yaz. İngilizce KULLANMA.

Kategoriler: et, sebze, meyve, bakliyat, sut, diger

Sadece JSON formatında yanıt ver:

[
    {"name": "Domates", "category": "sebze", "belirsiz": false},
    {"name": "Tavuk", "category": "et", "belirsiz": false}
]"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        text = response.choices[0].message.content.strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        text = text.strip()

        malzemeler = json.loads(text)

        ingilizce_turkce = {
            "tomato": "Domates", "chicken": "Tavuk", "egg": "Yumurta",
            "onion": "Soğan", "pepper": "Biber", "cheese": "Peynir",
            "milk": "Süt", "butter": "Tereyağı", "rice": "Pirinç",
            "pasta": "Makarna", "lettuce": "Marul", "cucumber": "Salatalık",
            "potato": "Patates", "carrot": "Havuç", "garlic": "Sarımsak",
            "lemon": "Limon", "apple": "Elma", "bread": "Ekmek",
            "yogurt": "Yoğurt", "meat": "Et", "fish": "Balık",
            "salt": "Tuz", "sugar": "Şeker", "oil": "Yağ",
            "olive oil": "Zeytinyağı", "flour": "Un", "banana": "Muz",
            "orange": "Portakal", "mushroom": "Mantar", "spinach": "Ispanak",
            "parsley": "Maydanoz", "eggplant": "Patlıcan", "zucchini": "Kabak",
            "lentil": "Mercimek", "bean": "Fasulye", "chickpea": "Nohut",
            "bulgur": "Bulgur", "ground meat": "Kıyma", "beef": "Dana Eti",
            "lamb": "Kuzu Eti", "cream": "Krema", "honey": "Bal",
            "tomato paste": "Salça", "bell pepper": "Dolmalık Biber",
            "green pepper": "Yeşil Biber", "red pepper": "Kırmızı Biber",
            "corn": "Mısır", "pea": "Bezelye", "cabbage": "Lahana",
            "cauliflower": "Karnabahar", "broccoli": "Brokoli",
            "leek": "Pırasa", "dill": "Dereotu", "mint": "Nane",
            "thyme": "Kekik", "cumin": "Kimyon", "cinnamon": "Tarçın",
            "walnut": "Ceviz", "hazelnut": "Fındık",
            "watermelon": "Karpuz", "peach": "Şeftali", "cherry": "Kiraz",
            "grape": "Üzüm", "strawberry": "Çilek", "apricot": "Kayısı"
        }

        for m in malzemeler:
            isim_lower = m["name"].lower().strip()
            if isim_lower in ingilizce_turkce:
                m["name"] = ingilizce_turkce[isim_lower]

        return {"success": True, "malzemeler": malzemeler}

    except json.JSONDecodeError as e:
        print(f"Fotoğraf JSON hatası: {e}")
        return {"success": False, "error": "AI yanıtı işlenemedi."}
    except Exception as e:
        print(f"Fotoğraf tanıma hatası: {e}")
        return {"success": False, "error": f"Tanıma hatası: {str(e)[:150]}"}