import domtoimage from 'dom-to-image';
import {
    afterAll,
    afterEach,
    beforeAll,
    describe,
    expect,
    it,
    vi,
} from 'vitest';
import tiles from 'Iaso/constants/mapTiles';

const DEPRECATED_SHARDED_TEMPLATE =
    'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

const SERVED_HOSTNAME = 'tile.openstreetmap.org';

// Leaflet substitutes one of its `subdomains` (a, b, c by default) for {s} and the tile coordinates
// for {z}/{x}/{y} before requesting the image.
const expandTileTemplate = (template: string): string =>
    template
        .replace('{s}', 'a')
        .replace('{z}', '6')
        .replace('{x}', '32')
        .replace('{y}', '21');

class OpenStreetMapPolicyXhr {
    static requestedUrls: string[] = [];

    readyState = 0;

    status = 0;

    response: Blob | null = null;

    responseType = '';

    timeout = 0;

    onreadystatechange: (() => void) | null = null;

    ontimeout: (() => void) | null = null;

    private url = '';

    open(_method: string, url: string): void {
        this.url = url;
    }

    send(): void {
        OpenStreetMapPolicyXhr.requestedUrls.push(this.url);
        if (new URL(this.url).hostname === SERVED_HOSTNAME) {
            this.status = 200;
            this.response = new Blob(['png-bytes'], { type: 'image/png' });
        } else {
            // Nothing answers on the retired subdomains, which is what the browser reports to XHR
            // as status 0 (the symptom in the ticket).
            this.status = 0;
            this.response = null;
        }
        this.readyState = 4;
        this.onreadystatechange?.();
    }
}

const originalSrcDescriptor = Object.getOwnPropertyDescriptor(
    HTMLImageElement.prototype,
    'src',
);

// An image whose bytes could not be fetched is inlined as a payload-less data URI: a blank tile.
const EMPTY_PNG_DATA_URI = 'data:image/png;base64,';

const inlineImages = (tileUrl: string) => {
    const container = document.createElement('div');
    const image = document.createElement('img');
    image.src = tileUrl;
    container.appendChild(image);
    // `impl` is dom-to-image's own test seam: the exact step dom-to-pdf runs on the cloned DOM.
    const inlineAll = (domtoimage as any).impl.images.inlineAll as (
        node: Node,
    ) => Promise<unknown>;
    return { image, inlined: inlineAll(container) };
};

describe('calendar PDF export, image inlining of OSM tiles', () => {
    const consoleError = vi.spyOn(console, 'error');

    beforeAll(() => {
        consoleError.mockImplementation(() => undefined);
        Object.defineProperty(HTMLImageElement.prototype, 'src', {
            configurable: true,
            get(): string {
                return this.getAttribute('src') ?? '';
            },
            set(value: string) {
                this.setAttribute('src', value);
                queueMicrotask(() => this.dispatchEvent(new Event('load')));
            },
        });
        vi.stubGlobal('XMLHttpRequest', OpenStreetMapPolicyXhr);
    });

    afterEach(() => {
        OpenStreetMapPolicyXhr.requestedUrls = [];
        consoleError.mockClear();
    });

    afterAll(() => {
        consoleError.mockRestore();
        if (originalSrcDescriptor) {
            Object.defineProperty(
                HTMLImageElement.prototype,
                'src',
                originalSrcDescriptor,
            );
        }
        vi.unstubAllGlobals();
    });

    it('loses the tile on the sharded URL the maps used to ship, with the status 0', async () => {
        const tileUrl = expandTileTemplate(DEPRECATED_SHARDED_TEMPLATE);

        const { image, inlined } = inlineImages(tileUrl);
        await inlined;

        expect(OpenStreetMapPolicyXhr.requestedUrls).toEqual([tileUrl]);
        expect(consoleError).toHaveBeenCalledWith(
            `cannot fetch resource: ${tileUrl}, status: 0`,
        );
        // No bytes behind the data URI: this is the blank map in the exported PDF.
        expect(image.src).toBe(EMPTY_PNG_DATA_URI);
    });

    it('keeps the tile on the URL the maps ship now', async () => {
        const tileUrl = expandTileTemplate(tiles.osm.url);

        const { image, inlined } = inlineImages(tileUrl);
        await inlined;

        expect(OpenStreetMapPolicyXhr.requestedUrls).toEqual([tileUrl]);
        expect(consoleError).not.toHaveBeenCalled();
        // Inlined with its bytes, so the tile is in the PDF and is not refetched while rendering.
        expect(image.src.startsWith(EMPTY_PNG_DATA_URI)).toBe(true);
        expect(image.src.length).toBeGreaterThan(EMPTY_PNG_DATA_URI.length);
    });

    it('keeps every tile of a multi-tile map inlinable', async () => {
        const container = document.createElement('div');
        [
            { x: '32', y: '21' },
            { x: '33', y: '21' },
            { x: '32', y: '22' },
        ].forEach(({ x, y }) => {
            const image = document.createElement('img');
            image.src = tiles.osm.url
                .replace('{z}', '6')
                .replace('{x}', x)
                .replace('{y}', y);
            container.appendChild(image);
        });

        await (domtoimage as any).impl.images.inlineAll(container);

        expect(OpenStreetMapPolicyXhr.requestedUrls).toHaveLength(3);
        expect(consoleError).not.toHaveBeenCalled();
        Array.from(container.querySelectorAll('img')).forEach(image => {
            expect(image.src.length).toBeGreaterThan(EMPTY_PNG_DATA_URI.length);
        });
    });

    it('does not request any retired tile subdomain', () => {
        expect(tiles.osm.url).not.toContain('{s}');
        expect(new URL(expandTileTemplate(tiles.osm.url)).hostname).toBe(
            SERVED_HOSTNAME,
        );
    });
});
