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
import { useGetFormARoundNumbers } from '../hooks/useGetFormARoundNumbers';
import { useIncidentOptions } from '../Modals/dropdownOptions';

type Props = {
    params: StockVariationParams;
    tab: StockVariationTab;
    dosesOptions?: DosesPerVialDropdownItem[];
};

type FilterValues = Partial<Record<StockVariationFilterKey, string>>;

const COLUMN_COUNT = 4;

const toColumns = (
    fields: StockVariationFilterField[],
): StockVariationFilterField[][] => {
    const columns: StockVariationFilterField[][] = Array.from(
        { length: COLUMN_COUNT },
        () => [],
    );
    fields.forEach((field, index) => {
        columns[index % COLUMN_COUNT].push(field);
    });
    return columns;
};

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
    const columns = useMemo(() => toColumns(fields), [fields]);
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
            ...(pageKey ? { [pageKey]: '1' } : {}),
        });
    }, [pageKey, params, redirectTo, values]);

    const filtersUpdated = !isEqual(values, urlValues);

    if (fields.length === 0) {
        return null;
    }

    const renderField = (field: StockVariationFilterField) =>
        field.type === 'date' ? (
            <Box mt={2} key={field.urlKey}>
                <DatePicker
                    label={formatMessage(field.label)}
                    currentDate={values[field.urlKey] ?? null}
                    onChange={date =>
                        handleChange(
                            field.urlKey,
                            date ? date.format(apiDateFormat) : null,
                        )
                    }
                    clearable
                    clearMessage={MESSAGES.clear}
                />
            </Box>
        ) : (
            <InputComponent
                key={field.urlKey}
                type={field.type}
                clearable
                keyValue={field.urlKey}
                value={values[field.urlKey] ?? ''}
                onChange={handleChange}
                labelString={formatMessage(field.label)}
                options={
                    field.type === 'select' ? getOptions(field) : undefined
                }
                onEnterPressed={
                    field.type === 'search' ? handleSearch : undefined
                }
                blockForbiddenChars={field.type === 'search'}
                onErrorChange={
                    field.type === 'search' ? setHasForbiddenChars : undefined
                }
            />
        );

    return (
        <Grid container spacing={2}>
            {columns.map((column, index) => (
                // eslint-disable-next-line react/no-array-index-key
                <Grid item xs={12} md={3} key={`filter-column-${index}`}>
                    {column.map(renderField)}
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
