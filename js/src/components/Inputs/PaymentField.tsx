import React, { ComponentProps, FunctionComponent, useMemo } from 'react';
import { useSafeIntl } from 'bluesquare-components';
import { DropdownOptions } from '../../../../../../hat/assets/js/apps/Iaso/types/utils';
import MESSAGES from '../../constants/messages';
import { Select } from './Select';

/** Everything Select needs except what this field fills in itself. */
type Props = Omit<ComponentProps<typeof Select>, 'label' | 'options'>;

export const PaymentField: FunctionComponent<Props> = props => {
    const { formatMessage } = useSafeIntl();
    const payment: DropdownOptions<string>[] = useMemo(
        () => [
            {
                value: 'DIRECT',
                label: 'Direct',
            },
            {
                value: 'DFC',
                label: 'DFC',
            },
            {
                value: 'MOBILE_PAYMENT',
                label: formatMessage(MESSAGES.mobilePayment),
            },
        ],
        [formatMessage],
    );
    return (
        <Select
            label={formatMessage(MESSAGES.paymentMode)}
            options={payment}
            {...props}
        />
    );
};
