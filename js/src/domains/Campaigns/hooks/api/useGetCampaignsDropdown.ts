import { UseQueryResult } from 'react-query';
import { getRequest } from '../../../../../../../../hat/assets/js/apps/Iaso/libs/Api';
import { useSnackQuery } from '../../../../../../../../hat/assets/js/apps/Iaso/libs/apiHooks';
import { CampaignCategory } from './useGetCampaigns';

export const CAMPAIGNS_DROPDOWN_ENDPOINT = '/api/polio/campaigns/dropdown/';

export type CampaignDropdownRound = {
    id: number;
    number: number;
    on_hold: boolean;
};

export type CampaignDropdownOption = {
    id: string;
    obr_name: string;
    created_at: string;
    rounds: CampaignDropdownRound[];
    campaign_types: { id: number; name: string }[];
};

export type CampaignsDropdownParams = {
    country__name?: string;
    country__id__in?: string;
    search?: string;
    campaign_types?: string;
    campaign_category?: CampaignCategory;
    show_test?: boolean;
    deletion_status?: string;
};

export const getCampaignsDropdownUrl = (
    params: CampaignsDropdownParams,
): string => {
    const queryString = new URLSearchParams(
        Object.entries(params)
            .filter(([, value]) => value !== undefined && value !== '')
            .map(([key, value]) => [key, String(value)]),
    ).toString();
    return queryString
        ? `${CAMPAIGNS_DROPDOWN_ENDPOINT}?${queryString}`
        : CAMPAIGNS_DROPDOWN_ENDPOINT;
};

export const makeCampaignsDropdownQueryKey = (url: string): unknown[] => [
    'campaigns-dropdown',
    url,
];

export const useGetCampaignsDropdown = (
    params: CampaignsDropdownParams = {},
    queryOptions?: Record<string, any>,
): UseQueryResult<CampaignDropdownOption[], Error> => {
    const url = getCampaignsDropdownUrl(params);
    return useSnackQuery({
        queryKey: makeCampaignsDropdownQueryKey(url),
        queryFn: (): Promise<CampaignDropdownOption[]> => getRequest(url),
        options: {
            keepPreviousData: true,
            staleTime: 1000 * 60 * 15,
            cacheTime: 1000 * 60 * 5,
            refetchOnWindowFocus: false,
            ...queryOptions,
        },
    });
};
