@echo off
echo 🚀 AACS Dashboard Launcher
echo ========================
echo.
echo اختر طريقة التشغيل:
echo 1. تشغيل مع الخادم المحلي (مستحسن)
echo 2. فتح النسخة المستقلة (بدون خادم)
echo 3. إلغاء
echo.
set /p choice="أدخل اختيارك (1-3): "

if "%choice%"=="1" goto server
if "%choice%"=="2" goto standalone
if "%choice%"=="3" goto end

:server
echo.
echo 🚀 Starting AACS Dashboard Server...
echo 📋 سيتم فتح http://localhost:8000 في المتصفح
echo ⏹️  اضغط Ctrl+C لإيقاف الخادم
echo.
cd dashboard
start http://localhost:8000
python serve.py
goto end

:standalone
echo.
echo 📋 Opening standalone dashboard...
echo ⚠️  ملاحظة: هذا وضع العرض التوضيحي بدون تحميل البيانات الحقيقية
echo.
start dashboard\standalone.html
goto end

:end
pause