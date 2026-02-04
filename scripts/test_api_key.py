#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار مفتاح API للذكاء الاصطناعي
"""

import os
import sys
import requests
import json
from pathlib import Path

def load_env_if_exists():
    """تحميل متغيرات البيئة من ملف .env إذا كان موجوداً"""
    env_file = Path('.env')
    if env_file.exists():
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            print("✅ تم تحميل متغيرات البيئة من .env")
        except Exception as e:
            print(f"⚠️ خطأ في تحميل .env: {e}")

def test_api_key():
    """اختبار مفتاح API"""
    print("🔍 اختبار مفتاح API للذكاء الاصطناعي...")
    
    # تحميل متغيرات البيئة
    load_env_if_exists()
    
    # فحص متغيرات البيئة
    ai_provider = os.getenv('AI_PROVIDER', 'غير محدد')
    api_key = os.getenv('AI_API_KEY')
    
    print(f"🤖 مزود الذكاء الاصطناعي: {ai_provider}")
    print(f"🔑 مفتاح API موجود: {'نعم' if api_key else 'لا'}")
    
    if not api_key:
        print("❌ مفتاح API غير موجود")
        return False
    
    if api_key == 'your_valid_groq_api_key_here':
        print("❌ مفتاح API لم يتم تحديثه (لا يزال القيمة الافتراضية)")
        return False
    
    # فحص تنسيق المفتاح
    if not api_key.startswith('gsk_'):
        print(f"⚠️ مفتاح API لا يبدو كمفتاح Groq صحيح (يجب أن يبدأ بـ gsk_)")
        print(f"   المفتاح الحالي يبدأ بـ: {api_key[:10]}...")
    
    # اختبار الاتصال
    try:
        print("🌐 اختبار الاتصال بـ Groq API...")
        
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.1-8b-instant',
                'messages': [
                    {'role': 'user', 'content': 'مرحبا، قل "اختبار ناجح" فقط'}
                ],
                'max_tokens': 10,
                'temperature': 0.1
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()
            print(f"✅ الاتصال ناجح! رد الذكاء الاصطناعي: {ai_response}")
            return True
        else:
            print(f"❌ فشل الاتصال: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   تفاصيل الخطأ: {error_data}")
            except:
                print(f"   نص الخطأ: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ انتهت مهلة الاتصال")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ خطأ في الطلب: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("=" * 50)
    print("🧪 اختبار مفتاح API - AACS")
    print("=" * 50)
    
    success = test_api_key()
    
    print("=" * 50)
    if success:
        print("🎉 الاختبار نجح! مفتاح API يعمل بشكل صحيح")
        sys.exit(0)
    else:
        print("💥 الاختبار فشل! يرجى التحقق من مفتاح API")
        print("\n📋 خطوات الإصلاح:")
        print("1. احصل على مفتاح API من: https://console.groq.com/keys")
        print("2. أضف المفتاح إلى GitHub Secrets باسم: AI_API_KEY")
        print("3. للاختبار المحلي، أضف المفتاح إلى ملف .env")
        sys.exit(1)

if __name__ == "__main__":
    main()