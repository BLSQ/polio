from django.shortcuts import get_object_or_404
from rest_framework import serializers

from iaso.models import Group
from plugins.polio.api.shared_serializers import GroupSerializer
from plugins.polio.models import Round, SubActivity, SubActivityScope
from plugins.polio.models.base import VACCINES_BY_VIRUS, invalid_vaccines_for_virus


class SubActivityScopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubActivityScope
        fields = ["group", "vaccine"]

    group = GroupSerializer(required=False)


class SubActivityCreateUpdateSerializer(serializers.ModelSerializer):
    round_number = serializers.IntegerField(write_only=True, required=False)
    campaign = serializers.CharField(write_only=True, required=False)
    scopes = SubActivityScopeSerializer(many=True, required=False)

    class Meta:
        model = SubActivity
        fields = [
            "id",
            "round_number",
            "campaign",
            "name",
            "start_date",
            "end_date",
            "scopes",
            "age_unit",
            "age_min",
            "age_max",
            "lqas_ended_at",
            "lqas_started_at",
            "im_ended_at",
            "im_started_at",
        ]

    def _campaign_under_edit(self, data):
        """The campaign this sub-activity belongs to, on create as well as on update."""
        if self.instance is not None:
            return self.instance.round.campaign
        campaign = data.get("campaign")
        round_number = data.get("round_number")
        if campaign is None or round_number is None:
            return None
        the_round = Round.objects.filter(campaign__obr_name=campaign, number=round_number).first()
        return the_round.campaign if the_round else None

    def validate(self, attrs):
        data = super().validate(attrs)
        campaign = self._campaign_under_edit(data)
        if campaign is None:
            return data

        stored_vaccines = set(self.instance.scopes.values_list("vaccine", flat=True)) if self.instance else set()
        submitted_vaccines = {scope["vaccine"] for scope in (data.get("scopes") or []) if scope.get("vaccine")}
        invalid_vaccines = invalid_vaccines_for_virus(campaign.virus, submitted_vaccines - stored_vaccines)
        if invalid_vaccines:
            raise serializers.ValidationError(
                f"Vaccine(s) {', '.join(invalid_vaccines)} cannot be used for virus {campaign.virus}. "
                f"Allowed: {', '.join(VACCINES_BY_VIRUS[campaign.virus])}"
            )
        return data

    def create(self, validated_data):
        round_number = validated_data.pop("round_number", None)
        campaign = validated_data.pop("campaign", None)
        scopes_data = validated_data.pop("scopes", [])

        if round_number is not None and campaign is not None:
            the_round = get_object_or_404(Round, campaign__obr_name=campaign, number=round_number)
            validated_data["round"] = the_round

            if self.context["request"].user.iaso_profile.account != the_round.campaign.account:
                raise serializers.ValidationError(
                    "You do not have permission to create a SubActivity for this Campaign."
                )

        else:
            raise serializers.ValidationError("Both round_number and campaign must be provided.")

        sub_activity = super().create(validated_data)
        org_units_in_parent_rnd_scope = sub_activity.round.actual_scopes.all().values_list(
            "group__org_units__id", flat=True
        )

        for scope_data in scopes_data:
            group_data = scope_data.pop("group")
            group_data["source_version"] = self.context["request"].user.iaso_profile.account.default_version
            group_org_units = group_data.pop("org_units", [])
            eligible_group_org_units = [
                org_unit for org_unit in group_org_units if org_unit.id in org_units_in_parent_rnd_scope
            ]
            group = Group.objects.create(**group_data)
            group.org_units.set(eligible_group_org_units)
            new_scope = SubActivityScope.objects.create(subactivity=sub_activity, group=group, **scope_data)
            group.name = f"scope {new_scope.id} for sub-activity {sub_activity.id} for round {round_number} of campaign {campaign}"
            group.save()

        return sub_activity

    def update(self, instance, validated_data):
        scopes_data = validated_data.pop("scopes", None)

        if scopes_data is not None:
            # Get the groups associated with the current scopes
            groups_to_check = [scope.group for scope in instance.scopes.all()]

            # Delete the scopes
            instance.scopes.all().delete()

            # Check if the groups are used by any other SubActivityScope
            for group in groups_to_check:
                if not SubActivityScope.objects.filter(group=group).exists():
                    group.delete()
            org_units_in_parent_rnd_scope = instance.round.actual_scopes.all().values_list(
                "group__org_units__id", flat=True
            )
            for scope_data in scopes_data:
                group_data = scope_data.pop("group")
                group_data["source_version"] = self.context["request"].user.iaso_profile.account.default_version
                group_org_units = group_data.pop("org_units", [])
                # We need to make this check here because
                eligible_group_org_units = [
                    org_unit for org_unit in group_org_units if org_unit.id in org_units_in_parent_rnd_scope
                ]
                group = Group.objects.create(**group_data)
                group.org_units.set(eligible_group_org_units)
                SubActivityScope.objects.create(subactivity=instance, group=group, **scope_data)

        return super().update(instance, validated_data)


class SubActivityListDetailSerializer(serializers.ModelSerializer):
    round_id = serializers.IntegerField(source="round.id", read_only=True)
    scopes = SubActivityScopeSerializer(many=True)

    class Meta:
        model = SubActivity
        fields = [
            "id",
            "round_id",
            "name",
            "start_date",
            "end_date",
            "scopes",
            "age_unit",
            "age_min",
            "age_max",
            "lqas_ended_at",
            "lqas_started_at",
            "im_ended_at",
            "im_started_at",
        ]
