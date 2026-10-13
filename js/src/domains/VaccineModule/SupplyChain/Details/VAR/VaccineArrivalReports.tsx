import React, { FunctionComponent, useCallback } from 'react';
import { useFormikContext } from 'formik';
import { userHasOneOfPermissions } from '../../../../../../../../../hat/assets/js/apps/Iaso/domains/users/utils';
import { useCurrentUser } from '../../../../../../../../../hat/assets/js/apps/Iaso/utils/usersUtils';
import {
    SUPPLYCHAIN_READ,
    SUPPLYCHAIN_WRITE,
} from '../../../../../constants/permissions';
import { VAR } from '../../constants';
import MESSAGES from '../../messages';
import {
    MultiFormTab,
    useDosesPerVialDropDownForVaccine,
    useEmptyArrivalReport,
} from '../shared';
import { VaccineArrivalReport } from './VaccineArrivalReport';

type Props = { className?: string; items?: any[] };

export const VaccineArrivalReports: FunctionComponent<Props> = ({
    className,
    items = [],
}) => {
    const { values, setFieldValue } = useFormikContext<any>();
    const vaccine = values.vrf?.vaccine_type;
    const dosesPerVaccineOptions = useDosesPerVialDropDownForVaccine(vaccine);
    const emptyArrivalReport = useEmptyArrivalReport(dosesPerVaccineOptions);
    const onClick = useCallback(() => {
        setFieldValue(VAR, [...values[VAR], emptyArrivalReport]);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [setFieldValue, values, vaccine, emptyArrivalReport]);

    const currentUser = useCurrentUser();
    const theMessage = userHasOneOfPermissions(
        [SUPPLYCHAIN_READ, SUPPLYCHAIN_WRITE],
        currentUser,
    )
        ? MESSAGES.addVar
        : null;

    return (
        <MultiFormTab
            className={className}
            titleMessage={MESSAGES.varsTitle}
            buttonMessage={theMessage}
            onClick={onClick}
        >
            {items.map((item, index) => {
                return (
                    <VaccineArrivalReport
                        index={index}
                        key={`vaccine-report-${item?.id ?? item?.po_number ?? index}`}
                        dosesForVaccineOptions={dosesPerVaccineOptions}
                    />
                );
            })}
        </MultiFormTab>
    );
};
