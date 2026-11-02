from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from plugins.polio.api.shared_serializers import GroupSerializer
from plugins.polio.models import (
    CampaignScope,
    CampaignType,
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
