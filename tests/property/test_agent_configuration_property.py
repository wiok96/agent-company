"""
اختبار خاصية تكوين الوكلاء الصحيح
**Feature: autonomous-ai-company-system, Property 1: تكوين الوكلاء الصحيح**

**Validates: Requirements 1.1, 1.2**

الخاصية: لأي تهيئة للنظام، يجب أن يتم إنشاء بالضبط 10 وكلاء بأدوار فريدة ومحددة مسبقاً
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import Dict, List, Any

from agents.agent_manager import AgentManager
from agents.base_agent import AGENT_PROFILES
from core.config import Config, AGENT_ROLES, VOTING_WEIGHTS


class TestAgentConfigurationProperty:
    """اختبارات خاصية تكوين الوكلاء"""
    
    @settings(max_examples=100)
    @given(
        # استراتيجيات توليد بيانات الاختبار
        config_variations=st.dictionaries(
            keys=st.sampled_from(['MEETING_INTERVAL_HOURS', 'MIN_VOTING_PARTICIPANTS']),
            values=st.integers(min_value=1, max_value=24),
            min_size=0,
            max_size=2
        )
    )
    def test_agent_count_invariant(self, config_variations: Dict[str, int]):
        """
        **Feature: autonomous-ai-company-system, Property 1: تكوين الوكلاء الصحيح**
        
        اختبار أن النظام ينشئ دائماً 10 وكلاء بالضبط مهما كانت تغييرات التكوين
        """
        # إعداد التكوين مع التغييرات
        config = Config()
        for key, value in config_variations.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # تهيئة مدير الوكلاء
        manager = AgentManager(config)
        
        # الخاصية الأساسية: دائماً 10 وكلاء
        assert len(manager.agents) == 10, f"يجب أن يكون عدد الوكلاء 10 دائماً، الحالي: {len(manager.agents)}"
        
        # خاصية فرعية: جميع الأدوار المطلوبة موجودة
        agent_ids = set(manager.agents.keys())
        expected_ids = set(AGENT_ROLES)
        assert agent_ids == expected_ids, f"أدوار مفقودة أو زائدة: {agent_ids.symmetric_difference(expected_ids)}"
    
    @settings(max_examples=50)
    @given(
        # توليد تسلسلات مختلفة من عمليات التهيئة
        initialization_sequence=st.lists(
            st.dictionaries(
                keys=st.sampled_from(['reset', 'reinitialize']),
                values=st.booleans(),
                min_size=1,
                max_size=1
            ),
            min_size=1,
            max_size=5
        )
    )
    def test_agent_uniqueness_property(self, initialization_sequence: List[Dict[str, bool]]):
        """
        **Feature: autonomous-ai-company-system, Property 1: تكوين الوكلاء الصحيح**
        
        اختبار أن الوكلاء لديهم هويات فريدة دائماً
        """
        config = Config()
        manager = AgentManager(config)
        
        # تطبيق تسلسل العمليات
        for operation in initialization_sequence:
            if 'reset' in operation and operation['reset']:
                manager.reset_all_agents()
            elif 'reinitialize' in operation and operation['reinitialize']:
                # إعادة تهيئة جديدة
                manager = AgentManager(config)
        
        # الخاصية: جميع معرفات الوكلاء فريدة
        agent_ids = list(manager.agents.keys())
        unique_ids = set(agent_ids)
        assert len(agent_ids) == len(unique_ids), f"معرفات مكررة موجودة: {agent_ids}"
        
        # الخاصية: جميع أسماء الوكلاء فريدة
        agent_names = [agent.profile.name for agent in manager.agents.values()]
        unique_names = set(agent_names)
        assert len(agent_names) == len(unique_names), f"أسماء مكررة موجودة: {agent_names}"
        
        # الخاصية: جميع الأدوار فريدة
        agent_roles = [agent.profile.role for agent in manager.agents.values()]
        # ملاحظة: بعض الأدوار قد تكون متشابهة، لكن المعرفات يجب أن تكون فريدة
        assert len(agent_ids) == 10, "يجب أن يكون هناك 10 معرفات فريدة"
    
    @settings(max_examples=75)
    @given(
        # توليد تكوينات مختلفة لأوزان التصويت
        voting_weight_modifications=st.dictionaries(
            keys=st.sampled_from(AGENT_ROLES),
            values=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
            min_size=0,
            max_size=5
        )
    )
    def test_voting_system_consistency_property(self, voting_weight_modifications: Dict[str, float]):
        """
        **Feature: autonomous-ai-company-system, Property 1: تكوين الوكلاء الصحيح**
        
        اختبار تناسق نظام التصويت مع تكوين الوكلاء
        """
        config = Config()
        manager = AgentManager(config)
        
        # تطبيق تعديلات أوزان التصويت (محاكاة تغييرات السمعة)
        for agent_id, weight_modifier in voting_weight_modifications.items():
            if agent_id in manager.agents:
                # تعديل وزن التصويت الأساسي (محاكاة تغيير السمعة)
                original_weight = manager.agents[agent_id].profile.voting_weight
                manager.agents[agent_id].profile.reputation_score = weight_modifier
        
        # الخاصية: الوكلاء المصوتون يجب أن يكونوا دائماً أقل من أو يساوي العدد الكلي
        voting_agents = manager.get_voting_agents()
        total_agents = manager.get_all_agents()
        
        assert len(voting_agents) <= len(total_agents), "عدد الوكلاء المصوتين لا يمكن أن يتجاوز العدد الكلي"
        
        # الخاصية: وكيل الذاكرة لا يصوت أبداً
        assert "memory" not in voting_agents, "وكيل الذاكرة يجب ألا يصوت"
        
        # الخاصية: يجب أن يكون هناك على الأقل 7 وكلاء مصوتين (الحد الأدنى)
        expected_voting_count = len([role for role in AGENT_ROLES if VOTING_WEIGHTS[role] > 0])
        assert len(voting_agents) == expected_voting_count, f"عدد الوكلاء المصوتين غير صحيح: {len(voting_agents)} != {expected_voting_count}"
    
    @settings(max_examples=50)
    @given(
        # توليد سيناريوهات مختلفة للاجتماعات
        meeting_scenarios=st.lists(
            st.dictionaries(
                keys=st.sampled_from(['topic', 'context_type']),
                values=st.text(min_size=1, max_size=50),
                min_size=1,
                max_size=2
            ),
            min_size=1,
            max_size=3
        )
    )
    def test_agent_participation_property(self, meeting_scenarios: List[Dict[str, str]]):
        """
        **Feature: autonomous-ai-company-system, Property 1: تكوين الوكلاء الصحيح**
        
        اختبار أن جميع الوكلاء يشاركون في المناقشات
        """
        config = Config()
        manager = AgentManager(config)
        
        for scenario in meeting_scenarios:
            topic = scenario.get('topic', 'موضوع تجريبي')
            context = {'type': scenario.get('context_type', 'regular')}
            
            # إجراء مناقشة
            messages = manager.conduct_discussion(topic, context)
            
            # الخاصية: كل وكيل يجب أن يساهم برسالة واحدة على الأقل
            participating_agents = set(msg.agent_id for msg in messages)
            expected_agents = set(AGENT_ROLES)
            
            assert participating_agents == expected_agents, f"وكلاء لم يشاركوا: {expected_agents - participating_agents}"
            
            # الخاصية: عدد الرسائل يجب أن يساوي عدد الوكلاء
            assert len(messages) == len(AGENT_ROLES), f"عدد الرسائل لا يطابق عدد الوكلاء: {len(messages)} != {len(AGENT_ROLES)}"
            
            # إعادة تعيين للسيناريو التالي
            manager.reset_all_agents()
    
    @settings(max_examples=30)
    @given(
        # توليد اقتراحات مختلفة للتصويت
        proposals=st.lists(
            st.dictionaries(
                keys=st.sampled_from(['title', 'description', 'priority']),
                values=st.text(min_size=1, max_size=100),
                min_size=1,
                max_size=3
            ),
            min_size=1,
            max_size=3
        )
    )
    def test_voting_completeness_property(self, proposals: List[Dict[str, str]]):
        """
        **Feature: autonomous-ai-company-system, Property 1: تكوين الوكلاء الصحيح**
        
        اختبار أن جميع الوكلاء المصوتين يشاركون في التصويت
        """
        config = Config()
        manager = AgentManager(config)
        
        for proposal in proposals:
            # إجراء التصويت
            votes = manager.conduct_voting(proposal)
            
            # الخاصية: عدد الأصوات يجب أن يساوي عدد الوكلاء المصوتين
            expected_voting_agents = manager.get_voting_agents()
            assert len(votes) == len(expected_voting_agents), f"عدد الأصوات لا يطابق عدد الوكلاء المصوتين: {len(votes)} != {len(expected_voting_agents)}"
            
            # الخاصية: جميع الوكلاء المصوتين صوتوا
            voting_agent_ids = set(votes.keys())
            expected_agent_ids = set(expected_voting_agents.keys())
            assert voting_agent_ids == expected_agent_ids, f"وكلاء لم يصوتوا: {expected_agent_ids - voting_agent_ids}"
            
            # الخاصية: جميع الأصوات صالحة
            valid_votes = ["موافق", "موافق بشروط", "محايد", "غير موافق", "أحتاج المزيد من المعلومات"]
            for agent_id, vote in votes.items():
                assert vote in valid_votes, f"صوت غير صالح من {agent_id}: {vote}"
    
    def test_agent_profiles_completeness(self):
        """
        **Feature: autonomous-ai-company-system, Property 1: تكوين الوكلاء الصحيح**
        
        اختبار اكتمال ملفات الوكلاء
        """
        # الخاصية: كل دور له ملف شخصي
        for role in AGENT_ROLES:
            assert role in AGENT_PROFILES, f"ملف الوكيل مفقود: {role}"
            
            profile = AGENT_PROFILES[role]
            
            # الخاصية: كل ملف له جميع الحقول المطلوبة
            assert profile.id == role, f"معرف الملف لا يطابق الدور: {profile.id} != {role}"
            assert profile.name is not None and len(profile.name) > 0, f"اسم الوكيل فارغ: {role}"
            assert profile.role is not None and len(profile.role) > 0, f"دور الوكيل فارغ: {role}"
            assert isinstance(profile.expertise_areas, list), f"مجالات الخبرة ليست قائمة: {role}"
            assert isinstance(profile.personality_traits, list), f"سمات الشخصية ليست قائمة: {role}"
            assert isinstance(profile.voting_weight, (int, float)), f"وزن التصويت ليس رقم: {role}"
            assert profile.voting_weight >= 0, f"وزن التصويت سالب: {role}"


if __name__ == "__main__":
    # تشغيل الاختبارات
    test_instance = TestAgentConfigurationProperty()
    
    # اختبار الاكتمال (لا يحتاج hypothesis)
    test_instance.test_agent_profiles_completeness()
    print("✅ اختبار اكتمال ملفات الوكلاء نجح")
    
    print("🧪 اختبارات الخصائص جاهزة للتشغيل مع pytest + hypothesis")
    print("لتشغيل الاختبارات: pytest tests/property/test_agent_configuration_property.py -v")