from rest_framework import serializers

from plugins.polio.api.shared_serializers import GroupSerializer
from plugins.polio.models import (
    Campaign,
    CampaignScope,
    CampaignType,
    Round,
)
from plugins.polio.preparedness.spreadsheet_manager import (
    Campaign,
)


class CampaignScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignScope
        fields = ["group", "vaccine"]

    group = GroupSerializer()


class CampaignTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignType
        fields = ["id", "name", "slug"]


class CampaignTypeIdAndNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignType
        fields = ["id", "name"]


class RoundDropdownOptionSerializer(serializers.ModelSerializer):
    """Only what a round select needs: `id` as value, `number` as label, `on_hold` to gate options."""

    class Meta:
        model = Round
        fields = ["id", "number", "on_hold"]


class CampaignDropdownOptionSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    rounds = RoundDropdownOptionSerializer(many=True, read_only=True)
    campaign_types = CampaignTypeIdAndNameSerializer(many=True, read_only=True)

    class Meta:
        model = Campaign
        fields = ["id", "obr_name", "created_at", "rounds", "campaign_types"]
