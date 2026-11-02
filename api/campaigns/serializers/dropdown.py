from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from plugins.polio.api.campaigns.serializers.shared import CampaignTypeIdAndNameSerializer
from plugins.polio.models import (
    Campaign,
    Round,
)


VACCINE_LIST_SCHEMA = serializers.ListField(child=serializers.CharField(), read_only=True)


def single_vaccines_of(scopes, *, only_with_org_units: bool = False):
    vaccines = {
        scope.vaccine
        for scope in scopes
        if scope.vaccine and (not only_with_org_units or getattr(scope, "group_has_org_units", True))
    }
    return sorted(Campaign.split_combined_vaccines(vaccines))


class RoundDropdownOptionSerializer(serializers.ModelSerializer):
    vaccines = serializers.SerializerMethodField()
    has_scope = serializers.SerializerMethodField()

    class Meta:
        model = Round
        fields = ["id", "number", "on_hold", "started_at", "ended_at", "vaccines", "has_scope"]

    @extend_schema_field(serializers.BooleanField(read_only=True))
    def get_has_scope(self, round):
        return bool(round.scopes.all())

    @extend_schema_field(VACCINE_LIST_SCHEMA)
    def get_vaccines(self, round):
        if self.context.get("separate_scopes_per_round"):
            scopes = list(round.scopes.all())
        else:
            scopes = list(self.context.get("campaign_scopes", []))
        for sub_activity in round.sub_activities.all():
            scopes.extend(sub_activity.scopes.all())
        return single_vaccines_of(scopes, only_with_org_units=True)


class CampaignDropdownOptionSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    rounds = serializers.SerializerMethodField()
    campaign_types = CampaignTypeIdAndNameSerializer(many=True, read_only=True)
    vaccines = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            "id",
            "obr_name",
            "created_at",
            "rounds",
            "campaign_types",
            "vaccines",
            "separate_scopes_per_round",
        ]

    @extend_schema_field(RoundDropdownOptionSerializer(many=True))
    def get_rounds(self, campaign):
        return RoundDropdownOptionSerializer(
            campaign.rounds.all(),
            many=True,
            context={
                **self.context,
                "separate_scopes_per_round": campaign.separate_scopes_per_round,
                "campaign_scopes": list(campaign.scopes.all()),
            },
        ).data

    @extend_schema_field(VACCINE_LIST_SCHEMA)
    def get_vaccines(self, campaign):
        if campaign.separate_scopes_per_round:
            scopes = [scope for round in campaign.rounds.all() for scope in round.scopes.all()]
        else:
            scopes = list(campaign.scopes.all())
        return single_vaccines_of(scopes, only_with_org_units=True)
