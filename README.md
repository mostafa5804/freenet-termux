<p align="center">
  <a href="https://github.com/mostafa5804/freenet-termux">
    <img src="https://raw.githubusercontent.com/mostafa5804/freenet-termux/main/freenet.jpg" alt="Freenet for Termux" width="300">
  </a>
</p>

<h3 align="center">Freenet برای Termux</h3>

<p align="center">
  ابزاری قدرتمند و آسان برای یافتن سریع‌ترین کانفیگ‌های V2Ray در ترمینال اندروید.
  <br>
  <a href="https://github.com/mostafa5804/freenet-termux/issues">گزارش مشکل</a>
  ·
  <a href="https://github.com/mostafa5804/freenet-termux/pulls">مشارکت در پروژه</a>
</p>

---

## ✨ ویژگی‌های کلیدی

- **🖥️ رابط کاربری خط فرمان (CLI) جذاب و رنگی:** تجربه‌ای لذت‌بخش در ترمینال.
- **📡 منابع متنوع کانفیگ:** دریافت کانفیگ از چندین سرور (Mirror) قابل انتخاب.
- **⚙️ فیلتر هوشمند:** فیلتر کردن کانفیگ‌ها بر اساس نوع پروتکل (Vmess، Vless و غیره).
- **⏱️ تست سرعت (Latency) پیشرفته:** تست همزمان چندین کانفیگ برای یافتن بهترین‌ها.
- **🏆 ذخیره نتایج برتر:** ذخیره ۱۰ کانفیگ با کمترین تاخیر به صورت خودکار.
- **📂 خروجی منظم:** ذخیره گزارش‌ها و کانفیگ‌های برتر در پوشه `Download` گوشی شما.

---

## 🚀 نصب و راه‌اندازی

برای نصب، می‌توانید از یکی از دو روش زیر استفاده کنید.

### ✅ روش ۱: نصب اتوماتیک (پیشنهادی)

این روش ساده‌ترین راه است. فقط یک دستور را در ترموکس وارد کنید تا همه کارها به صورت خودکار انجام شود:

```bash
curl -sL https://raw.githubusercontent.com/mostafa5804/freenet-termux/main/install.sh | bash
```

---

### 🧰 روش ۲: نصب دستی (برای کاربران حرفه‌ای)

اگر تمایل دارید مراحل را به صورت دستی کنترل کنید یا در نصب خودکار مشکلی داشتید، از این روش استفاده کنید.

#### ۱. به‌روزرسانی ترموکس (اختیاری):
```bash
pkg update && pkg upgrade -y
```

#### ۲. نصب Git(اختیاری):
```bash
pkg install git -y
```

#### ۳. دانلود (کلون کردن) پروژه:
```bash
git clone https://github.com/mostafa5804/freenet-termux.git
```

#### ۴. ورود به پوشه پروژه:
```bash
cd freenet-termux
```

#### ۵. اجرای اسکریپت نصب:
```bash
bash ./install.sh
```

پس از این مرحله، نصب کامل شده و برنامه آماده اجراست!


## ⚙️ نحوه استفاده

بعد از نصب موفق، برای اجرای برنامه مراحل زیر را انجام دهید:

#### ۱. ورود به پوشه پروژه:
```bash
cd ~/freenet-termux
```

#### ۲. اجرای برنامه:
```bash
python freenet_termux.py
```

> 💡 نکته: پس از هر بار بستن و باز کردن Termux، باید ابتدا وارد پوشه پروژه شوید و سپس برنامه را اجرا کنید.

---

## 📁 خروجی‌ها

بهترین کانفیگ‌های پیدا شده در فایل زیر ذخیره می‌شوند:

```
/sdcard/Download/freenet/best_configs.txt
```

می‌توانید آن‌ها را مستقیماً در کلاینت V2Ray خود استفاده کنید.

---

با ❤️ از [Mostafa](https://github.com/mostafa5804)
