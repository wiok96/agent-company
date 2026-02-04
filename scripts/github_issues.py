#!/usr/bin/env python3
"""
سكريبت إدارة GitHub Issues لنظام AACS V0
"""
import sys
import os
import json
import argparse
from pathlib import Path

# إضافة المسار الجذر للمشروع
sys.path.append(str(Path(__file__).parent.parent))

from core.config import Config
from core.github_issues_manager import GitHubIssuesManager


def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(description='إدارة GitHub Issues لنظام AACS V0')
    parser.add_argument('--convert-board', action='store_true',
                       help='تحويل المهام من board/tasks.json إلى GitHub Issues')
    parser.add_argument('--create-labels', action='store_true',
                       help='إنشاء العلامات المطلوبة في المستودع')
    parser.add_argument('--list-issues', action='store_true',
                       help='عرض قائمة Issues الحالية')
    parser.add_argument('--generate-report', action='store_true',
                       help='توليد تقرير عن Issues')
    parser.add_argument('--update-status', type=str, nargs=2, metavar=('ISSUE_NUMBER', 'STATUS'),
                       help='تحديث حالة Issue (رقم Issue والحالة الجديدة)')
    parser.add_argument('--board-file', type=str, default='board/tasks.json',
                       help='مسار ملف board (افتراضي: board/tasks.json)')
    parser.add_argument('--output', '-o', type=str,
                       help='مسار ملف الإخراج للتقارير')
    parser.add_argument('--state', type=str, choices=['open', 'closed', 'all'], default='open',
                       help='حالة Issues المراد عرضها (افتراضي: open)')
    
    args = parser.parse_args()
    
    # إنشاء مدير GitHub Issues
    config = Config()
    github_manager = GitHubIssuesManager(config)
    
    print("📋 أداة إدارة GitHub Issues لنظام AACS V0")
    print("=" * 50)
    
    # التحقق من توفر GitHub Token
    if not os.getenv('GITHUB_TOKEN'):
        print("⚠️ تحذير: GITHUB_TOKEN غير متوفر. بعض الوظائف قد لا تعمل.")
        print("   يرجى إضافة GITHUB_TOKEN إلى متغيرات البيئة أو GitHub Secrets.")
        print()
    
    # إنشاء العلامات
    if args.create_labels:
        print("🏷️ إنشاء العلامات المطلوبة...")
        if github_manager.ensure_labels_exist():
            print("✅ تم إنشاء/تحديث العلامات بنجاح")
        else:
            print("❌ فشل في إنشاء العلامات")
    
    # تحويل المهام من board
    if args.convert_board:
        print(f"\n🔄 تحويل المهام من {args.board_file} إلى GitHub Issues...")
        
        if not Path(args.board_file).exists():
            print(f"❌ ملف board غير موجود: {args.board_file}")
            return
        
        results = github_manager.convert_tasks_from_board(args.board_file)
        
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        print(f"📊 نتائج التحويل:")
        print(f"   ✅ نجح: {successful}")
        print(f"   ❌ فشل: {failed}")
        
        if failed > 0:
            print("\n❌ المهام التي فشل تحويلها:")
            for i, result in enumerate(results):
                if not result.success:
                    print(f"   {i+1}. {result.error}")
        
        if successful > 0:
            print(f"\n✅ تم إنشاء {successful} Issue جديد في GitHub")
    
    # عرض قائمة Issues
    if args.list_issues:
        print(f"\n📋 قائمة Issues ({args.state})...")
        
        if args.state == 'all':
            open_issues = github_manager.get_repository_issues('open')
            closed_issues = github_manager.get_repository_issues('closed')
            all_issues = open_issues + closed_issues
        else:
            all_issues = github_manager.get_repository_issues(args.state)
        
        if not all_issues:
            print("   لا توجد Issues")
        else:
            print(f"   إجمالي Issues: {len(all_issues)}")
            print()
            
            # عرض أول 10 Issues
            for issue in all_issues[:10]:
                state_icon = "🟢" if issue['state'] == 'open' else "🔴"
                labels = [label['name'] for label in issue.get('labels', [])]
                aacs_label = "🤖" if any('aacs:' in label for label in labels) else ""
                
                print(f"   {state_icon} #{issue['number']} {aacs_label} {issue['title']}")
                if labels:
                    print(f"      🏷️ {', '.join(labels[:5])}")
                print()
            
            if len(all_issues) > 10:
                print(f"   ... و {len(all_issues) - 10} Issues أخرى")
    
    # تحديث حالة Issue
    if args.update_status:
        issue_number, new_status = args.update_status
        print(f"\n🔄 تحديث حالة Issue #{issue_number} إلى {new_status}...")
        
        try:
            issue_num = int(issue_number)
            if github_manager.update_issue_status(issue_num, new_status):
                print(f"✅ تم تحديث حالة Issue #{issue_num} بنجاح")
            else:
                print(f"❌ فشل في تحديث حالة Issue #{issue_num}")
        except ValueError:
            print("❌ رقم Issue غير صحيح")
    
    # توليد تقرير
    if args.generate_report:
        print("\n📊 توليد تقرير GitHub Issues...")
        report = github_manager.generate_issues_report()
        
        if 'error' in report:
            print(f"❌ فشل في توليد التقرير: {report['error']}")
        else:
            print(f"📈 ملخص التقرير:")
            print(f"   📋 إجمالي Issues: {report['total_issues']}")
            print(f"   🟢 مفتوحة: {report['open_issues']}")
            print(f"   🔴 مغلقة: {report['closed_issues']}")
            print(f"   🤖 Issues AACS: {report['aacs_issues']}")
            
            if report.get('agent_statistics'):
                print(f"\n👥 إحصائيات الوكلاء:")
                for agent, count in sorted(report['agent_statistics'].items(), 
                                         key=lambda x: x[1], reverse=True):
                    print(f"   - {agent}: {count}")
            
            if report.get('label_statistics'):
                print(f"\n🏷️ أكثر العلامات استخداماً:")
                sorted_labels = sorted(report['label_statistics'].items(), 
                                     key=lambda x: x[1], reverse=True)[:10]
                for label, count in sorted_labels:
                    print(f"   - {label}: {count}")
            
            # حفظ التقرير إذا طُلب ذلك
            if args.output:
                output_file = args.output if args.output.endswith('.json') else f"{args.output}_issues_report.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                print(f"\n💾 تم حفظ التقرير في: {output_file}")
    
    # إذا لم يتم تحديد أي خيار، اعرض المساعدة
    if not any([args.convert_board, args.create_labels, args.list_issues, 
               args.generate_report, args.update_status]):
        print("\n❓ لم يتم تحديد أي إجراء. استخدم --help لعرض الخيارات المتاحة.")
        print("\nأمثلة:")
        print("  python scripts/github_issues.py --create-labels")
        print("  python scripts/github_issues.py --convert-board")
        print("  python scripts/github_issues.py --list-issues --state all")
        print("  python scripts/github_issues.py --generate-report --output issues_report")
        print("  python scripts/github_issues.py --update-status 123 done")
    
    print("\n" + "=" * 50)
    print("✅ اكتملت عملية إدارة GitHub Issues")


if __name__ == "__main__":
    main()