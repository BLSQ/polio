import React, { FunctionComponent } from 'react';
import { defineMessages } from 'react-intl';

import InputComponent from '../../../../../hat/assets/js/apps/Iaso/components/forms/InputComponent';
import { userHasOneOfPermissions } from '../../../../../hat/assets/js/apps/Iaso/domains/users/utils';
import { useCurrentUser } from '../../../../../hat/assets/js/apps/Iaso/utils/usersUtils';

import { POLIO, POLIO_ADMIN } from '../constants/permissions';

const MESSAGES = defineMessages({
    blockOfCountries: {
        defaultMessage: 'Block of countries',
        id: 'iaso.groups.blockOfCountries',
    },
});

type FieldState = {
    value?: boolean;
    errors?: string[];
};

type Props = {
    values: Record<string, FieldState>;
    onChange: (fieldName: string, fieldValue: boolean) => void;
};

export const BlockOfCountriesField: FunctionComponent<Props> = ({
    values,
    onChange,
}) => {
    const currentUser = useCurrentUser();
    if (!userHasOneOfPermissions([POLIO, POLIO_ADMIN], currentUser)) {
        return null;
    }
    const field = values.block_of_countries;
    return (
        <InputComponent
            keyValue="block_of_countries"
            value={field?.value}
            onChange={onChange}
            type="checkbox"
            errors={field?.errors ?? []}
            label={MESSAGES.blockOfCountries}
        />
    );
};

BlockOfCountriesField.displayName = 'BlockOfCountriesField';
