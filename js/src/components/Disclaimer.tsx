import React, { FC } from 'react';
import Typography from '@mui/material/Typography/Typography';
import { useSafeIntl } from 'bluesquare-components';
import MESSAGES from '../constants/messages';

export const Disclaimer: FC = () => {
    const { formatMessage } = useSafeIntl();
    return (
        <Typography color="secondary" sx={{ fontSize: '11px' }}>
            {formatMessage(MESSAGES.disclaimer)}
        </Typography>
    );
};
