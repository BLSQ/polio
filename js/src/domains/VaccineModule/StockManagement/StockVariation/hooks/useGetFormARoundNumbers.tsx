import { UseQueryResult } from 'react-query';
import { getRequest } from 'Iaso/libs/Api';
import { useSnackQuery } from 'Iaso/libs/apiHooks';

const modalUrl = '/api/polio/vaccine/stock/';

export const useGetFormARoundNumbers = (
    vaccineStockId: string,
): UseQueryResult<number[]> => {
    return useSnackQuery({
        queryKey: ['forma-round-numbers', vaccineStockId],
        queryFn: () =>
            getRequest(
                `${modalUrl}outgoing_stock_movement/round_numbers/?vaccine_stock=${vaccineStockId}`,
            ),
        options: {
            keepPreviousData: true,
            staleTime: 1000 * 60 * 15,
            cacheTime: 1000 * 60 * 5,
            refetchInterval: 1000 * 60 * 5,
            select: data => data ?? [],
            enabled: Boolean(vaccineStockId),
        },
    });
};
