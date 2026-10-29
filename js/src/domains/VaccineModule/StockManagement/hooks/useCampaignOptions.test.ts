import { renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { CampaignDropdownOption } from '../../../Campaigns/hooks/api/useGetCampaignsDropdown';
import { useCampaignOptions } from './api';

const mockUseGetCampaignsDropdown = vi.fn();

vi.mock('../../../Campaigns/hooks/api/useGetCampaignsDropdown', () => ({
    useGetCampaignsDropdown: (...args: unknown[]) =>
        mockUseGetCampaignsDropdown(...args),
}));

vi.mock('bluesquare-components', async () => {
    const actual = await vi.importActual('bluesquare-components');
    return {
        ...actual,
        useSafeIntl: () => ({
            formatMessage: (msg: { defaultMessage?: string } | string) =>
                typeof msg === 'string' ? msg : (msg?.defaultMessage ?? ''),
        }),
    };
});

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
    vaccines: [],
    has_scope: true,
    ...overrides,
});

const campaign = (
    obrName: string,
    rounds: CampaignDropdownOption['rounds'],
): CampaignDropdownOption => ({
    id: `uuid-${obrName}`,
    obr_name: obrName,
    created_at: '2020-01-01T00:00:00Z',
    vaccines: [],
    separate_scopes_per_round: false,
    campaign_types: [],
    rounds,
});

describe('useCampaignOptions', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        mockUseGetCampaignsDropdown.mockReturnValue({
            data: undefined,
            isFetching: false,
        });
    });

    describe('the request it makes', () => {
        it('asks the dropdown endpoint for the country and nothing else', () => {
            renderHook(() => useCampaignOptions('MALI'));

            expect(mockUseGetCampaignsDropdown).toHaveBeenCalledWith(
                { country__name: 'MALI', show_test: true },
                { enabled: true },
            );
        });

        it('stays disabled until a country is picked', () => {
            renderHook(() => useCampaignOptions(''));

            expect(mockUseGetCampaignsDropdown).toHaveBeenCalledWith(
                { country__name: '', show_test: true },
                { enabled: false },
            );
        });
    });

    describe('campaignOptions', () => {
        it('orders campaigns by their earliest round start date, most recent first', () => {
            mockUseGetCampaignsDropdown.mockReturnValue({
                data: [
                    campaign('MALI-2022', [round(3, 1, '2022-03-01')]),
                    campaign('MALI-2024', [
                        // Out of order on purpose: the campaign is placed by its earliest
                        // round, not by the first round the payload happens to list.
                        round(5, 2, '2024-09-01'),
                        round(4, 1, '2024-02-01'),
                    ]),
                    campaign('MALI-2023', [round(6, 1, '2023-05-01')]),
                ],
                isFetching: false,
            });

            const { result } = renderHook(() => useCampaignOptions('MALI'));

            expect(result.current.campaignOptions.map(o => o.value)).toEqual([
                'MALI-2024',
                'MALI-2023',
                'MALI-2022',
            ]);
        });

        it('puts campaigns with no usable round start date last', () => {
            mockUseGetCampaignsDropdown.mockReturnValue({
                data: [
                    campaign('MALI-NO-ROUNDS', []),
                    campaign('MALI-NO-DATE', [round(1, 1, null)]),
                    campaign('MALI-2021', [round(2, 1, '2021-01-01')]),
                ],
                isFetching: false,
            });

            const { result } = renderHook(() => useCampaignOptions('MALI'));

            expect(result.current.campaignOptions[0].value).toBe('MALI-2021');
            expect(
                result.current.campaignOptions.slice(1).map(o => o.value),
            ).toEqual(
                expect.arrayContaining(['MALI-NO-ROUNDS', 'MALI-NO-DATE']),
            );
        });

        it('returns label/value pairs built on obr_name alone', () => {
            mockUseGetCampaignsDropdown.mockReturnValue({
                data: [campaign('MALI-2021', [round(1, 1, '2021-01-01')])],
                isFetching: false,
            });

            const { result } = renderHook(() => useCampaignOptions('MALI'));

            expect(result.current.campaignOptions).toEqual([
                { label: 'MALI-2021', value: 'MALI-2021' },
            ]);
        });

        it('falls back to the selected campaign when the endpoint returns nothing', () => {
            mockUseGetCampaignsDropdown.mockReturnValue({
                data: [],
                isFetching: false,
            });

            const { result } = renderHook(() =>
                useCampaignOptions('MALI', 'MALI-2021'),
            );

            expect(result.current.campaignOptions).toEqual([
                { label: 'MALI-2021', value: 'MALI-2021' },
            ]);
        });
    });

    describe('round options', () => {
        const data = [
            campaign('MALI-2021', [
                round(10, 1, '2021-01-01'),
                round(11, 2, '2021-06-01', { on_hold: true }),
            ]),
            campaign('MALI-2022', [round(20, 1, '2022-01-01')]),
        ];

        it('builds the round options of the selected campaign only', () => {
            mockUseGetCampaignsDropdown.mockReturnValue({
                data,
                isFetching: false,
            });

            const { result } = renderHook(() =>
                useCampaignOptions('MALI', 'MALI-2021'),
            );

            expect(result.current.roundOptions).toEqual([
                { label: 'Round 1', value: 10 },
                { label: 'Round 2', value: 11 },
            ]);
        });

        it('returns no round option when no campaign is selected', () => {
            mockUseGetCampaignsDropdown.mockReturnValue({
                data,
                isFetching: false,
            });

            const { result } = renderHook(() => useCampaignOptions('MALI'));

            expect(result.current.roundOptions).toEqual([]);
            expect(result.current.roundNumberOptions).toEqual([]);
        });

        it('hides rounds on hold from roundNumberOptions', () => {
            mockUseGetCampaignsDropdown.mockReturnValue({
                data,
                isFetching: false,
            });

            const { result } = renderHook(() =>
                useCampaignOptions('MALI', 'MALI-2021'),
            );

            expect(
                result.current.roundNumberOptions.map(o => o.value),
            ).toEqual([1]);
        });

        it('keeps a round on hold when it is the one already selected', () => {
            mockUseGetCampaignsDropdown.mockReturnValue({
                data,
                isFetching: false,
            });

            const { result } = renderHook(() =>
                useCampaignOptions('MALI', 'MALI-2021', 2),
            );

            expect(
                result.current.roundNumberOptions.map(o => o.value),
            ).toEqual([1, 2]);
        });
    });
});
