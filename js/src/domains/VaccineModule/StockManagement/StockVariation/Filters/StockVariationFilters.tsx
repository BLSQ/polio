import React, {
    FunctionComponent,
    useCallback,
    useEffect,
    useMemo,
    useState,
} from 'react';
import { Box, Grid } from '@mui/material';
import { DatePicker, useRedirectTo, useSafeIntl } from 'bluesquare-components';
import { isEqual } from 'lodash';
import InputComponent from '../../../../../../../../../hat/assets/js/apps/Iaso/components/forms/InputComponent';
import { SearchButton } from '../../../../../../../../../hat/assets/js/apps/Iaso/components/SearchButton';
import { DropdownOptions } from '../../../../../../../../../hat/assets/js/apps/Iaso/types/utils';
import { apiDateFormat } from '../../../../../../../../../hat/assets/js/apps/Iaso/utils/dates';
import { baseUrls } from '../../../../../constants/urls';
import { useGetFormARoundNumbers } from '../../hooks/api';
import MESSAGES from '../../messages';
import type {
    DosesPerVialDropdownItem,
    StockVariationFilterKey,
    StockVariationParams,
    StockVariationTab,
} from '../../types';
import {
    StockVariationFilterField,
    stockVariationFilterFields,
    stockVariationPageKeys,
} from '../config';
import { useIncidentOptions } from '../Modals/dropdownOptions';

type Props = {
    params: StockVariationParams;
    tab: StockVariationTab;
    dosesOptions?: DosesPerVialDropdownItem[];
};

type FilterValues = Partial<Record<StockVariationFilterKey, string>>;

const valuesFromParams = (
    fields: StockVariationFilterField[],
    params: StockVariationParams,
): FilterValues =>
    fields.reduce(
        (values, field) => ({
            ...values,
            [field.urlKey]: params[field.urlKey],
        }),
        {},
    );

export const StockVariationFilters: FunctionComponent<Props> = ({
    params,
    tab,
    dosesOptions,
}) => {
    const { formatMessage } = useSafeIntl();
    const redirectTo = useRedirectTo();
    const fields = useMemo(() => stockVariationFilterFields[tab] ?? [], [tab]);
    const pageKey = stockVariationPageKeys[tab];

    const urlValues = useMemo(
        () => valuesFromParams(fields, params),
        [fields, params],
    );
    const [values, setValues] = useState<FilterValues>(urlValues);
    const [hasForbiddenChars, setHasForbiddenChars] = useState(false);

    useEffect(() => {
        setValues(urlValues);
    }, [urlValues]);

    const stockCorrectionOptions = useIncidentOptions(true);
    const formAStatusOptions = useMemo(
        () => [
            {
                label: formatMessage(MESSAGES.form_a_status_received),
                value: 'received',
            },
            {
                label: formatMessage(MESSAGES.form_a_status_temporary),
                value: 'temporary',
            },
        ],
        [formatMessage],
    );
    const dosesPerVialOptions = useMemo(
        () =>
            (dosesOptions ?? []).map(option => ({
                label: `${option.value}`,
                value: `${option.value}`,
            })),
        [dosesOptions],
    );
    const { data: roundNumbers } = useGetFormARoundNumbers(params.id);
    const roundNumberOptions = useMemo(
        () =>
            (roundNumbers ?? []).map(number => ({
                label: `${number}`,
                value: `${number}`,
            })),
        [roundNumbers],
    );

    const getOptions = useCallback(
        (field: StockVariationFilterField): DropdownOptions<string>[] => {
            if (field.optionsKey === 'stockCorrection') {
                return stockCorrectionOptions as DropdownOptions<string>[];
            }
            if (field.optionsKey === 'dosesPerVial') {
                return dosesPerVialOptions;
            }
            if (field.optionsKey === 'roundNumber') {
                return roundNumberOptions;
            }
            return formAStatusOptions;
        },
        [
            dosesPerVialOptions,
            formAStatusOptions,
            roundNumberOptions,
            stockCorrectionOptions,
        ],
    );

    const handleChange = useCallback((keyValue: string, value: unknown) => {
        setValues(current => ({
            ...current,
            [keyValue]: (value as string) || undefined,
        }));
    }, []);

    const handleSearch = useCallback(() => {
        redirectTo(baseUrls.stockVariation, {
            ...params,
            ...values,
            // Filtering with the table on page 5 would otherwise land on an empty page.
            ...(pageKey ? { [pageKey]: '1' } : {}),
        });
    }, [pageKey, params, redirectTo, values]);

    const filtersUpdated = !isEqual(values, urlValues);

    if (fields.length === 0) {
        return null;
    }

    return (
        <Grid container spacing={2}>
            {fields.map(field => (
                <Grid item xs={12} sm={6} md={3} key={field.urlKey}>
                    {field.type === 'date' ? (
                        <Box mt={2}>
                            <DatePicker
                                label={formatMessage(field.label)}
                                currentDate={values[field.urlKey] ?? null}
                                onChange={date =>
                                    handleChange(
                                        field.urlKey,
                                        date
                                            ? date.format(apiDateFormat)
                                            : null,
                                    )
                                }
                                clearable
                                clearMessage={MESSAGES.clear}
                            />
                        </Box>
                    ) : (
                        <InputComponent
                            type={field.type}
                            clearable
                            keyValue={field.urlKey}
                            value={values[field.urlKey] ?? ''}
                            onChange={handleChange}
                            labelString={formatMessage(field.label)}
                            options={
                                field.type === 'select'
                                    ? getOptions(field)
                                    : undefined
                            }
                            onEnterPressed={
                                field.type === 'search'
                                    ? handleSearch
                                    : undefined
                            }
                            blockForbiddenChars={field.type === 'search'}
                            onErrorChange={
                                field.type === 'search'
                                    ? setHasForbiddenChars
                                    : undefined
                            }
                        />
                    )}
                </Grid>
            ))}
            <Grid item xs={12}>
                <Box display="flex" justifyContent="flex-end">
                    <SearchButton
                        disabled={hasForbiddenChars || !filtersUpdated}
                        onSearch={handleSearch}
                    />
                </Box>
            </Grid>
        </Grid>
    );
};
