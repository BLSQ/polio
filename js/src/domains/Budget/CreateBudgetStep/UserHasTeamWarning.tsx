import React, { FunctionComponent } from 'react';
import Box from '@mui/material/Box/Box';
import Divider from '@mui/material/Divider/Divider';
import Typography from '@mui/material/Typography/Typography';
import { useSafeIntl } from 'bluesquare-components';
import MESSAGES from '../../../constants/messages';

export const UserHasTeamWarning: FunctionComponent = () => {
    const { formatMessage } = useSafeIntl();
    return (
        <>
            <Divider />
            <Box mb={2} mt={2}>
                <Typography style={{ fontWeight: 'bold' }}>
                    {formatMessage(MESSAGES.userNeedsTeam)}
                </Typography>
            </Box>
        </>
    );
};
