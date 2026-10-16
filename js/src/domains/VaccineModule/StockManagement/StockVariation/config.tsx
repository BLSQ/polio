import { useMemo } from 'react';
import { Column, IntlMessage } from 'bluesquare-components';
import { DESTRUCTION, EARMARKED, FORM_A, INCIDENT } from '../constants';
import {
    useGetDestructionList,
    useGetEarmarkedList,
    useGetFormAList,
    useGetIncidentList,
} from '../hooks/api';
import MESSAGES from '../messages';
import {
    StockVariationFilterKey,
    StockVariationPageKey,
    StockVariationParams,
    StockVariationTab,
} from '../types';
import {
    useDestructionTableColumns,
    useEarmarkedTableColumns,
    useFormATableColumns,
    useIncidentTableColumns,
} from './Table/columns';

export type StockVariationFilterOptionsKey =
    | 'formAStatus'
    | 'stockCorrection'
    | 'dosesPerVial'
    | 'roundNumber';

export type StockVariationFilterField = {
    urlKey: StockVariationFilterKey;
    apiKey: string;
    type: 'search' | 'select' | 'date';
    label: IntlMessage;
    optionsKey?: StockVariationFilterOptionsKey;
};

export const stockVariationFilterFields: Partial<
    Record<StockVariationTab, StockVariationFilterField[]>
> = {
    [FORM_A]: [
        {
            urlKey: 'formaSearch',
            apiKey: 'search',
            type: 'search',
            label: MESSAGES.search,
        },
        {
            urlKey: 'formaStatus',
            apiKey: 'status',
            type: 'select',
            label: MESSAGES.form_a_status,
            optionsKey: 'formAStatus',
        },
        {
            urlKey: 'formaRound',
            apiKey: 'round_number',
            type: 'select',
            label: MESSAGES.round,
            optionsKey: 'roundNumber',
        },
        {
            urlKey: 'formaDosesPerVial',
            apiKey: 'doses_per_vial',
            type: 'select',
            label: MESSAGES.doses_per_vial,
            optionsKey: 'dosesPerVial',
        },
        {
            urlKey: 'formaReceptionDateFrom',
            apiKey: 'form_a_reception_date_from',
            type: 'date',
            label: MESSAGES.formAReceptionDateFrom,
        },
        {
            urlKey: 'formaReceptionDateTo',
            apiKey: 'form_a_reception_date_to',
            type: 'date',
            label: MESSAGES.formAReceptionDateTo,
        },
        {
            urlKey: 'formaReportDateFrom',
            apiKey: 'report_date_from',
            type: 'date',
            label: MESSAGES.reportDateFrom,
        },
        {
            urlKey: 'formaReportDateTo',
            apiKey: 'report_date_to',
            type: 'date',
            label: MESSAGES.reportDateTo,
        },
    ],
    [DESTRUCTION]: [
        {
            urlKey: 'destructionSearch',
            apiKey: 'search',
            type: 'search',
            label: MESSAGES.search,
        },
        {
            urlKey: 'destructionDosesPerVial',
            apiKey: 'doses_per_vial',
            type: 'select',
            label: MESSAGES.doses_per_vial,
            optionsKey: 'dosesPerVial',
        },
        {
            urlKey: 'destructionDateFrom',
            apiKey: 'destruction_report_date_from',
            type: 'date',
            label: MESSAGES.reportDateFrom,
        },
        {
            urlKey: 'destructionDateTo',
            apiKey: 'destruction_report_date_to',
            type: 'date',
            label: MESSAGES.reportDateTo,
        },
        {
            urlKey: 'destructionRrtDateFrom',
            apiKey: 'rrt_reception_date_from',
            type: 'date',
            label: MESSAGES.rrtReceptionDateFrom,
        },
        {
            urlKey: 'destructionRrtDateTo',
            apiKey: 'rrt_reception_date_to',
            type: 'date',
            label: MESSAGES.rrtReceptionDateTo,
        },
    ],
    [INCIDENT]: [
        {
            urlKey: 'incidentSearch',
            apiKey: 'search',
            type: 'search',
            label: MESSAGES.search,
        },
        {
            urlKey: 'incidentStockCorrection',
            apiKey: 'stock_correction',
            type: 'select',
            label: MESSAGES.stockCorrection,
            optionsKey: 'stockCorrection',
        },
        {
            urlKey: 'incidentDateFrom',
            apiKey: 'date_of_incident_report_from',
            type: 'date',
            label: MESSAGES.reportDateFrom,
        },
        {
            urlKey: 'incidentDateTo',
            apiKey: 'date_of_incident_report_to',
            type: 'date',
            label: MESSAGES.reportDateTo,
        },
        {
            urlKey: 'incidentDosesPerVial',
            apiKey: 'doses_per_vial',
            type: 'select',
            label: MESSAGES.doses_per_vial,
            optionsKey: 'dosesPerVial',
        },
        {
            urlKey: 'incidentRrtDateFrom',
            apiKey: 'rrt_reception_date_from',
            type: 'date',
            label: MESSAGES.rrtReceptionDateFrom,
        },
        {
            urlKey: 'incidentRrtDateTo',
            apiKey: 'rrt_reception_date_to',
            type: 'date',
            label: MESSAGES.rrtReceptionDateTo,
        },
    ],
};

export const stockVariationPageKeys: Partial<
    Record<StockVariationTab, StockVariationPageKey>
> = {
    [FORM_A]: 'formaPage',
    [DESTRUCTION]: 'destructionPage',
    [INCIDENT]: 'incidentPage',
};

export const getFilterApiParams = (
    tab: StockVariationTab,
    params: StockVariationParams,
): Record<string, string> => {
    const fields = stockVariationFilterFields[tab] ?? [];
    return fields.reduce((apiParams, field) => {
        const value = params[field.urlKey];
        if (value) {
            return { ...apiParams, [field.apiKey]: value };
        }
        return apiParams;
    }, {});
};

export type StockVariationTabConfig = {
    data: { results?: any[]; count?: number; pages?: number };
    columns?: Column[];
    isFetching: boolean;
    defaultSorted: { id: string; desc: boolean }[];
};

type Args = {
    params: StockVariationParams;
    tab: StockVariationTab;
    countryName?: string;
    vaccineType?: string;
};

export const useStockVariationTabConfig = ({
    params,
    tab,
    countryName,
    vaccineType,
}: Args): StockVariationTabConfig => {
    const { data: formA, isFetching: isFetchingFormA } = useGetFormAList(
        params,
        tab === FORM_A,
    );
    const { data: destructions, isFetching: isFetchingDestructions } =
        useGetDestructionList(params, tab === DESTRUCTION);
    const { data: incidents, isFetching: isFetchingIncidents } =
        useGetIncidentList(params, tab === INCIDENT);
    const { data: earmarked, isFetching: isFetchingEarmarked } =
        useGetEarmarkedList(params, tab === EARMARKED);

    const formAColumns = useFormATableColumns(countryName, vaccineType);
    const destructionsColumns = useDestructionTableColumns(
        countryName,
        vaccineType,
    );
    const incidentsColumns = useIncidentTableColumns(countryName, vaccineType);
    const earmarkedColumns = useEarmarkedTableColumns(countryName, vaccineType);

    const tabConfigs: Record<StockVariationTab, StockVariationTabConfig> =
        useMemo(
            () => ({
                [FORM_A]: {
                    data: formA,
                    columns: formAColumns,
                    isFetching: isFetchingFormA,
                    defaultSorted: [
                        { id: 'form_a_reception_date', desc: true },
                    ],
                },
                [DESTRUCTION]: {
                    data: destructions,
                    columns: destructionsColumns,
                    isFetching: isFetchingDestructions,
                    defaultSorted: [
                        {
                            id: 'rrt_destruction_report_reception_date',
                            desc: true,
                        },
                    ],
                },
                [INCIDENT]: {
                    data: incidents,
                    columns: incidentsColumns,
                    isFetching: isFetchingIncidents,
                    defaultSorted: [
                        { id: 'incident_report_received_by_rrt', desc: true },
                    ],
                },
                // Earmarked is the only tab without filters
                [EARMARKED]: {
                    data: earmarked,
                    columns: earmarkedColumns,
                    isFetching: isFetchingEarmarked,
                    defaultSorted: [{ id: 'created_at', desc: true }],
                },
            }),
            [
                destructions,
                destructionsColumns,
                earmarked,
                earmarkedColumns,
                formA,
                formAColumns,
                incidents,
                incidentsColumns,
                isFetchingDestructions,
                isFetchingEarmarked,
                isFetchingFormA,
                isFetchingIncidents,
            ],
        );

    return tabConfigs[tab];
};
