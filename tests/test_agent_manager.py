"""
اختبارات مدير الوكلاء
"""
import pytest
from agents.agent_manager import AgentManager
from agents.base_agent import AGENT_PROFILES
from core.config import Config, AGENT_ROLES


def test_agent_manager_initialization():
    """اختبار تهيئة مدير الوكلاء"""
    config = Config()
    manager = AgentManager(config)
    
    # التحقق من العدد الصحيح
    assert len(manager.agents) == 10, f"يجب أن يكون عدد الوكلاء 10، الحالي: {len(manager.agents)}"
    
    # التحقق من وجود جميع الأدوار
    for role in AGENT_ROLES:
        assert role in manager.agents, f"الدور مفقود: {role}"
    
    # التحقق من أن كل وكيل له ملف صحيح
    for agent_id, agent in manager.agents.items():
        assert agent.profile.id == agent_id
        assert agent.profile.name is not None
        assert agent.profile.role is not None
        assert isinstance(agent.profile.expertise_areas, list)
        assert agent.profile.voting_weight >= 0


def test_voting_agents():
    """اختبار الوكلاء المصوتين"""
    config = Config()
    manager = AgentManager(config)
    
    voting_agents = manager.get_voting_agents()
    
    # يجب أن يكون هناك 9 وكلاء مصوتين (memory لا يصوت)
    assert len(voting_agents) == 9, f"يجب أن يكون عدد الوكلاء المصوتين 9، الحالي: {len(voting_agents)}"
    
    # التحقق من أن memory غير موجود في المصوتين
    assert "memory" not in voting_agents, "وكيل الذاكرة يجب ألا يصوت"
    
    # التحقق من أن جميع الوكلاء الآخرين موجودين
    expected_voting_agents = [role for role in AGENT_ROLES if role != "memory"]
    for agent_id in expected_voting_agents:
        assert agent_id in voting_agents, f"الوكيل المصوت مفقود: {agent_id}"


def test_agent_profiles_consistency():
    """اختبار تناسق ملفات الوكلاء"""
    # التحقق من أن جميع الأدوار لها ملفات
    for role in AGENT_ROLES:
        assert role in AGENT_PROFILES, f"ملف الوكيل مفقود: {role}"
    
    # التحقق من أن جميع الملفات لها أدوار صحيحة
    for agent_id, profile in AGENT_PROFILES.items():
        assert agent_id in AGENT_ROLES, f"دور غير معروف: {agent_id}"
        assert profile.id == agent_id, f"معرف الملف لا يطابق المفتاح: {agent_id}"


def test_voting_simulation():
    """اختبار محاكاة التصويت"""
    config = Config()
    manager = AgentManager(config)
    
    # اقتراح تجريبي
    proposal = {
        "title": "مشروع تجريبي",
        "description": "وصف المشروع التجريبي"
    }
    
    # إجراء التصويت
    votes = manager.conduct_voting(proposal)
    
    # التحقق من النتائج
    assert len(votes) == 9, f"يجب أن يكون عدد الأصوات 9، الحالي: {len(votes)}"
    
    # التحقق من أن جميع الأصوات صالحة
    valid_votes = ["موافق", "موافق بشروط", "محايد", "غير موافق", "أحتاج المزيد من المعلومات"]
    for agent_id, vote in votes.items():
        assert vote in valid_votes, f"صوت غير صالح من {agent_id}: {vote}"
    
    # حساب النتيجة
    result = manager.calculate_voting_result(votes)
    
    assert "outcome" in result
    assert result["outcome"] in ["approved", "rejected"]
    assert "approval_percentage" in result
    assert 0 <= result["approval_percentage"] <= 100


def test_discussion_simulation():
    """اختبار محاكاة المناقشة"""
    config = Config()
    manager = AgentManager(config)
    
    topic = "تطوير أداة جديدة"
    context = {"meeting_type": "regular"}
    
    messages = manager.conduct_discussion(topic, context)
    
    # يجب أن تكون هناك رسالة من كل وكيل
    assert len(messages) == 10, f"يجب أن يكون عدد الرسائل 10، الحالي: {len(messages)}"
    
    # التحقق من أن الرسالة الأولى من رئيس الاجتماع
    assert messages[0].agent_id == "chair", "الرسالة الأولى يجب أن تكون من رئيس الاجتماع"
    
    # التحقق من أن كل وكيل ساهم
    agent_ids = [msg.agent_id for msg in messages]
    for role in AGENT_ROLES:
        assert role in agent_ids, f"الوكيل لم يساهم: {role}"


def test_self_reflection_generation():
    """اختبار توليد تقارير المراجعة الذاتية"""
    config = Config()
    manager = AgentManager(config)
    
    meeting_summary = {
        "session_id": "test_meeting",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    reflections = manager.generate_all_self_reflections(meeting_summary)
    
    # يجب أن يكون هناك تقرير من كل وكيل
    assert len(reflections) == 10, f"يجب أن يكون عدد التقارير 10، الحالي: {len(reflections)}"
    
    # التحقق من أن كل تقرير يحتوي على محتوى
    for agent_id, reflection in reflections.items():
        assert agent_id in AGENT_ROLES, f"وكيل غير معروف: {agent_id}"
        assert len(reflection) > 0, f"تقرير فارغ للوكيل: {agent_id}"
        assert "تقرير المراجعة الذاتية" in reflection, f"تقرير غير صحيح للوكيل: {agent_id}"


if __name__ == "__main__":
    # تشغيل الاختبارات
    test_agent_manager_initialization()
    test_voting_agents()
    test_agent_profiles_consistency()
    test_voting_simulation()
    test_discussion_simulation()
    test_self_reflection_generation()
    
    print("✅ جميع اختبارات مدير الوكلاء نجحت!")