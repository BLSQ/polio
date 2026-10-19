import React, { ComponentProps, FunctionComponent } from 'react';
import { useSafeIntl } from 'bluesquare-components';
import { DropdownOptions } from '../../../../../../hat/assets/js/apps/Iaso/types/utils';
import MESSAGES from '../../constants/messages';
import { Select } from './Select';

/** Everything Select needs except what this field fills in itself. */
type Props = Omit<ComponentProps<typeof Select>, 'label' | 'options'>;

export const PaymentField: FunctionComponent<Props> = props => {
    const { formatMessage } = useSafeIntl();
    const PAYMENT = [
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
    ];
    return (
        <Select
            label={formatMessage(MESSAGES.paymentMode)}
            // Select types its options as DropdownOptions<number>, but payment modes are
            // string codes. The values are only passed through to the form, never used as
            // numbers. Widening Select's own prop would touch every other caller.
            options={PAYMENT as unknown as DropdownOptions<number>[]}
            {...props}
        />
    );
};
