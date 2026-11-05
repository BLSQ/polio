import { useMemo } from 'react';
import {
    UrlParams,
    renderTagsWithTooltip,
    textPlaceholder,
} from 'bluesquare-components';
import moment from 'moment';
import { UseMutationResult, UseQueryResult } from 'react-query';
import { openSnackBar } from '../../../../../../../../../hat/assets/js/apps/Iaso/components/snackBars/EventDispatcher';
import {
    errorSnackBar,
    succesfullSnackBar,
} from '../../../../../../../../../hat/assets/js/apps/Iaso/constants/snackBars';
import { OrgUnit } from '../../../../../../../../../hat/assets/js/apps/Iaso/domains/orgUnits/types/orgUnit';
import {
    FormattedApiParams,
    useApiParams,
} from '../../../../../../../../../hat/assets/js/apps/Iaso/hooks/useApiParams';
import { useUrlParams } from '../../../../../../../../../hat/assets/js/apps/Iaso/hooks/useUrlParams';
import {
    deleteRequest,
    getRequest,
    iasoFetch,
} from '../../../../../../../../../hat/assets/js/apps/Iaso/libs/Api';
import {
    useSnackMutation,
    useSnackQuery,
} from '../../../../../../../../../hat/assets/js/apps/Iaso/libs/apiHooks';
import { PostArg } from '../../../../../../../../../hat/assets/js/apps/Iaso/types/general';
import {
    DropdownOptions,
    DropdownOptionsWithOriginal,
    Optional,
} from '../../../../../../../../../hat/assets/js/apps/Iaso/types/utils';
import { dateApiToDateRangePicker } from '../../../../../../../../../hat/assets/js/apps/Iaso/utils/dates';
import { Campaign, Round } from '../../../../../constants/types';
import { useGetCountries } from '../../../../../hooks/useGetCountries';
import { orderCampaignsByEarliestRoundStartTimestamp } from '../../../../../utils';
import {
    CAMPAIGNS_ENDPOINT,
    CampaignCategory,
    Options,
    useGetCampaigns,
} from '../../../../Campaigns/hooks/api/useGetCampaigns';
import {
    CampaignDropdownRound,
    useGetCampaignsDropdown,
} from '../../../../Campaigns/hooks/api/useGetCampaignsDropdown';
import {
    apiUrl,
    fipvVaccineOptions,
    singleVaccinesList,
} from '../../constants';
import MESSAGES from '../../messages';
import {
    CampaignDropdowns,
    ParsedSettledPromise,
    VRF,
    VRFFormData,
} from '../../types';

const defaults = {
    order: '-start_date',
    pageSize: 20,
    page: 1,
};
const getVrfList = (
    params: FormattedApiParams,
): Promise<{ results: VRF[] }> => {
    const queryString = new URLSearchParams(params).toString();
    return getRequest(`${apiUrl}?${queryString}`);
};

export const useGetVrfList = (
    params: Partial<UrlParams>,
): UseQueryResult<any, any> => {
    const safeParams = useUrlParams(params, defaults);
    const apiParams = useApiParams(safeParams);
    return useSnackQuery({
        queryKey: [
            'getVrfList',
            apiParams,
            apiParams.page,
            apiParams.limit,
            apiParams.order,
        ],
        queryFn: () => getVrfList(apiParams),
        options: {
            select: data => {
                if (!data) return { results: [] };
                return data;
            },
            keepPreviousData: true,
            staleTime: 1000 * 60 * 15, // in MS
            cacheTime: 1000 * 60 * 5,
        },
    });
};

export const useGetVrfListByRound = (
    roundId: string,
): UseQueryResult<any, any> => {
    const apiParams = useApiParams({ round_id: roundId });
    return useSnackQuery({
        queryKey: ['getVrfListByRound', roundId],
        queryFn: () => getVrfList(apiParams),
        options: {
            select: data => {
                if (!data) return [];
                return data.results;
            },
            keepPreviousData: false,
            staleTime: 1000 * 60 * 15, // in MS
            cacheTime: 1000 * 60 * 5,
            enabled: Boolean(roundId),
        },
    });
};

const deleteVrf = (id: string) => {
    return deleteRequest(`${apiUrl}${id}`);
};

export const useDeleteVrf = (): UseMutationResult => {
    return useSnackMutation({
        mutationFn: deleteVrf,
        invalidateQueryKey: ['getVrfList'],
    });
};

export const useGetCountriesOptions = (
    enabled = true,
    groupId?: string,
): { data: DropdownOptions<number>[]; isFetching: boolean } => {
    const { data: countries, isFetching } = useGetCountries(
        'VALID',
        enabled,
        groupId,
    );
    return useMemo(() => {
        const options = countries
            ? countries.orgUnits.map((country: OrgUnit) => {
                  return {
                      label: country.name,
                      value: country.id,
                  };
              })
            : [];
        return { data: options, isFetching };
    }, [countries, isFetching]);
};

type UseCampaignDropdownsParams = {
    countryId?: number;
    campaign?: string;
    vaccine?: string;
    rounds?: number;
};

export const useCampaignDropDowns = ({
    countryId,
    campaign,
    vaccine,
    rounds: rndsParams,
}: UseCampaignDropdownsParams): CampaignDropdowns => {
    const options: Options = {
        enabled: Boolean(countryId),
        countries: Number.isSafeInteger(countryId) ? `${countryId}` : undefined,
        // Not 'regular': it also hides preventive, planned and on hold campaigns
        // (incl. campaigns whose next round is on hold), which can still need a VRF.
        // Deleted campaigns are excluded by default and test ones by show_test.
        campaignCategory: 'all' as CampaignCategory,
        campaignType: 'polio',
        show_test: false,
    };
    const { data, isFetching } = useGetCampaignsDropdown(
        {
            country__id__in: options.countries,
            campaign_types: options.campaignType,
            campaign_category: options.campaignCategory,
            show_test: options.show_test,
            has_scopes: true,
        },
        { enabled: options.enabled },
    );
    const { data: fIPVData } = useGetCampaigns(
        { ...options, campaignType: 'fIPV' },
        CAMPAIGNS_ENDPOINT,
    );
    return useMemo(() => {
        const polioCampaigns = data ?? [];
        const fipvCampaigns = (fIPVData as Campaign[]) ?? [];
        const list = [
            ...polioCampaigns,
            ...fipvCampaigns.filter(
                c => c.separate_scopes_per_round || (c.scopes ?? []).length > 0,
            ),
        ].sort(orderCampaignsByEarliestRoundStartTimestamp);

        const campaigns = list.map(c => ({
            label: c.obr_name,
            value: c.obr_name,
        }));
        const selectedFipvCampaign = fipvCampaigns.find(
            c => c.obr_name === campaign,
        );
        const isFipvCampaign = Boolean(selectedFipvCampaign);
        const selectedCampaign = polioCampaigns.find(
            c => c.obr_name === campaign,
        );
        let vaccines;
        if (isFipvCampaign) {
            vaccines = fipvVaccineOptions;
        } else {
            vaccines = (selectedCampaign?.vaccines ?? []).map(vaccineName => ({
                label: vaccineName,
                value: vaccineName,
            }));
            if (vaccines.length === 0) {
                vaccines = singleVaccinesList;
            }
        }

        const toRoundOption = (round: Round | CampaignDropdownRound) => ({
            label: `Round ${round.number}`,
            value: `${round.number}`,
            original: round,
        });
        const rounds = (() => {
            if (!vaccine) return [];
            if (isFipvCampaign) {
                return (selectedFipvCampaign?.rounds ?? [])
                    .filter(
                        round =>
                            (selectedFipvCampaign?.separate_scopes_per_round &&
                                (round?.scopes ?? []).length > 0) ||
                            (!selectedFipvCampaign?.separate_scopes_per_round &&
                                (selectedFipvCampaign?.scopes ?? []).length >
                                    0),
                    )
                    .map(toRoundOption);
            }
            return (selectedCampaign?.rounds ?? [])
                .filter(round => round.vaccines.includes(vaccine))
                .filter(
                    round =>
                        !selectedCampaign?.separate_scopes_per_round ||
                        round.has_scope,
                )
                .map(toRoundOption);
        })();
        return {
            campaigns,
            vaccines,
            rounds,
            isFetching,
            rndsParams,
            isFipvCampaign,
        };
    }, [data, fIPVData, vaccine, isFetching, rndsParams, campaign]);
};

const getVrfDetails = (id?: string) => {
    return getRequest(`${apiUrl}${id}`);
};

export const useGetVrfDetails = (id?: string): UseQueryResult => {
    return useSnackQuery({
        queryKey: ['getVrfDetails', id],
        queryFn: () => getVrfDetails(id),
        options: {
            keepPreviousData: true,
            staleTime: 1000 * 60 * 15, // in MS
            cacheTime: 1000 * 60 * 5,
            enabled: Boolean(id),
            select: data => {
                if (!data) return data;
                return {
                    ...data,
                    campaign: data.obr_name,
                    rounds: data.rounds.map((r: Round) => r.number),
                    country: data.country_id,
                };
            },
        },
    });
};

const createFormDataRequest = (
    method: 'PATCH' | 'POST',
    arg1: PostArg,
): Promise<any> => {
    const { url, data = {}, fileData = {}, signal = null } = arg1;

    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
        let converted_value = value;
        if (typeof converted_value === 'object') {
            converted_value = JSON.stringify(converted_value);
        }
        formData.append(key, converted_value);
    });

    if (Object.keys(fileData).length > 0) {
        Object.entries(fileData).forEach(([key, value]) => {
            if (key === 'files' && Array.isArray(value)) {
                formData.append('file', value[0]); // Use 'file' key
            } else if (Array.isArray(value)) {
                value.forEach((blob, index) => {
                    formData.append(`${key}[${index}]`, blob);
                });
            } else {
                formData.append(key, value);
            }
        });
    }
    const isFileDeleted =
        Array.isArray(fileData?.files) && fileData?.files?.length === 0;
    const body = isFileDeleted
        ? JSON.stringify({ ...data, file: null })
        : formData;

    const init: Record<string, unknown> = {
        method,
        body,
        signal,
        headers: {
            'Accept-Language': moment.locale(),
        },
    };
    if (isFileDeleted) {
        init.headers = {
            ...(init.headers as Record<string, string>),
            'Content-Type': 'application/json',
        };
    }

    return iasoFetch(url, init).then(response => response.json());
};

export const patchRequest2 = (arg1: PostArg): Promise<any> => {
    return createFormDataRequest('PATCH', arg1);
};

export const postRequest2 = (arg1: PostArg): Promise<any> => {
    return createFormDataRequest('POST', arg1);
};

export const saveVrf = (
    vrf: Optional<Partial<VRFFormData>>,
): Promise<any>[] => {
    const filteredParams = vrf
        ? Object.fromEntries(
              Object.entries(vrf).filter(
                  ([key, value]) =>
                      value !== undefined && value !== null && key !== 'file',
              ),
          )
        : {};

    const { rounds } = filteredParams;
    if (Array.isArray(rounds)) {
        if (rounds.length > 0) {
            filteredParams.rounds = rounds.join(',');
        } else {
            filteredParams.rounds = '';
        }
    }
    const requestBody: any = {
        url: `${apiUrl}${vrf?.id ? `${vrf.id}/` : ''}`,
        data: filteredParams,
    };

    if (vrf?.file) {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars, no-unused-vars
        const { files, ...data } = filteredParams;
        const fileData = { files: vrf.file };
        requestBody.data = data;
        requestBody.fileData = fileData;
    }

    if (vrf?.id) {
        return [patchRequest2(requestBody)];
    }
    return [postRequest2(requestBody)];
};

export const handleVrfPromiseErrors = (
    data: ParsedSettledPromise<VRF>[],
): void => {
    const vrf = data[0];
    const isSuccessful = vrf.status === 'fulfilled';
    if (isSuccessful) {
        openSnackBar(succesfullSnackBar(undefined, MESSAGES.vrfApiSuccess));
    } else {
        const details = Array.isArray(vrf.value)
            ? // there's only one element in the array
              vrf.value[0].reason.details
            : vrf.value;
        openSnackBar(errorSnackBar(undefined, MESSAGES.vrfApiError, details));
    }
};

export const getRoundTagTooltipTitle = (
    option: DropdownOptionsWithOriginal<Round>,
): string => {
    const tooltip = `${dateApiToDateRangePicker(
        option.original.started_at,
    )} - ${
        option.original.ended_at
            ? dateApiToDateRangePicker(option.original.ended_at)
            : textPlaceholder
    }`;
    return tooltip;
};

export const renderRoundTag = renderTagsWithTooltip(getRoundTagTooltipTitle);
