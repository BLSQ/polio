import { get, isEqual } from 'lodash';
import { TestConfig, TestContext } from 'yup';

import { PREALERT, VAR, VRF } from '../../constants';
import { ParsedSettledPromise } from '../../types';

type TestContextWithOriginal = TestContext & {
    originalValue: unknown;
};

const SKIPPED_ERROR_KEYS = new Set([
    'non_field_errors',
    'detail',
    'message',
    'status',
    'statusText',
    'url',
    'body',
    'ok',
    'formIndexes',
]);

const messageFromValue = (value: unknown): string | undefined => {
    if (typeof value === 'string' && value.trim()) {
        return value.trim();
    }
    if (
        Array.isArray(value) &&
        value.every(
            item => typeof item === 'string' || typeof item === 'number',
        )
    ) {
        const text = value
            .map(item => `${item}`.trim())
            .filter(Boolean)
            .join(', ');
        return text || undefined;
    }
    return undefined;
};

/**
 * Same rule as useAPIErrorValidator: keep the API message while the field
 * still has the value that was rejected. Paths are full Formik paths
 * (`pre_alerts[1].po_number`) because this form saves one tab at a time and
 * the API index is the index inside that create/update batch, not the form.
 */
export const apiFieldErrorTest = (
    errors: Record<string, string>,
    payload: unknown,
): TestConfig => ({
    name: 'api-field-error',
    test: (value, rawContext) => {
        const context = rawContext as TestContextWithOriginal;
        const message = errors[context.path];
        if (!message) {
            return true;
        }
        const submitted = get(payload, context.path);
        const current = context.originalValue ?? value;
        if (isEqual(current, submitted)) {
            return context.createError({
                path: context.path,
                message,
            });
        }
        return true;
    },
});

export const responseFailed = (item?: {
    status?: string;
    value?: { status?: number };
}): boolean => {
    if (!item) {
        return false;
    }
    if (item.status === 'rejected') {
        return true;
    }
    const httpStatus = item.value?.status;
    return typeof httpStatus === 'number' && httpStatus >= 400;
};

export const settledRequestsFailed = (
    items?: Array<{ status?: string; value?: { status?: number } }>,
): boolean => Boolean(items?.some(responseFailed));

export const mapApiBodyToFormErrors = (
    body: unknown,
    listKey: typeof PREALERT | typeof VAR,
    formIndexes: number[],
): Record<string, string> => {
    if (!body || typeof body !== 'object' || Array.isArray(body)) {
        return {};
    }
    const record = body as Record<string, unknown>;
    const errors: Record<string, string> = {};
    const nested = record[listKey];

    if (Array.isArray(nested)) {
        nested.forEach((item, requestIndex) => {
            const formIndex = formIndexes[requestIndex];
            if (
                formIndex === undefined ||
                !item ||
                typeof item !== 'object' ||
                Array.isArray(item)
            ) {
                return;
            }
            Object.entries(item as Record<string, unknown>).forEach(
                ([field, value]) => {
                    if (SKIPPED_ERROR_KEYS.has(field)) {
                        return;
                    }
                    const text = messageFromValue(value);
                    if (text) {
                        errors[`${listKey}[${formIndex}].${field}`] = text;
                    }
                },
            );
        });
    }

    if (formIndexes.length === 1 && Object.keys(errors).length === 0) {
        Object.entries(record).forEach(([field, value]) => {
            if (SKIPPED_ERROR_KEYS.has(field) || field === listKey) {
                return;
            }
            const text = messageFromValue(value);
            if (text) {
                errors[`${listKey}[${formIndexes[0]}].${field}`] = text;
            }
        });
    }

    return errors;
};

export const fieldErrorsFromSettled = (
    data: ParsedSettledPromise<any>[] | undefined,
    listKey: typeof PREALERT | typeof VAR,
): Record<string, string> => {
    if (!data) {
        return {};
    }
    return data.reduce<Record<string, string>>((acc, item) => {
        if (!responseFailed(item)) {
            return acc;
        }
        const body = item.value?.body ?? item.value;
        const formIndexes = item.value?.formIndexes ?? [];
        return {
            ...acc,
            ...mapApiBodyToFormErrors(body, listKey, formIndexes),
        };
    }, {});
};

export const vrfFieldErrorsFromSettled = (
    data: ParsedSettledPromise<any>[] | undefined,
): Record<string, string> => {
    if (!data) {
        return {};
    }
    return data.reduce<Record<string, string>>((acc, item) => {
        if (!responseFailed(item)) {
            return acc;
        }
        const body = item.value?.body ?? item.value;
        if (!body || typeof body !== 'object' || Array.isArray(body)) {
            return acc;
        }
        Object.entries(body as Record<string, unknown>).forEach(
            ([field, value]) => {
                if (SKIPPED_ERROR_KEYS.has(field)) {
                    return;
                }
                const text = messageFromValue(value);
                if (text) {
                    acc[`${VRF}.${field}`] = text;
                }
            },
        );
        return acc;
    }, {});
};

export const collectSupplyChainFieldErrors = (data?: {
    pre_alerts?: ParsedSettledPromise<any>[];
    arrival_reports?: ParsedSettledPromise<any>[];
    vrf?: ParsedSettledPromise<any>[];
}): Record<string, string> => ({
    ...fieldErrorsFromSettled(data?.pre_alerts, PREALERT),
    ...fieldErrorsFromSettled(data?.arrival_reports, VAR),
    ...vrfFieldErrorsFromSettled(data?.vrf),
});

export const supplyChainSaveFailed = (data?: {
    pre_alerts?: ParsedSettledPromise<any>[];
    arrival_reports?: ParsedSettledPromise<any>[];
    vrf?: ParsedSettledPromise<any>[];
}): boolean =>
    settledRequestsFailed(data?.pre_alerts) ||
    settledRequestsFailed(data?.arrival_reports) ||
    settledRequestsFailed(data?.vrf);
