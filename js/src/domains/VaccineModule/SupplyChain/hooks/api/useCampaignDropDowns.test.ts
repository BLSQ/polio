import { renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Campaign } from '../../../../../constants/types';
import type { CampaignDropdownOption } from '../../../../Campaigns/hooks/api/useGetCampaignsDropdown';
import { fipvVaccineOptions, singleVaccinesList } from '../../constants';
import { useCampaignDropDowns } from './vrf';

const mockUseGetCampaignsDropdown = vi.fn();
const mockUseGetCampaigns = vi.fn();

vi.mock('../../../../Campaigns/hooks/api/useGetCampaignsDropdown', () => ({
    useGetCampaignsDropdown: (...args: unknown[]) =>
        mockUseGetCampaignsDropdown(...args),
}));

vi.mock('../../../../Campaigns/hooks/api/useGetCampaigns', () => ({
    CAMPAIGNS_ENDPOINT: '/api/polio/campaigns/',
    useGetCampaigns: (...args: unknown[]) => mockUseGetCampaigns(...args),
}));

const COUNTRY_ID = 29702;

type RoundOverrides = Partial<CampaignDropdownOption['rounds'][number]>;

const round = (
    id: number,
    number: number,
    startedAt: string | null,
    overrides: RoundOverrides = {},
): CampaignDropdownOption['rounds'][number] => ({
    id,
    number,
    on_hold: false,
    started_at: startedAt,
    ended_at: null,
    vaccines: ['nOPV2'],
    has_scope: true,
    ...overrides,
});

const campaign = (
    obrName: string,
    rounds: CampaignDropdownOption['rounds'],
    overrides: Partial<CampaignDropdownOption> = {},
): CampaignDropdownOption => ({
    id: `uuid-${obrName}`,
    obr_name: obrName,
    created_at: '2020-01-01T00:00:00Z',
    vaccines: ['nOPV2'],
    separate_scopes_per_round: false,
    campaign_types: [],
    rounds,
    ...overrides,
});

// The fIPV half still goes through the full campaigns endpoint, so its fixtures carry the
// fields that payload has: campaign and round level `scopes`.
const fipvCampaign = (
    obrName: string,
    overrides: Partial<Campaign> = {},
): Campaign =>
    ({
        id: `uuid-${obrName}`,
        obr_name: obrName,
        separate_scopes_per_round: false,
        scopes: [{ vaccine: 'IPV', group: { org_units: [1] } }],
        rounds: [
            { id: 90, number: 1, started_at: '2023-01-01', scopes: [] },
            { id: 91, number: 2, started_at: '2023-06-01', scopes: [] },
        ],
        ...overrides,
    }) as unknown as Campaign;

const mockDropdown = (data?: CampaignDropdownOption[]) =>
    mockUseGetCampaignsDropdown.mockReturnValue({ data, isFetching: false });

const mockFipv = (data?: Campaign[]) =>
    mockUseGetCampaigns.mockReturnValue({ data, isFetching: false });

describe('useCampaignDropDowns', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        mockDropdown(undefined);
        mockFipv(undefined);
    });

    describe('the request it makes', () => {
        it('asks the dropdown endpoint for the country and nothing else', () => {
            renderHook(() => useCampaignDropDowns({ countryId: COUNTRY_ID }));

            expect(mockUseGetCampaignsDropdown).toHaveBeenCalledWith(
                {
                    country__id__in: `${COUNTRY_ID}`,
                    campaign_types: 'polio',
                    campaign_category: 'all',
                    show_test: false,
                    has_scopes: true,
                },
                { enabled: true },
            );
        });

        it('stays disabled and sends no country until one is picked', () => {
            renderHook(() => useCampaignDropDowns({}));

            expect(mockUseGetCampaignsDropdown).toHaveBeenCalledWith(
                expect.objectContaining({ country__id__in: undefined }),
                { enabled: false },
            );
        });

        it('keeps the fIPV query on the full campaigns endpoint', () => {
            renderHook(() => useCampaignDropDowns({ countryId: COUNTRY_ID }));

            expect(mockUseGetCampaigns).toHaveBeenCalledWith(
                expect.objectContaining({
                    campaignType: 'fIPV',
                    countries: `${COUNTRY_ID}`,
                }),
                '/api/polio/campaigns/',
            );
        });
    });

    describe('campaigns', () => {
        it('orders campaigns by their earliest round start date, most recent first', () => {
            mockDropdown([
                campaign('MALI-2022', [round(3, 1, '2022-03-01')]),
                campaign('MALI-2024', [
                    round(5, 2, '2024-09-01'),
                    round(4, 1, '2024-02-01'),
                ]),
                campaign('MALI-2023', [round(6, 1, '2023-05-01')]),
            ]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({ countryId: COUNTRY_ID }),
            );

            expect(result.current.campaigns.map(o => o.value)).toEqual([
                'MALI-2024',
                'MALI-2023',
                'MALI-2022',
            ]);
        });

        it('puts a campaign with no round start date last, like the endpoint does', () => {
            mockDropdown([
                campaign('MALI-NO-ROUNDS', []),
                campaign('MALI-2024', [round(1, 1, '2024-02-01')]),
                campaign('MALI-2021', [round(2, 1, '2021-01-01')]),
            ]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({ countryId: COUNTRY_ID }),
            );

            expect(result.current.campaigns.map(o => o.value)).toEqual([
                'MALI-2024',
                'MALI-2021',
                'MALI-NO-ROUNDS',
            ]);
        });

        it('sorts the fIPV campaigns into the same list', () => {
            mockDropdown([campaign('MALI-2024', [round(1, 1, '2024-02-01')])]);
            mockFipv([fipvCampaign('MALI-FIPV-2025')]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({ countryId: COUNTRY_ID }),
            );

            expect(result.current.campaigns.map(o => o.value)).toEqual([
                'MALI-2024',
                // fIPV rounds start in 2023, so it lands after the 2024 campaign.
                'MALI-FIPV-2025',
            ]);
        });

        it('drops a scopeless fIPV campaign', () => {
            mockDropdown([]);
            mockFipv([
                fipvCampaign('MALI-FIPV-NO-SCOPE', {
                    scopes: [],
                    separate_scopes_per_round: false,
                }),
            ]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({ countryId: COUNTRY_ID }),
            );

            expect(result.current.campaigns).toEqual([]);
        });

        it('returns label/value pairs built on obr_name alone', () => {
            mockDropdown([campaign('MALI-2021', [round(1, 1, '2021-01-01')])]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({ countryId: COUNTRY_ID }),
            );

            expect(result.current.campaigns).toEqual([
                { label: 'MALI-2021', value: 'MALI-2021' },
            ]);
        });
    });

    describe('vaccines', () => {
        it('takes the vaccines the endpoint resolved for the selected campaign', () => {
            mockDropdown([
                campaign('MALI-2021', [round(1, 1, '2021-01-01')], {
                    vaccines: ['bOPV', 'nOPV2'],
                }),
            ]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({
                    countryId: COUNTRY_ID,
                    campaign: 'MALI-2021',
                }),
            );

            expect(result.current.vaccines).toEqual([
                { label: 'bOPV', value: 'bOPV' },
                { label: 'nOPV2', value: 'nOPV2' },
            ]);
        });

        it('falls back to every single vaccine when the campaign names none', () => {
            mockDropdown([
                campaign('MALI-2021', [round(1, 1, '2021-01-01')], {
                    vaccines: [],
                }),
            ]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({
                    countryId: COUNTRY_ID,
                    campaign: 'MALI-2021',
                }),
            );

            expect(result.current.vaccines).toEqual(singleVaccinesList);
        });

        it('keeps the fIPV vaccine options for an fIPV campaign', () => {
            mockDropdown([]);
            mockFipv([fipvCampaign('MALI-FIPV')]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({
                    countryId: COUNTRY_ID,
                    campaign: 'MALI-FIPV',
                }),
            );

            expect(result.current.isFipvCampaign).toBe(true);
            expect(result.current.vaccines).toEqual(fipvVaccineOptions);
        });
    });

    describe('rounds', () => {
        it('returns no round until a vaccine is picked', () => {
            mockDropdown([campaign('MALI-2021', [round(1, 1, '2021-01-01')])]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({
                    countryId: COUNTRY_ID,
                    campaign: 'MALI-2021',
                }),
            );

            expect(result.current.rounds).toEqual([]);
        });

        it('keeps only the rounds the endpoint says carry that vaccine', () => {
            mockDropdown([
                campaign('MALI-2021', [
                    round(1, 1, '2021-01-01', { vaccines: ['nOPV2'] }),
                    round(2, 2, '2021-06-01', { vaccines: ['bOPV'] }),
                ]),
            ]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({
                    countryId: COUNTRY_ID,
                    campaign: 'MALI-2021',
                    vaccine: 'nOPV2',
                }),
            );

            expect(result.current.rounds).toEqual([
                expect.objectContaining({ label: 'Round 1', value: '1' }),
            ]);
        });

        it('matches a vaccine exactly, not as a substring', () => {
            mockDropdown([
                campaign('MALI-2021', [
                    round(1, 1, '2021-01-01', { vaccines: ['nOPV2'] }),
                ]),
            ]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({
                    countryId: COUNTRY_ID,
                    campaign: 'MALI-2021',
                    vaccine: 'OPV2',
                }),
            );

            expect(result.current.rounds).toEqual([]);
        });

        it('drops a round without its own scope when scopes are split per round', () => {
            mockDropdown([
                campaign(
                    'MALI-2021',
                    [
                        round(1, 1, '2021-01-01', { has_scope: true }),
                        round(2, 2, '2021-06-01', { has_scope: false }),
                    ],
                    { separate_scopes_per_round: true },
                ),
            ]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({
                    countryId: COUNTRY_ID,
                    campaign: 'MALI-2021',
                    vaccine: 'nOPV2',
                }),
            );

            expect(result.current.rounds.map(o => o.value)).toEqual(['1']);
        });

        it('keeps a scopeless round when the campaign holds the scope', () => {
            mockDropdown([
                campaign('MALI-2021', [
                    round(1, 1, '2021-01-01', { has_scope: false }),
                ]),
            ]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({
                    countryId: COUNTRY_ID,
                    campaign: 'MALI-2021',
                    vaccine: 'nOPV2',
                }),
            );

            expect(result.current.rounds.map(o => o.value)).toEqual(['1']);
        });

        it('does not filter fIPV rounds by vaccine', () => {
            mockDropdown([]);
            mockFipv([fipvCampaign('MALI-FIPV')]);

            const { result } = renderHook(() =>
                useCampaignDropDowns({
                    countryId: COUNTRY_ID,
                    campaign: 'MALI-FIPV',
                    vaccine: 'IPV',
                }),
            );

            expect(result.current.rounds.map(o => o.value)).toEqual(['1', '2']);
        });
    });
});
