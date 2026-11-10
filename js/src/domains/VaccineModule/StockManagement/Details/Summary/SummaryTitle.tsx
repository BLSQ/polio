import React, { FunctionComponent } from 'react';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { Box } from '@mui/material';
import { IconButton } from 'bluesquare-components';
import { DisplayIfUserHasPerm } from '../../../../../../../../../hat/assets/js/apps/Iaso/components/DisplayIfUserHasPerm';

import {
    SUPPLYCHAIN_READ,
    SUPPLYCHAIN_WRITE,
} from '../../../../../constants/permissions';
import { baseUrls } from '../../../../../constants/urls';
import MESSAGES from '../../messages';

const route = `/${baseUrls.vaccineSupplyChain}/page/1/campaign__country/`;

type Props = { title: string; id?: string };
export const SummaryTitle: FunctionComponent<Props> = ({ title, id }) => {
    return (
        <Box>
            <span>{title}</span>
            {id && (
                <DisplayIfUserHasPerm
                    permissions={[SUPPLYCHAIN_READ, SUPPLYCHAIN_WRITE]}
                >
                    <IconButton
                        overrideIcon={OpenInNewIcon}
                        url={`${route}${id}`}
                        target="_blank"
                        tooltipMessage={MESSAGES.seeSupplyChainForCountry}
                    />
                </DisplayIfUserHasPerm>
            )}
        </Box>
    );
};
