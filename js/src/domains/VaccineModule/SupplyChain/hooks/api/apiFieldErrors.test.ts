import * as yup from 'yup';

import { PREALERT } from '../../constants';
import {
    apiFieldErrorTest,
    collectSupplyChainFieldErrors,
    mapApiBodyToFormErrors,
} from './apiFieldErrors';

describe('mapApiBodyToFormErrors', () => {
    it('maps a nested list error onto the form row that was sent', () => {
        const errors = mapApiBodyToFormErrors(
            {
                pre_alerts: [
                    {},
                    {
                        po_number: [
                            'A pre-alert with this PO number already exists.',
                        ],
                    },
                ],
            },
            PREALERT,
            [0, 2],
        );

        expect(errors).toEqual({
            'pre_alerts[2].po_number':
                'A pre-alert with this PO number already exists.',
        });
    });

    it('maps a top-level field error when only one row was sent', () => {
        const errors = mapApiBodyToFormErrors(
            {
                po_number: ['A pre-alert with this PO number already exists.'],
            },
            PREALERT,
            [1],
        );

        expect(errors).toEqual({
            'pre_alerts[1].po_number':
                'A pre-alert with this PO number already exists.',
        });
    });

    it('leaves non-field errors off the inputs', () => {
        const errors = mapApiBodyToFormErrors(
            {
                detail: ['You are not allowed to edit the pre-alert with id 4'],
            },
            PREALERT,
            [0],
        );

        expect(errors).toEqual({});
    });
});

describe('collectSupplyChainFieldErrors', () => {
    it('reads field errors only from failed requests', () => {
        const errors = collectSupplyChainFieldErrors({
            pre_alerts: [
                {
                    status: 'fulfilled',
                    value: {
                        status: 201,
                        body: { pre_alerts: [{ id: 1 }] },
                        formIndexes: [0],
                    },
                },
                {
                    status: 'fulfilled',
                    value: {
                        status: 400,
                        body: {
                            pre_alerts: [
                                {
                                    po_number: [
                                        'A pre-alert with this PO number already exists.',
                                    ],
                                },
                            ],
                        },
                        formIndexes: [1],
                    },
                },
            ],
        });

        expect(errors).toEqual({
            'pre_alerts[1].po_number':
                'A pre-alert with this PO number already exists.',
        });
    });
});

describe('apiFieldErrorTest', () => {
    const schemaFor = (errors: Record<string, string>, payload: unknown) =>
        yup.object({
            pre_alerts: yup.array().of(
                yup.object({
                    po_number: yup
                        .string()
                        .nullable()
                        .test(apiFieldErrorTest(errors, payload)),
                }),
            ),
        });

    it('fails the field that still has the rejected value', async () => {
        const payload = {
            pre_alerts: [{ po_number: '141424' }, { po_number: '9001002' }],
        };
        const schema = schemaFor(
            {
                'pre_alerts[0].po_number':
                    'A pre-alert with this PO number already exists.',
            },
            payload,
        );

        await expect(
            schema.validate(payload, { abortEarly: false }),
        ).rejects.toMatchObject({
            inner: [
                expect.objectContaining({
                    path: 'pre_alerts[0].po_number',
                    message: 'A pre-alert with this PO number already exists.',
                }),
            ],
        });
    });

    it('clears the API error once the field value changes', async () => {
        const schema = schemaFor(
            {
                'pre_alerts[0].po_number':
                    'A pre-alert with this PO number already exists.',
            },
            { pre_alerts: [{ po_number: '141424' }] },
        );

        await expect(
            schema.validate({ pre_alerts: [{ po_number: '141425' }] }),
        ).resolves.toEqual({ pre_alerts: [{ po_number: '141425' }] });
    });
});
