#!/usr/bin/env python3
"""
سكريبت فحص الأمان لنظام AACS V0
"""
import sys
import os
import json
import argparse
from pathlib import Path

# إضافة المسار الجذر للمشروع
sys.path.append(str(Path(__file__).parent.parent))

from core.config import Config
from core.security_manager import SecurityManager


def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(description='فحص أمان نظام AACS V0')
    parser.add_argument('--scan-secrets', action='store_true', 
                       help='فحص المستودع للأسرار المكشوفة')
    parser.add_argument('--generate-report', action='store_true',
                       help='توليد تقرير أمني شامل')
    parser.add_argument('--check-config', action='store_true',
                       help='فحص تكوين الأسرار')
    parser.add_argument('--export-config', action='store_true',
                       help='تصدير تكوين الأمان')
    parser.add_argument('--output', '-o', type=str,
                       help='مسار ملف الإخراج')
    
    args = parser.parse_args()
    
    # إنشاء مدير الأمان
    config = Config()
    security_manager = SecurityManager(config)
    
    print("🔒 أداة فحص الأمان لنظام AACS V0")
    print("=" * 50)
    
    # فحص الأسرار المكشوفة
    if args.scan_secrets:
        print("\n🔍 فحص المستودع للأسرار المكشوفة...")
        scan_result = security_manager.scan_repository()
        
        print(f"📊 نتائج الفحص:")
        print(f"   - الملفات المفحوصة: {scan_result['scanned_files']}")
        print(f"   - الأسرار المكتشفة: {scan_result['total_findings']}")
        print(f"   - عالية الخطورة: {scan_result['findings_by_severity']['high']}")
        print(f"   - متوسطة الخطورة: {scan_result['findings_by_severity']['medium']}")
        print(f"   - منخفضة الخطورة: {scan_result['findings_by_severity']['low']}")
        
        if scan_result['total_findings'] > 0:
            print("\n⚠️ تفاصيل الأسرار المكتشفة:")
            for finding in scan_result['detailed_findings'][:10]:  # أول 10 فقط
                severity_icon = "🚨" if finding['severity'] == 'high' else "⚠️" if finding['severity'] == 'medium' else "ℹ️"
                print(f"   {severity_icon} {finding['file']}:{finding['line']} - {finding['category']}")
        
        if args.output:
            output_file = args.output if args.output.endswith('.json') else f"{args.output}_secrets_scan.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(scan_result, f, ensure_ascii=False, indent=2)
            print(f"💾 تم حفظ نتائج الفحص في: {output_file}")
    
    # فحص تكوين الأسرار
    if args.check_config:
        print("\n🔧 فحص تكوين الأسرار...")
        
        missing_secrets = []
        invalid_secrets = []
        valid_secrets = []
        
        for secret_name, secret_info in security_manager.required_secrets.items():
            env_value = os.getenv(secret_info.env_var_name)
            
            if secret_info.required and not env_value:
                missing_secrets.append(secret_name)
            elif env_value and secret_info.validation_pattern:
                import re
                if re.match(secret_info.validation_pattern, env_value):
                    valid_secrets.append(secret_name)
                else:
                    invalid_secrets.append(secret_name)
            elif env_value:
                valid_secrets.append(secret_name)
        
        print(f"✅ أسرار صحيحة ({len(valid_secrets)}):")
        for secret in valid_secrets:
            print(f"   - {secret}")
        
        if missing_secrets:
            print(f"\n❌ أسرار مطلوبة مفقودة ({len(missing_secrets)}):")
            for secret in missing_secrets:
                info = security_manager.required_secrets[secret]
                print(f"   - {secret} ({info.env_var_name})")
        
        if invalid_secrets:
            print(f"\n⚠️ أسرار بتنسيق غير صحيح ({len(invalid_secrets)}):")
            for secret in invalid_secrets:
                print(f"   - {secret}")
    
    # توليد تقرير شامل
    if args.generate_report:
        print("\n📊 توليد التقرير الأمني الشامل...")
        report = security_manager.generate_security_report()
        
        print(f"📈 ملخص التقرير:")
        print(f"   - الملفات المفحوصة: {report['secrets_scan']['scanned_files']}")
        print(f"   - الأسرار المكتشفة: {report['secrets_scan']['total_findings']}")
        print(f"   - إجمالي الوكلاء: {report['access_control']['total_agents']}")
        print(f"   - قواعد الوصول: {report['access_control']['total_rules']}")
        print(f"   - التوصيات الأمنية: {len(report['security_recommendations'])}")
        
        print(f"\n💡 أهم التوصيات الأمنية:")
        for i, recommendation in enumerate(report['security_recommendations'][:5], 1):
            print(f"   {i}. {recommendation}")
        
        if args.output:
            output_file = args.output if args.output.endswith('.json') else f"{args.output}_security_report.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"💾 تم حفظ التقرير في: {output_file}")
    
    # تصدير تكوين الأمان
    if args.export_config:
        print("\n📄 تصدير تكوين الأمان...")
        output_file = args.output if args.output else "security_config.json"
        config_file = security_manager.export_security_config(output_file)
        if config_file:
            print(f"✅ تم تصدير التكوين في: {config_file}")
    
    # إذا لم يتم تحديد أي خيار، اعرض المساعدة
    if not any([args.scan_secrets, args.generate_report, args.check_config, args.export_config]):
        print("\n❓ لم يتم تحديد أي إجراء. استخدم --help لعرض الخيارات المتاحة.")
        print("\nأمثلة:")
        print("  python scripts/security_scan.py --scan-secrets")
        print("  python scripts/security_scan.py --check-config")
        print("  python scripts/security_scan.py --generate-report --output security_report")
        print("  python scripts/security_scan.py --scan-secrets --generate-report --output full_scan")
    
    print("\n" + "=" * 50)
    print("✅ اكتمل فحص الأمان")


if __name__ == "__main__":
    main()