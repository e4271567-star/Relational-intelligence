# Relational Intelligence — Mobile Web Deployment

هذه النسخة مصممة لتعمل كخدمة Web واحدة:
- FastAPI backend
- واجهة Mobile-first مدمجة داخل نفس الخدمة
- لا تحتاج Python أو Node على الهاتف بعد النشر
- يوجد Mock Model Adapter داخل الـ demo حاليًا
- البيانات الحالية In-Memory لأغراض التجربة؛ إعادة تشغيل الخدمة تعيدها إلى V1

## الهدف
فتح الموقع من Android كرابط HTTPS عادي.

## تشغيل محليًا
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

ثم افتح:
http://localhost:8000

## Docker
```bash
docker build -t relational-intelligence .
docker run -p 8000:8000 relational-intelligence
```

## النشر
ارفع هذا المجلد إلى خدمة استضافة تدعم Docker/Container.
استخدم منفذ البيئة `PORT`.
بعد نجاح النشر ستحصل على رابط HTTPS تفتحه من Android.

## ما تم تجهيزه
Explore → Simulate → Analyze → Compare → Decide → Review & Apply → V2

## ما لم يتم ربطه بعد
- Model Engine الحقيقي
- PostgreSQL
- Authentication
- persistent storage
- production permissions
- production security

هذه النسخة هي نواة اختبار UX والـ workflow وليست نسخة إنتاجية نهائية.
