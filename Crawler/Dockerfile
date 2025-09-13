FROM python:3.10-slim

# 🧱 התקנת תלויות מערכת
RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip sudo \
    tshark \
    libnss3 libatk-bridge2.0-0 libgtk-3-0 libxss1 libasound2 \
    libappindicator3-1 libu2f-udev xdg-utils fonts-liberation \
    libvulkan1 libxshmfence1 libdrm2 \
    chromium \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 📂 תיקיית עבודה
WORKDIR /app

# 📝 העתקת הקבצים
COPY . .

# 📦 התקנת תלויות פייתון
RUN pip install --no-cache-dir \
    pandas \
    openpyxl \
    tldextract \
    selenium \
    undetected-chromedriver==3.5.4 \
    playwright

# 🧩 התקנת דפדפנים ל-Playwright
RUN playwright install --with-deps

# 🎯 הרשאות ל-tshark להרצה מתוך הדוקר
RUN adduser --disabled-password --gecos '' tshark && \
    chgrp tshark /usr/bin/dumpcap && \
    chmod 750 /usr/bin/dumpcap && \
    setcap cap_net_raw,cap_net_admin=eip /usr/bin/dumpcap

# 🏁 ברירת מחדל: הרץ את הסניפר הראשי
ENV PYTHONUNBUFFERED=1
CMD ["python", "ApplicationRunner.py"]
