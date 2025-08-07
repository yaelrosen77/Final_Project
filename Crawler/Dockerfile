FROM python:3.10-slim

# התקנת תלויות מערכת
RUN apt-get update && apt-get install -y \
    wget curl gnupg unzip sudo \
    tshark \
    libnss3 libatk-bridge2.0-0 libgtk-3-0 libxss1 libasound2 \
    libappindicator3-1 libu2f-udev xdg-utils fonts-liberation \
    libvulkan1 libxshmfence1 libdrm2 \
    chromium \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 🧩 תיקון כדי ש-uc ימצא את הדפדפן
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable


# תיקיית עבודה
WORKDIR /app

# העתקת הקבצים
COPY . .

# התקנת תלויות פייתון
RUN pip install --no-cache-dir \
    pandas \
    openpyxl \
    tldextract \
    selenium \
    undetected-chromedriver==3.5.4 \
    playwright

# התקנת דפדפנים ל-playwright
RUN playwright install --with-deps

# הרשאות tshark
RUN adduser --disabled-password --gecos '' tshark && \
    chgrp tshark /usr/bin/dumpcap && \
    chmod 750 /usr/bin/dumpcap && \
    setcap cap_net_raw,cap_net_admin=eip /usr/bin/dumpcap

# ברירת מחדל
CMD ["python", "ApplicationRunner.py"]
