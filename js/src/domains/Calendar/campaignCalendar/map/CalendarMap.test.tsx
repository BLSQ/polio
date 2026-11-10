import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import tiles from 'Iaso/constants/mapTiles';
import { CalendarMap } from './CalendarMap';

vi.mock('react-leaflet', () => ({
    MapContainer: ({ children }: { children: React.ReactNode }) => (
        <div data-testid="map-container">{children}</div>
    ),
    TileLayer: ({ url }: { url: string }) => (
        <div data-testid="tile-layer" data-url={url} />
    ),
}));

vi.mock('Iaso/utils/map/mapUtils', () => ({
    CloseTooltipOnMoveStart: () => null,
}));

vi.mock('./CalendarMapContainer', () => ({
    CalendarMapContainer: () => null,
}));

vi.mock('./hooks', () => ({
    useShapes: () => ({ shapes: [], isLoadingShapes: false, roundsDict: {} }),
    useMergedShapes: () => ({
        mergedShapes: [],
        isLoadingMergedShapes: false,
    }),
}));

vi.mock('./utils', () => ({
    makeSelections: () => [],
}));

const renderMap = (isPdf = false) =>
    render(
        <CalendarMap
            params={{} as any}
            campaigns={[]}
            loadingCampaigns={false}
            isPdf={isPdf}
        />,
    );

describe('CalendarMap tile layer (POLIO-2231)', () => {
    it('uses the single-host OSM tile URL', () => {
        renderMap();

        expect(screen.getByTestId('tile-layer')).toHaveAttribute(
            'data-url',
            tiles.osm.url,
        );
    });

    it('never asks leaflet for a sharded {s} subdomain, which would break the PDF export', () => {
        renderMap(true);

        const url = screen.getByTestId('tile-layer').getAttribute('data-url');
        expect(url).not.toContain('{s}');
    });
});
