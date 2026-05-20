# /nginx/Dockerfile

FROM nginx:1.25-alpine

# حذف کانفیگ پیش‌فرض
RUN rm /etc/nginx/conf.d/default.conf

# کپی کانفیگ اختصاصی
COPY nginx.conf /etc/nginx/nginx.conf

# کپی فایل‌های استاتیک (برای سرو مستقیم)
RUN mkdir -p /static /media /usr/share/nginx/html

# پورت‌ها
EXPOSE 80 443

# اجرای Nginx
CMD ["nginx", "-g", "daemon off;"]