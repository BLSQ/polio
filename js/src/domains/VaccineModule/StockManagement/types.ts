import { UrlParams } from 'bluesquare-components';

export type StockManagementListParams = {
    order?: string;
    pageSize?: string; // number as string
    page?: string; // number as string
    accountId: string; // number as string
    search?: string;
    country_id?: string; // number as string
    vaccine_type?: string;
};

export type TabValue = 'usableVials' | 'unusableVials' | 'earmarked';

export type StockManagementDetailsParams = Partial<UrlParams> & {
    id: string; // number as string
    tab?: TabValue;
    unusableVialsPageSize?: string; // number as string
    unusableVialsPage?: string; // number as string
    unusableVialsOrder?: string;
    usableVialsPageSize?: string; // number as string
    usableVialsPage?: string; // number as string
    usableVialsOrder?: string;
    earmarkedPageSize?: string; // number as string
    earmarkedPage?: string; // number as string
    earmarkedOrder?: string;
};

export type StockVariationTab =
    | 'forma'
    | 'destruction'
    | 'incident'
    | 'earmarked';

export type StockVariationSearchKey =
    | 'formaSearch'
    | 'destructionSearch'
    | 'incidentSearch';

export type formaFilterKey =
    | 'formaStatus'
    | 'formaRound'
    | 'formaDosesPerVial'
    | 'formaReceptionDateFrom'
    | 'formaReceptionDateTo'
    | 'formaReportDateFrom'
    | 'formaReportDateTo';

export type destructionFilterKey =
    | 'destructionDosesPerVial'
    | 'destructionDateFrom'
    | 'destructionDateTo'
    | 'destructionRrtDateFrom'
    | 'destructionRrtDateTo';

export type incidentFilterKey =
    | 'incidentStockCorrection'
    | 'incidentDosesPerVial'
    | 'incidentDateFrom'
    | 'incidentDateTo'
    | 'incidentRrtDateFrom'
    | 'incidentRrtDateTo';

export type StockVariationFilterKey =
    | StockVariationSearchKey
    | formaFilterKey
    | destructionFilterKey
    | incidentFilterKey;

export type StockVariationPageKey =
    | 'formaPage'
    | 'destructionPage'
    | 'incidentPage';

export type StockVariationParams = {
    id: string; // number as string
    tab: StockVariationTab;
    formaPageSize: string; // number as string
    formaPage: string; // number as string
    formaOrder: string;
    formaSearch?: string;
    formaStatus?: string;
    formaRound?: string; // number as string
    formaDosesPerVial?: string; // number as string
    formaReceptionDateFrom?: string; // YYYY-MM-DD
    formaReceptionDateTo?: string; // YYYY-MM-DD
    formaReportDateFrom?: string; // YYYY-MM-DD
    formaReportDateTo?: string; // YYYY-MM-DD
    destructionPageSize: string; // number as string
    destructionPage: string; // number as string
    destructionOrder: string;
    destructionSearch?: string;
    destructionDosesPerVial?: string; // number as string
    destructionDateFrom?: string; // YYYY-MM-DD
    destructionDateTo?: string; // YYYY-MM-DD
    destructionRrtDateFrom?: string; // YYYY-MM-DD
    destructionRrtDateTo?: string; // YYYY-MM-DD
    incidentPageSize: string; // number as string
    incidentPage: string; // number as string
    incidentOrder: string;
    incidentSearch?: string;
    incidentStockCorrection?: string;
    incidentDosesPerVial?: string; // number as string
    incidentDateFrom?: string; // YYYY-MM-DD
    incidentDateTo?: string; // YYYY-MM-DD
    incidentRrtDateFrom?: string; // YYYY-MM-DD
    incidentRrtDateTo?: string; // YYYY-MM-DD
    unusableVialsOrder: string; // number as string
    usableVialsPageSize: string; // number as string
    usableVialsPage: string; // number as string
    usableVialsOrder: string; // number as string
    earmarkedPageSize?: string; // number as string
    earmarkedPage?: string; // number as string
    earmarkedOrder?: string;
};

export type DosesPerVialDropdownItem = {
    label: string;
    value: number;
    doses_available: number;
    unusable_doses: number;
};

export type DosesPerVialDropdown = DosesPerVialDropdownItem[];
