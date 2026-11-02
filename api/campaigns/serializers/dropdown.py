from rest_framework import serializers

from plugins.polio.api.campaigns.serializers.shared import CampaignTypeIdAndNameSerializer
from plugins.polio.models import (
    Campaign,
    Round,
)
from plugins.polio.preparedness.spreadsheet_manager import (
    Campaign,
)


class RoundDropdownOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Round
        fields = ["id", "number", "on_hold", "started_at"]


class CampaignDropdownOptionSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    rounds = RoundDropdownOptionSerializer(many=True, read_only=True)
    campaign_types = CampaignTypeIdAndNameSerializer(many=True, read_only=True)

    class Meta:
        model = Campaign
        fields = ["id", "obr_name", "rounds", "campaign_types"]
