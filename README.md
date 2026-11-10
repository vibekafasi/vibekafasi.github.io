# Vibe Kafası — ücretsiz araçlar

**Kodla, Üret, Öğren, Eğlen!**

- Site: https://vibekafasi.github.io/
- KAFA ASİSTAN paneli: https://vibekafasi.github.io/kafa/
- Kullanım kılavuzu: https://vibekafasi.github.io/kilavuz/

Instagram · YouTube @vibe.kafasi · Telegram t.me/vibekafasi

## Bakım (sayfa ekleyen / üreten herkes için)

Yeni sayfa ekledikten ya da sayfaları yeniden ürettikten sonra depo kökünde tek komut:

```
python3 bakim/hepsi.py
```

Bu komut sayfa başlıklarını (yazı tipleri, ikonlar, güvenlik politikası, hreflang, sosyal paylaşım etiketleri) tek tipe getirir,
site arama dizinini (`assets/arama/`) ve `sitemap.xml`'i yeniler, eksik AVIF/WebP görselleri üretir. Tekrar çalıştırmak güvenlidir.
Unutulsa bile main'e gönderimden sonra **Site bakımı (otomatik)** iş akışı aynısını yapar.

- Denetim: `python3 bakim/denetim.py` (kırık bağlantı, hreflang, JSON-LD, alt metin)
- Arama motorlarına haber: `python3 bakim/indexnow.py --hepsi` (Bing/Yandex; otomatik bakım değişen sayfaları zaten bildirir)
- Yazı tiplerini yenilemek: `python3 bakim/yazi_indir.py`
- Arama motoru doğrulama kodları: `bakim/dogrulama.json`
- Sabit kurallar: `assets/sayilar.json` biçimine dokunulmaz; araç kartları yalnızca Telegram botuna bağlanır.
