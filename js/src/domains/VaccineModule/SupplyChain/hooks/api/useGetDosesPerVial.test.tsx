import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { IntlProvider } from 'react-intl';
import { QueryClient, QueryClientProvider } from 'react-query';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useGetDosesPerVial } from './useGetDosesPerVial';

const { mockGetRequest } = vi.hoisted(() => ({
    mockGetRequest: vi.fn(),
}));

vi.mock('Iaso/libs/Api', () => ({
    getRequest: (...args: unknown[]) => mockGetRequest(...args),
}));

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });
    const Wrapper = ({ children }: { children: React.ReactNode }) => (
        <IntlProvider locale="en" messages={{}}>
            <QueryClientProvider client={queryClient}>
                {children}
            </QueryClientProvider>
        </IntlProvider>
    );
    Wrapper.displayName = 'TestQueryClientWrapper';
    return Wrapper;
};

// The presentations the backend serves today, IPV included (migration 0259).
const dosesPerVial = {
    IPV: [1, 5],
    bOPV: [10, 20],
    mOPV2: [50],
    nOPV2: [20, 50],
};

// The endpoint returns a list of Config rows; the doses live on the first row's `data`.
const apiResponse = [
    {
        created_at: '2025-10-28T11:49:17Z',
        updated_at: '2025-10-29T16:12:45Z',
        key: 'vaccine_doses_per_vial',
        data: dosesPerVial,
    },
];

describe('useGetDosesPerVial', () => {
    beforeEach(() => {
        mockGetRequest.mockReset();
    });

    it('calls the doses per vial endpoint', async () => {
        mockGetRequest.mockResolvedValue(apiResponse);
        const { result } = renderHook(() => useGetDosesPerVial(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));

        expect(mockGetRequest).toHaveBeenCalledWith(
            '/api/polio/vaccine/doses_per_vial/',
        );
    });

    it('returns the doses per vial object from the first config row', async () => {
        mockGetRequest.mockResolvedValue(apiResponse);
        const { result } = renderHook(() => useGetDosesPerVial(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));

        const expected = dosesPerVial;
        const received = result.current.data;
        expect(received).toEqual(expected);
    });

    it('returns the real presentations for each vaccine', async () => {
        mockGetRequest.mockResolvedValue(apiResponse);
        const { result } = renderHook(() => useGetDosesPerVial(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));

        const expectedByVaccine: Record<string, number[]> = {
            IPV: [1, 5],
            bOPV: [10, 20],
            mOPV2: [50],
            nOPV2: [20, 50],
        };
        Object.entries(expectedByVaccine).forEach(([vaccine, expected]) => {
            const received = result.current.data?.[vaccine];
            expect(received).toEqual(expected);
        });
    });

    it('offers no fIPV presentation: fIPV is managed as IPV', async () => {
        mockGetRequest.mockResolvedValue(apiResponse);
        const { result } = renderHook(() => useGetDosesPerVial(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));

        expect(result.current.data).not.toHaveProperty('fIPV');
    });

    it('returns undefined when the endpoint sends nothing', async () => {
        mockGetRequest.mockResolvedValue(undefined);
        const { result } = renderHook(() => useGetDosesPerVial(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isSuccess).toBe(true));

        expect(result.current.data).toBeUndefined();
    });
});
