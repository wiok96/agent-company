"""
مكتبة الإخفاقات الأساسية لـ AACS V0
نظام شامل لتوثيق وتحليل ومنع تكرار الإخفاقات
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .config import Config
from .logger import setup_logger, SecureLogger
from .memory import MemorySystem


class FailureSeverity(Enum):
    """مستويات خطورة الإخفاقات"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FailureCategory(Enum):
    """فئات الإخفاقات"""
    TECHNICAL = "technical"
    BUSINESS = "business"
    COMMUNICATION = "communication"
    PLANNING = "planning"
    EXECUTION = "execution"
    RESOURCE = "resource"
    MARKET = "market"
    UNKNOWN = "unknown"


@dataclass
class FailurePattern:
    """نمط إخفاق محدد"""
    id: str
    title: str
    description: str
    category: FailureCategory
    severity: FailureSeverity
    causes: List[str]
    symptoms: List[str]
    lessons_learned: List[str]
    prevention_strategies: List[str]
    occurrence_count: int
    first_occurrence: str
    last_occurrence: str
    related_keywords: List[str]
    examples: List[Dict[str, Any]]


@dataclass
class FailureAnalysis:
    """تحليل إخفاق محدد"""
    failure_id: str
    project_context: Dict[str, Any]
    root_causes: List[str]
    contributing_factors: List[str]
    impact_assessment: Dict[str, Any]
    similar_patterns: List[str]
    recommendations: List[str]
    confidence_score: float


class FailureLibrary:
    """مكتبة الإخفاقات الشاملة"""
    
    def __init__(self, config: Config, memory_system: MemorySystem):
        self.config = config
        self.memory_system = memory_system
        self.logger = SecureLogger(setup_logger("failure_library"))
        
        # مسارات التخزين
        self.base_path = Path("memory/failures")
        self.patterns_file = self.base_path / "patterns.json"
        self.analysis_path = self.base_path / "analysis"
        
        # إنشاء المجلدات
        self._ensure_directories()
        
        # تحميل الأنماط الموجودة
        self.failure_patterns = self._load_failure_patterns()
        
        # كلمات مفتاحية للكشف عن الإخفاقات
        self.failure_keywords = {
            "technical": ["خطأ", "عطل", "فشل", "مشكلة تقنية", "باغ", "crash", "error"],
            "business": ["خسارة", "فشل تجاري", "عدم ربحية", "منافسة", "سوق"],
            "communication": ["سوء فهم", "تواصل ضعيف", "عدم وضوح", "تضارب"],
            "planning": ["تخطيط سيء", "تقدير خاطئ", "جدولة", "موارد"],
            "execution": ["تنفيذ ضعيف", "تأخير", "جودة منخفضة", "أداء"],
            "resource": ["نقص موارد", "ميزانية", "وقت", "فريق"],
            "market": ["طلب منخفض", "منافسة شديدة", "توقيت سيء", "جمهور"]
        }
        
        self.logger.info("📚 تم تهيئة مكتبة الإخفاقات")
    
    def _ensure_directories(self):
        """إنشاء المجلدات المطلوبة"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.analysis_path.mkdir(parents=True, exist_ok=True)
    
    def _load_failure_patterns(self) -> Dict[str, FailurePattern]:
        """تحميل أنماط الإخفاقات الموجودة"""
        if not self.patterns_file.exists():
            return {}
        
        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                patterns_data = json.load(f)
            
            patterns = {}
            for pattern_id, pattern_data in patterns_data.items():
                # تحويل البيانات إلى كائن FailurePattern
                pattern_data['category'] = FailureCategory(pattern_data['category'])
                pattern_data['severity'] = FailureSeverity(pattern_data['severity'])
                patterns[pattern_id] = FailurePattern(**pattern_data)
            
            self.logger.info(f"📖 تم تحميل {len(patterns)} نمط إخفاق")
            return patterns
            
        except Exception as e:
            self.logger.error(f"فشل في تحميل أنماط الإخفاقات: {e}")
            return {}
    
    def _save_failure_patterns(self):
        """حفظ أنماط الإخفاقات"""
        try:
            patterns_data = {}
            for pattern_id, pattern in self.failure_patterns.items():
                pattern_dict = asdict(pattern)
                pattern_dict['category'] = pattern.category.value
                pattern_dict['severity'] = pattern.severity.value
                patterns_data[pattern_id] = pattern_dict
            
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(patterns_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 تم حفظ {len(patterns_data)} نمط إخفاق")
            
        except Exception as e:
            self.logger.error(f"فشل في حفظ أنماط الإخفاقات: {e}")
    
    def document_failure(self, failure_data: Dict[str, Any]) -> str:
        """توثيق إخفاق جديد وتحليله"""
        try:
            self.logger.info("📝 توثيق إخفاق جديد")
            
            # تحليل الإخفاق
            analysis = self._analyze_failure(failure_data)
            
            # البحث عن أنماط مشابهة
            similar_patterns = self._find_similar_patterns(failure_data)
            
            # إنشاء أو تحديث نمط الإخفاق
            pattern_id = self._create_or_update_pattern(failure_data, analysis, similar_patterns)
            
            # حفظ التحليل المفصل
            self._save_failure_analysis(analysis)
            
            # حفظ في نظام الذاكرة
            self.memory_system.store_failure({
                "pattern_id": pattern_id,
                "analysis": asdict(analysis),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "severity": analysis.impact_assessment.get("severity", "medium"),
                "category": self._categorize_failure(failure_data).value
            })
            
            self.logger.info(f"✅ تم توثيق الإخفاق: {pattern_id}")
            return pattern_id
            
        except Exception as e:
            self.logger.error(f"فشل في توثيق الإخفاق: {e}")
            return ""
    
    def _analyze_failure(self, failure_data: Dict[str, Any]) -> FailureAnalysis:
        """تحليل إخفاق محدد"""
        failure_id = f"failure_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # استخراج السياق
        project_context = failure_data.get("project_context", {})
        description = failure_data.get("description", "")
        
        # تحليل الأسباب الجذرية
        root_causes = self._extract_root_causes(description, project_context)
        
        # العوامل المساهمة
        contributing_factors = self._identify_contributing_factors(failure_data)
        
        # تقييم التأثير
        impact_assessment = self._assess_impact(failure_data)
        
        # البحث عن أنماط مشابهة
        similar_patterns = self._find_similar_patterns(failure_data)
        
        # توصيات
        recommendations = self._generate_recommendations(root_causes, contributing_factors)
        
        # درجة الثقة في التحليل
        confidence_score = self._calculate_confidence_score(failure_data, root_causes)
        
        return FailureAnalysis(
            failure_id=failure_id,
            project_context=project_context,
            root_causes=root_causes,
            contributing_factors=contributing_factors,
            impact_assessment=impact_assessment,
            similar_patterns=[p.id for p in similar_patterns],
            recommendations=recommendations,
            confidence_score=confidence_score
        )
    
    def _extract_root_causes(self, description: str, context: Dict[str, Any]) -> List[str]:
        """استخراج الأسباب الجذرية للإخفاق"""
        causes = []
        description_lower = description.lower()
        
        # تحليل النص للبحث عن مؤشرات الأسباب
        cause_indicators = {
            "تخطيط ضعيف": ["لم نخطط", "تخطيط سيء", "عدم تخطيط", "تقدير خاطئ"],
            "نقص الموارد": ["نقص وقت", "نقص ميزانية", "نقص فريق", "موارد قليلة"],
            "مشاكل تقنية": ["خطأ تقني", "مشكلة في الكود", "باغ", "عطل تقني"],
            "سوء التواصل": ["سوء فهم", "عدم وضوح", "تواصل ضعيف", "معلومات ناقصة"],
            "تغيير المتطلبات": ["تغيير المتطلبات", "متطلبات جديدة", "تعديل الخطة"],
            "منافسة السوق": ["منافس قوي", "سوق مشبع", "منافسة شديدة"],
            "مشاكل الفريق": ["خلافات الفريق", "نقص خبرة", "دوران الموظفين"]
        }
        
        for cause, indicators in cause_indicators.items():
            if any(indicator in description_lower for indicator in indicators):
                causes.append(cause)
        
        # تحليل السياق
        if context.get("budget_exceeded"):
            causes.append("تجاوز الميزانية")
        
        if context.get("timeline_exceeded"):
            causes.append("تجاوز الجدول الزمني")
        
        if context.get("team_size", 0) < context.get("required_team_size", 1):
            causes.append("نقص في حجم الفريق")
        
        return causes if causes else ["سبب غير محدد"]
    
    def _identify_contributing_factors(self, failure_data: Dict[str, Any]) -> List[str]:
        """تحديد العوامل المساهمة في الإخفاق"""
        factors = []
        
        # عوامل من البيانات المباشرة
        if failure_data.get("external_factors"):
            factors.extend(failure_data["external_factors"])
        
        # عوامل من السياق
        context = failure_data.get("project_context", {})
        
        if context.get("first_time_project"):
            factors.append("مشروع جديد - نقص الخبرة")
        
        if context.get("tight_deadline"):
            factors.append("جدول زمني ضيق")
        
        if context.get("complex_requirements"):
            factors.append("متطلبات معقدة")
        
        if context.get("limited_budget"):
            factors.append("ميزانية محدودة")
        
        return factors
    
    def _assess_impact(self, failure_data: Dict[str, Any]) -> Dict[str, Any]:
        """تقييم تأثير الإخفاق"""
        impact = {
            "financial_loss": failure_data.get("financial_impact", 0),
            "time_lost_hours": failure_data.get("time_impact", 0),
            "reputation_impact": failure_data.get("reputation_impact", "low"),
            "team_morale_impact": failure_data.get("morale_impact", "medium"),
            "learning_value": "high",  # كل إخفاق له قيمة تعليمية
            "severity": self._determine_severity(failure_data).value
        }
        
        # حساب التأثير الإجمالي
        total_impact_score = 0
        
        if impact["financial_loss"] > 1000:
            total_impact_score += 3
        elif impact["financial_loss"] > 100:
            total_impact_score += 2
        elif impact["financial_loss"] > 0:
            total_impact_score += 1
        
        if impact["time_lost_hours"] > 40:
            total_impact_score += 3
        elif impact["time_lost_hours"] > 8:
            total_impact_score += 2
        elif impact["time_lost_hours"] > 0:
            total_impact_score += 1
        
        impact["total_impact_score"] = total_impact_score
        
        return impact
    
    def _determine_severity(self, failure_data: Dict[str, Any]) -> FailureSeverity:
        """تحديد مستوى خطورة الإخفاق"""
        financial_impact = failure_data.get("financial_impact", 0)
        time_impact = failure_data.get("time_impact", 0)
        reputation_impact = failure_data.get("reputation_impact", "low")
        
        # حساب النقاط
        severity_score = 0
        
        if financial_impact > 5000:
            severity_score += 4
        elif financial_impact > 1000:
            severity_score += 3
        elif financial_impact > 100:
            severity_score += 2
        elif financial_impact > 0:
            severity_score += 1
        
        if time_impact > 80:
            severity_score += 3
        elif time_impact > 40:
            severity_score += 2
        elif time_impact > 8:
            severity_score += 1
        
        if reputation_impact == "high":
            severity_score += 3
        elif reputation_impact == "medium":
            severity_score += 2
        elif reputation_impact == "low":
            severity_score += 1
        
        # تحديد المستوى
        if severity_score >= 8:
            return FailureSeverity.CRITICAL
        elif severity_score >= 5:
            return FailureSeverity.HIGH
        elif severity_score >= 2:
            return FailureSeverity.MEDIUM
        else:
            return FailureSeverity.LOW
    
    def _categorize_failure(self, failure_data: Dict[str, Any]) -> FailureCategory:
        """تصنيف الإخفاق"""
        description = failure_data.get("description", "").lower()
        
        # البحث في الكلمات المفتاحية
        category_mapping = {
            "technical": FailureCategory.TECHNICAL,
            "business": FailureCategory.BUSINESS,
            "communication": FailureCategory.COMMUNICATION,
            "planning": FailureCategory.PLANNING,
            "execution": FailureCategory.EXECUTION,
            "resource": FailureCategory.RESOURCE,
            "market": FailureCategory.MARKET
        }
        
        for category, keywords in self.failure_keywords.items():
            if any(keyword in description for keyword in keywords):
                return category_mapping.get(category, FailureCategory.UNKNOWN)
        
        # تصنيف بناءً على السياق
        context = failure_data.get("project_context", {})
        
        if context.get("technical_project"):
            return FailureCategory.TECHNICAL
        elif context.get("business_project"):
            return FailureCategory.BUSINESS
        
        return FailureCategory.UNKNOWN
    
    def _find_similar_patterns(self, failure_data: Dict[str, Any]) -> List[FailurePattern]:
        """البحث عن أنماط إخفاق مشابهة"""
        similar_patterns = []
        description = failure_data.get("description", "").lower()
        category = self._categorize_failure(failure_data)
        
        for pattern in self.failure_patterns.values():
            similarity_score = 0
            
            # مطابقة الفئة
            if pattern.category == category:
                similarity_score += 3
            
            # مطابقة الكلمات المفتاحية
            for keyword in pattern.related_keywords:
                if keyword.lower() in description:
                    similarity_score += 1
            
            # مطابقة الأعراض
            for symptom in pattern.symptoms:
                if symptom.lower() in description:
                    similarity_score += 2
            
            # إضافة الأنماط المشابهة
            if similarity_score >= 3:
                similar_patterns.append(pattern)
        
        # ترتيب حسب التشابه
        return sorted(similar_patterns, 
                     key=lambda p: self._calculate_similarity_score(p, failure_data), 
                     reverse=True)[:5]
    
    def _calculate_similarity_score(self, pattern: FailurePattern, failure_data: Dict[str, Any]) -> float:
        """حساب درجة التشابه بين نمط وإخفاق"""
        score = 0.0
        description = failure_data.get("description", "").lower()
        
        # مطابقة الفئة (وزن عالي)
        if pattern.category == self._categorize_failure(failure_data):
            score += 0.4
        
        # مطابقة الكلمات المفتاحية
        keyword_matches = sum(1 for keyword in pattern.related_keywords 
                            if keyword.lower() in description)
        if pattern.related_keywords:
            score += 0.3 * (keyword_matches / len(pattern.related_keywords))
        
        # مطابقة الأعراض
        symptom_matches = sum(1 for symptom in pattern.symptoms 
                            if symptom.lower() in description)
        if pattern.symptoms:
            score += 0.3 * (symptom_matches / len(pattern.symptoms))
        
        return score
    
    def _generate_recommendations(self, root_causes: List[str], 
                                contributing_factors: List[str]) -> List[str]:
        """توليد توصيات بناءً على التحليل"""
        recommendations = []
        
        # توصيات بناءً على الأسباب الجذرية
        cause_recommendations = {
            "تخطيط ضعيف": [
                "تطوير عملية تخطيط أكثر تفصيلاً",
                "استخدام أدوات إدارة المشاريع",
                "إشراك خبراء في مرحلة التخطيط"
            ],
            "نقص الموارد": [
                "تحسين تقدير الموارد المطلوبة",
                "إنشاء احتياطي للموارد الطارئة",
                "تطوير شراكات لتوفير موارد إضافية"
            ],
            "مشاكل تقنية": [
                "تحسين عمليات الاختبار والجودة",
                "استثمار في التدريب التقني",
                "إنشاء نظام مراجعة الكود"
            ],
            "سوء التواصل": [
                "تحسين قنوات التواصل",
                "إنشاء وثائق واضحة ومفصلة",
                "عقد اجتماعات دورية للمتابعة"
            ]
        }
        
        for cause in root_causes:
            if cause in cause_recommendations:
                recommendations.extend(cause_recommendations[cause])
        
        # توصيات عامة
        recommendations.extend([
            "توثيق الدروس المستفادة",
            "مراجعة العمليات الحالية",
            "تطوير خطة منع تكرار المشكلة"
        ])
        
        return list(set(recommendations))  # إزالة التكرار
    
    def _calculate_confidence_score(self, failure_data: Dict[str, Any], 
                                  root_causes: List[str]) -> float:
        """حساب درجة الثقة في التحليل"""
        confidence = 0.5  # قيمة أساسية
        
        # زيادة الثقة بناءً على جودة البيانات
        if failure_data.get("description") and len(failure_data["description"]) > 50:
            confidence += 0.2
        
        if failure_data.get("project_context"):
            confidence += 0.1
        
        if failure_data.get("financial_impact") is not None:
            confidence += 0.1
        
        if len(root_causes) > 1:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def validate_idea_against_failures(self, idea_data: Dict[str, Any]) -> Dict[str, Any]:
        """فحص فكرة جديدة مقابل الإخفاقات السابقة"""
        try:
            self.logger.info("🔍 فحص الفكرة مقابل الإخفاقات السابقة")
            
            idea_description = idea_data.get("description", "").lower()
            idea_category = idea_data.get("category", "")
            
            # البحث عن إخفاقات مشابهة
            similar_failures = []
            risk_factors = []
            warnings = []
            
            for pattern in self.failure_patterns.values():
                similarity_score = 0
                
                # مطابقة الكلمات المفتاحية
                for keyword in pattern.related_keywords:
                    if keyword.lower() in idea_description:
                        similarity_score += 1
                
                # مطابقة الفئة
                if pattern.category.value in idea_category.lower():
                    similarity_score += 2
                
                # إضافة الإخفاقات المشابهة
                if similarity_score >= 2:
                    similar_failures.append({
                        "pattern_id": pattern.id,
                        "title": pattern.title,
                        "similarity_score": similarity_score,
                        "occurrence_count": pattern.occurrence_count,
                        "severity": pattern.severity.value,
                        "main_causes": pattern.causes[:3],
                        "prevention_strategies": pattern.prevention_strategies[:3]
                    })
            
            # تحليل عوامل الخطر
            for failure in similar_failures:
                if failure["occurrence_count"] > 2:
                    risk_factors.append(f"نمط متكرر: {failure['title']}")
                
                if failure["severity"] in ["high", "critical"]:
                    warnings.append(f"خطر عالي: {failure['title']}")
            
            # تقييم المخاطر الإجمالية
            risk_level = "low"
            if len(warnings) > 0:
                risk_level = "high"
            elif len(similar_failures) > 2:
                risk_level = "medium"
            
            # توصيات
            recommendations = []
            if similar_failures:
                recommendations.append("مراجعة الإخفاقات المشابهة قبل البدء")
                recommendations.append("تطبيق استراتيجيات المنع المحددة")
                
                # جمع أهم استراتيجيات المنع
                all_strategies = []
                for failure in similar_failures:
                    all_strategies.extend(failure["prevention_strategies"])
                
                # أكثر الاستراتيجيات تكراراً
                strategy_counts = {}
                for strategy in all_strategies:
                    strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
                
                top_strategies = sorted(strategy_counts.items(), 
                                      key=lambda x: x[1], reverse=True)[:3]
                
                for strategy, count in top_strategies:
                    recommendations.append(f"تطبيق: {strategy}")
            
            validation_result = {
                "risk_level": risk_level,
                "similar_failures_count": len(similar_failures),
                "similar_failures": similar_failures,
                "risk_factors": risk_factors,
                "warnings": warnings,
                "recommendations": recommendations,
                "validation_timestamp": datetime.now(timezone.utc).isoformat(),
                "should_proceed": len(warnings) == 0,
                "confidence_score": min(0.9, 0.5 + (len(similar_failures) * 0.1))
            }
            
            self.logger.info(f"✅ تم فحص الفكرة - مستوى المخاطر: {risk_level}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"فشل في فحص الفكرة: {e}")
            return {
                "risk_level": "unknown",
                "error": str(e),
                "should_proceed": True,
                "confidence_score": 0.0
            }
    
    def search_failures(self, query: str, category: Optional[FailureCategory] = None,
                       severity: Optional[FailureSeverity] = None,
                       limit: int = 10) -> List[FailurePattern]:
        """البحث في مكتبة الإخفاقات"""
        try:
            results = []
            query_lower = query.lower()
            
            for pattern in self.failure_patterns.values():
                # فلترة حسب الفئة والخطورة
                if category and pattern.category != category:
                    continue
                
                if severity and pattern.severity != severity:
                    continue
                
                # البحث في المحتوى
                score = 0
                
                if query_lower in pattern.title.lower():
                    score += 3
                
                if query_lower in pattern.description.lower():
                    score += 2
                
                for keyword in pattern.related_keywords:
                    if query_lower in keyword.lower():
                        score += 1
                
                for cause in pattern.causes:
                    if query_lower in cause.lower():
                        score += 2
                
                if score > 0:
                    results.append((pattern, score))
            
            # ترتيب النتائج حسب النقاط
            results.sort(key=lambda x: x[1], reverse=True)
            
            return [pattern for pattern, score in results[:limit]]
            
        except Exception as e:
            self.logger.error(f"فشل في البحث: {e}")
            return []
    
    def _create_or_update_pattern(self, failure_data: Dict[str, Any], 
                                analysis: FailureAnalysis, 
                                similar_patterns: List[FailurePattern]) -> str:
        """إنشاء أو تحديث نمط إخفاق"""
        
        # البحث عن نمط مطابق تماماً
        exact_match = None
        for pattern in similar_patterns:
            if self._calculate_similarity_score(pattern, failure_data) > 0.8:
                exact_match = pattern
                break
        
        if exact_match:
            # تحديث النمط الموجود
            exact_match.occurrence_count += 1
            exact_match.last_occurrence = datetime.now(timezone.utc).isoformat()
            exact_match.examples.append({
                "failure_id": analysis.failure_id,
                "description": failure_data.get("description", ""),
                "context": failure_data.get("project_context", {}),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # تحديث الدروس المستفادة
            for lesson in analysis.recommendations:
                if lesson not in exact_match.lessons_learned:
                    exact_match.lessons_learned.append(lesson)
            
            pattern_id = exact_match.id
            
        else:
            # إنشاء نمط جديد
            pattern_id = f"pattern_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            new_pattern = FailurePattern(
                id=pattern_id,
                title=self._generate_pattern_title(failure_data),
                description=failure_data.get("description", "")[:200] + "...",
                category=self._categorize_failure(failure_data),
                severity=self._determine_severity(failure_data),
                causes=analysis.root_causes,
                symptoms=self._extract_symptoms(failure_data),
                lessons_learned=analysis.recommendations,
                prevention_strategies=self._generate_prevention_strategies(analysis),
                occurrence_count=1,
                first_occurrence=datetime.now(timezone.utc).isoformat(),
                last_occurrence=datetime.now(timezone.utc).isoformat(),
                related_keywords=self._extract_keywords(failure_data),
                examples=[{
                    "failure_id": analysis.failure_id,
                    "description": failure_data.get("description", ""),
                    "context": failure_data.get("project_context", {}),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }]
            )
            
            self.failure_patterns[pattern_id] = new_pattern
        
        # حفظ الأنماط المحدثة
        self._save_failure_patterns()
        
        return pattern_id
    
    def _generate_pattern_title(self, failure_data: Dict[str, Any]) -> str:
        """توليد عنوان للنمط"""
        category = self._categorize_failure(failure_data)
        description = failure_data.get("description", "")
        
        # استخراج الكلمات المفتاحية
        keywords = self._extract_keywords(failure_data)
        main_keyword = keywords[0] if keywords else "مشكلة"
        
        return f"إخفاق {category.value}: {main_keyword}"
    
    def _extract_symptoms(self, failure_data: Dict[str, Any]) -> List[str]:
        """استخراج أعراض الإخفاق"""
        symptoms = []
        description = failure_data.get("description", "").lower()
        
        # أعراض شائعة
        symptom_patterns = {
            "انخفاض الأداء": ["بطء", "أداء ضعيف", "استجابة بطيئة"],
            "أخطاء متكررة": ["خطأ متكرر", "مشاكل مستمرة", "أعطال متتالية"],
            "عدم رضا المستخدمين": ["شكاوى", "عدم رضا", "تقييمات سلبية"],
            "تجاوز الميزانية": ["تكلفة إضافية", "تجاوز الميزانية", "نفقات زائدة"],
            "تأخير في التسليم": ["تأخير", "عدم التزام بالمواعيد", "تأجيل"]
        }
        
        for symptom, patterns in symptom_patterns.items():
            if any(pattern in description for pattern in patterns):
                symptoms.append(symptom)
        
        return symptoms if symptoms else ["أعراض غير محددة"]
    
    def _extract_keywords(self, failure_data: Dict[str, Any]) -> List[str]:
        """استخراج الكلمات المفتاحية"""
        description = failure_data.get("description", "")
        
        # كلمات مفتاحية شائعة
        common_keywords = [
            "تطبيق", "موقع", "نظام", "أداة", "برنامج", "خدمة",
            "مشروع", "تطوير", "تصميم", "تسويق", "بيع"
        ]
        
        keywords = []
        for keyword in common_keywords:
            if keyword in description:
                keywords.append(keyword)
        
        # إضافة كلمات من السياق
        context = failure_data.get("project_context", {})
        if context.get("project_type"):
            keywords.append(context["project_type"])
        
        return keywords[:5]  # أول 5 كلمات مفتاحية
    
    def _generate_prevention_strategies(self, analysis: FailureAnalysis) -> List[str]:
        """توليد استراتيجيات المنع"""
        strategies = []
        
        # استراتيجيات بناءً على الأسباب الجذرية
        for cause in analysis.root_causes:
            if "تخطيط" in cause:
                strategies.append("تطبيق منهجية تخطيط صارمة")
            elif "موارد" in cause:
                strategies.append("تحسين تقدير وإدارة الموارد")
            elif "تقني" in cause:
                strategies.append("تعزيز عمليات الاختبار والمراجعة")
            elif "تواصل" in cause:
                strategies.append("تحسين آليات التواصل والتوثيق")
        
        # استراتيجيات عامة
        strategies.extend([
            "إجراء مراجعات دورية للمخاطر",
            "تطوير خطط طوارئ",
            "تحسين عمليات المراقبة والتتبع"
        ])
        
        return list(set(strategies))
    
    def _save_failure_analysis(self, analysis: FailureAnalysis):
        """حفظ تحليل الإخفاق المفصل"""
        try:
            analysis_file = self.analysis_path / f"{analysis.failure_id}.json"
            
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(analysis), f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 تم حفظ تحليل الإخفاق: {analysis.failure_id}")
            
        except Exception as e:
            self.logger.error(f"فشل في حفظ تحليل الإخفاق: {e}")
    
    def get_failure_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الإخفاقات"""
        try:
            total_patterns = len(self.failure_patterns)
            
            if total_patterns == 0:
                return {
                    "total_patterns": 0,
                    "total_occurrences": 0,
                    "message": "لا توجد أنماط إخفاق مسجلة"
                }
            
            # إحصائيات الفئات
            category_stats = {}
            severity_stats = {}
            total_occurrences = 0
            
            for pattern in self.failure_patterns.values():
                # إحصائيات الفئات
                category = pattern.category.value
                category_stats[category] = category_stats.get(category, 0) + 1
                
                # إحصائيات الخطورة
                severity = pattern.severity.value
                severity_stats[severity] = severity_stats.get(severity, 0) + 1
                
                # إجمالي التكرارات
                total_occurrences += pattern.occurrence_count
            
            # أكثر الأنماط تكراراً
            most_common = sorted(self.failure_patterns.values(), 
                               key=lambda p: p.occurrence_count, reverse=True)[:5]
            
            # الأنماط الأخيرة
            recent_patterns = sorted(self.failure_patterns.values(), 
                                   key=lambda p: p.last_occurrence, reverse=True)[:5]
            
            return {
                "total_patterns": total_patterns,
                "total_occurrences": total_occurrences,
                "average_occurrences": round(total_occurrences / total_patterns, 2),
                "category_distribution": category_stats,
                "severity_distribution": severity_stats,
                "most_common_patterns": [
                    {
                        "id": p.id,
                        "title": p.title,
                        "occurrences": p.occurrence_count,
                        "severity": p.severity.value
                    } for p in most_common
                ],
                "recent_patterns": [
                    {
                        "id": p.id,
                        "title": p.title,
                        "last_occurrence": p.last_occurrence,
                        "severity": p.severity.value
                    } for p in recent_patterns
                ]
            }
            
        except Exception as e:
            self.logger.error(f"فشل في حساب إحصائيات الإخفاقات: {e}")
            return {"error": str(e)}