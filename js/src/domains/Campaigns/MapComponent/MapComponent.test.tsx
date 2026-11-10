import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import tiles from 'Iaso/constants/mapTiles';
import { MapComponent } from './MapComponent';

vi.mock('react-leaflet', () => ({
    MapContainer: ({ children }: { children: React.ReactNode }) => (
        <div data-testid="map-container">{children}</div>
    ),
    TileLayer: ({ url }: { url: string }) => (
        <div data-testid="tile-layer" data-url={url} />
    ),
    GeoJSON: ({ children }: { children?: React.ReactNode }) => (
        <div>{children}</div>
    ),
    Tooltip: ({ children }: { children?: React.ReactNode }) => (
        <div>{children}</div>
    ),
    Pane: ({ children }: { children?: React.ReactNode }) => (
        <div>{children}</div>
    ),
}));

vi.mock('Iaso/utils/map/mapUtils', () => ({
    CloseTooltipOnMoveStart: () => null,
}));

vi.mock(
    '../../../../../../../hat/assets/js/apps/Iaso/components/maps/PaneWithPattern/PaneWithPattern',
    () => ({
        PaneWithPattern: ({ children }: { children?: React.ReactNode }) => (
            <div>{children}</div>
        ),
    }),
);

vi.mock(
    '../../../../../../../hat/assets/js/apps/Iaso/components/maps/tools/CustomZoomControl',
    () => ({
        CustomZoomControl: () => null,
    }),
);

describe('MapComponent tile layer', () => {
    it('uses the single-host OSM tile URL', () => {
        render(<MapComponent name="test-map" makePopup={() => null} />);

        expect(screen.getByTestId('tile-layer')).toHaveAttribute(
            'data-url',
            tiles.osm.url,
        );
        expect(
            screen.getByTestId('tile-layer').getAttribute('data-url'),
        ).not.toContain('{s}');
    });
});
