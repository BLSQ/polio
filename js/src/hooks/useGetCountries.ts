import { getRequest } from 'Iaso/libs/Api';
import { useSnackQuery } from 'Iaso/libs/apiHooks';
import { useAppId } from '../../../../../hat/assets/js/apps/Iaso/domains/app/hooks/useAppId';

export const useGetCountries = (
    status = 'all',
    enabled = true,
    groupId?: string,
) => {
    const appId = useAppId();
    const params: Record<string, string> = {
        validation_status: status,
        order: 'name',
        orgUnitTypeCategory: 'country',
        app_id: appId,
    };
    if (groupId) {
        params.group = groupId;
    }
    const queryString = new URLSearchParams(params);

    return useSnackQuery({
        queryKey: ['orgunits', 'countries', status, appId, groupId],
        queryFn: () => getRequest(`/api/orgunits/?${queryString.toString()}`),
        options: {
            staleTime: Infinity,
            cacheTime: Infinity,
            enabled,
        },
    });
};
