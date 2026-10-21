import { useMemo } from 'react';
import { useSafeIntl } from 'bluesquare-components';
import * as yup from 'yup';
import { TestConfig } from 'yup';

import MESSAGES from '../messages';
import { apiFieldErrorTest } from './api/apiFieldErrors';

yup.addMethod(
    yup.mixed,
    'isNumbersArrayString',
    function isNumbersArrayString(formatMessage) {
        return this.test('isNumbersArrayString', '', (value, context) => {
            const { path, createError } = context;
            let errorMessage;
            if (value) {
                const regexp = /^\d*$/;

                const valuesArray = Array.isArray(value)
                    ? value
                    : value
                          .split(',')
                          .map((v: string | number) => `${v}`.trim());
                const hasOtherChar = valuesArray.some(v => !regexp.test(v));
                if (hasOtherChar) {
                    errorMessage = formatMessage(MESSAGES.lotNumberError);
                }
            }

            if (errorMessage) {
                return createError({
                    path,
                    message: errorMessage,
                });
            }
            return true;
        });
    },
);
yup.addMethod(
    yup.string,
    'PONumberHasNoPrefix',
    function PONumberHasNoPrefix(formatMessage) {
        return this.test('PONumberHasNoPrefix', '', (value, context) => {
            const { path, createError } = context;
            let errorMessage;
            if (value) {
                if (Number.isNaN(parseInt(value.charAt(0), 10))) {
                    errorMessage = formatMessage(MESSAGES.PoNumberNoPrefix);
                }
            }

            if (errorMessage) {
                return createError({
                    path,
                    message: errorMessage,
                });
            }
            return true;
        });
    },
);

yup.addMethod(
    yup.string,
    'hasUniquePONumber',
    function hasUniquePONumber(formatMessage, dictKey) {
        return this.test('hasUniquePONumber', '', (value, context) => {
            // @ts-ignore
            const { path, createError, from: parents } = context;
            const pathIndex = parseInt(path.split('[')[1].split(']')[0], 10);
            const siblingsPONumbers = parents
                .filter(parent => Object.keys(parent.value).includes(dictKey))
                .map(parent => parent.value[dictKey])
                .flat()
                .filter((_parent, index) => {
                    return pathIndex !== index;
                })
                .map(sibling => sibling.po_number);

            let errorMessage;
            if (value && siblingsPONumbers.includes(value)) {
                errorMessage = formatMessage(MESSAGES.uniquePoNumberWarning);
            }
            if (errorMessage) {
                return createError({
                    path,
                    message: errorMessage,
                });
            }
            return true;
        });
    },
);

const useVrfShape = (apiErrorTest: TestConfig) => {
    const { formatMessage } = useSafeIntl();
    const withApiError = <T extends yup.AnySchema>(schema: T): T =>
        schema.test(apiErrorTest) as T;
    return yup.object().shape({
        id: withApiError(yup.string().nullable()),
        country: withApiError(
            yup
                .number()
                .required(formatMessage(MESSAGES.requiredField))
                .nullable()
                .min(0, formatMessage(MESSAGES.positiveInteger))
                .integer()
                .typeError(formatMessage(MESSAGES.positiveInteger)),
        ),
        campaign: withApiError(
            yup
                .string()
                .required(formatMessage(MESSAGES.requiredField))
                .nullable(),
        ),
        vaccine_type: withApiError(
            yup
                .string()
                .required(formatMessage(MESSAGES.requiredField))
                .nullable(),
        ),
        rounds: withApiError(
            yup
                .mixed()
                .nullable()
                .required(formatMessage(MESSAGES.requiredField)),
        ),
        date_vrf_signature: withApiError(
            yup
                .date()
                .typeError(formatMessage(MESSAGES.invalidDate))
                .nullable(),
        ),
        quantities_ordered_in_doses: withApiError(
            yup
                .number()
                .nullable()
                .min(0, formatMessage(MESSAGES.positiveInteger))
                .integer()
                .typeError(formatMessage(MESSAGES.positiveInteger)),
        ),
        wastage_rate_used_on_vrf: withApiError(
            yup
                .number()
                .nullable()
                .min(0, formatMessage(MESSAGES.positiveNumber)),
        ),
        date_vrf_reception: withApiError(
            yup
                .date()
                .typeError(formatMessage(MESSAGES.invalidDate))
                .nullable(),
        ),
        date_vrf_submission_to_orpg: withApiError(
            yup
                .date()
                .typeError(formatMessage(MESSAGES.invalidDate))
                .nullable(),
        ),
        quantities_approved_by_orpg_in_doses: withApiError(
            yup
                .number()
                .nullable()
                .min(0, formatMessage(MESSAGES.positiveInteger))
                .integer()
                .typeError(formatMessage(MESSAGES.positiveInteger)),
        ),
        date_rrt_orpg_approval: withApiError(
            yup
                .date()
                .typeError(formatMessage(MESSAGES.invalidDate))
                .nullable(),
        ),
        date_vrf_submitted_to_dg: withApiError(
            yup
                .date()
                .typeError(formatMessage(MESSAGES.invalidDate))
                .nullable(),
        ),
        quantities_approved_by_dg_in_doses: withApiError(
            yup
                .number()
                .nullable()
                .min(0, formatMessage(MESSAGES.positiveInteger))
                .integer()
                .typeError(formatMessage(MESSAGES.positiveInteger)),
        ),
        date_dg_approval: withApiError(
            yup
                .date()
                .typeError(formatMessage(MESSAGES.invalidDate))
                .nullable(),
        ),
        target_population: withApiError(
            yup
                .number()
                .nullable()
                .min(0, formatMessage(MESSAGES.positiveInteger))
                .integer()
                .typeError(formatMessage(MESSAGES.positiveInteger)),
        ),
        comments: withApiError(yup.string().nullable()),
        document: withApiError(yup.mixed().nullable()),
    });
};

const usePreAlertShape = (apiErrorTest: TestConfig) => {
    const { formatMessage } = useSafeIntl();
    const withApiError = <T extends yup.AnySchema>(schema: T): T =>
        schema.test(apiErrorTest) as T;
    return yup.object().shape({
        date_pre_alert_reception: withApiError(
            yup
                .date()
                .required(formatMessage(MESSAGES.requiredField))
                .typeError(formatMessage(MESSAGES.invalidDate))
                .nullable(),
        ),
        po_number: withApiError(
            yup
                .string()
                .nullable()
                // @ts-ignore
                .PONumberHasNoPrefix(formatMessage)
                // @ts-ignore
                .hasUniquePONumber(formatMessage, 'pre_alerts')
                .required(formatMessage(MESSAGES.requiredField)),
        ),
        estimated_arrival_time: withApiError(
            yup
                .date()
                .typeError(formatMessage(MESSAGES.invalidDate))
                .nullable(),
        ),
        doses_shipped: withApiError(
            yup
                .number()
                .nullable()
                .required(formatMessage(MESSAGES.requiredField))
                .min(0, formatMessage(MESSAGES.positiveInteger))
                .integer()
                .typeError(formatMessage(MESSAGES.positiveInteger)),
        ),
        doses_per_vial: withApiError(
            yup
                .number()
                .nullable()
                .min(0, formatMessage(MESSAGES.positiveInteger))
                .integer()
                .typeError(formatMessage(MESSAGES.positiveInteger)),
        ),
        vials_shipped: withApiError(yup.number().nullable()),
        file: withApiError(yup.mixed().nullable()),
    });
};
const useArrivalReportShape = (apiErrorTest: TestConfig) => {
    const { formatMessage } = useSafeIntl();
    const withApiError = <T extends yup.AnySchema>(schema: T): T =>
        schema.test(apiErrorTest) as T;
    return yup.object().shape({
        arrival_report_date: withApiError(
            yup
                .date()
                .required(formatMessage(MESSAGES.requiredField))
                .typeError(formatMessage(MESSAGES.invalidDate))
                .nullable(),
        ),
        po_number: withApiError(
            yup
                .string()
                .nullable()
                // @ts-ignore
                .PONumberHasNoPrefix(formatMessage)
                // @ts-ignore
                .hasUniquePONumber(formatMessage, 'arrival_reports')
                .required(formatMessage(MESSAGES.requiredField)),
        ),
        doses_per_vial: withApiError(
            yup
                .number()
                .nullable()
                .min(0, formatMessage(MESSAGES.positiveInteger))
                .integer()
                .typeError(formatMessage(MESSAGES.positiveInteger)),
        ),
        doses_shipped: withApiError(
            yup
                .number()
                .nullable()
                .required(formatMessage(MESSAGES.requiredField))
                .min(0, formatMessage(MESSAGES.positiveInteger))
                .integer()
                .typeError(formatMessage(MESSAGES.positiveInteger)),
        ),
        doses_received: withApiError(
            yup
                .number()
                .nullable()
                .required(formatMessage(MESSAGES.requiredField))
                .min(0, formatMessage(MESSAGES.positiveInteger))
                .integer()
                .typeError(formatMessage(MESSAGES.positiveInteger)),
        ),
        vials_shipped: withApiError(yup.number().nullable()),
        vials_received: withApiError(yup.number().nullable()),
    });
};

export const useSupplyChainFormValidator = (
    apiErrors: Record<string, string> = {},
    apiPayload?: unknown,
) => {
    const apiErrorTest = useMemo(
        () => apiFieldErrorTest(apiErrors, apiPayload),
        [apiErrors, apiPayload],
    );
    const vrf = useVrfShape(apiErrorTest);
    const preAlert = usePreAlertShape(apiErrorTest);
    const arrivalReport = useArrivalReportShape(apiErrorTest);
    return useMemo(() => {
        return yup.object().shape({
            vrf,
            pre_alerts: yup.array().of(preAlert),
            arrival_reports: yup.array().of(arrivalReport),
        });
    }, [vrf, preAlert, arrivalReport]);
};
