import React, { FunctionComponent } from 'react';
import Box from '@mui/material/Box/Box';
import Chip from '@mui/material/Chip/Chip';
import Typography from '@mui/material/Typography/Typography';
import { useSafeIntl } from 'bluesquare-components';
import MESSAGES from '../../../../constants/messages';
import { LqasImCampaign } from '../../types';

type Props = {
    campaign?: string;
    data?: Record<string, LqasImCampaign>;
};

export const DistrictsNotFound: FunctionComponent<Props> = ({
    data,
    campaign,
}) => {
    const { formatMessage } = useSafeIntl();
    const districtsNotFound =
        (campaign && data?.[campaign]?.districts_not_found) || [];

    return campaign && districtsNotFound.length > 0 ? (
        <>
            <Typography variant="h6">
                {`${formatMessage(MESSAGES.districtsNotFound)}:`}
            </Typography>
            <Box mt={2}>
                {districtsNotFound.map(d => (
                    <Box mr={1} mb={1} display="inline-block" key={d}>
                        <Chip label={d} variant="outlined" color="secondary" />
                    </Box>
                ))}
            </Box>
        </>
    ) : null;
};
