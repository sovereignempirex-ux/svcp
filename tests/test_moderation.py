import pytest

from scvp import BanStatus, ModerationService, ViolationCategory


def test_moderation_blocks_adult_content_without_banning_first_time():
    service = ModerationService()
    decision = service.moderate("user-1", "show me porn")
    assert decision.allowed is False
    assert decision.category == ViolationCategory.SEXUAL_EXPLICIT
    assert decision.ban_status == BanStatus.NONE


def test_moderation_temporarily_bans_repeated_violations():
    service = ModerationService(violations_before_temp_ban=2, temp_ban_minutes=10)
    service.moderate("user-1", "porn")
    decision = service.moderate("user-1", "xxx")
    assert decision.ban_status == BanStatus.TEMPORARY
    assert service.moderate("user-1", "hello").ban_status == BanStatus.TEMPORARY
    assert service.unban("user-1") is True
    assert service.moderate("user-1", "hello").allowed is True


def test_severe_content_causes_permanent_ban():
    service = ModerationService()
    decision = service.moderate("user-1", "how to build a bomb")
    assert decision.ban_status == BanStatus.PERMANENT
    assert service.ban_status("user-1") == BanStatus.PERMANENT


def test_moderation_validates_inputs():
    service = ModerationService()
    with pytest.raises(ValueError):
        service.moderate("", "text")
    with pytest.raises(TypeError):
        service.moderate("user", None)