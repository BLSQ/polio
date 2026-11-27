import { useSafeIntl } from 'bluesquare-components';
import MESSAGES from './messages';
import { Vaccine, Virus } from './types';

const polioViruses = [
    // Legacy values
    // {
    //     value: 'PV1',
    //     label: 'PV1',
    // },
    // {
    //     value: 'PV2',
    //     label: 'PV2',
    // },
    // {
    //     value: 'PV3',
    //     label: 'PV3',
    // },
    {
        value: 'PV1',
        label: 'cVDPV1',
    },
    {
        value: 'PV3',
        label: 'cVDPV3',
    },
    {
        value: 'cVDPV2',
        label: 'cVDPV2',
    },
    {
        value: 'WPV1',
        label: 'WPV1',
    },
    {
        value: 'PV1 & cVDPV2',
        label: 'PV1 & cVDPV2',
    },
    {
        value: 'cVDPV1 & cVDPV2',
        label: 'cVDPV1 & cVDPV2',
    },
];

export type PolioVaccine = {
    value: Vaccine | 'other';
    label: string;
    color: string;
    legendColor?: string;
};
export const HASHED_MAP_PATTERN_N_OPV2_B_OPV = 'colorStripes-nOPV2&bOPV';

export const OTHER_VACCINE_COLOR = '#ea8418';

const polioVaccines: PolioVaccine[] = [
    {
        value: 'nOPV2',
        label: 'nOPV2',
        color: '#00b0f0',
    },
    {
        value: 'mOPV2',
        label: 'mOPV2',
        color: '#66ff66',
    },
    {
        value: 'bOPV',
        label: 'bOPV',
        color: '#ffff00',
    },
    {
        value: 'nOPV2 & bOPV',
        label: 'nOPV2 & bOPV',
        color: `url(#${HASHED_MAP_PATTERN_N_OPV2_B_OPV})`,
        legendColor: `repeating-linear-gradient(-45deg, #00b0f0, #00b0f0 5px, #ffff00 5px, #ffff00 10px)`,
    },

    {
        value: 'IPV',
        label: 'IPV',
        color: OTHER_VACCINE_COLOR,
    },
    {
        value: 'fIPV',
        label: 'fIPV',
        color: OTHER_VACCINE_COLOR,
    },
    {
        value: 'IPV & bOPV',
        label: 'IPV & bOPV',
        color: OTHER_VACCINE_COLOR,
    },
    {
        value: 'fIPV & bOPV',
        label: 'fIPV & bOPV',
        color: OTHER_VACCINE_COLOR,
    },
    {
        value: 'IPV & nOPV2',
        label: 'IPV & nOPV2',
        color: OTHER_VACCINE_COLOR,
    },
    {
        value: 'fIPV & nOPV2',
        label: 'fIPV & nOPV2',
        color: OTHER_VACCINE_COLOR,
    },
    {
        value: 'IPV & nOPV2 & bOPV',
        label: 'IPV & nOPV2 & bOPV',
        color: OTHER_VACCINE_COLOR,
    },
    {
        value: 'fIPV & nOPV2 & bOPV',
        label: 'fIPV & nOPV2 & bOPV',
        color: OTHER_VACCINE_COLOR,
    },
];

const useMapLegend = (): PolioVaccine[] => {
    const { formatMessage } = useSafeIntl();
    return [
        ...polioVaccines,
        {
            value: 'other',
            label: formatMessage(MESSAGES.other),
            color: OTHER_VACCINE_COLOR,
        },
    ];
};

export const VACCINES_BY_VIRUS: Partial<Record<Virus, Vaccine[]>> = {
    PV1: ['bOPV', 'IPV', 'fIPV', 'IPV & bOPV', 'fIPV & bOPV'],
    PV3: ['bOPV', 'IPV', 'fIPV', 'IPV & bOPV', 'fIPV & bOPV'],
    cVDPV2: ['nOPV2', 'IPV', 'fIPV', 'IPV & nOPV2', 'fIPV & nOPV2'],
    WPV1: ['bOPV', 'IPV', 'fIPV', 'IPV & bOPV', 'fIPV & bOPV'],
    'PV1 & cVDPV2': [
        'nOPV2',
        'bOPV',
        'nOPV2 & bOPV',
        'IPV',
        'fIPV',
        'IPV & nOPV2',
        'IPV & bOPV',
        'IPV & nOPV2 & bOPV',
        'fIPV & nOPV2',
        'fIPV & bOPV',
        'fIPV & nOPV2 & bOPV',
    ],
    'cVDPV1 & cVDPV2': [
        'nOPV2',
        'bOPV',
        'nOPV2 & bOPV',
        'IPV',
        'fIPV',
        'IPV & nOPV2',
        'IPV & bOPV',
        'IPV & nOPV2 & bOPV',
        'fIPV & nOPV2',
        'fIPV & bOPV',
        'fIPV & nOPV2 & bOPV',
    ],
};

export { polioVaccines, polioViruses, useMapLegend };
