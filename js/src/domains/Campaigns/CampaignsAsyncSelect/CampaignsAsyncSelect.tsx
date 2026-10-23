import React, { FunctionComponent, useCallback, useMemo } from 'react';
import { getRequest, IntlMessage, AsyncSelect } from 'bluesquare-components';
import { useQueryClient } from 'react-query';
import { openSnackBar } from 'Iaso/components/snackBars/EventDispatcher';
import { errorSnackBar } from 'Iaso/constants/snackBars';
import { useAsyncInitialState } from 'Iaso/hooks/useAsyncInitialState';
import MESSAGES from '../../../constants/messages';
import { CampaignCategory } from '../hooks/api/useGetCampaigns';
import {
    CampaignDropdownOption,
    CampaignsDropdownParams,
    getCampaignsDropdownUrl,
    makeCampaignsDropdownQueryKey,
    useGetCampaignsDropdown,
} from '../hooks/api/useGetCampaignsDropdown';
import { useCampaignTypeNames } from './useCampaignTypeNames';

type Props = {
    handleChange: (keyValue: string, value: unknown) => void;
    label?: IntlMessage;
    multi?: boolean;
    keyValue?: string;
    clearable?: boolean;
    initialValue?: string; // obr name
    showTest?: boolean;
    campaignCategory?: CampaignCategory;
    campaignType?: 'polio' | 'non-polio' | string;
};

/**
 * A wrapper on AsyncSelect geared towards polio campaigns
 * The filters to apply to the campaigns API can be parametrized using the components props
 * The component reads /api/polio/campaigns/dropdown/, the lightweight endpoint, and reformats the
 * response to be usable by AsyncSelect
 *
 */

const toAsyncSelectOption = (campaign: CampaignDropdownOption) => ({
    label: campaign.obr_name,
    value: campaign.id,
    campaign_types: campaign.campaign_types,
});

export const CampaignAsyncSelect: FunctionComponent<Props> = ({
    keyValue = 'campaigns',
    handleChange,
    multi,
    clearable,
    initialValue,
    // 'all' and not 'regular', which also hides on hold campaigns (incl. next round on hold).
    // Test campaigns are hidden by showTest, deleted ones by the API default.
    campaignCategory = 'all' as CampaignCategory,
    showTest = false,
    campaignType = 'polio',
    label = MESSAGES.campaign,
}) => {
    const queryClient = useQueryClient();
    const campaignTypes = useCampaignTypeNames(campaignType);
    const [search, setSearch, isStateSet] = useAsyncInitialState<
        string | undefined
    >(initialValue);

    const baseParams: CampaignsDropdownParams = useMemo(() => {
        return {
            campaign_category: campaignCategory,
            campaign_types: campaignTypes,
            show_test: showTest,
        };
    }, [campaignCategory, campaignTypes, showTest]);

    const fetchOptions = useCallback(
        async (query: string): Promise<any[]> => {
            const url = getCampaignsDropdownUrl({
                ...baseParams,
                search: query,
            });
            const queryKey = makeCampaignsDropdownQueryKey(url);
            const cached =
                queryClient.getQueryData<CampaignDropdownOption[]>(queryKey);
            if (cached) {
                return cached.map(toAsyncSelectOption);
            }

            try {
                const searchResult: CampaignDropdownOption[] =
                    await getRequest(url);
                queryClient.setQueryData(queryKey, searchResult);
                return searchResult.map(toAsyncSelectOption);
            } catch (e) {
                openSnackBar(errorSnackBar(undefined, MESSAGES.error, e));
                return [];
            }
        },
        [baseParams, queryClient],
    );

    const { data: selectedCampaigns } = useGetCampaignsDropdown(
        { ...baseParams, search },
        { keepPreviousData: false, enabled: isStateSet },
    );

    const campaignOptions = useMemo(() => {
        return selectedCampaigns?.map(toAsyncSelectOption) ?? [];
    }, [selectedCampaigns]);

    const handleChangeCampaigns = useCallback(
        (keyValue, newValue) => {
            const val = multi
                ? newValue?.map(r => r.label)?.join(',') // using label i.o value to get the obr name
                : newValue;
            setSearch(val?.label ? val.label : undefined);
            handleChange(keyValue, val ? val : undefined);
        },
        [handleChange, multi, setSearch],
    );

    return (
        <AsyncSelect
            keyValue={keyValue}
            label={label}
            value={campaignOptions ?? ''}
            onChange={handleChangeCampaigns}
            debounceTime={500}
            multi={multi}
            clearable={clearable}
            fetchOptions={input => fetchOptions(input)}
        />
    );
};
